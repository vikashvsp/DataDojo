from apify import Actor
from .analyzer import SQLAnalyzer
from .data_gen import DataGenerator
from .executor import SQLExecutor
from .visualizer import Visualizer
import pandas as pd
import base64
import markdown

async def main():
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        user_input = actor_input.get('sql', 'SELECT department, COUNT(*) as count FROM employees GROUP BY department')
        gemini_api_key = actor_input.get('geminiApiKey')
        
        # Check if input looks like SQL
        is_sql = user_input.strip().upper().startswith(("SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"))
        
        if gemini_api_key:
            Actor.log.info(f"Gemini API Key received (length: {len(gemini_api_key)})")
        else:
            Actor.log.warning("Gemini API Key is MISSING! Advanced features will fallback to basic mode.")

        sql_query = user_input
        if not is_sql:
            Actor.log.info(f"Detected Natural Language input: {user_input}")
            analyzer_temp = SQLAnalyzer("", api_key=gemini_api_key)
            converted_sql = analyzer_temp.convert_to_sql(user_input)
            if converted_sql:
                Actor.log.info(f"Converted to SQL: {converted_sql}")
                sql_query = converted_sql
            else:
                Actor.log.warning("Could not convert to SQL. Proceeding with original input.")
        
        Actor.log.info(f"Processing SQL: {sql_query}")

        # 1. Analyze
        analyzer = SQLAnalyzer(sql_query, api_key=gemini_api_key)
        tables = analyzer.get_tables()
        columns = analyzer.get_columns()
        explanation = analyzer.explain()
        
        Actor.log.info(f"Identified tables: {tables}")
        Actor.log.info(f"Identified columns: {columns}")

        # 2. Generate Data
        # Ensure we have at least some columns for the tables found
        # If columns is empty but tables exist, we need to handle that in data_gen
        # Refine columns dict to ensure every table has an entry
        for table in tables:
            if table not in columns:
                columns[table] = [] # Let generator pick defaults

        gen = DataGenerator()
        dummy_data = gen.generate_data(columns)
        
        # Convert dataframes to dict records for JSON output
        dummy_data_json = {k: v.to_dict(orient='records') for k, v in dummy_data.items()}

        # 3. Execute
        executor = SQLExecutor()
        executor.load_data(dummy_data)
        
        try:
            result_df = executor.execute(sql_query)
        except Exception as e:
            Actor.log.warning(f"Execution Error: {e}")
            Actor.log.info("Attempting to Auto-Fix with Gemini...")
            
            fixed_sql = analyzer.fix_sql_error(sql_query, str(e))
            if fixed_sql:
                Actor.log.info(f"Fixed SQL: {fixed_sql}")
                sql_query = fixed_sql # Update for output
                result_df = executor.execute(fixed_sql)
            else:
                raise e
        
        # Generate Insights
        insights = analyzer.generate_data_insights(result_df)
        
        # Charge for the event (Pay-per-event)
        # This event name 'sql-analysis' must be configured in Apify Console
        await Actor.charge('sql-analysis')
        Actor.log.info("Charged for event: sql-analysis")
        
        # 4. Visualize
        viz = Visualizer(api_key=gemini_api_key)
        chart_base64 = viz.create_chart(result_df, sql_query)

        # Output
        # Output
        output = {
            "original_sql": sql_query,
            "explanation": explanation,
            "data_insights": insights,
            "tables_involved": tables,
            "dummy_data_sample": dummy_data_json,
            "query_results": result_df.to_dict(orient='records'),
            # "visualization_image": chart_base64 # Removing base64 to keep JSON clean
        }

        # Save image to KVS
        if chart_base64:
            try:
                # Remove header if present
                img_str = chart_base64.replace('data:image/png;base64,', '')
                img_bytes = base64.b64decode(img_str)
                await Actor.set_value('visualization.png', img_bytes, content_type='image/png')
                Actor.log.info("Saved visualization.png to Key-Value Store")
                
                output["visualization_url"] = "visualization.png" 
            except Exception as e:
                Actor.log.error(f"Failed to save image to KVS: {e}")
        else:
            # Generate a placeholder "No Chart Available" image
            try:
                import matplotlib.pyplot as plt
                import io
                
                plt.figure(figsize=(8, 4))
                plt.text(0.5, 0.5, 'No Chart Available\n(Check Data or API Key)', 
                         horizontalalignment='center', verticalalignment='center', fontsize=14, color='gray')
                plt.axis('off')
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                plt.close()
                buf.seek(0)
                img_bytes = buf.read()
                
                await Actor.set_value('visualization.png', img_bytes, content_type='image/png')
                Actor.log.info("Saved placeholder visualization.png to Key-Value Store")
                output["visualization_url"] = "visualization.png"
            except Exception as e:
                Actor.log.error(f"Failed to save placeholder image: {e}")

        # Generate HTML Report
        try:
            # Convert markdown to HTML
            formatted_explanation = markdown.markdown(explanation) if explanation else "No explanation available."
            formatted_insights = markdown.markdown(insights) if insights else "No insights available."
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>SQL Analysis Report</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; line-height: 1.6; color: #333; }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    .section {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    code {{ background: #eee; padding: 2px 5px; border-radius: 3px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .viz-container {{ text-align: center; margin-top: 20px; }}
                    img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                </style>
            </head>
            <body>
                <h1>SQL Analysis Report 📊</h1>
                
                <div class="section">
                    <h2>🔍 Original Query</h2>
                    <code>{sql_query}</code>
                </div>

                <div class="section">
                    <h2>🧠 Explanation</h2>
                    <div>{formatted_explanation}</div>
                </div>

                <div class="section">
                    <h2>💡 Smart Insights</h2>
                    <div>{formatted_insights}</div>
                </div>

                <div class="section">
                    <h2>📈 Visualization</h2>
                    <div class="viz-container">
                        <img src="visualization.png" alt="Chart">
                    </div>
                </div>

                <div class="section">
                    <h2>📋 Query Results (Top 50)</h2>
                    {result_df.head(50).to_html(index=False, classes='table table-striped')}
                </div>
            </body>
            </html>
            """
            
            await Actor.set_value('report.html', html_content, content_type='text/html')
            Actor.log.info("Saved report.html to Key-Value Store")
            output["report_url"] = "report.html"
            
        except Exception as e:
            Actor.log.error(f"Failed to generate HTML report: {e}")

        # Save the main output JSON to the 'OUTPUT' key in KVS
        # This is what the output_schema.json will point to.
        await Actor.set_value('OUTPUT', output)
        
        # Push the structured output to the dataset
        # This matches the schema defined in dataset_schema.json for monetization
        await Actor.push_data(output)
        
        Actor.log.info("Results saved to KVS 'OUTPUT' and pushed to dataset.")

if __name__ == '__main__':
    # Run the Actor
    # Note: Apify's async main wrapper handles the event loop
    import asyncio
    asyncio.run(main())
