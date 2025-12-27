from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import pandas as pd
import json

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer import SQLAnalyzer
from src.executor import SQLExecutor
from src.data_gen import DataGenerator
from src.visualizer import Visualizer
from src.importer import ApifyImporter

app = FastAPI(title="DataDojo API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    sql: str
    geminiApiKey: str | None = None
    datasetId: str | None = None
    apifyToken: str | None = None

class ImportRequest(BaseModel):
    datasetId: str
    apifyToken: str | None = None

class AnalysisResponse(BaseModel):
    original_sql: str
    explanation: str
    data_insights: str | None
    tables_involved: list[str]
    dummy_data_sample: dict
    query_results: list[dict]
    visualization_base64: str | None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "DataDojo API is running"}

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_query(request: QueryRequest):
    try:
        sql_query = request.sql
        api_key = request.geminiApiKey
        
        # 1. Analyze
        analyzer = SQLAnalyzer(sql_query, api_key=api_key)
        tables = analyzer.get_tables()
        columns = analyzer.get_columns()
        explanation = analyzer.explain()
        
        # 2. Prepare Data (Hybrid: Real + Dummy)
        combined_data = {}
        
        # 2a. Load Real Data if datasetId matches a table or is requested
        if request.datasetId:
            csv_file = f"temp_{request.datasetId}.csv"
            real_table_name = f"dataset_{request.datasetId}"
            
            if os.path.exists(csv_file):
                try:
                    real_df = pd.read_csv(csv_file)
                    # Heuristic: If the query explicitly mentions the dataset table ID, use it.
                    # Otherwise, if the query only mentions one table and it's NOT a standard dummy name, map it?
                    # For safety, we just register the table with its official name
                    combined_data[real_table_name] = real_df
                    
                    # Also, if the user wrote "SELECT * FROM data", map 'data' to this df
                    combined_data['data'] = real_df
                except Exception as e:
                    print(f"Failed to load temp CSV: {e}")

        # 2b. Identify missing tables for Dummy Generation
        missing_tables = [t for t in tables if t not in combined_data]
        
        # Generate schema for missing tables
        columns_for_dummy = {t: columns.get(t, []) for t in missing_tables}
        
        gen = DataGenerator()
        dummy_data = gen.generate_data(columns_for_dummy)
        
        # Merge all data
        combined_data.update(dummy_data)
        
        # Preview for JSON output (limit rows for performance)
        dummy_data_json = {k: v.head(5).to_dict(orient='records') for k, v in combined_data.items()}
        
        # 3. Execute
        executor = SQLExecutor()
        executor.load_data(combined_data)
        try:
            result_df = executor.execute(sql_query)
        except Exception as e:
            # Auto-fix attempt
            fixed_sql = analyzer.fix_sql_error(sql_query, str(e))
            if fixed_sql:
                request.sql = fixed_sql # Update logic if needed
                result_df = executor.execute(fixed_sql)
                sql_query = fixed_sql
            else:
                raise HTTPException(status_code=400, detail=f"Execution Error: {str(e)}")

        # 4. Insights
        insights = analyzer.generate_data_insights(result_df)
        
        # 5. Visualize
        viz = Visualizer(api_key=api_key)
        chart_base64 = viz.create_chart(result_df, sql_query)
        
        return {
            "original_sql": sql_query,
            "explanation": explanation,
            "data_insights": insights,
            "tables_involved": tables,
            "dummy_data_sample": dummy_data_json,
            "query_results": result_df.to_dict(orient='records'),
            "visualization_base64": chart_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/import", response_model=dict)
def import_dataset(request: ImportRequest):
    try:
        importer = ApifyImporter(api_token=request.apifyToken)
        df = importer.fetch_dataset(request.datasetId)
        
        if df.empty:
            return {"message": "Dataset is empty or could not be loaded."}
            
        # Preview
        preview = df.head(5).to_dict(orient='records')
        columns = list(df.columns)
        
        # In a real app, we would cache this DF or save to a DB
        # For this Hackathon demo, we might return the schema and ask the frontend 
        # to send the dataset ID with every query, effectively re-fetching or caching in memory?
        # Better: Save to a global variable or simpler: Save to a temp CSV file named after ID.
        
        filename = f"temp_{request.datasetId}.csv"
        df.to_csv(filename, index=False)
        
        return {
            "message": f"Dataset {request.datasetId} imported successfully.",
            "table_name": f"dataset_{request.datasetId}",
            "row_count": len(df),
            "columns": columns,
            "preview": preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
