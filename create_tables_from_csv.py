#!/usr/bin/env python3
"""
Generate CREATE TABLE statements from CSV files
"""
import csv
import os
import sys
import glob

def create_table_sql(csv_file, schema_name):
    """Generate CREATE TABLE SQL from CSV file headers"""
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=',')
            headers = next(reader)

            # Clean header names and limit to 128 characters
            clean_headers = []
            for idx, h in enumerate(headers):
                # Remove special characters and limit length
                h = h.strip()
                h = ''.join(c if c.isalnum() or c in ('_', ) else '_' for c in h)
                h = h[:100]  # Leave room for potential de-duplication suffix

                # If header is empty or starts with a number, prefix with 'Col'
                if not h or h[0].isdigit():
                    h = f"Col{idx+1}"

                # Ensure uniqueness
                base_name = h
                counter = 1
                while h in clean_headers:
                    h = f"{base_name}_{counter}"
                    counter += 1

                clean_headers.append(h[:128])  # Final length check

            # Get table name from filename
            table_name = os.path.splitext(os.path.basename(csv_file))[0]

            # Generate CREATE TABLE statement
            sql = f"IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table_name}' AND schema_id = SCHEMA_ID('{schema_name}'))\n"
            sql += "BEGIN\n"
            sql += f"    CREATE TABLE [{schema_name}].[{table_name}] (\n"

            columns = []
            for header in clean_headers:
                columns.append(f"        [{header}] NVARCHAR(MAX) NULL")

            sql += ",\n".join(columns)
            sql += "\n    );\n"
            sql += "END\n"
            sql += "GO\n"

            return sql, table_name

    except Exception as e:
        print(f"Error processing {csv_file}: {e}", file=sys.stderr)
        return None, None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: create_tables_from_csv.py <csv_directory> <schema_name>")
        sys.exit(1)

    csv_dir = sys.argv[1]
    schema_name = sys.argv[2]

    # Find all CSV files
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    print(f"Found {len(csv_files)} CSV files in {csv_dir}")

    # Generate SQL for all tables
    all_sql = ""
    tables_created = []

    for csv_file in sorted(csv_files):
        sql, table_name = create_table_sql(csv_file, schema_name)
        if sql:
            all_sql += sql + "\n"
            tables_created.append(table_name)
            print(f"Generated CREATE TABLE for: {table_name}")

    # Write to output file
    output_file = "create_all_tables.sql"
    with open(output_file, 'w') as f:
        f.write(all_sql)

    print(f"\nGenerated SQL for {len(tables_created)} tables")
    print(f"Output written to: {output_file}")
