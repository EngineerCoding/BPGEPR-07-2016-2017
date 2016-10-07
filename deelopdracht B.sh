#!/bin/bash

# Set the working directory to a new directory to have the overview
mkdir outputs
cd outputs

# Assignment 3 of B

# Retrieve the genome transcript in FASTA format of Alligator Sinensis
wget "ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF_000455745.1_ASM45574v1/GCF_000455745.1_ASM45574v1_rna.fna.gz" -O alligator_sinensis_cds.fa.gz
gunzip alligator_sinensis_cds.fa.gz
# Create the database and BLAST our sequences against it
formatdb -i alligator_sinensis_cds.fa -pF
blastall -i ../sequentie.fa -d alligator_sinensis_cds.fa -p blastn -o out_sequentie_blast.txt -m8
# Retrieve the first hit of the BLAST from each of our sequence
# Then link a sequence name with an accession
# Finally link the genecodes with accessions and write it to the file 'genecodes'
awk 'BEGIN { last = ""; } { if ($1 != last) { last = $1; print $1 "\t" $2; }}' out_sequentie_blast.txt | sort -k2 | awk '
BEGIN {
	geneList = "";
	last = "";
}
{
	if (seqs[$2] == "") {
		seqs[$2] = $1
	} else {
		seqs[$2] = seqs[$2] "," $1
	}
	if ($2 != last) {
		last = $2;
		geneList = geneList "," $2	
	}
}
END {
	geneList = substr(geneList, 2, length(geneList) - 1);
	system("wget -qO- \"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=protein&id=" geneList "&rettype=fasta\" | egrep ^\\> | cut -c5- | sed \"s/|ref|/ /g\" | tr -d \"|\" > output")
	while ((getline line < "output") > 0) {
		spaceIndex = index(line, " ");		
		geneId = substr(line, 1, spaceIndex - 1);
		remainingLine = substr(line, spaceIndex + 1, length(line) - spaceIndex - 1)
		key = substr(remainingLine, 1, index(remainingLine, " ") - 1)
		geneIds[key] = geneId;	 
	}	
	system("rm output")
	for (key in seqs) {
		print key " " geneIds[key] " " seqs[key];
	}
}' > genecodes

# Assignment 4 of B
# Create a directory where our protein genbank files are going to be stored
cd ..
mkdir protein_genbank_files

for accession in $(awk '{print $1}' outputs/genecodes)
do
	# Download the genbank file for proteins
	wget -qO "protein_genbank_files/$accession.gb" "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=protein&id=$accession&rettype=gb"
	# Parse the name of the product
	product=$(cat "protein_genbank_files/$accession.gb" | grep -Pzo "(?s)product=\".*?\"" | tr -d '[\n"]' | tr -s ' ' | cut -c9-)
	# Parse the GI code (protein code)
	gi=$(cat "protein_genbank_files/$accession.gb" | grep -Pzo "(?s)db_xref=\"GI:.*?\"" | sed 's/GI://' | tr -d '"' | cut -c9-)
	if [[ $gi == "" ]]; then
		gi="-"
	fi
	echo "$accession $gi $product" >> outputs/proteincodes
done

