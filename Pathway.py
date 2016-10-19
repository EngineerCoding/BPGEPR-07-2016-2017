try:
    import urllib.request as urllib
except ImportError:
    import urllib
from re import split


def get_line(lines, starting):
    """ Reads lines until it hits the starting string. Note that the read
    line is being stripped, meaning that putting whitespace in the starting
    string would be redundant.

    Arguments:
        lines - File like object. A file like (or url) object which can be iterated through
        for lines.
        starting - string. The string which the line should start with.
    Returns:
        The line which starts with the line. If not available it will return
        an empty string.
    """
    for line in lines:
        line = line.decode().strip()
        if line.startswith(starting):
            return line[len(starting):].lstrip()
    return ""


def get_asn_for_gene(protein_code):
    """ Does the API call to retrieve the ASN code for the protein code.

    Arguments:
        protein_code - string or int. The protein code which the API needs
        to convert to an ASN code.
    Returns:
        When available, the asn code.
    """
    connection = urllib.urlopen(
        'http://rest.kegg.jp/find/genes/' + str(protein_code))
    # Only read the first line
    line = connection.readline().decode()
    connection.close()
    return split('\s+', line)[0]


def get_pathways(asncode):
    """ Retrieves all the asn codes for the pathway which the gene asn code
    contains.

    Parameters:
        asncode - string. This is the asn code which is retrieved by the
        get_asn_for_gene function.
    Returns:
        A list of pathway asn codes.
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
    # Close the connection
    connection.close()
    return pathways


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


def get_data_from_pathway(asn_pathway_code):
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


def main():
    eiwit_codes = ['102381974', '102383435']
    for protein_code in eiwit_codes:
        asn_code = get_asn_for_gene(protein_code)
        pathways = get_pathways(asn_code)
        pathway_data = {}
        for pathway in pathways:
            pathway_data[pathway] = get_data_from_pathway(pathway)
        print(json.dumps(pathway_data, sort_keys=True, indent=4))


main()
