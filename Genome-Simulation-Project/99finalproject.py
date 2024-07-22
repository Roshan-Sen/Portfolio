import finalprojectgenome as sim

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

#E. coli information
genecount = 4285
#orf sizes will use the defaults set in the genome simulator

"""
----------------------------
Functions for Accuracy Check
----------------------------
"""

#Finds orfs in a single strand genome and returns the
#orfs in a list, checks the other strand as well
def orffinder(genome):
	orflist = []
	#checking first strand
	index = 0
	countingorf = False
	orflistindex = -1
	while index < len(genome) - 2:
		codon = genome[index:index + 3]
		if countingorf:
			if gcode[codon] == '*':
				countingorf = False
				orflist[orflistindex] += codon
				index += 1
			else:
				orflist[orflistindex] += codon
				index += 3
		elif codon == 'ATG':
			countingorf = True
			orflistindex += 1
			orflist.append('ATG')
			index += 3
		else: index += 1
	lastorf = orflist[len(orflist) - 1]
	if lastorf[len(lastorf) - 3:] not in list(sim.stopcodons.keys()):
		orflist.pop()
	return orflist

#extracts the orfs above a certain cutoff size from
#a list of orfs, returns a list of lengths along with
#a cleared list of orfs where all orfs less than
#the cutoff are removed
def clearedorfs(orfarray, cutoff = 0):
	neworfs = []
	orflen = []
	for orf in orfarray:
		length = len(orf) / 3 - 1
		if length >= cutoff:
			neworfs.append(orf)
			orflen.append(length)
	return neworfs, orflen

#Finds common orfs between a 'real' set of orfs
#and a computed set function
def commonorfs(realset, foundset):
	commonelements = []
	for i in range(len(realset)):
		realentry = realset[i]
		for j in range(len(foundset)):
			if realentry == foundset[j]:
				commonelements.append(realentry)
				break
	return commonelements

#Function Tester
"""
def functiontester():
	samplegenelibrary = sim.genomelibrary(100)
	sampleorfs = sim.extractorfs(samplegenelibrary)
	samplegenome = sim.buildgenome(samplegenelibrary)
	samplefoundorfs = orffinder(samplegenome)
	samplecommonorfs = commonorfs(sampleorfs, samplefoundorfs)
	print(samplecommonorfs)
	

functiontester()
"""

#main program: build a bacterial genome, run an orf finder
#function and see whether the orfs line up to the ones built
#into the genome
ecgenelib = sim.genomelibrary(genecount)
ecorfs = sim.extractorfs(ecgenelib)
ecgenome = sim.buildgenome(ecgenelib)
ecfoundorfs = orffinder(ecgenome)
ecfoundorfs.append(orffinder(sim.reversecomplement(ecgenome)))

print('The simulated genome contained ' + str(len(ecgenelib)) + ' orfs.')

trialcutoffs = [100, 200, 300]
for value in trialcutoffs:
	ecclearedorfs, ecorfslen = clearedorfs(ecfoundorfs, cutoff = value)
	eccommonorfs = commonorfs(ecorfs, ecclearedorfs)
	print('At a cutoff of ' + str(value) + ' base pairs as the minimum length:')
	print('The number of orfs found in the genome was ' + str(len(ecclearedorfs)) + '.')
	print('The number of found orfs that were \"real\" was ' + str(len(eccommonorfs)) + '.')
	print('The number of missed orfs was ' + str(genecount - len(eccommonorfs)))
