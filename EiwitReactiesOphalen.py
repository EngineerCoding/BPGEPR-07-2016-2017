import urllib
from re import split
        
        
def reaction_number(rn_geneid_list):
    """
    Every geneId in the rn_geneid_list will be used to find all of the
    reactions.

    rn_dict_reactions = dictionary with geneID as key and all of the reaction
    numbers(rn_list_reactions) as a value.
    rn_htmlfile = link to KEGG page that contains all of the reactions per enzyme
    """
    rn_dict_reactions = {} 
    for x in range(len(rn_geneid_list)):
        rn_htmlfile = urllib.urlopen("http://www.genome.jp/dbget-bin/get_linkdb?-t+reaction+asn:" + str(rn_geneid_list[x]))
        rn_htmltext = rn_htmlfile.read().decode()
        rn_list_reactions = search_reactionnr(rn_htmltext)
        for i in range(len(rn_list_reactions)):
            rn_dict_reactions.update({rn_geneid_list[x]: rn_list_reactions})
    return rn_dict_reactions


def search_reactionnr(sr_htmltext):
    sr_tag = 0
    sr_collection = ""
    sr_all_reactions = []
    sr_reaction_nr = ""
    for sr_kar in sr_htmltext:
        if sr_kar == '>' and sr_tag == 0:
            sr_collection = ""
        else :
            sr_collection += sr_kar
        if sr_collection == 'R' and sr_tag == 0:
            sr_tag = 1
        sr_tag, sr_reaction_nr, sr_all_reactions = tag_reactionnr(sr_kar, sr_tag,
                                                        sr_all_reactions, sr_reaction_nr)
    return sr_all_reactions


def tag_reactionnr(tr_char, tr_tag, tr_all_reactions, tr_reaction_nr):
    """
    Whenever a specific part in the html code is tagged (tr_tag = 1), add 
    all of the following characters ( tr_char) to the string tr_reaction_nr.

    tr_tag = indicates when text is tagged
    tr_char = character in text
    tr_reaction_nr = string containg reactionnumber
    tr_all_reactions = contains all reaction numbers
    """
    if tr_tag == 1 :
        if tr_char != "<" :
            tr_reaction_nr += tr_char
        else :
            tr_all_reactions.append(tr_reaction_nr)
            tr_reaction_nr = ""
            tr_tag = 0
    return tr_tag, tr_reaction_nr, tr_all_reactions 


def get_line(lines, starting):
    for line in lines:
        line = line.strip()
        if line.startswith(starting):
            return line[len(starting):].lstrip()
    return ""


def main():
    """
    m_dict_reactions_prot = contains all reaction numbers
    m_reactions_prot = list that saves all reactions per enzyme
    m_final_output = dictionary with geneID as key and reactions (m_reactions_prot) as values
    m_geneid_list = list of all geneids (from ncbi) """
    m_geneid_list = ['102381974', '102383435']
    gene_code_rcodes = reaction_number(m_geneid_list)
    gene_code_reaction = {}
    for genecode in gene_code_rcodes:
        gene_code_reaction[genecode] = {}
        for rcode in gene_code_rcodes[genecode]:
            kegg_api = urllib.urlopen("http://rest.kegg.jp/get/reaction:{}"
                                      .format(rcode))
            contents = kegg_api.read().decode().split('\n')
            gene_code_reaction[genecode]['reaction'] = get_line(contents, 
                                                                'DEFINITION')
            ec = split('\s+', get_line(contents, 'ENZYME'))
            gene_code_reaction[genecode]['ec'] = ec
    print(gene_code_reaction)


main()

