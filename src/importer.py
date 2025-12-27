from apify_client import ApifyClient
import pandas as pd
import os

class ApifyImporter:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get("APIFY_TOKEN")
        if not self.api_token:
            print("Warning: No Apify Token provided. Scraper integration will fail.")
        else:
            self.client = ApifyClient(self.api_token)

    def fetch_dataset(self, dataset_id, max_items=1000):
        """
        Fetches items from an Apify Dataset and converts them to a DataFrame.
        """
        if not self.api_token:
            raise ValueError("Apify Token is missing. Please provide it in settings.")

        try:
            # Fetch items
            dataset_client = self.client.dataset(dataset_id)
            items = list(dataset_client.list_items(limit=max_items).items)
            
            if not items:
                return pd.DataFrame()

            # Flatten nested JSON if possible, but for now simple conversion
            # Using pandas json_normalize can help with nested structures
            df = pd.json_normalize(items)
            
            # Clean up columns (remove too many dots from flattening)
            df.columns = [c.replace('.', '_') for c in df.columns]
            
            # Heuristic: Drop columns that are entirely null or lists/dicts if simple SQL is desired
            # For now, let's keep them but maybe convert lists to strings for SQL storage
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                     df[col] = df[col].astype(str)
            
            return df

        except Exception as e:
            print(f"Error fetching dataset {dataset_id}: {e}")
            raise e
