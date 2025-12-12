IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers' AND schema_id = schema_id('Sales'))
BEGIN
    CREATE TABLE dbo.Customers (
        CustomerID INT PRIMARY KEY,
        CustomerName VARCHAR(255) NOT NULL,
        CreatedDate DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT 'Table Sales.Customers created successfully.';
END
ELSE
BEGIN
    PRINT 'Table Sales.Customers already exists. Skipping.';
END
GO