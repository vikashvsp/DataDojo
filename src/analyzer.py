import sqlglot
from sqlglot import exp
from .ai_client import AIClient

class SQLAnalyzer:
    def __init__(self, sql_query, api_key=None):
        self.sql_query = sql_query
        self.api_key = api_key
        self.parsed = None
        if sql_query:
            try:
                self.parsed = sqlglot.parse_one(sql_query)
            except Exception as e:
                # Store error but don't crash, allows using other methods like convert_to_sql
                print(f"Warning: SQL parsing failed: {e}")

    def get_tables(self):
        """Extracts table names from the query."""
        if not self.parsed: return []
        return [table.name for table in self.parsed.find_all(exp.Table)]

    def get_columns(self):
        """
        Extracts column names, resolving aliases to table names.
        """
        if not self.parsed: return {}
        columns = {}
        alias_map = {}

        # 1. Build Alias Map
        for table in self.parsed.find_all(exp.Table):
            if table.alias:
                alias_map[table.alias] = table.name
            # Also map the table name to itself
            alias_map[table.name] = table.name

        # 2. Extract Columns
        for col in self.parsed.find_all(exp.Column):
            # col.table might be an alias or a full table name
            table_ref = col.table
            
            real_table_name = None
            if table_ref:
                real_table_name = alias_map.get(table_ref)
            
            # If still not found, and we have only one table, assume it belongs there
            if not real_table_name:
                tables = self.get_tables()
                if len(tables) == 1:
                    real_table_name = tables[0]
            
            if real_table_name:
                if real_table_name not in columns:
                    columns[real_table_name] = set()
                columns[real_table_name].add(col.name)
        
        return columns

    def explain(self):
        """Generates a natural language explanation."""
        if self.api_key:
            try:
                client = AIClient(self.api_key)
                prompt = (
                    f"Act as an expert SQL tutor. Explain this SQL query in detail to a beginner: '{self.sql_query}'.\n"
                    "Structure your explanation as follows:\n"
                    "1. **Concept**: Briefly explain the core SQL concept being used (especially if this looks like a demo query).\n"
                    "2. **Order of Execution**: Explain the steps in the logical order the database executes them (e.g., FROM -> WHERE -> GROUP BY -> SELECT).\n"
                    "3. **Data Flow**: Describe how data is filtered, transformed, or aggregated at each step.\n"
                    "4. **Business Context**: Infer a likely business scenario for this query.\n"
                    "5. **Metadata Reasoning**: Explain WHY the query is structured this way. For example: 'Detected GROUP BY because aggregation (COUNT) is used', 'Primary table inferred: employees', 'Relevant columns identified: department'.\n"
                    "Keep it clear, educational, and engaging."
                )
                return client.generate_content(prompt)
            except Exception as e:
                print(f"AI Error: {e}")
                # Fallback to basic explanation with error note
                return f"**AI API Error**: {str(e)}<br><br>**Basic Explanation**: The query performs an operation on the following tables: {', '.join(self.get_tables())}."

        # sqlglot has a transpiler, but not a "explainer". 
        # We'll construct a simple one.
        explanation = []
        explanation.append(f"The query performs an operation on the following tables: {', '.join(self.get_tables())}.")
        
        if self.parsed and self.parsed.find(exp.Group):
            explanation.append("It groups the results.")
        
        if self.parsed and self.parsed.find(exp.Order):
            explanation.append("It orders the output.")
            
        if self.parsed and self.parsed.find(exp.Join):
            explanation.append("It joins multiple tables together.")

        return " ".join(explanation)

    def convert_to_sql(self, text):
        """Converts natural language to SQL using Gemini."""
        if not self.api_key:
            return None
            
        try:
            client = AIClient(self.api_key)
            prompt = (
                f"You are a SQL expert. Convert this input to a standard SQL query: '{text}'.\n"
                "Rules:\n"
                "1. If the input is a specific data request (e.g., 'Show top sales'), convert it to SQL.\n"
                "2. If the input is a CONCEPTUAL question (e.g., 'What is a Window Function?', 'Explain LEFT JOIN'), generate a VALID SQL query that DEMONSTRATES that concept clearly.\n"
                "   - Use standard tables: 'employees' (id, name, department, salary, hire_date), 'sales' (id, product, amount, date), 'products' (id, name, price).\n"
                "   - For 'Window Function', generate a query using `AVG() OVER()` or `RANK()`.\n"
                "   - For 'JOIN', generate a query joining employees and sales.\n"
                "3. Return ONLY the SQL string. No markdown, no explanations."
            )
            sql = client.generate_content(prompt).strip()
            
            # Clean up potential markdown if Gemini ignores instructions
            if sql.startswith("```sql"):
                sql = sql[6:-3]
            elif sql.startswith("```"):
                sql = sql[3:-3]
            
            return sql.strip()
        except Exception as e:
            print(f"AI NL2SQL Error: {e}")
            return None

    def generate_data_insights(self, df):
        """Generates insights from the query results using Gemini."""
        if not self.api_key:
            return "Please provide a valid Gemini API Key to see AI-generated insights."
        if df.empty:
            return "No data available to generate insights."
            
        try:
            client = AIClient(self.api_key)
            
            # Prepare data sample (first 20 rows to avoid token limits)
            data_sample = df.head(20).to_string()
            
            prompt = (
                f"Analyze this data resulting from the SQL query '{self.sql_query}':\n{data_sample}\n"
                "Provide a smart, one-paragraph natural-language data insight report.\n"
                "Include specific details like:\n"
                "- Top/Bottom performers (with specific values)\n"
                "- Key trends or distributions (e.g., uneven distribution)\n"
                "- Potential anomalies or business implications (e.g., resource gaps)\n"
                "Make it sound like a professional data analyst."
            )
            return client.generate_content(prompt)
        except Exception as e:
            error_msg = f"AI Insights Error: {str(e)}"
            print(error_msg)
            return error_msg

    def fix_sql_error(self, broken_sql, error_message):
        """Fixes a broken SQL query using Gemini."""
        if not self.api_key:
            return None
            
        try:
            client = AIClient(self.api_key)
            
            prompt = (
                f"The following SQL query failed with an error:\n"
                f"Query: '{broken_sql}'\n"
                f"Error: '{error_message}'\n"
                "Fix the SQL query to resolve the error. Return ONLY the corrected SQL string (no markdown, no explanations)."
            )
            sql = client.generate_content(prompt).strip()
            
            # Clean up potential markdown
            if sql.startswith("```sql"):
                sql = sql[6:-3]
            elif sql.startswith("```"):
                sql = sql[3:-3]
            
            return sql.strip()
        except Exception as e:
            print(f"AI Auto-Fix Error: {e}")
            return None
