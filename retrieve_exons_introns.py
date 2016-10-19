from os import system, mkdir
from csv import reader
from genbankparser.genbank_parser import GenbankParser
from genbankparser.location_parser import JoinedLocation, ComplementLocation
# Be python2 compatible
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen


def download_nucleotide_genbank_files():
    """ Downloads all the required Genbank Files to get and saves those files
     by their accession numbers in the folder nucleotide_genbank_files. For
     this the genecodes must be known, and is being read from the
     outputs/genecodes file.
     At the same time a dictionary is created with accession string as keys
     and the associated genecode as value.

     Returns:
         A dictionary with accession number as keys and genecodes as values.
    """
    genecode_accession_dict = {}
    mkdir("nucleotide_genbank_files")
    # Open the genecodes file for use as csv
    with open('outputs/genecodes', 'r') as csvfile:
        # Genecodes file looks like:
        # <accession> <genecode> <etc.>
        # So it is a CSV file except that the delimiter is not a comma but a
        # space. Why reinvent the wheel while there is already a solution?
        for row in reader(csvfile, delimiter=' '):
            # Download the file
            request = urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
                              'efetch.fcgi?db=nucleotide&id={}&rettype=gb'
                              .format(row[1]))
            filename = 'nucleotide_genbank_files/{}.gb'.format(row[0])
            # Write to the file as we read
            with open(filename, 'w') as file:
                file.write(request.read().decode())
            request.close()
            genecode_accession_dict[row[0]] = row[1]
    return genecode_accession_dict


def find_cds_feature(features):
    """ Finds the CDS part which has the actual location of our gene.

    Arguments:
        features - iterable. An iterable containing Feature object.
    Returns:
        When the CDS feature has been found, this feature. If not, None.
    """
    for feature in features:
        if feature.name == 'CDS':
            return feature
    # Return None, is not needed implicitly


def calc_total_len(locations, sequence):
    """ Calculates the total length of all the locations.

    Parameters:
        locations - iterable. An iterable containing Location objects.
        sequence - A sequence object which determines how the location is
        placed exactly.
    Returns:
        The amount of locations and the total lenght of locations.
    """
    total_length = 0
    for location in locations:
        total_length += len(sequence.get_sequence_from_location(location))    
    return len(locations), total_length


def extract_information(features, sequence):
    """ Actually has the algorithm to generate the amount of exons and the
    total length of these exons. Same goes for the introns.

    Parameters:
        features - iterable. An iterable containing Feature objects.
        sequence - A sequence object.
    Returns:
        A dictionary with the keys:
            - exons
            - exons_length
            - introns
            - introns_length
    """
    # Find the CDS feature
    cds_feature = find_cds_feature(features)
    # Default variables if no CDS is available (tRNA)
    amount_exons = 0
    amount_introns = 0
    length_exons = sequence.length()
    length_introns = 0
    if cds_feature:
        # Get the complement joined location if it is a ComplementLocation
        if isinstance(cds_feature.location, ComplementLocation):
            cds_feature.location = cds_feature.location.get_translated_joined()
            sequence = sequence.get_complement_sequence()
        elif not isinstance(cds_feature.location, JoinedLocation):
            cds_feature.location = JoinedLocation(cds_feature.location)
        # Calculate amount of exons and the total of their length        
        seq_length = sequence.length()        
        inversed_locations = (cds_feature.location
                              .calculate_inversed_locations(seq_length))
        amount_exons, length_exons = calc_total_len(cds_feature.location
                                                    .locations, sequence)
        amount_introns, length_introns = calc_total_len(inversed_locations,
                                                        sequence)
    else:
        amount_exons = 1
    # Create a dictionary
    return dict(exons=amount_exons, exons_length=length_exons, 
                introns=amount_introns, introns_length=length_introns)
    

def gene_information_generator(accession_genecode_map):
    """ This is a generator to get the information of an accession code,
    which is fed by a dictionary which is returned from the function
    download_nucleotide_genbank_files. This function actually calls the
    functions which parse the Genbank Files.

    Parameters:
        accession_genecode_map - dictionary
    Returns:
        Generator object which yields dictionaries which contains information
        as described by extract_infomration and sequence, accession and
        genecode.
    """
    for accession in accession_genecode_map:
        with GenbankParser("nucleotide_genbank_files/{}.gb"
                           .format(accession)) as parser:
            # We are not interested in the metadata, so don't parse it
            # properly
            parser.parse_metadata(False)
            features = parser.parse_features()
            sequence = parser.parse_origin()
            information = extract_information(features, sequence)
            information['sequence'] = sequence.sequence
            information['accession'] = accession
            information['genecode'] = accession_genecode_map[accession]
            yield information


def main():
    # Execute the bash script
    system("bash deelopdracht\ B.sh")
    # Download the nucleotide genbank files
    accession_to_genecode = download_nucleotide_genbank_files()
    # Parse the genbank files
    gen = gene_information_generator(accession_to_genecode)
    for a in gen:
        print("======")
        for key in a:
            print("{}: {}".format(key, a[key]))
        print("======")


main()

