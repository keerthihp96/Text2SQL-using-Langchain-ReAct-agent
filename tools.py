# tools.py
import streamlit as st
import json
import os
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from database import execute_query
from schema import TABLE_SCHEMA

# ── Shared LLM ───────────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=st.secrets["GROQ_API_KEY"],
        temperature=0,
        max_tokens=1024,
        max_retries=3
    )


# ── Tool 1: Schema Lookup ─────────────────────────────────────────────────────
@tool
def get_schema(query: str) -> str:
    """
    Returns the full database schema including all tables,
    columns, relationships and join examples.
    Use this FIRST before writing any SQL query.
    """
    return TABLE_SCHEMA


# ── Tool 2: SQL Generator ─────────────────────────────────────────────────────
@tool
def generate_sql(question: str) -> str:
    """
    Converts a plain English question into a Snowflake SQL query.
    Use this after looking up the schema.
    Input: plain English question about the data.
    Output: SQL query string.
    """
    prompt = f"""
You are an expert Snowflake SQL engineer.
Convert this question into a valid Snowflake SQL query.

Database Schema:
{TABLE_SCHEMA}

Question: {question}

Rules:
- Use UPPERCASE for table and column names
- Always qualify columns with table alias when joining
- Use TRUE/FALSE for boolean filters
- Add LIMIT 100 unless user asks for all records
- Return ONLY the raw SQL query, nothing else
"""
    llm      = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Tool 3: SQL Validator ─────────────────────────────────────────────────────
@tool
def validate_sql(sql: str) -> str:
    """
    Validates a SQL query for syntax errors, missing joins,
    incorrect column names, and Snowflake-specific issues.
    Always validate SQL before executing it.
    Input: SQL query string.
    Output: Validation result with any issues found.
    """
    prompt = f"""
You are a Snowflake SQL validator.
Check this SQL query for any issues:

{sql}

Database Schema for reference:
{TABLE_SCHEMA}

Check for:
1. Syntax errors
2. Non-existent table or column names
3. Missing JOIN conditions
4. Incorrect Snowflake syntax
5. Logic errors

Respond with:
- VALID: if no issues found
- INVALID: <specific issue> if problems found
"""
    llm      = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Tool 4: SQL Executor ──────────────────────────────────────────────────────
@tool
def execute_sql(sql: str) -> str:
    """
    Executes a SQL query on Snowflake and returns results.
    Only use this AFTER validating the SQL query.
    Input: valid SQL query string.
    Output: query results as formatted text.
    """
    columns, rows, error = execute_query(sql)

    if error:
        return f"EXECUTION ERROR: {error}"

    if not rows:
        return "Query executed successfully but returned no results."

    # Format results as readable text
    header    = " | ".join(columns)
    separator = "─" * len(header)
    data_rows = "\n".join([
        " | ".join(str(v) for v in row)
        for row in rows[:50]
    ])

    result = f"{header}\n{separator}\n{data_rows}"

    if len(rows) > 50:
        result += f"\n... and {len(rows) - 50} more rows"

    result += f"\n\nTotal rows returned: {len(rows)}"
    return result


# ── Tool 5: Query Optimizer ───────────────────────────────────────────────────
@tool
def optimize_sql(sql: str) -> str:
    """
    Optimizes a SQL query for better performance on Snowflake.
    Suggests improvements like better JOINs, avoiding SELECT *,
    adding WHERE clauses, and using appropriate aggregations.
    Input: SQL query string.
    Output: Optimized SQL query with explanation of changes.
    """
    prompt = f"""
You are a Snowflake SQL performance expert.
Optimize this SQL query for better performance:

{sql}

Consider:
1. Replace SELECT * with specific column names
2. Add WHERE clauses to filter early
3. Use appropriate aggregations
4. Optimize JOIN order (smaller tables first)
5. Use LIMIT where appropriate
6. Avoid unnecessary subqueries

Respond with:
OPTIMIZED SQL:
<optimized query>

CHANGES MADE:
<bullet points of what was changed and why>
"""
    llm      = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Tool 6: Error Fixer ───────────────────────────────────────────────────────
@tool
def fix_sql_error(input: str) -> str:
    """
    Fixes a SQL query that caused an execution error.
    Use this when execute_sql returns an EXECUTION ERROR.
    Input: JSON string with 'sql' and 'error' keys.
    Example: '{"sql": "SELECT...", "error": "column not found"}'
    Output: Fixed SQL query.
    """
    try:
        data  = json.loads(input)
        sql   = data.get("sql", "")
        error = data.get("error", "")
    except json.JSONDecodeError:
        # Handle plain text input
        sql   = input
        error = "Unknown error"

    prompt = f"""
You are a Snowflake SQL debugging expert.
Fix this SQL query that caused an error.

Original SQL:
{sql}

Error message:
{error}

Database Schema:
{TABLE_SCHEMA}

Analyze the error and return ONLY the corrected SQL query, nothing else.
"""
    llm      = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Tool 7: Result Explainer ──────────────────────────────────────────────────
@tool
def explain_results(input: str) -> str:
    """
    Converts raw SQL query results into a clear natural language answer.
    Always use this as the FINAL step to answer the user's question.
    Input: JSON string with 'question', 'sql', and 'results' keys.
    Output: Natural language answer.
    """
    try:
        data     = json.loads(input)
        question = data.get("question", "")
        sql      = data.get("sql", "")
        results  = data.get("results", "")
    except json.JSONDecodeError:
        question = "the user's question"
        sql      = ""
        results  = input

    prompt = f"""
The user asked: "{question}"

SQL that was run:
{sql}

Results from database:
{results}

Write a clear, conversational answer to the user's question.
Rules:
- Speak directly to the user
- Include specific numbers and names from results
- Be concise — 2-4 sentences max
- If no results, say so clearly
"""
    llm      = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Export all tools ──────────────────────────────────────────────────────────
all_tools = [
    get_schema,
    generate_sql,
    validate_sql,
    execute_sql,
    optimize_sql,
    fix_sql_error,
    explain_results
]
