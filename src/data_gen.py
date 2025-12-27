from faker import Faker
import pandas as pd
import random

fake = Faker()

class DataGenerator:
    def __init__(self):
        self.fake = Faker()

    def generate_data(self, tables_columns, num_rows=50):
        """
        Generates a dictionary of DataFrames.
        tables_columns: dict {table_name: [col1, col2, ...]}
        """
        data = {}
        
        for table, columns in tables_columns.items():
            table_data = {}
            # If no columns detected, generate some default ones
            if not columns:
                columns = ['id', 'name', 'created_at']

            for col in columns:
                table_data[col] = [self._generate_value(col) for _ in range(num_rows)]
            
            data[table] = pd.DataFrame(table_data)
            
        return data

    def _generate_value(self, column_name):
        """Heuristic to generate data based on column name."""
        col_lower = column_name.lower()
        
        if 'id' in col_lower:
            return self.fake.unique.random_int(min=1, max=1000)
        elif 'name' in col_lower:
            return self.fake.name()
        elif 'email' in col_lower:
            return self.fake.email()
        elif 'date' in col_lower or 'time' in col_lower:
            return self.fake.date_this_year()
        elif 'price' in col_lower or 'amount' in col_lower or 'salary' in col_lower:
            return round(random.uniform(10.0, 1000.0), 2)
        elif 'count' in col_lower or 'num' in col_lower:
            return random.randint(1, 100)
        elif 'department' in col_lower:
            return random.choice(['HR', 'Engineering', 'Sales', 'Marketing'])
        elif 'status' in col_lower:
            return random.choice(['Active', 'Inactive', 'Pending'])
        elif col_lower.startswith('is_') or col_lower.startswith('has_') or 'active' in col_lower:
            return random.choice([0, 1])
        else:
            return self.fake.word()
