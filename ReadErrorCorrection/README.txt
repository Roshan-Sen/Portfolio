Roshan Sen
12/30/2023

This project solves the Error Correction
in Reads problem on Rosalind. After the previous
RNA splicing practice, I modified the FastaReader class
to return the output as a HashMap rather than a 2D array.
This makes the output more relevant for the user. The ReadCorrector
class can then take the hashmap to identify which
reads are accurate (in that they appear in the list
more than once) and inaccurate (a read appearing once).
The program can then find the closest match in an attempt
to fix the incorrect read.