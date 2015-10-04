from pandas.io.sql import read_sql
import pandas as pd
import numpy as np
import itertools
import os
import psycopg2


class WineRanking(object):

    def __init__(self, country, grape, rating_cutoff, wine_type_id):
        """
        INPUT:
            country (str) - country to limit search to
            grape (str) - grape name
            rating_cutoff (int) - number of reviews wine needs to have
            wine_type_id (int) - type id to narrow results by
        OUTPUT:
            None
        Queries database and returns pandas dataframe.
        """
        self.country = country
        self.grape = grape
        self.rating_cutoff = rating_cutoff
        self.wine_type_id = wine_type_id

    def get_data(self):
        """
        INPUT:
            None
        OUTPUT:
            df
        Queries database and returns pandas dataframe.
        """
        postgres_pass = os.getenv('POSTGRES_PASSWORD')
        conn = psycopg2.connect(database='vivino', user='postgres',
                                password=postgres_pass)
        query = '''SELECT vintage_id, user_id, rating
                   FROM cleaned
                   WHERE country=%s AND wine_grape_name=%s AND
                   rate_count>%d AND wine_type_id=%d;''' % (self.country,
                                                            self.grape,
                                                            self.rating_cutoff,
                                                            self.wine_type_id)
        return read_sql(query, conn)

    def clean_data(self, df):
        """
        INPUT:
            df (df) - Dataframe to be cleaned.
        OUTPUT:
            df
        Cleans the data before processing.
        """
        # Cast as int (Default was float)
        df['vintage_id'] = df['vintage_id'].astype('int')
        df['user_id'] = df['user_id'].astype('int')
        df = df.drop_duplicates(['vintage_id', 'user_id'])
        return df

    def pivot_table(self, df):
        """
        INPUT:
            df (df) - Dataframe to pivot.
        OUTPUT:
            df
        Pivots dataframe to put users as columns, wines as rows,
            ratings as values.
        """
        # Pivot for more useful dataframe
        data_pivot = df.pivot('vintage_id', 'user_id', 'rating')
        return data_pivot

    def get_values(self, column, wins_dict, total_dict, pairs_dict):
        """
        INPUT:
            column (array) - Column corresponding to one user's ratings.
            wins_dict (dict) - dict with wines as keys, wins as values.
            total_dict (dict) - dict with wines as keys, 'games played'
                                as values.
            pairs_dict (dict) - dict with wine pairs as keys, 'matches played'
                                as values.
        OUTPUT:
            dict, dict, dict
        Inputs information into dicts based on one user's ratings.
        """
        # Get non-NaN ratings for the user
        filtered = column[column > 0]
        vintages = list(filtered.index)

        # Need more than one wine to make pairs
        if len(vintages) > 1:
            # Make list of all possible pairs of vintages rated by user
            combinations = itertools.combinations(vintages, 2)
            for combination in combinations:
                wines = (combination[0], combination[1])
                if filtered[wines[0]] == filtered[wines[1]]:
                    # Wines tied. Count as two games where each wine won one.
                    for wine in wines:
                        wins_dict[wine] += 1
                        total_dict[wine] += 1
                    pairs_dict[combination] += 1
                elif filtered[wines[0]] > filtered[wines[1]]:
                    # Win goes to wine 1
                    wins_dict[wines[0]] += 1
                else:
                    # Win goes to wine 2
                    wins_dict[wines[1]] += 1

                for wine in wines:
                    # Add to number of games played for each wine
                    total_dict[wine] += 1
                # Add to games played between the two wines
                pairs_dict[combination] += 1
        return wins_dict, total_dict, pairs_dict

    def create_dicts(self, df):
        """
        INPUT:
            df (df) - Pivoted dataframe.
        OUTPUT:
            dict, dict, dict
        Initializes and fills dictionaries.
        """
        users = list(df.columns.values)
        vintages = list(df.index)

        # Get all possible pairs of vintages
        combinations = itertools.combinations(vintages, 2)

        # Initialize dicts
        wins_dict = dict.fromkeys(vintages, 0)
        total_dict = dict.fromkeys(vintages, 0)
        pairs_dict = dict.fromkeys(combinations, 0)
        # Calculate wins and losses for each wine
        for user in users:
            wins_dict, total_dict, pairs_dict = self.get_values(df[user],
                                                                wins_dict,
                                                                total_dict,
                                                                pairs_dict)
        return wins_dict, total_dict, pairs_dict

    def solve(self, vintages, wins_dict, total_dict, pairs_dict):
        """
        INPUT:
            vintages (list) - list of all wines in dataframe.
            wins_dict (dict) - dict with wines as keys, wins as values.
            total_dict (dict) - dict with wines as keys, 'games played'
                                as values.
            pairs_dict (dict) - dict with wine pairs as keys,
                                'matches played' as values.
        OUTPUT:
            df
        Solves matrix equation and returns sorted dataframe based on ranking.
        """
        # Initialize matrix and column vector to fill with calculated values
        vint_len = len(vintages)
        matrix = np.zeros((vint_len, vint_len))
        col_vector = np.zeros((vint_len, 1))

        # Fill the matrix and vector
        for ix in xrange(vint_len):
            wins = wins_dict[vintages[ix]]
            total = total_dict[vintages[ix]]
            losses = total - wins
            col_vector[ix] = 1 + (wins - losses)/2.0
            for jx in xrange(vint_len):
                if ix == jx:
                    matrix[ix][jx] = total + 2
                else:
                    tup_key = tuple(sorted((vintages[ix], vintages[jx])))
                    matrix[ix][jx] = -pairs_dict[tup_key]

        # Solve matrix equation to obtain calculated ratings
        new_ratings = np.linalg.solve(matrix, col_vector)
        final = pd.DataFrame(np.column_stack(
                                            (np.array(vintages), new_ratings)
                                            ),
                             columns=['vintage_id', 'rating'])
        # Final array with vintages and calculated ratings
        return final.sort('rating', axis=0, ascending=False)

    def rank_wines(self):
        """
        INPUT:
            None
        OUTPUT:
            df
        Returns sorted dataframe based on ranking.
        """
        df = self.get_data()
        df = self.clean_data(df)
        data_pivot = self.pivot_table(df)

        wins_dict, total_dict, pairs_dict = self.create_dicts(data_pivot)

        vintages = list(data_pivot.index)
        self.ranking = self.solve(vintages, wins_dict, total_dict, pairs_dict)
        return self.ranking
