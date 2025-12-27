# 🧙‍♂️ SQL Explainer & Visualizer (AI Powered)

**Turn any SQL query (or English question) into a visual data story.**

[![Apify](https://img.shields.io/badge/Apify-Actor-green)](https://apify.com) [![Gemini](https://img.shields.io/badge/AI-Gemini%202.0-blue)](https://deepmind.google/technologies/gemini/)

This Actor is your **AI-powered SQL Professor and Analytics Assistant**. It doesn't just run queries; it understands them, explains them, fixes them, and visualizes the results—all automatically.

---

## 🚀 Key Features

### 🧠 1. The "SQL Professor" Mode
Ask a conceptual question like *"What is a Window Function?"* or *"Explain LEFT JOIN"*.
*   **Auto-Demo**: The Actor generates a valid SQL query to **demonstrate** the concept.
*   **Deep Explanation**: Explains the concept, order of execution, and data flow.
*   **Visual Proof**: Runs the query and shows you the result.

### 🗣️ 2. Natural Language to SQL
Don't know SQL? Just ask in English.
*   *"Show me the top 5 departments by average salary"*
*   *"Calculate the 7-day moving average of sales"*
*   The Actor converts it to optimized SQL automatically.

### 🛠️ 3. Auto-Fix & Self-Healing
Made a typo? Forgot a `GROUP BY`?
*   The Actor detects the error.
*   **Gemini AI** analyzes the error message and **fixes the SQL** automatically.
*   It retries execution without you lifting a finger.

### 📊 4. Intelligent Visualization
No configuration needed.
*   The AI analyzes your data and picks the **perfect chart** (Bar, Line, Pie, Scatter).
*   Generates a beautiful, embeddable PNG chart.

### 📑 5. Smart Insights Report
Get the "So What?" from your data.
*   Generates a **professional one-paragraph report**.
*   Highlights top performers, trends, and business implications.

### 🧪 6. Zero-Config Execution
*   **No Database Required**: The Actor generates realistic **dummy data** on the fly based on your query's schema.
*   **In-Memory Engine**: Runs instantly using SQLite.

---

## 📖 How It Works

1.  **Input**: You provide a SQL query OR a natural language question.
2.  **Analysis**: Gemini AI analyzes the intent, structure, and logic.
3.  **Data Gen**: We generate synthetic data matching your table names and columns.
4.  **Execution**: The query runs against this data.
5.  **Report**: We generate a **beautiful HTML Report** containing:
    *   The Explanation
    *   The Chart
    *   The Insights
    *   The Data Table

---

## 🎯 Use Cases

*   **Education**: Learn SQL concepts by seeing them in action.
*   **Debugging**: Paste a broken query and let the AI fix and explain it.
*   **Quick Analytics**: Generate instant visualizations for presentations without setting up a database.
*   **Hackathons**: Use it as a backend to power "Text-to-Insight" dashboards.

---

## 🔌 Input & Output

### Input
*   `sql`: (String) Your SQL query OR English question.
*   `geminiApiKey`: (String, Optional) Your Google Gemini API Key.

### Output
*   **Analysis Report Tab**: A full HTML dashboard in the Apify UI.
*   **Dataset**: JSON data with all raw results.
*   **Key-Value Store**: `visualization.png` and `report.html`.

---

## 💎 Monetization
This Actor is available on the Apify Store with **Pay-Per-Event** pricing. You only pay when a successful analysis is generated.

---

*Built with ❤️ using Apify SDK, Python, and Google Gemini.*
