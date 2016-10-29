try:
    import urllib.request as urllib
except ImportError:
    import urllib
from re import split
from utils import get_line


def reaction_number(proteincode_kegg):
    """
    Every geneId in the geneid_list will be used to find all of the
    reactions.

    proteincode_kegg = dictionary which contains the protein to kegg asn code
    values.
    htmlfile = link to KEGG page that contains all of the reactions per enzyme
    """
    dict_reactions = {}
    for proteincode in proteincode_kegg:
        htmlfile = urllib.urlopen("http://www.genome.jp/dbget-bin/get_linkdb?"
                                  "-t+reaction+"
                                  + proteincode_kegg[proteincode])
        htmltext = htmlfile.read().decode()
        htmlfile.close()
        list_reactions = search_reactionnr(htmltext)
        for i in range(len(list_reactions)):
            dict_reactions.update({proteincode: list_reactions})
    return dict_reactions


def search_reactionnr(htmltext):
    """ Searches for the reaction numbers in the html text

    Parameters:
        htmltext - string.
    Returns:
        A list of reaction numbers which can be used in the KEGG API.
    """
    tag = 0
    collection = ""
    all_reactions = []
    reaction_nr = ""
    for char in htmltext:
        if char == '>' and tag == 0:
            collection = ""
        else:
            collection += char
        if collection == 'R' and tag == 0:
            tag = 1
        tag, reaction_nr, all_reactions = tag_reactionnr(char, tag,
                                                         all_reactions,
                                                         reaction_nr)
    return all_reactions


def tag_reactionnr(char, tag, all_reactions, reaction_nr):
    """
    Whenever a specific part in the html code is tagged (tag = 1), add
    all of the following characters ( char) to the string reaction_nr.

    tag = indicates when text is tagged
    char = character in text
    reaction_nr = string containg reactionnumber
    all_reactions = contains all reaction numbers
    """
    if tag == 1:
        if char != "<":
            reaction_nr += char
        else:
            all_reactions.append(reaction_nr)
            reaction_nr = ""
            tag = 0
    return tag, reaction_nr, all_reactions


def get_reaction_data(gene_codes):
    # Get reaction R codes
    gene_code_rcodes = reaction_number(gene_codes)
    gene_code_reaction = {}
    for genecode in gene_code_rcodes:
        gene_code_reaction[genecode] = []
        # Get all reactions for this cdoe
        for rcode in gene_code_rcodes[genecode]:
            kegg_api = urllib.urlopen("http://rest.kegg.jp/get/reaction:{}"
                                      .format(rcode))
            reaction = get_line(kegg_api, 'DEFINITION')
            ec = split('\s+', get_line(kegg_api, 'ENZYME'))
            kegg_api.close()
            gene_code_reaction[genecode].append(dict(reaction=reaction, ec=ec,
                                                     id=rcode))
    return gene_code_reaction
