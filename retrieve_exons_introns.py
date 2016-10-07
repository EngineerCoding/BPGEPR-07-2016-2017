from os import system, mkdir, listdir
from csv import reader
from genbankparser.genbank_parser import GenbankParser
from genbankparser.location_parser import JoinedLocation, ComplementLocation


def download_nucleotide_genbank_files():
	genecode_accession_dict = {}
	mkdir("nucleotide_genbank_files")
	with open('outputs/genecodes', 'r') as csvfile:
		for row in reader(csvfile, delimiter=' '):
			system("wget -qO nucleotide_genbank_files/{}.gb \"https://eutils."
				   "ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&"
				   "id={}&rettype=gb\"".format(row[0], row[1]))
			genecode_accession_dict[row[0]] = row[1]
	return genecode_accession_dict


def find_cds_feature(features):
    for feature in features:
        if feature.name == 'CDS':
            return feature
    # Return None, is not needed implicitly


def calc_total_len(locations, sequence):
    total_length = 0
    for location in locations:
        total_length += len(sequence.get_sequence_from_location(location))    
    return len(locations), total_length


def extract_information(features, sequence):
    # Find the CDS feature
    cds_feature = find_cds_feature(features)
    # Default variables if not CDS is available (tRNA)
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
        amount_introns, length_intros = calc_total_len(inversed_locations, 
                                                       sequence)            
    else:
        amount_exons = 1
    # Create a dictionary
    return dict(exons=amount_exons, exons_length=length_exons, 
                introns=amount_introns, introns_length=length_introns)
    

def gene_information_generator(accesion_genecode_map):
    for accession in accesion_genecode_map:
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
            #information['genecode'] = accession_genecode_map[accession]
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

