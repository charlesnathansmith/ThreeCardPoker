#!/usr/bin/env python

from threecardpoker import ThreeCardPoker
from threecardlookup import ThreeCardLookup
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as backend_pdf

__author__ ="Charles Nathan Smith"
__license__ = "GPLv3"


#Amount being risked by the player taking the house side of each bet (the player/dealer)
#Winning and losing bets from each round are matched in turn against the bank until it is exhausted
BANK_AMOUNT = 5000

#Number of players per hand excluding the player/dealer
NUM_PLAYERS = 5

#Total number of rounds to simulate
#Each round consists of one deal of hands to NUM_PLAYERS and the player/dealer
#Each player hand is evaluated against the player/dealer's hand,
#With the player/dealer collecting any losses and losing bonus bets and paying any bonuses won,
NUM_ROUNDS = 100000

#Per betting spot per player [play, ante, pair-plus, 6-card]
#Play must be the same as ante, and pair-plus cannot be more than ante
bet_size = np.array([20,20,20,20])


tcpoker = ThreeCardPoker()

print "Three Card Poker - Player Banking Simulator\n\n"

print "Drawing cards for %d rounds of play," % NUM_ROUNDS
print "Each with %d regular players and one player/dealer..." % NUM_PLAYERS,

hands = tcpoker.GenerateHands(NUM_ROUNDS,NUM_PLAYERS)


print "DONE"
print "Evaluating hand values (for %d total hands)..." % ((NUM_PLAYERS+1) * NUM_ROUNDS),
values = tcpoker.evaluate_hands(hands)

print "DONE"
print "Determining wins, losses, and bonus payouts...",
multipliers = tcpoker.GenerateMultipliers(hands, values, NUM_PLAYERS)
multipliers[:] *= bet_size
adj_payouts = tcpoker.AdjustForAction(multipliers, BANK_AMOUNT)

print "DONE\n\n"


#We are interested in returns from the player/dealer's perspective,
#Who wins when the other plays lose and vice versa
adj_payouts[:] *= -1


print "Total player/dealer profit/loss:  $%d ($%d per round)" % (adj_payouts.sum(), adj_payouts.sum(axis=2).sum(axis=1).mean())
print "Profit/loss unadjusted for max payouts: $%d ($%d per round)\n\n" % (-multipliers.sum(), -multipliers.sum(axis=2).sum(axis=1).mean())
print "Total Profit/Loss per betting spot\n"

for spot_name, spot_values in zip(["Play", "Ante", "P-Plus", "6-card"], adj_payouts.sum(axis=1).T):
    print spot_name + ":\t\t" + str(spot_values.sum())


#Split hands into rounds and take all but the first hand (the dealer hand) from each
player_values = values.reshape(-1, NUM_PLAYERS+1).T[1:].T

value_bins = [0,
        1,
        ThreeCardLookup.MAX_STRAIGHT_FLUSH+1,
        ThreeCardLookup.MAX_TRIPS+1,
        ThreeCardLookup.MAX_STRAIGHT+1,
        ThreeCardLookup.MAX_FLUSH+1,
        ThreeCardLookup.MAX_PAIR+1,
        ThreeCardLookup.MAX_HIGH_CARD]

value_labels = ["Royal Flush:",
                "Straight Flush:",
                "Trips:\t",
                "Straight:",
                "Flush:\t",
                "Pair:\t",
                "High card:"]

value_hist, value_bins = np.array(np.histogram(player_values, bins=value_bins))
total_values = value_hist.sum()

print "\n\nPlayer hands by type\n"

for label, value in zip(value_labels, value_hist):
    print label +"\t\t" + str(value) + "\t(%.1f%%)" % (value/float(total_values)*100)

print "\n\n"

pdf = backend_pdf.PdfPages("Charts.pdf")

returns_by_round = adj_payouts.sum(axis=2).sum(axis=1)

plt.figure()
plt.plot(returns_by_round.cumsum()[:1000])
plt.title('Cumulative returns (1000 rounds)')
plt.ylabel('Return ($)')
plt.xlabel('Betting Rounds')
pdf.savefig()
plt.close()

plt.figure()
plt.plot(returns_by_round.cumsum())
plt.title('Cumulative returns (' + str(NUM_ROUNDS) + ' rounds)')
plt.ylabel('Return ($)')
plt.xlabel('Betting Rounds')
pdf.savefig()
plt.close()

#Split an array into strides of length window
#Eg. For window=3, [0,1,2,3,4,5,...] -> [0,1,2],[1,2,3],[2,3,4],...
#http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

returns_by_hundred = rolling_window(returns_by_round, 100).sum(axis=1)

#Normalize
y,x = np.histogram(returns_by_hundred, bins=8)
xm = [(x[i]+x[i+1])/2 for i in xrange(len(x)-1)]
y = y/float(y.sum())*100

plt.figure()
plt.bar(xm,y,xm[1]-xm[0])
plt.title("Return per 100 hands")
plt.ylabel('Occurrence %')
plt.xlabel('Return')
pdf.savefig()
plt.close()

returns_by_thousand = rolling_window(returns_by_round, 1000).sum(axis=1)

y,x = np.histogram(returns_by_thousand, bins=8)
xm = [(x[i]+x[i+1])/2 for i in xrange(len(x)-1)]
y = y/float(y.sum())*100

plt.figure()
plt.bar(xm,y,xm[1]-xm[0])
plt.title("Return per 1000 hands")
plt.ylabel('Occurrence %')
plt.xlabel('Return')
pdf.savefig()
plt.close()

pdf.close()
