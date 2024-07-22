/**
 * Program to read the fasta file and build
 * a set of reads. Updated to use HashMaps.
 * 
 * Written by RS
 * 
 * Updated 12/25/2023
 */
import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.lang.Exception;
import java.util.HashMap;

public class FastaReader {
	private static final boolean debug = false;
	
	/**
	 * Read Fasta Method that uses a HashMap
	 * Returns <Read ID : read>
	 */
	public static HashMap<String, String> readFasta(String filePath){
		HashMap<String, String> reads = new HashMap<String, String>();
		try {
			FileReader fr = new FileReader(filePath);
			BufferedReader br = new BufferedReader(fr);
			boolean end = false;
			int lineNumber = 1;
			String currentEntryName = null;
			String currentSequence = null;
			while(!end){
				String line = br.readLine();
				if(debug){
					System.out.println("Reading line " + lineNumber);
					System.out.println(line);
				}
				
				if(line == null) {
					end = true;
					if(currentEntryName != null){
						reads.put(currentEntryName, currentSequence);
						if(debug){
							System.out.println(currentEntryName + ": " + currentSequence);
						}
					}
				}
				else if(line.substring(0,1).equals(">")){
					if(currentEntryName != null){
						reads.put(currentEntryName, currentSequence);
						if(debug){
							System.out.println(currentEntryName + ": " + currentSequence);
						}
					}
					currentEntryName = line.split(" ")[0].substring(1);
					currentSequence = null;
				}
				else {
					if(currentSequence == null){
						currentSequence = line;
					}
					else{
						currentSequence += line;
					}
				}
				lineNumber++;
			}
			br.close();
		}
		catch(IOException i){
			System.out.println("There was an error reading the file.");
			System.out.println(i.toString());
		}
		catch(Exception e){
			System.out.println("Something went wrong.");
			System.out.println(e.toString());
		}
		return reads;
	}
	/**
	 * Method to count the entries in a Fasta file.
	 * Used in the old readFasta(String filePath) method which used an array.
	 * Keeping in case it becomes applicable.
	 */
	public static int countEntries(String filePath){
		int lineNumber = 1;
		int count = 0;
		try {
			FileReader fr = new FileReader(filePath);
			BufferedReader br = new BufferedReader(fr);
			boolean end = false;
			while(!end){
				String line = br.readLine();
				if(debug){
					System.out.println("Reading line " + lineNumber);
					System.out.println(line);
					lineNumber++;
				}
				
				if(line == null){
					end = true;
				}
				else if(line.substring(0,1).equals(">")){
					count++;
				}
				else {
					continue;
				}
			}
		}
		catch(IOException i){
			System.out.println("There was an error reading the file.");
			System.out.println(i.toString());
		}
		catch(Exception e){
			System.out.println("Something went wrong.");
			System.out.println(e.toString());
		}
		return count;
	}
}