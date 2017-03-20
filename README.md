# ThreeCardPoker
Three Card Poker Player Banking Simulation and Analysis

In California casinos, any player at any table game can take on the role of "player/dealer," taking the house side of the bet against other players at the table.

This project builds on Will Drevo's deuces poker library (https://github.com/worldveil/deuces) to provide fast generation, evaluation, and game-play simulation of Face Up Three Card Poker hands in order to determine the profitability and risk profile of acting as player/dealer on this game.

While retaining the idea of using prime lookup tables, speed is further increased by taking advantage of NumPy's vectorized array operations to efficiently process huge arrays of hands at a time.

tcbanking.py uses the libraries to simulate several rounds of play with 5 players betting $20 per betting spot and analyzes the results in order to help determine an appropriate initial investment that minimizes the risk of ruin to an acceptable level.


```python
>>> execfile("tcbanking.py")
```
```
Three Card Poker - Player Banking Simulator


Drawing cards for 5000000 rounds of play,
Each with 5 regular players and one player/dealer... DONE
Evaluating hand values (for 30000000 total hands)... DONE
Determining wins, losses, and bonus payouts... DONE


Total player/dealer profit/loss:  $141535020 ($28 per round)
Profit/loss unadjusted for max payouts: $138260400 ($27 per round)


Total Profit/Loss per betting spot

Play:		-16194500
Ante:		42960820
P-Plus:		35172100
6-card:		79596600


Player hands by type

Royal Flush:		0	(0.0%)
Straight Flush:		54504	(0.2%)
Trips:			59064	(0.2%)
Straight:		814417	(3.3%)
Flush:			1238843	(5.0%)
Pair:			4236608	(16.9%)
High card:		18596564	(74.4%)
```

Examining Charts.pdf, we see that the risk of losing more than $5000 during any sample of hands is relatively small (2-3%.)  Considering we must keep $5000 available to continue funding each round, an initial bankroll of $10,000 should be reasonably sufficient for taking the player/dealer side of this game.
