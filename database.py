# database.py

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()
import streamlit as st

def get_connection():
    """Create and return a Snowflake connection."""
    return snowflake.connector.connect(
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        database=st.secrets["SNOWFLAKE_DATABASE"],
        schema=st.secrets["SNOWFLAKE_SCHEMA"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"]
    )



def execute_query(sql: str):
    """
    Execute SQL on Snowflake.
    Returns: (columns, rows, error)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows    = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return columns, rows, None

    except Exception as e:
        return None, None, str(e)

    finally:
        if conn:
            conn.close()


def test_connection():
    """Test Snowflake connection."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)
