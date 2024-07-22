/**
 * Driver to test the Splicing of mRNA
 * using data from a mock fasta file.
 *
 * Writter by RS
 * 12/11/2023
 */
public class Driver{
	/**
	 * Main Method
	 */
	public static void main(String[] args){
		String localPath = "C:/Users/Roshan/Documents/01_Programming_Practice/RNASplicing/data/seq.txt";
		//Read the file
		String[][] seqData = FastaReader.readFasta(localPath);
		//Display input
		System.out.println("Input Reads\n");
		for(int i = 0; i < seqData[0].length; i++){
			System.out.println(seqData[0][i] + " - " + seqData[1][i]);
		}
		String transcript = "";
		String[] introns = new String[seqData[0].length - 1];
		for(int j = 0; j < seqData[0].length; j++){
			if(j == 0){
				transcript = seqData[1][j];
			}
			else {
				introns[j - 1] = seqData[1][j];
			}
		}
		//Make MessengerRNA object and display the spliced mRNA along with translation.
		System.out.println("");
		MessengerRNA m = new MessengerRNA(transcript, introns);
		System.out.print("mRNA Sequence: ");
		System.out.println(m.getMRNA());
		System.out.print("Translation: ");
		System.out.println(m.getTranslation());
	}
}