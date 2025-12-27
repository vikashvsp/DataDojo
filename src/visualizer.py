import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for server
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import json
from .ai_client import AIClient

class Visualizer:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def _get_gemini_config(self, df, sql_query):
        """Asks AI for the best visualization config."""
        try:
            client = AIClient(self.api_key)
            
            # Prepare data sample (first 5 rows)
            data_sample = df.head().to_string()
            
            prompt = (
                f"I have a pandas DataFrame with this data:\n{data_sample}\n"
                f"It is the result of this SQL query: '{sql_query}'\n"
                "Recommend the best matplotlib chart to visualize this data.\n"
                "Return ONLY a JSON object with this structure (no markdown, no code blocks):\n"
                "{\n"
                "  \"chart_type\": \"bar\" | \"line\" | \"scatter\" | \"pie\",\n"
                "  \"x_column\": \"column_name\",\n"
                "  \"y_column\": \"column_name\",\n"
                "  \"title\": \"Chart Title\",\n"
                "  \"xlabel\": \"Label for X axis\",\n"
                "  \"ylabel\": \"Label for Y axis\"\n"
                "}"
            )
            
            text = client.generate_content(prompt).strip()
            
            # Clean response
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            return json.loads(text)
        except Exception as e:
            print(f"AI Viz Error: {e}")
            return None

    def create_chart(self, df, sql_query=""):
        """
        Analyzes the DataFrame and creates a chart if applicable.
        Returns a base64 encoded image string or None.
        """
        if df.empty or 'error' in df.columns:
            return None

        plt.figure(figsize=(10, 6))
        chart_created = False

        # Try AI first
        if self.api_key:
            config = self._get_gemini_config(df, sql_query)
            if config:
                try:
                    chart_type = config.get('chart_type')
                    x = config.get('x_column')
                    y = config.get('y_column')
                    
                    if chart_type == 'bar':
                        plt.bar(df[x], df[y])
                    elif chart_type == 'line':
                        plt.plot(df[x], df[y], marker='o')
                    elif chart_type == 'scatter':
                        plt.scatter(df[x], df[y])
                    elif chart_type == 'pie':
                        plt.pie(df[y], labels=df[x], autopct='%1.1f%%')
                    
                    plt.title(config.get('title', ''))
                    if chart_type != 'pie':
                        plt.xlabel(config.get('xlabel', ''))
                        plt.ylabel(config.get('ylabel', ''))
                        plt.xticks(rotation=45)
                    
                    chart_created = True
                except Exception as e:
                    print(f"AI Charting Error: {e}")
                    plt.clf() # Clear if failed

        # Fallback heuristic
        if not chart_created:
            num_cols = df.select_dtypes(include=['number']).columns
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            
            if len(cat_cols) >= 1 and len(num_cols) >= 1:
                # Bar chart
                x_col = cat_cols[0]
                y_col = num_cols[0]
                plt.bar(df[x_col], df[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.title(f'{y_col} by {x_col}')
                plt.xticks(rotation=45)
            elif len(num_cols) >= 2:
                # Line chart (assuming sequence)
                x_col = num_cols[0]
                y_col = num_cols[1]
                plt.plot(df[x_col], df[y_col], marker='o')
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.title(f'{y_col} vs {x_col}')
            else:
                plt.close()
                return None

        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        # Encode to base64
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"
