#!/usr/python
import psycopg2
from os import system, mkdir
from csv import reader

from location_parser import parse_location, ComplementLocation, JoinedLocation
from utils import get_line

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen


def prep_inserting():
    system('bash deelopdracht\\ B.sh')
    # Execute CREATE statements


def get_accession_dictionaries():
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
        holders = ', '.join(['%s' for a in range(len(values))])
        cursor.execute(query.format(table, columns, holders), values)


def read_sequence(file):
    get_line(file, 'ORIGIN')
    sequence = ''
    line = file.readline()
    while line and not line.startswith('//'):
        sequence += ''.join(line.strip().split()[1:])
        line = file.readline()
    return sequence


def get_exon_rows(cursor, location, genecode):
    location = parse_location(location)
    is_complement_location = isinstance(location, ComplementLocation)
    table_data = []
    base_dict = dict(gen_id=genecode, complement=is_complement_location)
    if isinstance(location, JoinedLocation):
        for begin, end in location.get_ranges():
            base_dict['start_positie'] = begin
            base_dict['eind_positie'] = end
            # Only append new instances of a dictionary
            table_data.append(dict(base_dict))
    else:
        start, end = location.get_range()
        base_dict['start_positie'] = start
        base_dict['eind_positie'] = end
        table_data.append(base_dict)
    return table_data


def insert_gene_exon(cursor, accesion_genecode):
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
            # Strip off the first part

            row['gen_naam'] = definition_line
            exon_line = get_line(genbank, 'CDS')
            if exon_line:
                exon_data.extend(get_exon_rows(cursor, exon_line,
                                               row['gen_id']))
            # Read until ORIGIN
            row['gen_sequentie'] = read_sequence(genbank)
        gene_data.append(row)
    insert_data(cursor, 'Gen_07', gene_data)
    insert_data(cursor, 'Exon_07', exon_data)


def insert_protein(cursor, accession_genecode, genecode_proteincode):
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
        if proteincode == '-':
            continue
        row = dict(eiwit_id=proteincode, gen_id=genecode,
                   eiwit_naam=protein_names[proteincode])
        # Retrieve the sequence
        path = 'protein_genbank_files/{}.gb'.format(gene_accession[genecode])
        with open(path, 'r') as genbank:
            row['eiwit_sequentie'] = read_sequence(genbank)
        table_data.append(row)
    insert_data(cursor, 'Eiwit_07', table_data)


def insert_protein_reactions(cursor):
    pass


def insert_pathway_domains(cursor):
    pass


def main():
    prep_inserting()
    genecode, proteincode, genecode2proteincode = get_accession_dictionaries()
    connection = psycopg2.connect(host="localhost", dbname="dbname",
                                  user="postgres", password="BiOLaB15")
    cursor = connection.cursor()
    insert_gene_exon(cursor, genecode)
    insert_protein(cursor, genecode, genecode2proteincode)
    insert_protein_reactions(cursor)
    insert_pathway_domains(cursor)
    connection.commit()
    connection.close()
