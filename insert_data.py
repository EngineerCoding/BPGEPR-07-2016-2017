import psycopg2
from os import system
from csv import reader

from location_parser import parse_location, ComplementLocation, JoinedLocation
from pathway_pfam import get_pathway_pfam_data
from protein_reaction import get_reaction_data
from utils import get_line, convert_gi_to_asn

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen


def prep_inserting():
    system('bash deelopdracht\\ B.sh')
    # Execute CREATE statements
    pass


def get_accession_dictionaries():
    """ Generates 3 dictionaries:
    1. accession to genecode
    2. accession to proteincode
    3. genecode to proteincode
    For this, it uses two files which are generated in the method
    prep_inserting():
    1. outputs/genecodes
    2. outputs/proteincodes

    Returns:
        3 dictionaries in a tuple:
            1. accession to genecode
            2. accession to proteincode
            3. genecode to proteincode
    """
    # Generate an accession - genecode dict
    acc_genecode = {}
    with open('outputs/genecodes', 'r') as file:
        for row in reader(file, delimiter=' '):
            acc_genecode[row[0]] = row[1]
    # Generate an accession - protein dict
    acc_proteincode = {}
    with open('outputs/proteincodes', 'r') as file:
        for row in reader(file, delimiter=' '):
            acc_proteincode[row[0]] = row[1]
    # Merge the dictionaries so a dictionary genecode - proteincodes gets
    # created
    genecode_proteincode = {}
    for acc in acc_genecode:
        genecode_proteincode[acc_genecode[acc]] = acc_proteincode[acc]
    return acc_genecode, acc_proteincode, genecode_proteincode


def get_gi_kegg_dictionary(proteincodes):
    proteincode2kegg = {proteincode: convert_gi_to_asn(proteincode)
                        for proteincode in proteincodes}
    # Find keys which contain '-' as value
    del_keys = []
    for proteincode in proteincode2kegg:
        if proteincode2kegg[proteincode] == '-':
            del_keys.append(proteincode)
    # Delete the keys
    for key in del_keys:
        del proteincode2kegg[key]
    return proteincode2kegg


def insert_data(cursor, table, lst_data):
    """ Inserts data based on the table name and a list of
    dictionaries which represent a row which should be 
    inserted.

    Parameters:
        cursor - Cursor object. The connection cursor which executes
        the query
        table - string. The table name to insert into.
        lst_data - list. This list should contain dictionaries which
        represent a row with the correct columns.
    Return:
        Nothing.
    """
    query = 'INSERT INTO {} ({}) VALUES ({});'
    for query_data in lst_data:
        # Create lists with the column names and values
        columns = []
        values = []
        for column in query_data:
            columns.append(column)
            values.append(query_data[column])
        # Generate the columns string for the query
        columns = ", ".join(columns)
        # Generate the values string for the query
        holders = ', '.join(['%s' for _ in range(len(values))])
        cursor.execute(query.format(table, columns, holders), values)


def read_sequence(file):
    """ Reads a sequence from a file, specifically the ORIGIN.
    Parameters:
        file - File object.
    Returns:
        When the origin has been found, the string of the sequence. Otherwise,
        an empty string.
    """
    get_line(file, 'ORIGIN')
    sequence = ''
    line = file.readline()
    while line and not line.startswith('//'):
        sequence += ''.join(line.strip().split()[1:])
        line = file.readline()
    return sequence


def get_exon_rows(location, genecode):
    """ Returns a list of dictionaries which represent rows in the database.
    These still need to be inserted, but the Gen_07 table must be filled in
    first.

    Parameters:
        location - string. A string representing the location of the CDS
        genecode - string. The genecode where this location is for
    Returns:
        A list of dictionaries.
    """
    location = parse_location(location)
    # Check if it is a complement location
    is_complement_location = isinstance(location, ComplementLocation)
    table_data = []
    # The base data is always the same
    base_dict = dict(gen_id=genecode, complement=is_complement_location)
    if isinstance(location, JoinedLocation):
        # Multiple entries in the exon table for this exon
        for begin, end in location.get_ranges():
            base_dict['start_positie'] = begin
            base_dict['eind_positie'] = end
            # Only append new instances of a dictionary
            table_data.append(dict(base_dict))
    else:
        # Single entry for this exon
        start, end = location.get_range()
        base_dict['start_positie'] = start
        base_dict['eind_positie'] = end
        table_data.append(base_dict)
    return table_data


def insert_gene_exon(cursor, accesion_genecode):
    """ Inserts the Gen_07 and Exon_07 tables with information they require

    Parameters:
        cursor - Cursor object. The cursor object which executes queries.
        accesion_genecode - dictionary. The accession - genecode dictionary
        generated by get_accession_dictionaries()
    Returns:
        Nothing
    """
    # First insert the literal gene information
    gene_data = []
    exon_data = []
    for accession in accesion_genecode:
        row = dict(accession_code=accession,
                   gen_id=accesion_genecode[accession])
        # Read data from the nucleotide genbank file such as, name,
        # exon location and sequence.
        path = 'protein_genbank_files/{}.gb'.format(accession)
        with open(path, 'r') as genbank:
            # Get the gene name
            definition_line = get_line(genbank, 'DEFINITION')
            line = genbank.readline()
            while not line.startswith('ACCESSION'):
                definition_line += ' ' + line.strip()
                line = genbank.readline()
            row['gen_naam'] = definition_line
            exon_line = get_line(genbank, 'CDS')
            if exon_line:
                exon_data.extend(get_exon_rows(exon_line, row['gen_id']))
            # Read until ORIGIN
            row['gen_sequentie'] = read_sequence(genbank).upper()
        gene_data.append(row)
    # Insert data into Gen_07 and Exon_07
    insert_data(cursor, 'Gen_07', gene_data)
    insert_data(cursor, 'Exon_07', exon_data)


def insert_protein(cursor, accession_genecode, genecode_proteincode):
    """ Inserts data to the Eiwit_07 table.
    Parameters:
        cursor - Cursor object. The cursor object which executes queries.
        accession_genecode - dictionary. The accession to genecode dictionary
        generated by get_accession_dictionaries()
        genecode_proteincode - dictionary. The genecode to proteincode
        dictionary generated by get_accession_dictionaries()
    Returns:
        Nothing
    """
    # First map proteincode to its name
    protein_names = {}
    with open('outputs/proteincodes', 'r') as file:
        for row in reader(file, delimiter=' '):
            proteincode = row[1]
            del row[1], row[0]
            protein_names[proteincode] = ' '.join(row)
    # Reverse genecode_accession
    gene_accession = {accession_genecode[k]: k for k in accession_genecode}
    # Generate the table data
    table_data = []
    for genecode in genecode_proteincode:
        proteincode = genecode_proteincode[genecode]
        # If no proteincode is available, don't add it to the database
        if proteincode == '-':
            continue
        row = dict(eiwit_id=proteincode, gen_id=genecode,
                   eiwit_naam=protein_names[proteincode])
        # Retrieve the sequence
        path = 'protein_genbank_files/{}.gb'.format(gene_accession[genecode])
        with open(path, 'r') as genbank:
            sequence = get_line(genbank, '/translation="')
            while sequence[-1] != '"':
                sequence += genbank.readline().strip()
            row['eiwit_sequentie'] = sequence[:-1]
        table_data.append(row)
    insert_data(cursor, 'Eiwit_07', table_data)


def insert_protein_reactions(cursor, proteincode_kegg):
    reaction_data = get_reaction_data(proteincode_kegg)
    print(reaction_data)


def create_formatted_pathway_data(pathway, id, path_data, stored_authors,
                                  author_data, ref_author_links,
                                  ref_data):
    """ Creates a row for the pathway, reference and author. This function
    should only be called when a new pathway is encountered, since this
    function does not check for duplicate pathways. All formatted data is
    appended to lists or dictionaries passed to this function.

    Parameters:
        pathway - dictionary. The pathway dictionary which contains the
        information about this pathway.
        id - string. The pathway id.
        path_data - list. This list is the actual data of the pathway which
        is eventually used with insert_data and thus contains rows.
        stored_authors - list. A list of authors which already are in a row.
        author_data - list. This list is the actual data of the authors which
        is eventually used with insert_data and thus contains rows.
        ref_author_links - dictionary. The dictionary which contains the
        information which reference links to which author.
        ref_data - list. This list is the actual data of the references which
        is eventually used with insert_data and thus contains rows.
    Returns:
        nothing
    """
    path_data.append({'class': pathway['class'],
                      'pathway_naam': pathway['name'], 'pathway_id': id})
    for pub in pathway['publications']:
        ref_data.append({'referentie_id': pub['id'], 'pathway_id': id,
                         'titel': pub['title'], 'journal': pub['journal']})
        ref_author_links[pub['id']] = []
        for author in pub['authors']:
            if author not in stored_authors:
                stored_authors.append(author)
                author_data.append({'auteur_naam': author})
            ref_author_links[pub['id']].append(stored_authors.index(author))


def insert_reference_author_junction(cursor, ref_author_links):
    """ This function inserts the data of the junction table
    'ReferentieAuteur_07'. The SERIAL primary key is starting from 1 and thus
    reliable to make a connection from.

    Parameters:
        cursor - Cursor object. The cursor to execute queries from.
        ref_author_links - dictionary. The dictionary which contains the
        information which reference links to which author.
    """
    reference_author_data = []
    for ref in ref_author_links:
        for author_id in ref_author_links[ref]:
            # Create a row for the junction table
            reference_author_data.append({'auteur_id': author_id + 1,
                                          'referentie_id': ref})
    insert_data(cursor, 'ReferentieAuteur_07', reference_author_data)


def insert_domain(cursor, pfam):
    """ Inserts all the data for the domain table in the database. Also
    inserts the associated junction table with it.

    Parameters:
        cursor - Cursor object. The cursor to execute queries from.
        pfam - dictionary. The dictionary containing all the pfam data which
        is retrieved by get_pathway_pfam_data.
    Returns:
        Nothing
    """
    junction_data, domain_data, domain_indices = [], [], []
    for protein_code in pfam:
        for domain in pfam[protein_code]:
            if domain in domain_indices:
                # Only a junction row entry has to be made
                junction_data.append({'eiwit_id': protein_code,
                                      'domein_id': (domain_indices
                                                    .index(domain) + 1)})
                continue
            domain_indices.append(domain)
            # Create new domain row
            d = pfam[protein_code][domain]
            domain_row = {'domein_naam': domain,
                          'gem_domein_lengte': d['av_length'],
                          'gem_alignment_coverage': d['percentage_identity'],
                          'gem_sequentie_coverage': d['av_coverage']}
            domain_data.append(domain_row)
            # Create the junction row
            junction_data.append({'eiwit_id': protein_code,
                                  'domein_id': len(domain_indices)})
    # Insert the actual data to tables
    insert_data(cursor, 'Domein_07', domain_data)
    insert_data(cursor, 'EiwitDomein_07', junction_data)


def insert_pathway_domains(cursor, proteincode_kegg):
    """ This is the main function of retrieving data for the pathway branch
    of the database and insert it into this database. The script pathway_pfam
    is responsible for retrieving all raw data for the pathway and pfam
    (domains).

    Parameters:
        cursor - Cursor object. The Cursor object to execute queries on.
        proteincode_kegg - dictionary. This is the dictionary which has
        proteincodes as keys and the kegg asn's as values.
    Returns:
        Nothing
    """
    # Retrieve the actual data
    pathway, pfam = get_pathway_pfam_data(proteincode_kegg)
    # Insert domain info
    insert_domain(cursor, pfam)
    # Insert the pathways, reference and the authors
    stored_pathways, stored_authors, pathway_data = [], [], []
    author_data, reference_data = [], []
    reference_author_links, protein_links = {}, {}
    for protein_code in pathway:
        # If no pathways are available, the algorithm will not work
        if len(pathway[protein_code]) == 0:
            continue
        # Make a link with the protein code to the pathway id
        for pathwaycode in pathway[protein_code]:
            protein_links[protein_code] = pathwaycode
            # If not stored yet, create an entry
            if pathwaycode not in stored_pathways:
                create_formatted_pathway_data(
                    pathway[protein_code][pathwaycode], pathwaycode,
                    pathway_data, stored_authors, author_data,
                    reference_author_links, reference_data)
                stored_pathways.append(pathwaycode)
    # Insert all the data
    insert_data(cursor, 'Pathway_07', pathway_data)
    # Use correct format for the protein - pathway junction table
    insert_data(cursor, 'EiwitPathway_07',
                [{'eiwit_id': k, 'pathway_id': protein_links[k]} for k in
                 protein_links])
    insert_data(cursor, 'Referentie_07', reference_data)
    insert_data(cursor, 'Auteur_07', author_data)
    insert_reference_author_junction(cursor, reference_author_links)


def main():
    prep_inserting()
    genecode, proteincode, genecode2proteincode = get_accession_dictionaries()
    proteincode2kegg = get_gi_kegg_dictionary([code for code in 
                                               proteincode.values()])
    connection = psycopg2.connect(host="localhost", dbname="postgres",
                                  user="postgres", password="MyPassword")
    cursor = connection.cursor()
    insert_gene_exon(cursor, genecode)
    insert_protein(cursor, genecode, genecode2proteincode)
    connection.commit()
    insert_protein_reactions(cursor, proteincode2kegg)
    insert_pathway_domains(cursor, proteincode2kegg)
    connection.commit()
    connection.close()


main()
