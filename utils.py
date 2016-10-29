from json import loads
try:
    import urllib.request as urllib
except ImportError:
    import urllib


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
    line = lines.readline()
    while line:
        if isinstance(line, bytes):
            line = line.decode()
        line = line.strip()
        if line.startswith(starting):
            return line[len(starting):].lstrip()
        line = lines.readline()
    return ""


def convert_gi_to_asn(protein_code):
    """ Does the API call to retrieve the ASN code for the protein code.

    Arguments:
        protein_code - string or int. The protein code which the API needs
        to convert to an ASN code.
    Returns:
        When available, the asn code.
    """
    connection = urllib.urlopen(
        'https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestAp'
        'i.json?method=db2db&input=ginumber&inputValues={}&outputs=kegggeneid&'
        'format=row'.format(str(protein_code)))
    # Only read the first line
    json = loads(connection.read().decode())
    connection.close()
    return json[0]['KEGG Gene ID']
