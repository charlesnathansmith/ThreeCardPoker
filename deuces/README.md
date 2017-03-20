deuces is a library created by Will Drevos for analyzing 5-, 6-, and 7-card poker hands.
https://github.com/worldveil/deuces 

We borrow some techniques and data structures from his work in our Three Card Poker libraries, and use his 6-card hand evaluator to process the 6-card bonuses in our game.

Our evaluators offer signifant speed improvement over his work by using NumPy's vectorized calculations to process large arrays of hands at a time.

The deuces libraries are included here for reference, and for easy building of our own libraries without having to explicitly install these.
