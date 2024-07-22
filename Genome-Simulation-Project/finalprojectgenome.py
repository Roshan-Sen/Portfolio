import random

#Comment out to fully simulate random genomes
random.seed(4)

#Prokaryotic Gene Finding
"""
A convenient way to find genes in prokaryotic genomes is to say that any ORF >
100 aa codes for a protein. But how accurate is this practice? Are there a lot
of fake genes in the genome because of this? Using simulations, how many genes
in a genome are probably not real?

+ Simulate a prokaryotic genome
+ Make a histogram of ORF sizes
+ Use various cutoffs and report the number of fake genes found
+ Estimate the number of fake genes in E. coli (for example)
"""

"""
The structure of a prokaryotic gene includes a promoter
that include a -35 and -10 sequence. These sequences are
consensus sequences and each letter has a chance of being
the same as the consensus. This is followed by a spacer into
the ribosome binding site. Right after the ribosome binding
site, we have the ORF beginning with ATG. Some genes
can have multiple ORFs, so each ORF will need a rbs before
it. After the ORF(s), there is either a rho-dependent or 
rho-independent terminator for transcription.

---------------------------------------
Data for gene preparation:
---------------------------------------
"""
gcode = {
	'AAA' : 'K',	'AAC' : 'N',	'AAG' : 'K',	'AAT' : 'N',
	'ACA' : 'T',	'ACC' : 'T',	'ACG' : 'T',	'ACT' : 'T',
	'AGA' : 'R',	'AGC' : 'S',	'AGG' : 'R',	'AGT' : 'S',
	'ATA' : 'I',	'ATC' : 'I',	'ATG' : 'M',	'ATT' : 'I',
	'CAA' : 'Q',	'CAC' : 'H',	'CAG' : 'Q',	'CAT' : 'H',
	'CCA' : 'P',	'CCC' : 'P',	'CCG' : 'P',	'CCT' : 'P',
	'CGA' : 'R',	'CGC' : 'R',	'CGG' : 'R',	'CGT' : 'R',
	'CTA' : 'L',	'CTC' : 'L',	'CTG' : 'L',	'CTT' : 'L',
	'GAA' : 'E',	'GAC' : 'D',	'GAG' : 'E',	'GAT' : 'D',
	'GCA' : 'A',	'GCC' : 'A',	'GCG' : 'A',	'GCT' : 'A',
	'GGA' : 'G',	'GGC' : 'G',	'GGG' : 'G',	'GGT' : 'G',
	'GTA' : 'V',	'GTC' : 'V',	'GTG' : 'V',	'GTT' : 'V',
	'TAA' : '*',	'TAC' : 'Y',	'TAG' : '*',	'TAT' : 'Y',
	'TCA' : 'S',	'TCC' : 'S',	'TCG' : 'S',	'TCT' : 'S',
	'TGA' : '*',	'TGC' : 'C',	'TGG' : 'W',	'TGT' : 'C',
	'TTA' : 'L',	'TTC' : 'F',	'TTG' : 'L',	'TTT' : 'F',
}

aminoacids = {
	'AAA' : 'K',	'AAC' : 'N',	'AAG' : 'K',	'AAT' : 'N',
	'ACA' : 'T',	'ACC' : 'T',	'ACG' : 'T',	'ACT' : 'T',
	'AGA' : 'R',	'AGC' : 'S',	'AGG' : 'R',	'AGT' : 'S',
	'ATA' : 'I',	'ATC' : 'I',	'ATG' : 'M',	'ATT' : 'I',
	'CAA' : 'Q',	'CAC' : 'H',	'CAG' : 'Q',	'CAT' : 'H',
	'CCA' : 'P',	'CCC' : 'P',	'CCG' : 'P',	'CCT' : 'P',
	'CGA' : 'R',	'CGC' : 'R',	'CGG' : 'R',	'CGT' : 'R',
	'CTA' : 'L',	'CTC' : 'L',	'CTG' : 'L',	'CTT' : 'L',
	'GAA' : 'E',	'GAC' : 'D',	'GAG' : 'E',	'GAT' : 'D',
	'GCA' : 'A',	'GCC' : 'A',	'GCG' : 'A',	'GCT' : 'A',
	'GGA' : 'G',	'GGC' : 'G',	'GGG' : 'G',	'GGT' : 'G',
	'GTA' : 'V',	'GTC' : 'V',	'GTG' : 'V',	'GTT' : 'V',
	'TAC' : 'Y',	'TAT' : 'Y',	'TCA' : 'S',	'TCC' : 'S',
	'TCG' : 'S',	'TCT' : 'S',	'TGC' : 'C',	'TGG' : 'W',
	'TGT' : 'C',	'TTA' : 'L',	'TTC' : 'F',	'TTG' : 'L',
	'TTT' : 'F',
}

stopcodons = {
	'TAG' : '*',	'TAA' : '*',	'TGA' : '*',
}

#ORF sizes were specified as ranging from around 50aa to
#around 700. That will be the range used by the simulation.
orfmin = 50
orfmax = 700

#Source: https://en.wikipedia.org/wiki/Promoter_(genetics)/
#-35 sequence along with probaility of getting each consensus nt
minus35seq = [
	'TTGACA',	[0.69, 0.79, 0.61, 0.56, 0.54, 0.54]
]

#spacer optimal length is 17 but can be +-1
promspacerlen = [16, 17, 18]

#-10 sequence along with probability of getting each consensus nt
minus10seq = [
	'TATAAT', [0.77, 0.76, 0.60, 0.61, 0.56, 0.82]
]

#spacer between -10 and rbs was uncertain, used previous
#spacer length for now

#Source: https://en.wikipedia.org/wiki/Ribosome-binding_site/

#Shine-Dalgarno sequence (ribosome binding site)
#immediately followed by start codon
rbs = 'TAAGGAAGG'

#Source: https://en.wikipedia.org/wiki/Rho_factor/
#rho factor is 72 nt long C rich, G poor sequence after
#an ORF or the final ORF of an operon. The sequence probabilities
#were not defined so going with some made up ones for now.
#rho threshold is the proportion of genes that will have
#rho dependent termination, around half
rholen = 72
rhoprobs = [0.2, 0.5, 0.2, 0.1] 
rhothresh = 0.5

#Source: https://en.wikipedia.org/wiki/Intrinstic_termination/
#rho-independent termination involves formation of a GC stem loop
#followed by a U rich sequence. The stem loop stalls transcription
#and terminates it. Parameters uncertain, so used
#estimates base on the picture
intrinparam = [20, 7, 4, 16]
#[pre-loop section, zipper length, loop length, poly-U length]
loopprobs = [0, 0.5, 0.5, 0] #[A, C, G, T]
polyuprobs = [0.05, 0.05, 0.05, 0.85] #[A, C, G, T]

#Bacterial genomes have most coding sequences on one strand,
#but there are a few on the other strand as well. Information
#about this was scarce, so these values are arbitrary
mainstrprob = 0.50

#Spacer length between genes is set arbitrarily to 20
spacerlength = 20

"""
--------------------------------------------------------
Functions for prokaryotic gene preparation
--------------------------------------------------------
"""

#builds an ORF of random sequence given an
#amino acid length
def buildorf(aalength):
	neworf = 'ATG'
	for i in range(aalength - 1):
		newcodon = random.choice(list(aminoacids.keys()))
		neworf += newcodon
	newstop = random.choice(list(stopcodons.keys()))
	neworf += newstop
	return neworf

#builds a promoter sequence based on known consensus
def buildpromoter():
	newprom = ''
	#adding -35 sequence
	partone = ''
	for i in range(len(minus35seq[0])):
		if random.random() > minus35seq[1][i]:
			if minus35seq[0][i] == 'A':   partone += random.choice('CGT')
			elif minus35seq[0][i] == 'C': partone += random.choice('AGT')
			elif minus35seq[0][i] == 'G': partone += random.choice('ACT')
			else:                         partone += random.choice('ACG')
		else: partone += minus35seq[0][i]
	newprom += partone
	#adding spacer and -10 sequence
	newprom += randseq(random.choice(promspacerlen))
	parttwo = ''
	for i in range(len(minus10seq[0])):
		if random.random() > minus10seq[1][i]:
			if minus10seq[0][i] == 'A':   parttwo += random.choice('CGT')
			elif minus10seq[0][i] == 'C': parttwo += random.choice('AGT')
			elif minus10seq[0][i] == 'G': parttwo += random.choice('ACT')
			else:                         parttwo += random.choice('ACG')
		else: parttwo += minus10seq[0][i]
	newprom += parttwo
	#add another spacer and rbs
	newprom += randseq(random.choice(promspacerlen))
	newprom += rbs
	return newprom

#building transcription terminator
def buildterm(rhodep):
	if rhodep: terminus = randseq(rholen, prb = rhoprobs)
	else:
		zip = randseq(intrinparam[1], loopprobs)
		terminus = randseq(intrinparam[0]) + zip + randseq(intrinparam[2]) + reversecomplement(zip) +  randseq(intrinparam[3], prb = polyuprobs)
	return terminus
		

#Builds a random sequence of a given length, parameters show
#A, C, G, T probabilities respectively, used in rho-dependent
#transcription termination
def randseq(length, prb = [0.25, 0.25, 0.25, 0.25]):
	newsequence = ''
	for i in range(length):
		v = random.random()
		if v < prb[0]:                     newsequence += 'A'
		elif v < prb[0] + prb[1]:          newsequence += 'C'
		elif v < prb[0] + prb[1] + prb[2]: newsequence += 'G'
		else:                              newsequence += 'T'
	return newsequence

#Builds a reverse complement of a sequence
def reversecomplement(seq):
	revcomp = ''
	for i in range(len(seq) - 1, -1, -1):
		base = seq[i:i + 1]
		if base == 'A': revcomp += 'T'
		elif base == 'T': revcomp += 'A'
		elif base == 'C': revcomp += 'G'
		else: revcomp += 'C'
	return revcomp

#Builds a genome library full of genes
#minlen is mininum gene length, maxlen is maximum gene length
#{Promoter, ORF, Terminator, Direction (either forward or reverse)}
def genomelibrary(numgenes, minlen = orfmin, maxlen = orfmax):
	genome = []
	for i in range(numgenes):
		newentry = {}
		newentry['Promoter'] = buildpromoter()
		newentry['ORF'] = buildorf(random.randint(minlen, maxlen))
		
		if random.random() < rhothresh:	newentry['Terminator'] = buildterm(True)
		else:                       	newentry['Terminator'] = buildterm(False)
		
		if random.random() < mainstrprob:   newentry['Direction'] = 'F'
		else:                               newentry['Direction'] = 'R'
		genome.append(newentry)
	return genome

#Extracts the ORFs from a genome library and stores
#them into an array, important for analysis
def extractorfs(genelibrary):
	orfs = []
	for gene in genelibrary:
		orfs.append(gene['ORF'])
	return orfs

#Builds a genome from a genome library.
#spacelen is the space between genes
def buildgenome(genelibrary, spacelen = spacerlength):
	genomestr = ''
	genomestr += randseq(spacelen)
	for gene in genelibrary:
		geneseq = ''
		for key in gene:
			if key != 'Direction': geneseq += gene[key]	
		if gene['Direction'] == 'F': genomestr += geneseq
		else:                        genomestr += reversecomplement(geneseq)
		genomestr += randseq(spacelen)
	return genomestr

"""
#function tester
def functiontester():
	print(buildorf(500))
	print(randseq(5))
	print(buildpromoter())
	print(buildterm(True))
	print(buildterm(False))
	print(reversecomplement('ACGTACGT'))
	samplelibrary = genomelibrary(5)
	print(samplelibrary)
	print(buildgenome(samplelibrary))
functiontester()
"""
