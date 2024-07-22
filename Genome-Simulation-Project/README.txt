The goal of this project was to see how many fake open reading frames
could be found in a simulated prokaryotic genome. The project involved
creating a thorough way to simulate a prokaryotic genome with all the
features that are usually seen. One fault in this program is that it
is prone to miss open reading frames when a mistaken one is caught that
happens to overlap with a real one. The fix to this is to loop at 3 different
offsets over the genome in order to make sure all open reading frames are
caught.
