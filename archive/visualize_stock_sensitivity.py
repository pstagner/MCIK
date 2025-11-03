
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import copy


# --- 1. Database Connection and Data Fetching ---

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password="postgres"  # Assuming 'postgres' is the password for dev
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Could not connect to the database: {e}")
        print("Please ensure the database is running and the credentials are correct.")
        return None

def fetch_stock_data(conn, symbols):
    """Fetches historical price data for a list of symbols from the database."""
    print(f"Fetching data for symbols: {symbols}")
    query = f"""
    SELECT ts AS "Date", symbol, open, high, low, close, volume
    FROM prices
    WHERE symbol IN ({','.join(['%s'] * len(symbols))})
    ORDER BY ts ASC;
    """
    
    # Use pandas to read the SQL query directly into a DataFrame
    df = pd.read_sql_query(query, conn, params=symbols)
    
    # Data preparation
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        # Convert numeric columns to float, handling potential errors
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print("Data fetching complete.")
    return df

# --- Main execution block ---
if __name__ == "__main__":
    MAGNIFICENT_SEVEN = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META']
    
    connection = get_db_connection()
    
    if connection:
        all_data = fetch_stock_data(connection, MAGNIFICENT_SEVEN)
        connection.close()
        
        if not all_data.empty:
            print("\n--- Data Preview ---")
            print(all_data.head())
            
            # Placeholder for the next steps
            print("\nNext steps: Integrate signalmill_engine and build 3D visualization.")
        else:
            print("No data was fetched. Cannot proceed with visualization.")
