__author__ ="Charles Nathan Smith"
__license__ = "GPLv3"


class ThreeCardLookup(object):
    """
    Build an evaluation table for Three Card Poker hands
    """
    
    #It is worth noting that with 3-card hands, trips are ranked higher than straights,
    #and straights higher than flushes, as the relative odds of receiving certain types of hands
    #differs from those applicable to 5-card hands

    #Distinct Hands:

    #Straight flushes    12    AKQs-A23S
    #Trips               13    AAA-222
    #Straights           12    AKQ-A23
    #Flushes            274    (13 choose 3) - 12 straight flushes
    #One Pair           156    (13 choose 2) * (2 choose 1)
    #High Card          274    (13 choose 3) - 12 straights
    #-----------------------
    #Total              741
    

    FLUSH_OFFSET = 430 #156+274
    #Set up the ranks so Straight and Straight Flush ranks differ by the same amount as
    #Flush and high card ranks, so we can simply subtract the offset to get suited hand ranks
    
    MIN_STRAIGHT_FLUSH = 1
    MAX_STRAIGHT_FLUSH = 12
    MIN_TRIPS = 13
    MAX_TRIPS = 25
    #Skip rank values to adjust for flush offset
    MIN_STRAIGHT = 431 #MIN_STRAIGHT_FLUSH + FLUSH_OFFSET
    MAX_STRAIGHT = 442 #MIN_STRAIGHT + 12-1
    MIN_FLUSH = 443
    MAX_FLUSH = 716 #MIN_FLUSH + 274-1
    MIN_PAIR = 717
    MAX_PAIR = 872 #MIN_PAIR + 156-1
    MIN_HIGH_CARD = 873 #MIN_FLUSH + FLUSH_OFFSET
    MAX_HIGH_CARD = 1146 #MIN_HIGH_CARD + 274-1
    
    lookup = {}
    
    STR_RANKS = 'A23456789TJQKA'
    PRIMES = [41, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
    
    def __init__(self):
        """
        Calculate Three Card Poker lookup table
        Lookup table maps hands to unsuited ranks
        These can be converted to suited ranks by subtracting FLUSH_OFFSET
        """

        #straight flushes and straights
        #Set the unsuited straights, then straight flushes can be easily calculated from these
        #By subtracting FLUSH_OFFSET
    
        rank = self.MIN_STRAIGHT_FLUSH
    
        for i in xrange(13, 1, -1):
            self.lookup[self.PRIMES[i] * self.PRIMES[i-1] * self.PRIMES[i-2]] = rank + self.FLUSH_OFFSET
            rank += 1
    
        #Trips
        for i in xrange(13, 0, -1):
            self.lookup[self.PRIMES[i]**3] = rank
            rank +=1

        #Flushes and High cards
        #Flushes = High cards - FLUSH_OFFSET
        rank = self.MIN_HIGH_CARD

        for c1 in xrange(13, 0, -1):
            for c2 in xrange(c1 - 1, 0, -1):
                for c3 in xrange(c2 - 1, 0, -1):
                    multiple = self.PRIMES[c1] * self.PRIMES[c2] * self.PRIMES[c3]

                    #skip straights
                    if multiple not in self.lookup:
                        self.lookup[multiple] = rank
                        rank += 1

        #Pairs
        rank = self.MIN_PAIR

        for i in xrange(13, 0, -1):
            for kicker in xrange(13, 0, -1):
                if kicker != i:
                    self.lookup[self.PRIMES[i]**2 * self.PRIMES[kicker]] = rank
                    rank += 1
