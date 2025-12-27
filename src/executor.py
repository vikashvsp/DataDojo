import sqlite3
import pandas as pd

class SQLExecutor:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')

    def load_data(self, data_dict):
        """Loads pandas DataFrames into SQLite."""
        for table_name, df in data_dict.items():
            df.to_sql(table_name, self.conn, index=False, if_exists='replace')

    def execute(self, sql_query):
        """Executes the query and returns a DataFrame."""
        try:
            return pd.read_sql_query(sql_query, self.conn)
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
