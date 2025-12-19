# AdventureWorks Database CSV Exporter

This repository contains scripts to export Microsoft AdventureWorks database tables to CSV files.

## Quick Start (Without Docker)

Since you don't have Docker, you have a few options:

### Option 1: Use Azure SQL Database (Recommended - Free tier available)

1. **Set up Azure SQL Database:**
   - Sign up for a free Azure account: https://azure.microsoft.com/free/
   - Create a new SQL Database in Azure Portal
   - Note your server name (e.g., `yourserver.database.windows.net`), username, and password

2. **Restore AdventureWorks to Azure:**
   - Download AdventureWorks backup: https://github.com/Microsoft/sql-server-samples/releases/tag/adventureworks
   - Download `AdventureWorks2019.bak`
   - Use Azure Portal or Azure Data Studio to restore the backup to your Azure SQL Database

3. **Install ODBC Driver (macOS):**
   ```bash
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew install --no-sandbox msodbcsql17 mssql-tools
   ```

4. **Run the export script:**
   ```bash
   python3 export_adventureworks.py
   ```
   - Enter your Azure SQL Database connection details when prompted
   - CSV files will be saved in the current directory

### Option 2: Use a Local/Remote SQL Server

If you have access to a SQL Server instance (local or remote):

1. **Install ODBC Driver (macOS):**
   ```bash
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew install --no-sandbox msodbcsql17 mssql-tools
   ```

2. **Restore AdventureWorks database:**
   - Download `AdventureWorks2019.bak` from: https://github.com/Microsoft/sql-server-samples/releases/tag/adventureworks
   - Restore it to your SQL Server instance using SQL Server Management Studio or Azure Data Studio

3. **Run the export script:**
   ```bash
   python3 export_adventureworks.py
   ```
   - Enter your SQL Server connection details when prompted

### Option 3: Install Docker (If you change your mind)

If you decide to use Docker later:

1. **Install Docker Desktop for Mac:**
   - Download from: https://www.docker.com/products/docker-desktop

2. **Run the Docker-based script:**
   ```bash
   python3 download_adventureworks.py
   ```

## Scripts

- **`export_adventureworks.py`**: Simple script that works with any SQL Server connection (local, remote, or Azure)
- **`download_adventureworks.py`**: Full-featured script with Docker support (requires Docker)

## Requirements

- Python 3.6+
- pandas
- pyodbc
- ODBC Driver 17 for SQL Server (for macOS)

Install Python dependencies:
```bash
pip3 install pandas pyodbc
```

## Output

All CSV files will be saved in the current directory (or specified output directory) with the table name as the filename (e.g., `Person.csv`, `Product.csv`, etc.).

Each CSV file includes:
- Column headers in the first row
- All data rows from the table

## Troubleshooting

### ODBC Driver Issues on macOS

If you get connection errors, make sure ODBC Driver is installed:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install --no-sandbox msodbcsql17 mssql-tools
```

### Connection Timeout

- Check if your SQL Server is accessible
- Verify firewall settings allow connections
- For Azure SQL Database, ensure "Allow Azure services and resources to access this server" is enabled

### Authentication Errors

- Double-check your username and password
- For Azure SQL Database, make sure you're using SQL authentication (not Azure AD) unless configured properly

## Resources

- [AdventureWorks Sample Databases](https://github.com/Microsoft/sql-server-samples/releases/tag/adventureworks)
- [Azure SQL Database Documentation](https://docs.microsoft.com/azure/azure-sql/)
- [ODBC Driver for SQL Server](https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
