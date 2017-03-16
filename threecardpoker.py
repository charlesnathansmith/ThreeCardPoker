import numpy as np
from tempfile import mkdtemp
import os.path as path

from threecardlookup import ThreeCardLookup
from deuces.card import Card
from deuces.deck import Deck
from deuces.evaluator import Evaluator

__author__ ="Charles Nathan Smith"
__license__ = "GPLv3"


class ThreeCardPoker(object):
    """
    Provide fast vectorized generation and evaluation of Three Card Poker hands
    
    All arrays returned are memmapped -
        use "del array_name" when finished to close open file references
    """
    
    def __init__(self, data_dir=None):
        self.tc_lookup = ThreeCardLookup()
        self.FULL_DECK = Deck.GetFullDeck()
        
        if data_dir is None:
            self.tmp_dir = mkdtemp()
        else:
            self.tmp_dir = data_dir

    
    def GenerateHands(self, num_rounds, num_players=4, data_dir=None):
        """
        Generate an array of Three Card Poker hands
        
            num_rounds:  Number of banking rounds to generate
                         each round consists of 4 player hands vs one bank/dealer hand
                         
            num_players: Number of player hands, not including the player/dealer

            data_dir:    Disk storage location for the memory mapped hand array
        """
        
        if data_dir is None:
            data_dir = self.tmp_dir
        
        all_players = num_players+1


        #hands - Flatolds the hands drawn for every round
        #In each round, 4 player hands play against one dealer hand
        #Format:
        #    [(dealer_card_0.0, dealer_card_0.1, dealer_card_1.2),
        #     (player_card_0.0.0, player_card_0.0.1, player_card_0.0.2),
        #     (player_card_0.1.0, player_card_0.1.1, player_card_0.1.2),
        #     (player_card_0.2.0, player_card_0.2.1, player_card_0.2.2),
        #     (player_card_0.3.0, player_card_0.3.1, player_card_0.3.2),
        #     (dealer_card_1.0, ...]

        hands = np.memmap(path.join(data_dir,'played_hands'), dtype='int32', mode='w+', shape=(num_rounds * all_players, 3))


        bank_rounds = hands.reshape(-1, 3 * all_players)    #3 card per hand
        full_deck = Deck.GetFullDeck()

        for bank_round in bank_rounds:
            #Draw dealer hand and player hands from a single deck for each round
            bank_round[:] = np.random.choice(full_deck, size=3*all_players, replace=False)

        return hands


    def evaluate_hand(self, hand):
        """
        Evaluate a single Three Card Poker hand
        Useful for testing
        """
        prime = 1
        suit = 0xF000

        for card in hand:
            prime *= card & 0xFF
            suit &= card

        suited = 1 if suit else 0

        return self.tc_lookup.lookup[prime] - suited * self.tc_lookup.FLUSH_OFFSET


    def evaluate_hands(self, hands, data_dir=None):
        """
        Evaluate an array of Three Card Poker hands
        Return an array of corresponding hand ranks
        """
        
        if data_dir is None:
            data_dir = self.tmp_dir
        
        num_hands = len(hands)
        

        #int rank value, A=12, K=11, etc..
        hand_ranks = np.memmap(path.join(data_dir,'hand_ranks'), dtype='int32', mode='w+', shape=(num_hands, 3))
        
        #Equals FLUSH_OFFSET for suited hands and 0 for unsuited hands
        hand_flush_adj = np.memmap(path.join(data_dir, 'hand_flush_adjs'), dtype='int32', mode='w+', shape=(num_hands))

        #Multiplied hand ranks (hand_rank[0] * hand_rank[1] * hand_rank[2])
        hand_primes = np.memmap(path.join(data_dir,'hand_primes'), dtype='int32', mode='w+', shape=(num_hands))
        
        #Output array
        hand_values = np.memmap(path.join(data_dir, 'hand_values'), dtype='int32', mode='w+', shape=(num_hands))

        
        #Array-wide version of tc_evaluate_hand
        
        #Equivalent to:
        #hand_value[i] = self.tc_lookup.lookup[(hands[i][0] & 0xFF) * (hands[i][1] & 0xFF) * (hands[i][2] & 0xFF)]
        #                    - FLUSH_OFFSET * (hands[i][0] & hands[i][1] & hands[i][2] & 0xF000)

        hand_ranks[:] = hands & 0xFF
        hand_primes[:] = np.multiply.reduce(hand_ranks, axis=1)
        
        #We want to use bitwise_and.reduce(axis=1) here, but there are known bugs in its implementation
        #that keep it from doing what we expect.  We settle for using DeMorgan's identity as recommended
        #http://stackoverflow.com/questions/21050875/numpy-bitwise-and-reduce-behaving-unexpectedly
        hand_flush_adj[:] = np.where(~np.bitwise_or.reduce(np.invert(hands), axis=1) & 0xF000, self.tc_lookup.FLUSH_OFFSET, 0)

        tc_eval = np.vectorize(lambda x: self.tc_lookup.lookup[x])
        hand_values[:] = tc_eval(hand_primes) - hand_flush_adj
        
        del hand_ranks
        del hand_flush_adj
        del hand_primes
        
        return hand_values


    def GenerateMultipliers(self, hands, hand_values, num_players=4, data_dir=None):
        """
        Generates an array full of multipliers used to calculate the results of gameplay
        
        hands =         Array of hands (rounds*all_hands_per_round, 3) with format:
                        [[dealer_Cards], [player1_cards], [player2_cards], [player3_cards], ...]
            
        hand_values =   Array of the associated hand ranks returned from evaluate_hands
        
        num_players =   Number of players per round (excluding the player/dealer)
        
        
        Returns array of multipliers (num_rounds,num_players,4) specifying the following for each hand:

            multipliers[round,hand,0]:    Play multiplier -- determines whether hand should be played
                                                             and whether it wins, loses, or pushes
                                                             (1 = win, -1 = loss, 0 = no play or push)
                                                            
            multipliers[round,hand,1]:    Ante multiplier -- 0 = ante pushes, 1 = ante wins, -1 = ante loses
            
            multipliers[round,hand,2]:    Pair Plus multiplier -- -1 if Pair Plus loses, otherwise the bonus multiple
            
            multipliers[round,hand,3]:    6-Card Multiplier -- -1 if 6-Card bonus loses, otherwise the bonus multiple
        """
        
        if data_dir is None:
            data_dir = self.tmp_dir


        all_hands = num_players+1        
        num_rounds = len(hands)/all_hands

        multipliers = np.memmap(path.join(data_dir,'multipliers'), dtype='int32', mode='w+', shape=(num_rounds, num_players, 4))

        play_multipliers = multipliers[:,:,0]
        ante_multipliers = multipliers[:,:,1]
        pair_plus_multipliers = multipliers[:,:,2]
        six_card_multipliers = multipliers[:,:,3]


        #group hand values into sets of 1 dealer hand + related player hands
        #Split the dealer values into one group and player values into another
        splittable_values = hand_values.reshape(-1, all_hands)
        dealer_values = splittable_values.T[0].reshape(-1, 1)
        player_values = splittable_values.T[1:].T


        #Lower valued hands beat higher valued hands
        #Win_lose = -1 for player hands that lose, 1 for wins, and 0 for ties
        win_lose = np.memmap(path.join(data_dir,'win_lose'), dtype='int32', mode='w+', shape=(num_rounds, num_players))
        win_lose[:] = np.copysign(1, dealer_values - player_values)
        
        #Hand and card ranks needed to determine when play bet should be made for each hand
        #The suits are arbitrary as long as these are unsuited hands
        ACE_HIGH = self.evaluate_hand(Card.hand_to_binary(['Ac','2d','4d']))
        KING_HIGH = self.evaluate_hand(Card.hand_to_binary(['Kc','2d','3d']))
        QUEEN_HIGH = self.evaluate_hand(Card.hand_to_binary(['Qc','2d','3d']))
        ACE = Card.get_rank_int(Card.new('Ac'))
        KING = Card.get_rank_int(Card.new('Kc'))
        QUEEN = Card.get_rank_int(Card.new('Qc'))

        
        #In each round, one dealer card is dealt face up
        #Here we build an array view containing the first dealer card for each round as our face up card
        #hands.reshape(1,-1)[0] is equivalent to hands.flatten() without copying into a new array
        
        dealer_face_up = hands.reshape(1,-1)[0][0::all_hands*3].reshape(-1,1)


        #Face up dealer cards are converted to int ranks
        #face_up_rank = (dealer_face_up>>8)&0xFF

        #Hand plays based on House Way:
        #    Always play A high or better
        #    Play K high if dealer face up card is K or worse
        #    Play Q high if dealer face up card is Q or worse
        #    Never play hands less than Q high

        #Play the hand = 1, don't play = 0

        play_multipliers[:] = np.where(player_values <= ACE_HIGH, 1,
                                  np.where(player_values <= KING_HIGH, np.where((dealer_face_up>>8)&0xF < ACE, 1, 0),
                                      np.where(player_values <= QUEEN_HIGH, np.where((dealer_face_up>>8)&0xF < KING, 1, 0), 0)))

        
        #Pair Plus bonus loses (-1) when a player's hand is less than a pair
        #Otherwise it pays a multiple of the bet depending on the hand strength for pairs and better
        #The bet plays independently of the hand winning or losing,
        #but if the player does not make a play bet, the Pair Plus bonus is forfeit (-1)

        #Pay chart
        #    Worse than one pair:  -1
        #    Pair: 1x
        #    Flush: 3x
        #    Straight: 6x
        #    Straight flush: 30x
        #    Royal flush: 50x

        pair_plus_multipliers[:] = np.where(play_multipliers == 0, -1,
                                       np.where(player_values > self.tc_lookup.MAX_PAIR, -1,
                                           np.where(player_values > self.tc_lookup.MAX_FLUSH, 1,
                                               np.where(player_values > self.tc_lookup.MAX_STRAIGHT, 3,
                                                  np.where(player_values > self.tc_lookup.MAX_TRIPS, 6,
                                                      np.where(player_values > self.tc_lookup.MAX_STRAIGHT_FLUSH, 30,
                                                          np.where(player_values > 1, 40, 50)))))))
        
        #Calculate Ante wins/losses
        #If a play bet is not made, ante loses (-1) automatically
        #If a play bet is made:
        #    Hand wins:  ante wins (+1)
        #    Hand loses: ante loses (-1) if dealer has Q high or better, otherwise pushes (0)

        ante_multipliers[:] =  np.where(play_multipliers == 0, -1,
                                   np.where(win_lose > -1, win_lose,
                                       np.where(dealer_values <= QUEEN_HIGH, -1, 0)))
        
        #Calculate Play wins/losses
        #We need to do this after calculating the Pair Plus bonus
        #so we don't confuse ties with forfeit hands
        #If the dealer hand is worse than Q high, the Play bet pushes (0)
        
        play_multipliers[:] = np.where(dealer_values <= QUEEN_HIGH, play_multipliers*win_lose, 0)

        del win_lose


        #Now we need to compute the 6-card bonuses
        #These are based on the best 5-card hand that can be made from the player's 3 card and the dealer's 3

        #The first out of each group of hands is the dealer hand for that group
        #The rest are the player hands
        #we want groups like: [dcard1, dcard2, dcard3, pcard1, pcard2, pcard3]
        #to pass to deuces' hand evaluator
        #This requires some slicing arobatics to avoid building new arrays

        #Hands are arranged by round such as dealer_cards, player1_cards, player2_cards, etc.
        #Then stepped slices are taken and truncated to form slices for each combo of dealer and player cards

        #eg. If hands = [D01, D02, D03, Pa1, Pa2, Pa3, Pb1, Pb2, Pb3,
        #                D11, D12, D13, Pc1, Pc2, Pc3, Pd1, Pd2, Pd3]
        #
        #Then eval_hands[0] = [[D01, D02, D03, Pa1, Pa2, Pa3],
        #                      [D11, D12, D13, Pc1, Pc2, Pc3]]
        #
        #     eval_hands[1] = [[D01, D02, D03, Pb1, Pb2, Pb3],
        #                      [D11, D12, D13, Pd1, Pd2, Pd3]]

        eval_hands = [hands.reshape(-1,all_hands,3)[:,::i+1][:,:2].reshape(-1,6) for i in xrange(num_players)]

        #calculate 6card bonuses
        evaluator = Evaluator()

        
        #This is the main bottleneck in the simulator
        #The only real way to resolve it is to rebuild the deuces library's
        #hand evaluator to process arrays of hands rather than one at a time,
        #which is currently beyond the scope of this project
        
        for i in xrange(num_players):
            six_card_multipliers[:,i] = np.apply_along_axis(evaluator._six, 1, eval_hands[i])

        #Map hand values to bonus payouts

        SC_MAX_STRAIGHT_FLUSH  = evaluator.table.MAX_STRAIGHT_FLUSH
        SC_MAX_QUADS           = evaluator.table.MAX_FOUR_OF_A_KIND
        SC_MAX_FULL_HOUSE      = evaluator.table.MAX_FULL_HOUSE 
        SC_MAX_FLUSH           = evaluator.table.MAX_FLUSH
        SC_MAX_STRAIGHT        = evaluator.table.MAX_STRAIGHT
        SC_MAX_TRIPS           = evaluator.table.MAX_THREE_OF_A_KIND

        #6-Card Bonus Payout table
        #Worse than trips  -1
        #Trips              5
        #Straight           10
        #Flush              15
        #Full House         25
        #Quads              50
        #Straight Flush     200
        #Royal Flush        1000

        six_card_multipliers[:] = np.where(six_card_multipliers > SC_MAX_TRIPS, -1,
                                           np.where(six_card_multipliers > SC_MAX_STRAIGHT, 5,
                                               np.where(six_card_multipliers > SC_MAX_FLUSH, 10,
                                                  np.where(six_card_multipliers > SC_MAX_FULL_HOUSE, 15,
                                                      np.where(six_card_multipliers > SC_MAX_QUADS, 25,
                                                          np.where(six_card_multipliers > SC_MAX_STRAIGHT_FLUSH, 50,
                                                              np.where(six_card_multipliers > 1, 200, 1000)))))))

        return multipliers


    def AdjustForAction(self, payouts, bank_amount, data_dir=None):
        """
        Adjust for situations when the Max Payout does not cover all players' bets
        
        Since players may put up any amount of their choosing (the "bank") to play as the house
        in California casinos, the amount they risk may not be enough to cover all other
        players' payouts
        
        When this happens, wins and losses are matched up against the bank
        until it is exhausted.  Most casinos use one of the hidden dealer cards to randomize
        where action starts for the benefit of the players, but for our puposes, starting from
        seat one is sufficient.
        """

        if data_dir is None:
            data_dir = self.tmp_dir
        
        num_rounds = payouts.shape[0]
        num_players = payouts.shape[1]
        
        #We check all 4 betting spots (play, ante, pair plus, 6-card) for each hand in turn,
        #hence num_players*4 as the width for each array in this function
        payouts = payouts.reshape(num_rounds, num_players*4)
        
        cum_payout = np.memmap(path.join(data_dir,'cum_payout'), dtype='int32', mode='w+', shape=(num_rounds,num_players*4))
        adj_payouts = np.memmap(path.join(data_dir,'adj_payouts'), dtype='int32', mode='w+', shape=(num_rounds,num_players*4))
        
        #cum_payout is filled with the running total of absolute dollar amounts of wins and losses per round
        cum_payout[:] = np.absolute(payouts.reshape(-1,num_players*4)).cumsum(axis=1)
        
        #If the first win or loss exceeds the amount in the bank,
        #Then the win or loss is capped at the amount in the bank
        adj_payouts[:,0] = np.where(cum_payout[:,0] < bank_amount, payouts[:,0], np.copysign(bank_amount, payouts[:,0]))
        
        #For all bets after the first, check to see if the bank has been exhausted
        #If this is the last bet being matched against the bank, the win or loss needs to be
        #adjusted to the remaining bank balance.
        #If a previous bet has already exhausted the bank, no subsequent bets are paid or collected,
        #so this bet's payout should be 0
        for i in xrange(1, num_players*4):
            adj_payouts[:,i] = np.where(cum_payout[:,i] < bank_amount, payouts[:,i],
                                         np.where(cum_payout[:,i-1] < bank_amount,
                                                  np.copysign(bank_amount - cum_payout[:,i-1], payouts[:,i]), 0))

        return adj_payouts.reshape(num_rounds, num_players, 4)
