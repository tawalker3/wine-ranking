<h1>Wine Ranking Using Colley Matrix Method</h1>

The goal of this project was to develop a more absolute ranking system for the wines on a popular wine app.

<h2>Method</h2>

The Colley Matrix Method was used to determine the ranking of the wines in the database. This method is used to rank professional sports teams. It can be applied to wines by taking each user's wine ratings in a category (i.e. German Rieslings) and making pair-wise comparisons. In each "match", the wine with the higher rating receives a win. The total number of wins and losses are used to calculate a score. To account for "strength of schedule", the rating points added for the winning wine after each "match" are weighted by the strength of the other wine.
More details on the method can be found at this link: http://www.colleyrankings.com/matrate.pdf

<h2>Example Usage</h2>

The data must be in a .csv file with columns "user_id", "vintage_id", and "rating". The class can then be used as shown below. "rates_min" is the minimum number of ratings a wine must have to be included in the final rankings list. Wines with fewer ratings than this are still included in calculations, because they provide information about how well other wines are competing overall.

```python
wr = WineRanking(csv_path='data.csv', rates_min=50, out_path='results.csv')
wr.rank_wines() # Call ranking method
```

The resulting table of wines ordered by their calculated ranking is also stored. It can be accessed by calling
the ranking attribute:
```python
print wr.ranking
```

This code can be used to rank other products, not just wines. The input csv should be structured similarly to the example above, except the "vintage_id" column would contain the id numbers for the products being ranked.

<b>Note:</b> This method may not work well for comparing across multiple subcategories of products due to variations in subcategory attributes. For example, red wines and white wines have significantly different defining characteristics, so should not be ranked together as one category.
