IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers' AND schema_id = schema_id('Sales'))
BEGIN
    CREATE TABLE dbo.Customers (
        CustomerID INT PRIMARY KEY,
        CustomerName VARCHAR(255) NOT NULL,
        CreatedDate DATETIME2 DEFAULT GETUTCDATE()
    );
    PRINT 'Table Dbo.Customers created successfully.';
    INSERT INTO dbo.Customers (CustomerID, CustomerName, CreatedDate)
VALUES
(1, 'Acme Corp', GETDATE()),
(2, 'Global Tech Solutions', GETDATE()),
(3, 'Retail Innovations LLC', GETDATE()),
(4, 'The Green Grocer', GETDATE()),
(5, 'Sunrise Manufacturing', GETDATE()),
(6, 'Apex Consulting', GETDATE()),
(7, 'Coastal Banking', GETDATE()),
(8, 'Future Builders', GETDATE()),
(9, 'Westside Distributors', GETDATE()),
(10, 'Zenith Energy', GETDATE());
PRINT 'Data inserted into Dbo.Customers'
END
ELSE
BEGIN
    PRINT 'Table Dbo.Customers already exists. Skipping.';
END
GO