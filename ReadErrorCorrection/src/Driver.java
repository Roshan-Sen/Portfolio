/**
 * Driver for the Read Error Correction problem from Rosalind.
 *
 * Written by RS
 *
 * 12/30/2023
 */
import java.util.HashMap;
import java.util.Map;

public class Driver {
	// Main method
	public static void main(String[] args){
		//Read the file
		HashMap<String, String> results =  FastaReader.readFasta("C:/Users/Roshan/Documents/01_Programming_Practice/ReadErrorCorrection/data/sequencingdata.txt");
		System.out.println("\nInput Reads for Error Correction");
		for (Map.Entry<String, String> entry : results.entrySet()) {
			System.out.println(entry.getKey() + ": " + entry.getValue());
		}
		//Correcting reads
		ReadCorrector r = new ReadCorrector(results);
		
		//Display corrected reads
		HashMap<String, String> corrections = r.getCorrectedReads();
		System.out.println("\nThe following reads were corrected");
		for (Map.Entry<String, String> entry : corrections.entrySet()){
			System.out.println(entry.getKey() + ": " + results.get(entry.getKey()) + " --> " +entry.getValue());
		}
	}
}