/**
 * Messenger RNA class.
 *
 * Written by RS
 * 12/10/2023
 */

public class MessengerRNA {
	private String transcript;
	private String[] introns;
	private String mRNA;
	private String translation;
	private static final String[] gcode = {"ACC-T", "ATG-M", "AAG-K", "AAA-K", "ATC-I", "AAC-N", "ATA-I", "AGG-R", "CCT-P", "CTC-L", "AGC-S", "ACA-T", "AGA-R", "CAT-H", "AAT-N", "ATT-I", "CTG-L", "CTA-L", "ACT-T", "CAC-H", "ACG-T", "CAA-Q", "AGT-S", "CAG-Q", "CCG-P", "CCC-P", "TAT-Y", "GGT-G", "TGT-C", "CGA-R", "CCA-P", "CGC-R", "GAT-D", "CGG-R", "CTT-L", "TGC-C", "GGG-G", "TAG-*", "GGA-G", "TAA-*", "GGC-G", "TAC-Y", "GAG-E", "TCG-S", "TTA-L", "TTT-F", "GAC-D", "CGT-R", "GAA-E", "TCA-S", "GCA-A", "GTA-V", "GCC-A", "GTC-V", "GCG-A", "GTG-V", "TTC-F", "GTT-V", "GCT-A", "TGA-*", "TTG-L", "TCC-S", "TGG-W", "TCT-S"};
	/**
	 * Constructor for mRNA. Takes a raw transcript and the introns
	 */
	public MessengerRNA(String t, String[] i){
		transcript = t;
		introns = i;
		this.spliceRNA();
		this.translateRNA();
	}
	
	//Get methods
	/**
	 * Getter method for the mRNA after processing.
	 */
	public String getMRNA(){
		return mRNA;
	}
	/**
	 * Getter method for the original transcript.
	 */
	public String getTranscript(){
		return transcript;
	}
	/**
	 * Getter method for the introns
	 */
	public String[] getIntrons(){
		return introns;
	}
	/**
	 * Getter method for the translation
	 */
	public String getTranslation(){
		return translation;
	}
	
	//Private Methods
	/**
	 * Method to splice the RNA. Called upon object creation.
	 */
	private void spliceRNA(){
		String tempTranscript = transcript;
		for(int i = 0; i < introns.length; i++){
			int spliceInd = tempTranscript.indexOf(introns[i]);
			if(spliceInd != -1) {
				tempTranscript = tempTranscript.substring(0, spliceInd) + tempTranscript.substring(spliceInd + introns[i].length());
			}
		}
		mRNA = tempTranscript;
	}
	private void translateRNA(){
		String tempTranslation = "";
		boolean translationStart = false;
		boolean translationEnd = false;
		for(int i = 0; i < mRNA.length(); i+=3){
			String codon = mRNA.substring(i, i + 3);
			if(translationStart){
				for(int j = 0; j < gcode.length; j++){
					if(gcode[j].substring(0,3).equals(codon)){
						tempTranslation += gcode[j].substring(4);
						if(gcode[j].substring(4).equals("*")){
							translationEnd = true;
							translationStart = false;
						}
						break;
					}
				}
			}
			else if(translationEnd){
				break;
			}
			else if(codon.equals("ATG")){
				tempTranslation += "M";
				translationStart = true;
			}
			else{
				continue;
			}
		}
		translation = tempTranslation;
	}
}