/**
 * Program to read the fasta file and build
 * a set of reads.
 * 
 * Written by RS
 * 
 * 12/10/2023
 */
import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.lang.Exception;

public class FastaReader {
	private static final boolean debug = false;
	/**
	 * Method to read the Fasta file and return a set of reads.
	 * Index 0 refers to the read name, and index 1 refers to the sequence.
	 */
	public static String[][] readFasta(String filePath){
		int numEntries = countEntries(filePath);
		String[][] data = new String[2][numEntries];
		try {
			FileReader fr = new FileReader(filePath);
			BufferedReader br = new BufferedReader(fr);
			boolean end = false;
			int readIndex = -1;
			int lineNumber = 1;
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
					readIndex++;
					data[0][readIndex] = line.split(" ")[0].substring(1);
				}
				else {
					if(data[1][readIndex] == null){
						data[1][readIndex] = line;
					}
					else{
						data[1][readIndex] = data[1][readIndex] + line;
					}
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
		return data;
	}
	/**
	 * Method to count the entries in a Fasta file
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