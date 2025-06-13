### **1. Core SQL Concepts**
#### **SELECT & Filtering**
- **Basic Query**: Retrieve data with `SELECT`, `WHERE`, and logical operators (`AND`, `OR`, `NOT`).
  ```sql
  SELECT FirstName, LastName FROM Employees WHERE Department = 'Sales' AND Salary > 50000;
  ```

#### **Joins**
- **INNER JOIN**: Rows with matching values in both tables.
  ```sql
  SELECT e.Name, d.DepartmentName 
  FROM Employees e
  INNER JOIN Departments d ON e.DepartmentID = d.DepartmentID;
  ```
- **LEFT/RIGHT JOIN**: Include all rows from one table, even if no match in the other.
- **SELF JOIN**: Join a table to itself (e.g., employee-manager hierarchy).

#### **Aggregation**
- **GROUP BY**, **HAVING**, and aggregate functions (`SUM`, `AVG`, `COUNT`, `MIN/MAX`).
  ```sql
  SELECT DepartmentID, AVG(Salary) AS AvgSalary 
  FROM Employees 
  GROUP BY DepartmentID 
  HAVING AVG(Salary) > 60000;
  ```

#### **Sorting & Limiting**
- `ORDER BY` for sorting, `TOP` (SQL Server) to limit rows.
  ```sql
  SELECT TOP 5 * FROM Employees ORDER BY Salary DESC; -- Top 5 highest salaries
  ```

---

### **2. Data Manipulation**
#### **INSERT/UPDATE/DELETE**
- Insert new records, update existing ones, or delete rows.
  ```sql
  UPDATE Employees SET Salary = Salary * 1.05 WHERE DepartmentID = 3;
  ```

#### **Transactions**
- Use `BEGIN TRANSACTION`, `COMMIT`, and `ROLLBACK` for atomic operations.
  ```sql
  BEGIN TRANSACTION;
  UPDATE Accounts SET Balance = Balance - 100 WHERE AccountID = 1;
  UPDATE Accounts SET Balance = Balance + 100 WHERE AccountID = 2;
  COMMIT;
  ```

---

### **3. Advanced Queries**
#### **Subqueries & CTEs**
- **Subquery**: Nested query inside another query.
  ```sql
  SELECT Name FROM Employees 
  WHERE Salary > (SELECT AVG(Salary) FROM Employees);
  ```
- **CTE (Common Table Expression)**:
  ```sql
  WITH HighEarners AS (
    SELECT Name, Salary FROM Employees WHERE Salary > 100000
  )
  SELECT * FROM HighEarners;
  ```

#### **Window Functions**
- `ROW_NUMBER()`, `RANK()`, `SUM() OVER()`, etc.
  ```sql
  SELECT Name, Salary, 
    RANK() OVER (ORDER BY Salary DESC) AS SalaryRank 
  FROM Employees;
  ```

#### **Pivot & Dynamic SQL**
- Convert rows to columns with `PIVOT` (static or dynamic).

---

### **4. Indexes & Performance**
#### **Clustered vs. Non-Clustered Indexes**
- **Clustered**: Determines physical order of data (one per table).
- **Non-Clustered**: Separate structure for faster lookups (multiple allowed).

#### **Query Optimization**
- Use `EXPLAIN` (execution plans) to analyze queries.
- Avoid `SELECT *`; use covering indexes.

---

### **5. Common Interview Problems**
1. **Second Highest Salary**:
   ```sql
   SELECT MAX(Salary) FROM Employees 
   WHERE Salary < (SELECT MAX(Salary) FROM Employees);
   ```

2. **Delete Duplicates**:
   ```sql
   WITH CTE AS (
     SELECT *, ROW_NUMBER() OVER (PARTITION BY Email ORDER BY ID) AS RN
     FROM Employees
   )
   DELETE FROM CTE WHERE RN > 1;
   ```

3. **Hierarchical Data (Manager-Employee)**:
   ```sql
   WITH OrgChart AS (
     SELECT EmployeeID, Name, ManagerID 
     FROM Employees WHERE ManagerID IS NULL
     UNION ALL
     SELECT e.EmployeeID, e.Name, e.ManagerID 
     FROM Employees e
     INNER JOIN OrgChart o ON e.ManagerID = o.EmployeeID
   )
   SELECT * FROM OrgChart;
   ```

4. **Gaps in Data** (e.g., missing dates/IDs):
   ```sql
   SELECT MissingID = a.ID + 1
   FROM TableA a
   WHERE NOT EXISTS (SELECT 1 FROM TableA b WHERE b.ID = a.ID + 1);
   ```

---

### **6. Practice Questions**
1. Write a query to find employees with salaries above their department’s average.
2. How would you handle a deadlock scenario in SQL Server?
3. Optimize a slow-running query using indexes.
4. Explain the difference between `WHERE` and `HAVING`.

---

### **7. Tips for the Interview**
- **Think Aloud**: Explain your logic while solving problems.
- **Test Edge Cases**: Mention NULLs, duplicates, or performance impacts.
- **Know T-SQL Functions**: `COALESCE`, `ISNULL`, `TRY_CONVERT`, etc.
- **Practice Writing Queries by Hand**: No autocomplete in interviews!

---

Let me know if you’d like deep dives into specific topics or more practice problems! 🚀


Absolutely! Let’s dive deeper into each topic with expanded explanations, examples, and strategies to tackle common interview questions.

---

### **1. Core SQL Concepts: Expanded**
#### **Joins**
- **Types of Joins**:
  - **INNER JOIN**: Returns rows with matches in both tables.
  - **LEFT JOIN**: Returns all rows from the left table, even if no match in the right table. Unmatched right table fields return `NULL`.
  - **RIGHT JOIN**: Opposite of LEFT JOIN.
  - **FULL OUTER JOIN**: Returns all rows when there’s a match in either table.
  - **CROSS JOIN**: Returns the Cartesian product (all possible combinations). Rarely used but good to know.
  - **SELF JOIN**: Join a table to itself (e.g., finding employees and their managers):
    ```sql
    SELECT e1.Name AS Employee, e2.Name AS Manager
    FROM Employees e1
    LEFT JOIN Employees e2 ON e1.ManagerID = e2.EmployeeID;
    ```

#### **Filtering**
- **WHERE vs. HAVING**:
  - `WHERE` filters rows **before** aggregation.
  - `HAVING` filters groups **after** aggregation.
  ```sql
  -- Example: Departments with more than 5 employees
  SELECT DepartmentID, COUNT(*) AS EmployeeCount
  FROM Employees
  GROUP BY DepartmentID
  HAVING COUNT(*) > 5;
  ```

#### **Set Operations**:
  - `UNION` (removes duplicates) vs. `UNION ALL` (keeps duplicates).
  - `INTERSECT` and `EXCEPT` (rows in the first query but not the second).

---

### **2. Advanced Aggregation**
#### **ROLLUP & CUBE**:
- **ROLLUP**: Hierarchical subtotals (e.g., total sales by region, then grand total).
  ```sql
  SELECT Region, SUM(Sales) 
  FROM SalesData 
  GROUP BY ROLLUP (Region);
  ```
- **CUBE**: Subtotals for all combinations of columns.
  ```sql
  SELECT Region, Product, SUM(Sales) 
  FROM SalesData 
  GROUP BY CUBE (Region, Product);
  ```

#### **GROUPING SETS**:
- Custom grouping combinations.
  ```sql
  SELECT Region, Product, SUM(Sales)
  FROM SalesData
  GROUP BY GROUPING SETS ((Region), (Product), ()); -- Grand total
  ```

---

### **3. Subqueries & CTEs: Deep Dive**
#### **Correlated Subqueries**:
- A subquery that references the outer query (executed row-by-row).
  ```sql
  -- Employees earning more than their department’s average
  SELECT Name, Salary, DepartmentID
  FROM Employees e1
  WHERE Salary > (
    SELECT AVG(Salary) 
    FROM Employees e2 
    WHERE e2.DepartmentID = e1.DepartmentID
  );
  ```

#### **CTEs vs. Temp Tables**:
- **CTEs**:
  - Exist only during query execution.
  - Can reference themselves (recursive CTEs).
  ```sql
  WITH RecursiveCTE AS (
    SELECT EmployeeID, ManagerID, 1 AS Level
    FROM Employees
    WHERE ManagerID IS NULL
    UNION ALL
    SELECT e.EmployeeID, e.ManagerID, Level + 1
    FROM Employees e
    INNER JOIN RecursiveCTE r ON e.ManagerID = r.EmployeeID
  )
  SELECT * FROM RecursiveCTE;
  ```
- **Temp Tables** (`#Temp`):
  - Persist for the session.
  - Useful for complex multi-step operations.

---

### **4. Window Functions: Advanced Use Cases**
#### **Frame Clauses**:
- Control the subset of rows in a window (e.g., rolling averages).
  ```sql
  SELECT Date, Sales,
    AVG(Sales) OVER (ORDER BY Date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) 
    AS RollingAvg
  FROM DailySales;
  ```

#### **LEAD() & LAG()**:
- Compare current row with previous/next rows.
  ```sql
  SELECT Month, Revenue,
    LAG(Revenue, 1) OVER (ORDER BY Month) AS PreviousMonthRevenue,
    LEAD(Revenue, 1) OVER (ORDER BY Month) AS NextMonthRevenue
  FROM MonthlyRevenue;
  ```

#### **PARTITION BY**:
- Split data into partitions for window operations.
  ```sql
  SELECT DepartmentID, Name, Salary,
    RANK() OVER (PARTITION BY DepartmentID ORDER BY Salary DESC) AS DeptSalaryRank
  FROM Employees;
  ```

---

### **5. Indexes & Performance Tuning**
#### **Clustered Index**:
- Determines physical data order. Choose a column with unique, sequential values (e.g., `ID`).

#### **Non-Clustered Index**:
- Separate structure for faster lookups. Use `INCLUDE` to add columns to the index leaf.
  ```sql
  CREATE NONCLUSTERED INDEX IX_Employees_DepartmentID
  ON Employees (DepartmentID)
  INCLUDE (Name, Salary); -- Covering index
  ```

#### **Execution Plans**:
- Use `SET SHOWPLAN_TEXT ON` or SSMS’s "Include Actual Execution Plan" to analyze query performance.

#### **Deadlocks**:
- Common causes: Competing transactions locking resources.
- Fixes: Use `NOLOCK` (dirty reads), optimize transaction order, or reduce isolation levels.

---

### **6. SQL Server-Specific Features**
#### **Stored Procedures**:
- Parameterized, reusable SQL blocks.
  ```sql
  CREATE PROCEDURE GetEmployeeByID @EmployeeID INT
  AS
  BEGIN
    SELECT * FROM Employees WHERE EmployeeID = @EmployeeID;
  END;
  ```

#### **TRY...CATCH**:
- Error handling in T-SQL.
  ```sql
  BEGIN TRY
    INSERT INTO Orders (OrderID) VALUES (1);
  END TRY
  BEGIN CATCH
    SELECT ERROR_MESSAGE() AS ErrorMessage;
  END CATCH;
  ```

#### **Dynamic SQL**:
- Build SQL queries dynamically (use with caution to avoid SQL injection).
  ```sql
  DECLARE @ColumnName NVARCHAR(50) = 'Salary';
  DECLARE @SQL NVARCHAR(1000);
  SET @SQL = N'SELECT ' + @ColumnName + ' FROM Employees';
  EXEC sp_executesql @SQL;
  ```

---

### **7. Common Interview Problems (Expanded)**
#### **Nth Highest Salary**:
- Use `DENSE_RANK()` for ties.
  ```sql
  WITH SalaryRanks AS (
    SELECT Salary, DENSE_RANK() OVER (ORDER BY Salary DESC) AS Rank
    FROM Employees
  )
  SELECT Salary FROM SalaryRanks WHERE Rank = 3; -- 3rd highest
  ```

#### **Pagination**:
- Use `OFFSET` and `FETCH` (SQL Server 2012+).
  ```sql
  SELECT Name, Salary
  FROM Employees
  ORDER BY Salary DESC
  OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY; -- Page 3 (rows 11-15)
  ```

#### **Hierarchical Data**:
- Recursive CTE to traverse trees (e.g., organizational hierarchy).

---

### **8. Practice Scenarios**
1. **Data Consistency**:
   - How would you ensure data integrity when transferring funds between accounts?
   - **Answer**: Use transactions with proper isolation levels (e.g., `SERIALIZABLE`).

2. **Query Optimization**:
   - A query is slow. How would you troubleshoot?
   - **Steps**: Check execution plan, look for table scans, add indexes, or rewrite the query.

3. **Design a Schema**:
   - Design a database for an e-commerce platform (tables: Users, Products, Orders, OrderItems).

---

### **9. Tips for Advanced Topics**
- **Temporal Tables**: Track historical data changes automatically.
- **JSON/XML Support**: Parse JSON/XML data using `OPENJSON` or `XML` methods.
- **Columnstore Indexes**: Optimized for analytics workloads (OLAP).

---

### **10. Final Interview Prep Checklist**
1. Master writing complex joins and subqueries.
2. Practice window functions (`RANK`, `ROW_NUMBER`, `LEAD/LAG`).
3. Understand index types and when to use them.
4. Prepare for scenario-based questions (e.g., “How would you design X?”).
5. Review SQL Server-specific features (e.g., CTEs, dynamic SQL).

---

Need even more details on a specific topic? Let me know! 😊

Certainly! Let’s break down advanced SQL concepts, optimization strategies, and real-world scenarios to ensure you’re fully prepared for your SQL Server interview. I’ll expand with **detailed explanations**, **practical examples**, and **problem-solving frameworks**.

---

### **1. Advanced Query Techniques**
#### **Pivoting and Unpivoting Data**
- **PIVOT**: Convert rows to columns (e.g., summarize sales by year).
  ```sql
  SELECT *
  FROM (
    SELECT Year, Product, Sales
    FROM Sales
  ) AS SourceTable
  PIVOT (
    SUM(Sales)
    FOR Year IN ([2020], [2021], [2022])
  ) AS PivotTable;
  ```
- **UNPIVOT**: Convert columns back to rows.
  ```sql
  SELECT Product, Year, Sales
  FROM (
    SELECT Product, [2020], [2021], [2022]
    FROM PivotedSales
  ) AS SourceTable
  UNPIVOT (
    Sales FOR Year IN ([2020], [2021], [2022])
  ) AS UnpivotTable;
  ```

#### **Dynamic SQL**
- Build SQL queries dynamically (useful for flexible filtering or schema changes).
  ```sql
  DECLARE @ColumnName NVARCHAR(50) = 'Salary';
  DECLARE @SQL NVARCHAR(MAX);
  SET @SQL = N'SELECT ' + QUOTENAME(@ColumnName) + ' FROM Employees;';
  EXEC sp_executesql @SQL;
  ```
  - **Caution**: Sanitize inputs to prevent SQL injection.

---

### **2. Performance Optimization**
#### **Indexing Strategies**
1. **Covering Index**: Include all columns needed for a query.
   ```sql
   CREATE NONCLUSTERED INDEX IX_Employee_Department
   ON Employees (DepartmentID)
   INCLUDE (Name, Salary); -- Covers SELECT Name, Salary WHERE DepartmentID = X
   ```
2. **Filtered Index**: Optimize for a subset of data.
   ```sql
   CREATE INDEX IX_ActiveEmployees
   ON Employees (DepartmentID)
   WHERE IsActive = 1;
   ```
3. **Index Fragmentation**: Rebuild or reorganize fragmented indexes.
   ```sql
   ALTER INDEX IX_Employees ON Employees REBUILD;
   ```

#### **Query Tuning**
- **Avoid Scans**: Use `WHERE` clauses and indexes to reduce table scans.
- **Parameter Sniffing**: Use `OPTION (RECOMPILE)` for queries with varying parameters.
- **Temporary Tables vs. CTEs**:
  - Temp tables are better for large datasets or multi-use scenarios.
  - CTEs are ideal for readability and single-use cases.

---

### **3. SQL Server-Specific Features**
#### **Stored Procedures & Functions**
- **Stored Procedure**:
  ```sql
  CREATE PROCEDURE GetEmployeesByDepartment @DeptID INT
  AS
  BEGIN
    SELECT Name, Salary FROM Employees WHERE DepartmentID = @DeptID;
  END;
  ```
- **Table-Valued Function**:
  ```sql
  CREATE FUNCTION GetEmployeeSalaries (@MinSalary INT)
  RETURNS TABLE
  AS
  RETURN (
    SELECT Name, Salary FROM Employees WHERE Salary > @MinSalary
  );
  ```

#### **Triggers**
- Automate actions on data changes (e.g., audit logs).
  ```sql
  CREATE TRIGGER LogSalaryChange
  ON Employees
  AFTER UPDATE
  AS
  BEGIN
    INSERT INTO AuditLog (EmployeeID, OldSalary, NewSalary)
    SELECT d.EmployeeID, d.Salary, i.Salary
    FROM deleted d
    INNER JOIN inserted i ON d.EmployeeID = i.EmployeeID;
  END;
  ```

#### **JSON & XML Support**
- Parse JSON data:
  ```sql
  DECLARE @json NVARCHAR(MAX) = N'{"Name": "John", "Age": 30}';
  SELECT *
  FROM OPENJSON(@json)
  WITH (Name NVARCHAR(50), Age INT);
  ```

---

### **4. Advanced Problem-Solving Scenarios**
#### **Problem 1: Find Employees with Duplicate Emails**
- **Solution**:
  ```sql
  WITH Duplicates AS (
    SELECT Email, COUNT(*) AS Count
    FROM Employees
    GROUP BY Email
    HAVING COUNT(*) > 1
  )
  SELECT e.*
  FROM Employees e
  INNER JOIN Duplicates d ON e.Email = d.Email;
  ```

#### **Problem 2: Calculate Running Total**
- **Solution with Window Function**:
  ```sql
  SELECT Date, Sales,
    SUM(Sales) OVER (ORDER BY Date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) 
    AS RunningTotal
  FROM DailySales;
  ```

#### **Problem 3: Find Missing Order IDs**
- **Solution**:
  ```sql
  WITH AllIDs AS (
    SELECT MIN(OrderID) AS StartID, MAX(OrderID) AS EndID 
    FROM Orders
  )
  SELECT a.ID AS MissingID
  FROM AllIDs
  CROSS APPLY (
    SELECT StartID + number AS ID
    FROM master..spt_values
    WHERE type = 'P' AND number <= EndID - StartID
  ) a
  WHERE NOT EXISTS (SELECT 1 FROM Orders WHERE OrderID = a.ID);
  ```

---

### **5. Real-World Scenario: E-Commerce Database Design**
#### **Tables**:
- **Users**: `UserID`, `Name`, `Email`.
- **Products**: `ProductID`, `Name`, `Price`.
- **Orders**: `OrderID`, `UserID`, `OrderDate`.
- **OrderItems**: `OrderItemID`, `OrderID`, `ProductID`, `Quantity`.

#### **Sample Query: Top-Selling Products**
  ```sql
  SELECT TOP 5 p.Name, SUM(oi.Quantity * p.Price) AS TotalRevenue
  FROM Products p
  INNER JOIN OrderItems oi ON p.ProductID = oi.ProductID
  GROUP BY p.Name
  ORDER BY TotalRevenue DESC;
  ```

---

### **6. Interview Strategy**
1. **Clarify Requirements**:
   - Ask about edge cases (e.g., NULLs, duplicates).
   - Example: “Should the second highest salary query handle multiple employees with the same salary?”

2. **Break Down the Problem**:
   - For hierarchical data, start with a recursive CTE structure.
   - For performance issues, mention execution plans and indexing.

3. **Test Your Solution**:
   - Use sample data to validate your query.
   - Example: Test the “delete duplicates” query with a table containing duplicates and NULLs.

4. **Explain Tradeoffs**:
   - “Using a correlated subquery here could be slow for large datasets. An alternative is a CTE with window functions.”

---

### **7. Common Pitfalls to Avoid**
1. **Ignoring NULLs**:
   - Use `IS NULL` or `COALESCE` to handle NULLs in joins or filters.
2. **Overusing Cursors**:
   - Opt for set-based operations instead of row-by-row processing.
3. **Forgetting Index Maintenance**:
   - Fragmented indexes can degrade performance over time.

---

### **8. Final Practice Problems**
1. **Top 3 Products by Category**:
   ```sql
   SELECT Category, Product, Sales
   FROM (
     SELECT Category, Product, Sales,
       ROW_NUMBER() OVER (PARTITION BY Category ORDER BY Sales DESC) AS Rank
     FROM Products
   ) AS Ranked
   WHERE Rank <= 3;
   ```

2. **Last Login Date for Each User**:
   ```sql
   SELECT UserID, MAX(LoginDate) AS LastLogin
   FROM UserLogins
   GROUP BY UserID;
   ```

3. **Merge Two Tables** (UPSERT):
   ```sql
   MERGE INTO Employees AS Target
   USING UpdatedEmployees AS Source
   ON Target.EmployeeID = Source.EmployeeID
   WHEN MATCHED THEN
     UPDATE SET Target.Salary = Source.Salary
   WHEN NOT MATCHED THEN
     INSERT (EmployeeID, Name, Salary) VALUES (Source.EmployeeID, Source.Name, Source.Salary);
   ```

---

Let me know if you’d like to focus on **specific areas** like query optimization, database design, or T-SQL functions! 😊


Let’s continue with advanced scenarios, SQL Server-specific optimizations, and strategies to tackle design and behavioral questions. Here’s the next phase of your preparation:

---

### **1. Advanced SQL Server-Specific Features**
#### **Temporal Tables**
- Automatically track historical data changes (e.g., auditing).
  ```sql
  -- Create a temporal table
  CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY,
    Name NVARCHAR(100),
    Salary DECIMAL,
    ValidFrom DATETIME2 GENERATED ALWAYS AS ROW START,
    ValidTo DATETIME2 GENERATED ALWAYS AS ROW END,
    PERIOD FOR SYSTEM_TIME (ValidFrom, ValidTo)
  )
  WITH (SYSTEM_VERSIONING = ON (HISTORY_TABLE = dbo.EmployeeHistory));
  ```
  - Query historical data:
    ```sql
    SELECT * FROM Employees
    FOR SYSTEM_TIME BETWEEN '2023-01-01' AND '2023-12-31';
    ```

#### **Columnstore Indexes**
- Optimized for analytical queries (OLAP) with high compression.
  ```sql
  CREATE COLUMNSTORE INDEX IX_Orders_Columnstore
  ON Orders (OrderID, ProductID, Quantity, OrderDate);
  ```

#### **Partitioning**
- Split large tables into smaller partitions for faster access.
  ```sql
  -- Create a partition function
  CREATE PARTITION FUNCTION OrderDatePF (DATE)
  AS RANGE RIGHT FOR VALUES ('2023-01-01', '2024-01-01');

  -- Create a partition scheme
  CREATE PARTITION SCHEME OrderDatePS
  AS PARTITION OrderDatePF
  TO (Filegroup2022, Filegroup2023, Filegroup2024);
  ```

---

### **2. Database Design & Normalization**
#### **ACID Properties**
- **Atomicity**: Transactions succeed or fail entirely (e.g., `COMMIT`/`ROLLBACK`).
- **Consistency**: Data meets all constraints before/after transactions.
- **Isolation**: Concurrent transactions don’t interfere (see [isolation levels](#isolation-levels)).
- **Durability**: Committed data survives system failures.

#### **Normalization**
- **1NF**: Eliminate repeating groups (atomic values).
- **2NF**: Remove partial dependencies (all non-key columns depend on the entire primary key).
- **3NF**: Remove transitive dependencies (non-key columns depend only on the primary key).

#### **Denormalization**
- Intentionally duplicate data to optimize read performance (common in OLAP).

---

### **3. Transaction Isolation Levels**
- **Read Uncommitted**: No locks; can read uncommitted data (dirty reads).
- **Read Committed**: Default. Avoid dirty reads but allow non-repeatable reads.
- **Repeatable Read**: Locks rows to prevent updates/deletes during a transaction.
- **Serializable**: Highest isolation; prevents phantom reads.
- **Snapshot**: Uses row versioning to avoid locks (concurrency at the cost of tempdb usage).

```sql
-- Set isolation level for a transaction
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
BEGIN TRANSACTION;
-- Your queries
COMMIT;
```

---

### **4. Query Optimization Scenarios**
#### **Scenario 1: Slow-Running Report Query**
- **Problem**: A monthly sales report takes 5 minutes to run.
- **Solution**:
  - Check execution plan for table scans.
  - Add covering indexes on filtered/joined columns.
  - Use `WITH (NOLOCK)` for dirty reads (if real-time consistency isn’t critical).
  - Archive old data to reduce table size.

#### **Scenario 2: Deadlocks During Order Processing**
- **Problem**: Concurrent orders cause deadlocks.
- **Solution**:
  - Use `TRY...CATCH` blocks to retry transactions.
  - Access tables in the same order across transactions.
  - Reduce isolation level to `READ COMMITTED SNAPSHOT`.

---

### **5. Advanced Problem-Solving**
#### **Problem 1: Find Consecutive Login Days**
- **Solution**:
  ```sql
  WITH LoginsWithGroups AS (
    SELECT UserID, LoginDate,
      DATEADD(DAY, -ROW_NUMBER() OVER (PARTITION BY UserID ORDER BY LoginDate), LoginDate) AS GroupID
    FROM UserLogins
  )
  SELECT UserID, COUNT(*) AS ConsecutiveDays
  FROM LoginsWithGroups
  GROUP BY UserID, GroupID
  HAVING COUNT(*) >= 5; -- Users with 5+ consecutive logins
  ```

#### **Problem 2: Calculate Median Salary**
- **Solution**:
  ```sql
  WITH OrderedSalaries AS (
    SELECT Salary, ROW_NUMBER() OVER (ORDER BY Salary) AS RowAsc,
      ROW_NUMBER() OVER (ORDER BY Salary DESC) AS RowDesc
    FROM Employees
  )
  SELECT AVG(Salary) AS Median
  FROM OrderedSalaries
  WHERE RowAsc = RowDesc OR RowAsc + 1 = RowDesc OR RowAsc - 1 = RowDesc;
  ```

#### **Problem 3: Calculate Employee Tenure**
- **Solution**:
  ```sql
  SELECT EmployeeID, DATEDIFF(MONTH, HireDate, GETDATE()) AS TenureMonths
  FROM Employees;
  ```

---

### **6. Behavioral & Design Questions**
#### **Question 1**: "Design a schema for a ride-sharing app."
- **Tables**:
  - **Users**: `UserID`, `Name`, `Email`.
  - **Drivers**: `DriverID`, `UserID` (FK to Users), `LicenseNumber`.
  - **Rides**: `RideID`, `UserID`, `DriverID`, `StartTime`, `EndTime`, `Fare`.
  - **Payments**: `PaymentID`, `RideID`, `Amount`, `Status`.

#### **Question 2**: "How would you back up a critical database?"
- **Answer**:
  - Use SQL Server Agent for automated full/differential/log backups.
  - Store backups in offsite/cloud storage.
  - Test restore procedures regularly.

#### **Question 3**: "Explain how you’d migrate data from an old system."
- **Steps**:
  1. Analyze source data structure.
  2. Cleanse data (handle NULLs, duplicates).
  3. Use SSIS (SQL Server Integration Services) for ETL.
  4. Validate migrated data with reconciliation queries.

---

### **7. Final Tips for Success**
1. **Practice Writing Queries by Hand**:
   - No autocomplete in interviews! Get comfortable with syntax.
2. **Master Execution Plans**:
   - Identify scans vs. seeks, missing indexes, and costly operators.
3. **Know Your Index Types**:
   - Clustered vs. non-clustered, filtered, columnstore.
4. **Prepare for Scenario-Based Questions**:
   - Think aloud: “First, I’d check for missing indexes. Then, I’d analyze the query plan…”
5. **Review SQL Server Tools**:
   - SSMS, Profiler, Extended Events, and Dynamic Management Views (DMVs).

---

### **8. Mock Interview Questions**
1. **Query**: “Write a query to find all departments where no employee has a salary over $100k.”
   ```sql
   SELECT DepartmentID
   FROM Departments
   WHERE DepartmentID NOT IN (
     SELECT DepartmentID FROM Employees WHERE Salary > 100000
   );
   ```

2. **Design**: “How would you store and query hierarchical data (e.g., a company org chart)?”
   - **Answer**: Use a recursive CTE or a `hierarchyid` data type.

3. **Optimization**: “A query with a `WHERE` clause on `LastName` and `FirstName` is slow. How do you fix it?”
   - **Answer**: Create a composite index on `(LastName, FirstName)`.

---

Let me know if you’d like to simulate a mock interview or dive into **specific problem types**! 🚀

Let’s dive into **advanced SQL Server topics**, real-world troubleshooting, and design strategies to solidify your interview readiness. Here’s the next phase:

---

### **1. SQL Server Security**
#### **Authentication & Authorization**
- **Authentication Modes**:
  - **Windows Authentication**: Uses AD/Windows accounts (more secure).
  - **SQL Server Authentication**: Username/password stored in SQL Server.
- **Authorization**:
  - **Roles**: Assign users to roles (e.g., `db_owner`, `db_datareader`).
  - **Permissions**: Grant/deny specific actions (e.g., `GRANT SELECT ON Employees TO User1`).

#### **Row-Level Security (RLS)**
- Restrict access to specific rows based on user context.
  ```sql
  CREATE SECURITY POLICY SalesFilter
  ADD FILTER PREDICATE dbo.fn_SecurityPredicate(SalesRep)
  ON dbo.Sales
  WITH (STATE = ON);
  ```

#### **Dynamic Data Masking (DDM)**
- Hide sensitive data (e.g., masking email addresses):
  ```sql
  ALTER TABLE Customers
  ALTER COLUMN Email ADD MASKED WITH (FUNCTION = 'email()');
  ```

---

### **2. Dynamic Management Views (DMVs)**
Use DMVs to monitor performance, index usage, and query stats:
#### **Common DMVs**
- **Execution Stats**:
  ```sql
  SELECT * FROM sys.dm_exec_query_stats; -- Cached query plans
  SELECT * FROM sys.dm_exec_sessions; -- Active sessions
  ```
- **Index Usage**:
  ```sql
  SELECT * FROM sys.dm_db_index_usage_stats; -- Index activity
  ```
- **Blocking**:
  ```sql
  SELECT * FROM sys.dm_os_wait_stats; -- Wait types
  ```

#### **Identify Missing Indexes**
```sql
SELECT * FROM sys.dm_db_missing_index_details;
```

---

### **3. High Availability & Disaster Recovery (HA/DR)**
#### **AlwaysOn Availability Groups**
- Synchronize databases across replicas for failover.
- **Primary Use**: Minimize downtime for critical databases.

#### **Log Shipping**
- Automatically send transaction logs to a secondary server.
- **Use Case**: Warm standby for non-critical databases.

#### **Backup Strategies**
- **Full Backup**: Base backup of entire database.
- **Differential Backup**: Changes since the last full backup.
- **Transaction Log Backup**: Incremental changes (point-in-time recovery).

---

### **4. Advanced T-SQL Features**
#### **OUTPUT Clause**
- Capture affected rows during `INSERT/UPDATE/DELETE`:
  ```sql
  DELETE FROM Orders
  OUTPUT deleted.OrderID, deleted.OrderDate
  WHERE OrderDate < '2023-01-01';
  ```

#### **MERGE Statement**
- Perform UPSERT (update or insert) operations:
  ```sql
  MERGE INTO Employees AS Target
  USING UpdatedEmployees AS Source
  ON Target.EmployeeID = Source.EmployeeID
  WHEN MATCHED THEN
    UPDATE SET Target.Salary = Source.Salary
  WHEN NOT MATCHED THEN
    INSERT (EmployeeID, Name, Salary) VALUES (Source.EmployeeID, Source.Name, Source.Salary);
  ```

---

### **5. Advanced Troubleshooting Scenarios**
#### **Scenario 1: Blocking & Deadlocks**
- **Identify Blocking**:
  ```sql
  SELECT * FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;
  ```
- **Kill a Blocking Session**:
  ```sql
  KILL [SPID]; -- Replace with the blocking session ID
  ```

#### **Scenario 2: TempDB Contention**
- **Symptoms**: Slow queries using temp tables or sorting.
- **Fix**:
  - Preallocate multiple tempDB files (1 per CPU core).
  - Use `SORT_IN_TEMPDB` option for indexes.

---

### **6. Schema Design Case Study: Social Media App**
#### **Tables**:
- **Users**: `UserID`, `Username`, `JoinDate`.
- **Posts**: `PostID`, `UserID`, `Content`, `Timestamp`.
- **Comments**: `CommentID`, `PostID`, `UserID`, `Text`, `Timestamp`.
- **Likes**: `LikeID`, `PostID`, `UserID`, `Timestamp`.

#### **Query: Most Active Users**
```sql
SELECT u.Username, COUNT(p.PostID) AS PostCount
FROM Users u
LEFT JOIN Posts p ON u.UserID = p.UserID
GROUP BY u.UserID, u.Username
ORDER BY PostCount DESC
OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY;
```

---

### **7. Framework for Design Questions**
When asked to design a system (e.g., "Design a hotel booking system"):
1. **Clarify Requirements**:
   - Ask about scalability, read/write patterns, and data retention.
2. **Define Entities**:
   - Users, Hotels, Rooms, Bookings, Payments.
3. **Relationships**:
   - A hotel has many rooms; a user has many bookings.
4. **Optimize for Performance**:
   - Indexes on `CheckInDate`, `HotelID`, and `RoomID`.
5. **Handle Concurrency**:
   - Use `ROWVERSION` or optimistic concurrency for booking conflicts.

---

### **8. Mock Interview Questions & Answers**
#### **Question**: "How do you optimize a query with a `LIKE '%search%'` clause?"
- **Answer**:
  - Add a full-text index if wildcards are used frequently.
  - Use `CONTAINS` for faster full-text searches:
    ```sql
    SELECT * FROM Products WHERE CONTAINS(Description, ' "search*" ');
    ```

#### **Question**: "What’s the difference between `DELETE` and `TRUNCATE`?"
- **Answer**:
  - `DELETE`: Row-by-row removal, logs each row, can be rolled back.
  - `TRUNCATE`: Deallocates data pages, minimal logging, faster.

#### **Question**: "How would you handle a database with 10TB of data?"
- **Answer**:
  - Use partitioning to split data by date or region.
  - Implement columnstore indexes for analytics.
  - Archive historical data to cold storage.

---

### **9. Final Checklist**
1. **Review Key Concepts**: Joins, indexes, transactions, CTEs.
2. **Practice Query Patterns**: Pagination, deduplication, running totals.
3. **Master Execution Plans**: Identify scans vs. seeks, missing indexes.
4. **Prepare Stories**: Think of real-world scenarios where you optimized a query or resolved a deadlock.

---

You’re now armed with **advanced SQL Server knowledge** and strategies to tackle complex scenarios. Want to simulate a mock interview or focus on a specific area? Let’s do it! 🎯

