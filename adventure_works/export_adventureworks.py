#!/usr/bin/env python3
"""
Simple script to export AdventureWorks database tables to CSV files.
Works with any SQL Server connection (local, remote, or Azure SQL Database).
"""

import os
import sys

try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

try:
    import pyodbc
except ImportError:
    print("Installing pyodbc...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyodbc"])
    import pyodbc


def export_tables_to_csv(server, database, username=None, password=None, output_dir=None):
    """
    Export all tables from AdventureWorks database to CSV files.
    
    Args:
        server: SQL Server name (e.g., 'localhost' or 'server.database.windows.net')
        database: Database name (e.g., 'AdventureWorks2019')
        username: SQL Server username (optional if using Windows authentication)
        password: SQL Server password (optional if using Windows authentication)
        output_dir: Output directory for CSV files (default: current directory)
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Connecting to SQL Server: {server}")
    print(f"Database: {database}")
    print(f"Output directory: {output_dir}\n")
    
    # Build connection string
    if username and password:
        # SQL Server authentication
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )
    else:
        # Windows authentication (may not work on macOS, but try anyway)
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'Trusted_Connection=yes;'
        )
    
    try:
        print("Establishing connection...")
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        
        # Get all table names
        print("Fetching table list...")
        query = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables to export...\n")
        
        exported_count = 0
        failed_count = 0
        
        for schema, table in tables:
            full_table_name = f'[{schema}].[{table}]'
            csv_file = os.path.join(output_dir, f'{table}.csv')
            
            try:
                print(f"Exporting {full_table_name}...", end=' ', flush=True)
                query = f'SELECT * FROM {full_table_name}'
                df = pd.read_sql(query, conn)
                df.to_csv(csv_file, index=False)
                print(f"✓ ({len(df)} rows)")
                exported_count += 1
            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")
                failed_count += 1
        
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"Export complete!")
        print(f"Successfully exported: {exported_count} tables")
        if failed_count > 0:
            print(f"Failed: {failed_count} tables")
        print(f"CSV files saved to: {output_dir}")
        print(f"{'='*60}")
        
        return True
        
    except pyodbc.Error as e:
        print(f"\n❌ Database connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure SQL Server is running and accessible")
        print("2. Check if ODBC Driver 17 for SQL Server is installed")
        print("   On macOS, install with:")
        print("   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release")
        print("   brew install --no-sandbox msodbcsql17 mssql-tools")
        print("3. Verify your connection details (server, database, credentials)")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main function with interactive prompts."""
    print("=" * 60)
    print("AdventureWorks Database CSV Exporter")
    print("=" * 60)
    print()
    
    # Get connection details
    print("Please provide SQL Server connection details:")
    print("(You can use Azure SQL Database, local SQL Server, or any remote SQL Server)")
    print()
    
    server = input("Server name (e.g., localhost or server.database.windows.net): ").strip()
    if not server:
        print("Server name is required!")
        return
    
    database = input("Database name (default: AdventureWorks2019): ").strip() or "AdventureWorks2019"
    
    use_auth = input("Use SQL Server authentication? (y/n, default: y): ").strip().lower()
    if use_auth != 'n':
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        if not username or not password:
            print("Username and password are required for SQL Server authentication!")
            return
    else:
        username = None
        password = None
    
    output_dir = input(f"Output directory (default: {os.getcwd()}): ").strip() or os.getcwd()
    
    print()
    export_tables_to_csv(server, database, username, password, output_dir)


if __name__ == '__main__':
    main()
