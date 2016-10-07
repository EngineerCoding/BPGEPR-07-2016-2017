import urllib

def main():
    """
    m_dict_reactions_prot = contains all reaction numbers
    m_reactions_prot = list that saves all reactions per enzyme
    m_final_output = dictionary with geneID as key and reactions (m_reactions_prot) as values
    m_geneid_list = list of all geneids (from ncbi) """
    m_geneid_list = ['102381974', '102383435']
    m_dict_reactions_prots = reaction_number(m_geneid_list)
    m_final_output = {}
    m_reactions_prot = []
    for x in range(len(m_geneid_list)):
        m_list_reactions = m_dict_reactions_prots.get(m_geneid_list[x])
        m_reactions_prot = reaction(m_list_reactions, m_geneid_list[x])
        m_final_output.update({m_geneid_list[x]: m_reactions_prot})
    print(m_final_output)

    
def reaction(r_list_reactions, r_geneid):
    """
    Every page that is linked to a reaction number will be opened through this function
    
    r_list_reactions = list with all reaction numbers 
    r_htmlfile = link to the Kegg reaction page
    r_reaction = string
    r_all = list containing all reactions of a specific enzyme"""
    r_all = [] 
    for r in range(len(r_list_reactions)):
        r_htmlfile = urllib.urlopen("http://www.genome.jp/dbget-bin/www_bget?rn:"+ \
                                    str(r_list_reactions[r]))
        r_htmltext = r_htmlfile.read()
        print "loading reaction", str(r+1), "of protein", str(r_geneid)
        r_reaction = find_reaction(r_htmltext)
        r_reaction = r_reaction.replace("&lt;", "<")
        r_all.append(r_reaction)
    return r_all
        
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
        rn_htmltext = rn_htmlfile.read()
        rn_list_reactions = search_reactionnr(rn_htmltext)
        for i in range(len(rn_list_reactions)):
            rn_dict_reactions.update({rn_geneid_list[x]: rn_list_reactions})
            
    return rn_dict_reactions
        
def find_reaction(fr_htmltext):
    """
    Everytime there is a '<' symbol ( while there is no tag)
    fr_sentence will be filled with characters (fr_char).
    If fr_sentence is filled with a specific sequence of chars, a tag will
    be made. In the function get_reaction a decision will be made: wether or
    not the output equals the reaction (fr_output). In the function
    get_exceptions the same decision will be made for the exceptions (fr_sn).

    """
    fr_sentence = ""
    fr_reaction = ""
    fr_tag = 0
    fr_found =0
    fr_sn = 0  # search number
    for fr_char in fr_htmltext:
        if fr_char == "<" and fr_tag == 0:
            fr_sentence = ""
        else :
            fr_sentence += fr_char
        if fr_sentence == 'div style="width:555px;overflow-x:auto;overflow-y:hidden">' :  
            fr_tag = 1 # wordt getagd omdat het de potentie heeft om een reactie te bevatten
        if fr_found != 3:
            fr_tag, fr_reaction, fr_found, fr_sn = get_reaction(fr_char, fr_tag, fr_reaction,
                                                                fr_found, fr_sn)
            fr_reaction, fr_sn, fr_found = get_exceptions(fr_sn, fr_char, fr_found, fr_reaction)
    return fr_reaction

def get_exceptions(ge_sn, ge_char, ge_found, ge_reaction):
    """
    This function takes every character from the reaction. And puts it in
    a list called ge_reaction. This function is used to collect all
    reactions that start off with a number instead of a letter.
   
    
    ge_reaction = string thats filled up with chars once the reaction
       found.
    ge_sn = if g_sn is equal to one. It means that the reaction is
        an exception. ge_sn becomes 3 to prevent the the function from
        collecting irrelevant data.
    ge_char = character in text
    ge_found = indicates wether or not the the reaction is found already,
        becomes 2 to prevent the the function from collecting irrelevant data.
    """
    if ge_sn == 1:
        if ge_char == "<" :
            ge_sn = 3
        else :
            if len(ge_reaction) == 4 and ((ge_reaction[2] == "-" or \
                                        ge_reaction[3] == "-") or \
                                        (ge_reaction[2] == " " or \
                                        ge_reaction[3] == " ")):
                ge_found = 3                
            ge_reaction += ge_char
    return ge_reaction, ge_sn, ge_found

def get_reaction(gr_char, gr_tag, gr_reaction, gr_found, gr_sn):
    """
    This function takes every character from the reaction. And puts it in
    a list called gr_reaction
    
    gr_reaction = string thats filled up with chars once the reaction
       found.
    gr_found = indicates wether or not the the reaction is found already
    gr_char = character in text
    """
    if gr_tag > 0 and gr_found == 0:
        gr_tag += 1
        gr_tag, gr_found, gr_sn = tag_check(gr_char, gr_tag, gr_found, gr_sn)
    if gr_found == 1 :
        if gr_char == "<" :
            gr_found = 3
        else :
            gr_reaction += gr_char
    return gr_tag, gr_reaction, gr_found, gr_sn

def tag_check(tc_char, tc_tag, tc_found, tc_sn):
    """
    Checks if the third character (tc_tag = 3) is a string. When that is the
    case tc_found will get a value of one. When tc_found is 1 it means that
    the reaction is found. Otherwise tc_sn will get a value of one. Tc_sn
    is an indicator that basically tells the script to search
    for a number (in case the Kegg reaction starts with a number instead of
    a string).

    
    tc_tag = indicates when text is tagged
    tc_char = character in text
    tc_found = indicates if the reaction if found
    tc_sn = indicator (sn = search number)
    """
    if (tc_tag == 3) and tc_char.isalpha() == 1:
        if tc_found != 3:
            tc_found = 1
        tc_tag = 0
    elif (tc_tag == 3) and tc_char.isalpha() == 0:
        if tc_sn != 2 :
            tc_sn = 1
        tc_tag = 0
    return tc_tag, tc_found, tc_sn

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
        

main()



