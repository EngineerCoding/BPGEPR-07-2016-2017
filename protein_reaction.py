try:
    import urllib.request as urllib
except ImportError:
    import urllib
from re import split
from utils import get_line


def reaction_number(proteincode_kegg):
    """ Every kegg proteincode will be used to find all reaction
    numbers by parsing a HTML file. This HTML file contains the R codes
    specific for the protein.

    Parameters:
        proteincode_kegg - dictionary. A dictionary with proteincodes
        as keys and kegg proteincodes as values.
    Returns:
        A dictionary containing proteincodes as keys and as values
        there will be a list with Rcodes.
    """
    dict_reactions = {}
    for proteincode in proteincode_kegg:
        html_file = urllib.urlopen("http://www.genome.jp/dbget-bin/get_linkdb?"
                                   "-t+reaction+" +
                                   proteincode_kegg[proteincode])
        html_text = html_file.read().decode()
        html_file.close()
        list_reactions = search_reaction_nr(html_text)
        for i in range(len(list_reactions)):
            dict_reactions[proteincode] = list_reactions
    return dict_reactions


def search_reaction_nr(html_text):
    """ This function actually searches for the reaction number and
    collects them.

    Parameters:
        html_text - string. The text of the HTML file which contains
        Rcodes.
    Returns:
        A list of reaction numbers which can be used in the KEGG API.
    """
    tag = False
    collection = ""
    all_reactions = []
    reaction_nr = ""
    for char in html_text:
        if char == '>' and not tag:
            collection = ""
        else:
            collection += char
        if collection == 'R' and not tag:
            tag = True
        tag, reaction_nr, all_reactions = tag_reaction_nr(char, tag,
                                                          all_reactions,
                                                          reaction_nr)
    return all_reactions


def tag_reaction_nr(char, tag, all_reactions, reaction_nr):
    """ Whenever a specific part in the html code is tagged
    (tag = True), add all of the following characters (char) to the
    string reaction_nr.

    Parameters:
        tag - boolean. Indicates when text is tagged.
        char - string. Character in text.
        reaction_nr - string. Contains the reaction number.
        all_reactions - list. Contains all reaction numbers.
    Returns:
        tag - boolean.
        reaction_nr - string.
        all_reactions - list.
    """
    if tag:
        if char != "<":
            reaction_nr += char
        else:
            all_reactions.append(reaction_nr)
            reaction_nr = ""
            tag = False
    return tag, reaction_nr, all_reactions


def get_reaction_data(proteincode_kegg):
    """ This is the main function which handles all functions in this
    file. It takes a dictionary with proteincodes and KEGG proteincodes
    and converts this in a dictionary with proteincodes linked to the
    reaction and a dictionary with the actual reaction data.

    Parameters:
        proteincode_kegg - dictionary. A dictionary with proteincodes
        as keys and KEGG proteincodes as values.
    Returns:
        1. A dictionary with proteincodes as keys and reaction codes as
        values. This represents the linkage between proteins and
        reactions.
        2. A dictionary with rcodes as keys and a dictionary with
        'reaction', 'ec' and 'id' as keys and thus contains the
        information for the reactions.
    """
    proteincodes_rcodes = reaction_number(proteincode_kegg)
    proteincode_reaction = {}
    reaction = {}
    for proteincode in proteincodes_rcodes:
        proteincode_reaction[proteincode] = []
        # Get all reactions for this code
        for rcode in proteincodes_rcodes[proteincode]:
            if rcode not in reaction:
                kegg_api = urllib.urlopen("http://rest.kegg.jp/get/reaction:{}"
                                          .format(rcode))
                reaction_line = get_line(kegg_api, 'DEFINITION')
                ec = split('\s+', get_line(kegg_api, 'ENZYME'))
                kegg_api.close()
                reaction[rcode] = dict(reaction=reaction_line, ec=ec, id=rcode)
            if proteincode not in proteincode_reaction:
                proteincode_reaction[proteincode] = []
            proteincode_reaction[proteincode].append(rcode)
    return proteincode_reaction, reaction
