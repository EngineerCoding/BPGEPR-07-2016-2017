try:
    import urllib.request as urllib
except ImportError:
    import urllib
from re import split, search
from utils import get_line
from collections import OrderedDict


def get_pathways_pfams(asncode):
    """ Retrieves all the asn codes for the pathway which the gene asn code
    contains. At the same time, it will retrieve the pfam families of this
    gene.

    Parameters:
        asncode - string. This is the asn code which is retrieved by the
        get_asn_for_gene function.
    Returns:
        A list of pathway asn codes, and a list of pfam families.
    """
    # Do the API call
    connection = urllib.urlopen('http://rest.kegg.jp/get/' + asncode)
    pathways = []
    # Read until the line
    pathway_line = get_line(connection, 'PATHWAY')
    # Read while an asn code is available (mutliple are)
    while pathway_line.startswith('asn'):
        pathways.append(split('\s+', pathway_line)[0])
        pathway_line = connection.readline().decode().strip()
    # Retrieve the pfam families if available
    pfams = []
    pfam_string = get_line(connection, 'MOTIF')
    if pfam_string:
        # Check if the line starts with Pfam, otherwise these are not Pfam
        # families
        if pfam_string.startswith('Pfam:'):
            pfams = split('\s+', pfam_string[5:].lstrip())
    # Close the connection
    connection.close()
    return pathways, pfams


def get_authors_list(connection):
    """ Reads the next AUTHORS line and collects all authors which are
    associated with the publication.

    Parameters:
        connection - A file-like object. Usually this will be a connection
        to the KEGG API.
    Returns:
        A list with author names
    """
    authors = get_line(connection, 'AUTHORS')
    authors_list = authors.split(',')
    for i in range(len(authors_list)):
        authors_list[i] = authors_list[i].strip()
        if authors_list[i][-1] == '.':
            authors_list[i] = authors_list[i][:-1]
    return authors_list


def get_pathway_data(asn_pathway_code):
    """ Retrieves all the data of the pathway such as name, class and all the
     publications that are available on this pathway. This includes the
     publication information such as title, journal, reference and authors.

     Parameters:
         asn_pathway_code - string. The asn code that is retrieved by te
         get_pathways function.
     Returns:
         A dictionary with the collected information.
    """
    connection = urllib.urlopen(
        'http://rest.kegg.jp/get/path:' + asn_pathway_code)
    # Collect the general data of the pathway
    collected_data = {'name': get_line(connection, 'NAME'),
                      'class': get_line(connection, 'CLASS'),
                      'publications': []}
    # Read all the publications if available
    reference_line = get_line(connection, 'REFERENCE')
    while reference_line:
        # Retrieves the complete authors list
        publication = dict(authors=get_authors_list(connection))
        # Retrieves other information about the publications
        publication['title'] = get_line(connection, 'TITLE')
        publication['journal'] = get_line(connection, 'JOURNAL')
        publication['id'] = reference_line.split(':')[1]
        collected_data['publications'].append(publication)
        reference_line = get_line(connection, 'REFERENCE')
    connection.close()
    return collected_data


def get_pfam_data(pfam):
    """ Retrieves the average domain length, identity percentage and average
    coverage of the domain from the PFAM api.

    Parameters:
        pfam - string.
    Returns:
        A dictionary with the following keys:
            - av_length (average domain length)
            - percentage_identity
            - av_coverage (average coverage)
    """
    # Read the xml
    connection = urllib.urlopen('http://pfam.xfam.org/family/{}?output=xml'
                                .format(pfam))
    xml = connection.read().decode()
    connection.close()
    # Get the data
    pfam_data = {}
    matching_pattern = '<{0}>([-+]?\d*\.\d+|\d+)</{0}>'
    for tag in ['av_length', 'percentage_identity', 'av_coverage']:
        pfam_data[tag] = search(matching_pattern.format(tag), xml).group(1)
        if '.' in pfam_data[tag]:
            pfam_data[tag] = float(pfam_data[tag])
        else:
            pfam_data[tag] = int(pfam_data[tag])
    return pfam_data


def get_pathway_pfam_data(proteincode_kegg):
    """ Downloads all the data and stores this for the pathway and domain
    data. This is done in an efficient way: a file is only downloaded once
    and reused which reduses the execution time of the complete script since
    there is less to be downloaded.

    Parameters:
        proteincode_kegg - dictionary. The dictionary containing proteincodes
        as keys and kegg asn numbers as values.
    Return:
        pathway - dictionary. The key represents the asn code for the pathway
        and the value is another dictionary with the name, class and
        publications.
        pathway_links - dictionary. The key represents a proteincode and the
        values are the asn codes for the pathways.
        domains - dictionary. The key represents the name of a domain and the
        values are dictionaries with the information associated with that
        domain.
        domain_links - dictionary. The key represents the proteincode and the
        value is the correct index to the correct domain in the database.
    """
    stored_pathways, stored_domains = [], []
    pathway, domains = {}, OrderedDict()
    pathway_links, domain_links = {}, {}
    # handle each protein code
    for protein_code in proteincode_kegg:
        pathway_list, pfam_list = get_pathways_pfams(
            proteincode_kegg[protein_code])
        # Handle pathway data
        pathway_links[protein_code] = pathway_list
        for pcode in pathway_list:
            if pcode not in stored_pathways:
                pathway[pcode] = get_pathway_data(pcode)
                stored_pathways.append(pcode)
        # Handle Pfam data
        domain_links[protein_code] = []
        for pfam in pfam_list:
            if pfam not in stored_domains:
                stored_domains.append(pfam)
                domains[pfam] = get_pfam_data(pfam)
                domain_links[protein_code].append(len(stored_domains))
            else:
                domain_links[protein_code].append(stored_domains.index(pfam)
                                                  + 1)
    return pathway, pathway_links, domains, domain_links
