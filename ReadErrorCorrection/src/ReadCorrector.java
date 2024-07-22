/**
 * This is the read corrector.
 * The purpose is to identify correct reads (appear at least twice
 * either as an original read or as a reverse complement) and
 * incorrect reads (appear only once).
 *
 * Written by RS
 *
 * 12/30/2023
 */
import java.util.HashMap;
import java.util.Map;
import java.lang.Math;
import java.lang.Character;

public class ReadCorrector {
	private HashMap<String, String> inputReads; //<Read ID : original read>
	private String[] complementReads;
	private HashMap<String, String> correctedReads;	//<Read ID : corrected read>
	private final static boolean debug = false;
	/**
	 * Constructor for the ReadCorrector objects
	 */
	public ReadCorrector(HashMap<String, String> givenReads){
		inputReads = givenReads;
		this.setComplementReads();
		this.setCorrectedReads();
	}
	
	//Getter methods
	/**
	 * Get method for input reads
	 */
	public HashMap<String, String> getInputReads(){
		return inputReads;
	}
	/**
	 * Get method for the correctedReads
	 */
	public HashMap<String, String> getCorrectedReads() {
		return correctedReads;
	}
	
	//Setter methods
	/**
	 * Method to set the complementary reads
	 */
	private void setComplementReads(){
		complementReads = new String[inputReads.size()];
		int index = 0;
		for (Map.Entry<String, String> entry : inputReads.entrySet()) {
			String read = entry.getValue();
			complementReads[index] = reverseComplement(read);
			if(debug) {
				System.out.println(entry.getKey() + ": " + read + " | complement: " + complementReads[index]);
			}
			index++;
		}
	}
	/** 
	 * Method to find and correct the reads
	 */
	private void setCorrectedReads(){
		correctedReads = new HashMap<String, String>();
		for (Map.Entry<String, String> entry : inputReads.entrySet()) {
			String read = entry.getValue();
			int hitCount = countReadInstances(read);
			if(debug) {
				System.out.println(entry.getKey() + ": " + read + " | " + hitCount + " instances");
			}
			
			if(hitCount < 2) {
				String match = findClosestMatch(read);
				if(debug){
					System.out.println("The closest match is " + match);
				}
				correctedReads.put(entry.getKey(), match);
			}
		}
	}
	
	//other methods
	/**
	 * Method to count instances of a read among the reverse complements and 
	 * original reads.
	 */
	private int countReadInstances(String read){
		int count = 0;
		for (Map.Entry<String, String> entry : inputReads.entrySet()) {
			String parsedRead = entry.getValue();
			if(read.equals(parsedRead)){
				count++;
			}
		}
		
		for(int j = 0; j < complementReads.length; j++){
			if(read.equals(complementReads[j])){
				count++;
			}
		}
		return count;
	}
	/**
	 * Method to find the closest match to a read
	 * but not equal to it.
	 */
	private String findClosestMatch(String read){
		String closest = null;
		int closestDistance = complementReads[0].length();
		for (Map.Entry<String, String> entry : inputReads.entrySet()) {
			String parsedRead = entry.getValue();
			int parsedDistance = hammingDistance(read, parsedRead);
			if(parsedDistance < closestDistance && parsedDistance != 0){
				closest = parsedRead;
				closestDistance = parsedDistance;
			}
		}
		
		for(int j = 0; j < complementReads.length; j++){
			String parsedRead = complementReads[j];
			int parsedDistance = hammingDistance(read, parsedRead);
			if(parsedDistance < closestDistance && parsedDistance != 0){
				closest = parsedRead;
				closestDistance = parsedDistance;
			}
		}
		return closest;
	}
	
	/**
	 * Method to calculate the Hamming Distance between two strings of equal
	 * length.
	 */
	public static int hammingDistance(String a, String b){
		int distance = 0;
		for(int i = 0; i < a.length(); i++){
			if(a.charAt(i) != b.charAt(i)){
				distance++;
			}
		}
		return distance;
	}
	/**
	 * Method to create a reverse complement string for an input string of DNA bases.
	 */
	public static String reverseComplement(String s){
		String output = "";
		for(int i = s.length() - 1; i > -1; i--){
			if(Character.toUpperCase(s.charAt(i)) == 'A'){
				output += 'T';
			}
			else if(Character.toUpperCase(s.charAt(i)) == 'C'){
				output += 'G';
			}
			else if(Character.toUpperCase(s.charAt(i)) == 'G'){
				output += 'C';
			}
			else if(Character.toUpperCase(s.charAt(i)) == 'T'){
				output += 'A';
			}
			else {
				output += 'X';
			}
		}
		return output;
	}
	
}