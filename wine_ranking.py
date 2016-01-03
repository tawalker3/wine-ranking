import pandas as pd
import numpy as np
import itertools
from collections import Counter
from scipy import linalg


class WineRanking(object):

    def __init__(self, csv_path, rates_min, out_path):
        """
        INPUT:
            csv_path (str) - path to csv file from which to load data.
            rates_min (int) - number of ratings wine needs to have.
            out_path (str) - csv file path to write results.
        OUTPUT:
            None
        Sets variables for csv file paths and minimum number of ratings for a
        wine to be considered.
        """

        self.csv_path = csv_path
        self.rates_min = rates_min
        if out_path[-4:] != '.csv':
            raise Exception('out_path must be .csv format.')
        self.out_path = out_path

    def clean_data(self, df):
        """
        INPUT:
            df (df) - Dataframe to be cleaned.
        OUTPUT:
            df
        Cleans the data before calculations.
        """
        # Cast as int (Default was float)
        df['vintage_id'] = df['vintage_id'].astype('int')
        df['user_id'] = df['user_id'].astype('int')
        df = df.drop_duplicates(['vintage_id', 'user_id'])
        users = df['user_id']
        c = Counter(users)
        users = set(users)
        keep = set()
        # Only consider users with at least 2 ratings to reduce memory usage
        for user in users:
            if c[user] > 1:
                keep.add(user)
        df = df[df['user_id'].isin(keep)]
        return df

    def get_values(self, column, vint_d, wins_d):
        """
        INPUT:
            column (array) - Column corresponding to one user's ratings.
            vint_d (dict) - Nested dict with wines as keys, dicts as values.
                            The dict for each wine contains wines
                            the key wine has 'played' as keys and the values
                            are the negative number of times they have
                            'played'.
            wins_d (dict) - Dict with wines as keys, 'games played'
                            as values.
        OUTPUT:
            dict, dict
        Inputs information into dicts based on one user's ratings.
        """
        # Get non-NaN ratings for the user
        filtered = column[column > 0]
        vintages = set(filtered.index)  # Set of all vintage ids user has rated

        if len(vintages) > 1:
            combinations = itertools.combinations(vintages, 2)
            for combination in combinations:
                wine1, wine2 = combination[0], combination[1]
                # Wines 'played' once. Subtract 1 from negative games played
                vint_d[wine1][wine2] = vint_d[wine1].get(wine2, 0) - 1
                vint_d[wine2][wine1] = vint_d[wine2].get(wine1, 0) - 1
                # Add 1 to total games played for each wine.
                vint_d[wine1][wine1] += 1
                vint_d[wine2][wine2] += 1
                # Account for ties. Counts as 2 games. Each won 1, lost 1
                if filtered[wine1] == filtered[wine2]:
                    wins_d[wine1] += 1
                    wins_d[wine2] += 1
                    vint_d[wine1][wine1] += 1
                    vint_d[wine2][wine2] += 1
                    vint_d[wine1][wine2] -= 1
                    vint_d[wine2][wine1] -= 1
                # Wine 1 won, add 1 to wins
                elif filtered[wine1] > filtered[wine2]:
                    wins_d[wine1] += 1
                # Wine 2 won, add 1 to wins
                else:
                    wins_d[wine2] += 1
        return vint_d, wins_d

    def create_dicts(self, df):
        """
        INPUT:
            df (df) - Pivoted dataframe.
        OUTPUT:
            dict, dict
        Initializes and fills dictionaries.
        """
        users = list(df.columns.values)
        vintages = set(df.index)

        # Initialize dicts
        vint_d = {}
        wins_d = dict.fromkeys(vintages, 0)
        for vintage in vintages:
            d = {vintage: 2}  # Start with 2. Will add games played below.
            vint_d[vintage] = d
        # Calculate wins and losses for each wine.
        for user in users:
            vint_d, wins_d = self.get_values(df[user], vint_d, wins_d)
        return vint_d, wins_d

    def solve(self, vintages, vint_d, wins_d):
        """
        INPUT:
            vintages (list) - list of all wines in dataframe.
            vint_d (dict) - Nested dict with wines as keys, dicts as values.
                            The dict for each wine contains wines
                            the key wine has 'played' as keys and the values
                            are the negative number of times they have
                            'played'.
            wins_d (dict) - Dict with wines as keys, 'games played'
                            as values.
        OUTPUT:
            df
        Solves matrix equation and returns sorted dataframe based on ranking.
        """
        # Initialize matrix and column vector to fill with calculated values.
        vintages = sorted(vintages)
        matrix = np.array(pd.DataFrame(vint_d))
        col_vector = np.zeros((len(vintages), 1))

        # Fill the column vector.
        for ix in xrange(len(vintages)):
            vintage = vintages[ix]
            wins = wins_d[vintage]
            total = vint_d[vintage][vintage] - 2
            losses = total - wins
            col_vector[ix] = 1 + (wins - losses) / 2.0
        # Solve matrix equation to obtain calculated ratings.
        matrix = np.nan_to_num(matrix)  # Replace NaNs with zeros.
        new_ratings = linalg.solve(matrix, col_vector, sym_pos=True,
                                   overwrite_a=True, overwrite_b=True)
        final = pd.DataFrame(np.column_stack(
                                            (np.array(vintages), new_ratings)
                                            ),
                             columns=['vintage_id', 'score'])
        # Get number of ratings for each wine.
        final['n_rate'] = final['vintage_id'].apply(lambda x: self.rate_cnt[x])
        # Only include wines with at least rates_min ratings.
        final = final[final['n_rate'] >= self.rates_min]
        # Final array with vintages and calculated ratings
        return final.sort('score', axis=0, ascending=False)

    def rank_wines(self):
        """
        INPUT:
            None
        OUTPUT:
            df
        Returns sorted dataframe based on ranking.
        """
        # Read data from csv and clean it.
        df = pd.read_csv(self.csv_path)
        self.df = self.clean_data(df)
        # Pivot for more useful dataframe
        data_pivot = self.df.pivot('vintage_id', 'user_id', 'rating')
        # Get number of ratings for each wine
        self.rate_cnt = data_pivot.count(axis=1)
        # Calculate values and fill dicts
        vint_d, wins_d = self.create_dicts(data_pivot)

        vintages = list(data_pivot.index)
        # Solve the matrix equation
        ranking = self.solve(vintages, vint_d, wins_d)
        ranking['vintage_id'] = ranking['vintage_id'].astype('int')
        self.ranking = ranking.reset_index(drop=True)
        # Write results to csv
        self.ranking.to_csv(self.out_path)
        return self.ranking
