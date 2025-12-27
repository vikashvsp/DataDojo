import os
import sys
import base64
import pandas as pd
from src.analyzer import SQLAnalyzer
from src.data_gen import DataGenerator
from src.executor import SQLExecutor
from src.visualizer import Visualizer

# Helper to clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*60)
    print("       🎓 SQL INTERACTIVE TUTOR (Powered by Gemini) 🎓")
    print("="*60)
    print("Type your SQL query OR a natural language question to learn.")
    print("Example: 'Show me average salary by department'")
    print("Type 'exit' to quit.")
    print("-" * 60)

def main():
    clear_screen()
    print_header()

    # Get API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Tip: Set GEMINI_API_KEY env var to skip this step.")
        api_key = input("Enter your Gemini API Key: ").strip()
        if not api_key:
            print("Warning: No API Key provided. Explanations and Viz will be limited.")
    
    while True:
        print("\n" + "-"*60)
        user_input = input("\nQuery > ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye! Keep practicing! 👋")
            break
            
        if not user_input:
            continue

        try:
            # Check if input looks like SQL
            is_sql = user_input.strip().upper().startswith(("SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"))
            
            sql_query = user_input
            if not is_sql:
                print("\n🤖 Detecting Natural Language...")
                analyzer_temp = SQLAnalyzer("", api_key=api_key)
                converted_sql = analyzer_temp.convert_to_sql(user_input)
                if converted_sql:
                    print(f"✨ Converted to SQL: {converted_sql}")
                    sql_query = converted_sql
                else:
                    print("⚠️ Could not convert to SQL. Trying as is...")

            print("\n🔍 Analyzing...")
            
            # 1. Analyze
            analyzer = SQLAnalyzer(sql_query, api_key=api_key)
            tables = analyzer.get_tables()
            columns = analyzer.get_columns()
            explanation = analyzer.explain()
            
            print(f"\n📝 EXPLANATION:\n{explanation}")
            print(f"\n📋 Tables Involved: {', '.join(tables)}")

            # 2. Generate Data
            print("\n🎲 Generating Context-Aware Dummy Data...")
            for table in tables:
                if table not in columns:
                    columns[table] = []
            
            gen = DataGenerator()
            dummy_data = gen.generate_data(columns)
            
            # Show sample
            for table, df in dummy_data.items():
                print(f"\nTable: {table} (First 3 rows)")
                print(df.head(3).to_string(index=False))

            # 3. Execute
            print("\n⚡ Executing Query...")
            executor = SQLExecutor()
            executor.load_data(dummy_data)
            
            try:
                result_df = executor.execute(sql_query)
            except Exception as e:
                print(f"\n⚠️ Execution Error: {e}")
                print("🔧 Attempting to Auto-Fix with Gemini...")
                
                fixed_sql = analyzer.fix_sql_error(sql_query, str(e))
                if fixed_sql:
                    print(f"✨ Fixed SQL: {fixed_sql}")
                    print("🔄 Retrying execution...")
                    sql_query = fixed_sql # Update for visualization/insights
                    result_df = executor.execute(fixed_sql)
                else:
                    raise e # Re-raise if fix failed
            
            print("\n📊 RESULTS:")
            if result_df.empty:
                print("Query returned no results.")
            else:
                print(result_df.to_string(index=False))
                
                # Generate Insights
                print("\n💡 Generating Data Insights...")
                insights = analyzer.generate_data_insights(result_df)
                if insights:
                    print(f"\n{insights}")

            # 4. Visualize
            print("\n🎨 Generating Visualization...")
            viz = Visualizer(api_key=api_key)
            chart_base64 = viz.create_chart(result_df, sql_query)
            
            if chart_base64:
                # Save and open
                img_str = chart_base64.replace('data:image/png;base64,', '')
                img_bytes = base64.b64decode(img_str)
                
                viz_filename = "temp_viz.png"
                with open(viz_filename, "wb") as f:
                    f.write(img_bytes)
                
                print(f"Opening chart in default viewer...")
                if os.name == 'nt': # Windows
                    os.startfile(viz_filename)
                else: # Mac/Linux
                    os.system(f"open {viz_filename}" if sys.platform == 'darwin' else f"xdg-open {viz_filename}")
            else:
                print("Could not generate a visualization for this result.")

        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
