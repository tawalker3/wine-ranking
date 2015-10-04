<h1>Wine Ranking Using Colley Matrix Method</h1>

The goal of this project was to develop a more absolute ranking system for the wines on a popular wine app.

<h2>Method</h2>

The Colley Matrix Method was used to determine the ranking of the wines in the database. This method is used to rank professional sports teams. It can be applied to wines by taking each user's wine ratings in a category (i.e. German Rieslings) and making pair-wise comparisons. In each "match", the wine with the higher rating receives a win. The total number of wins and losses are used to calculate a score. To account for "strength of schedule", the rating points added for the winning wine after each "match" are weighted by the strength of the other wine.
More details on the method can be found at this link: http://www.colleyrankings.com/matrate.pdf

<h2>Example Usage</h2>

This class is set up for the specific database used, but here is an example of how to use it to rank all the German Rieslings in the database with more than 1 review:

wr = WineRanking("'de'", "'Riesling'", 1, 2)
wr.rank_wines() # Call ranking method

The resulting table of wines ordered by their calculated ranking is also stored. It can be accessed by calling
the ranking attribute:

print wr.ranking
