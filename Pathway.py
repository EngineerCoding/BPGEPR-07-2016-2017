try:
    import urllib.request as urllib
except ImportError:
    import urllib
import json
from re import split


def get_line(lines, starting):
    for line in lines:
        line = line.decode().strip()
        if line.startswith(starting):
            return line[len(starting):].lstrip()
    return ""


def get_asn_for_gene(protein_code):
    connection = urllib.urlopen(
        'http://rest.kegg.jp/find/genes/' + str(protein_code))
    # Only read the first line
    line = connection.readline().decode()
    connection.close()
    return split('\s+', line)[0]


def get_pathways(asncode):
    connection = urllib.urlopen('http://rest.kegg.jp/get/' + asncode)
    pathways = []
    pathway_line = get_line(connection, 'PATHWAY')
    while pathway_line.startswith('asn'):
        pathways.append(split('\s+', pathway_line)[0])
        pathway_line = connection.readline().decode().strip()
    connection.close()
    return pathways


def get_authors_list(connection):
    authors = get_line(connection, 'AUTHORS')
    authors_list = authors.split(',')
    for i in range(len(authors_list)):
        authors_list[i] = authors_list[i].strip()
        if authors_list[i][-1] == '.':
            authors_list[i] = authors_list[i][:-1]
    return authors_list


def get_data_from_pathway(asn_pathway_code):
    connection = urllib.urlopen(
        'http://rest.kegg.jp/get/path:' + asn_pathway_code)
    collected_data = {'name': get_line(connection, 'NAME'),
                      'class': get_line(connection, 'CLASS'),
                      'publications': []}
    reference_line = get_line(connection, 'REFERENCE')
    while reference_line:
        publication = dict(authors=get_authors_list(connection))
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
