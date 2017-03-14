# ThreeCardPoker
Three Card Poker Player Banking Simulation and Analysis

In California casinos, any player at any table game can take on the role of "player/dealer," taking the house side of the bet against other players at the table.

This project builds on Will Drevo's deuces poker library (https://github.com/worldveil/deuces) to provide fast generation, evaluation, and game-play simulation of Face Up Three Card Poker hands in order to determine the profitability and risk profile of acting as player/dealer on this game.

While retaining the idea of using prime lookup tables, speed is further increased by taking advantage of NumPy's vectorized array operations to efficiently process huge arrays of hands at a time.

Run tcbanking.py for an example of using the libraries to simulate several rounds of play and analyze the results.
See Charts.pdf and the below output for the results of a typical analysis.

```python
>>> execfile("tcbanking.py")
```
```
Three Card Poker - Player Banking Simulator


Drawing cards for 100000 rounds of play,
Each with 5 regular players and one player/dealer... DONE
Evaluating hand values (for 600000 total hands)... DONE
Determining wins, losses, and bonus payouts... DONE


Total player/dealer profit/loss:  $1477120 ($14 per round)
Profit/loss unadjusted for max payouts: $1429380 ($14 per round)


Total Profit/Loss per betting spot

Play:		-322640
Ante:		-478240
P-Plus:		647940
6-card:		1630060


Player hands by type

Royal Flush:		0	(0.0%)
Straight Flush:		1143	(0.2%)
Trips:			1266	(0.3%)
Straight:		16057	(3.2%)
Flush:			24837	(5.0%)
Pair:			84408	(16.9%)
High card:		372289	(74.5%)
```
