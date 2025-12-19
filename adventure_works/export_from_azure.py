#!/usr/bin/env python3
"""
Quick script to export AdventureWorks from Azure SQL Database.
Azure offers AdventureWorks as a sample database that you can use for free.
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


def export_from_azure(server, database, username, password, output_dir=None):
    """Export tables from Azure SQL Database to CSV files."""
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'adventureworks_csv')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Azure SQL Database connection string
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    
    try:
        print(f"Connecting to Azure SQL Database: {server}...")
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        
        # Get all table names
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
        for schema, table in tables:
            full_table_name = f'[{schema}].[{table}]'
            csv_file = os.path.join(output_dir, f'{table}.csv')
            
            try:
                print(f"Exporting {full_table_name}...", end=' ', flush=True)
                query = f'SELECT * FROM {full_table_name}'
                df = pd.read_sql(query, conn)
                df.to_csv(csv_file, index=False)
                print(f"✓ {len(df)} rows -> {csv_file}")
                exported_count += 1
            except Exception as e:
                print(f"✗ Error: {e}")
        
        conn.close()
        print(f"\n{'='*60}")
        print(f"Export complete! {exported_count}/{len(tables)} tables exported.")
        print(f"CSV files saved to: {output_dir}")
        print(f"{'='*60}")
        return True
        
    except pyodbc.Error as e:
        print(f"\nConnection error: {e}")
        print("\nMake sure:")
        print("1. Your Azure SQL Database firewall allows your IP address")
        print("2. Server name format: yourserver.database.windows.net")
        print("3. ODBC Driver 17 is installed (brew install msodbcsql17)")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("Azure SQL Database - AdventureWorks CSV Exporter")
    print("=" * 60)
    print("\nTo use this script:")
    print("1. Create a free Azure account at https://azure.microsoft.com/free/")
    print("2. Create an Azure SQL Database and select 'AdventureWorks' as sample")
    print("3. Add your IP to the firewall rules in Azure Portal")
    print("4. Get your connection details from Azure Portal\n")
    
    server = input("Server (e.g., myserver.database.windows.net): ").strip()
    if not server:
        print("Server name is required.")
        return
    
    database = input("Database name (default: AdventureWorks): ").strip() or 'AdventureWorks'
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("Username and password are required.")
        return
    
    export_from_azure(server, database, username, password)


if __name__ == '__main__':
    main()

