### Common Table Expressions (CTEs) in SQL: What You Can and Cannot Include

A **Common Table Expression (CTE)** is a temporary named result set that can be referenced within a SQL query. It is defined using the `WITH` clause and is particularly useful for breaking down complex queries.

---

#### **What You Can Include in a CTE**:
1. **Basic SELECT Operations**: Including `JOIN`, `WHERE`, `GROUP BY`, `HAVING`, etc.
2. **Recursive Queries**: Using `UNION ALL` to combine an anchor member (base case) and a recursive member.
3. **Multiple CTEs**: Define multiple CTEs in a single `WITH` clause, separated by commas.
4. **References to Other CTEs**: A CTE can reference previously defined CTEs in the same `WITH` clause.

#### **What You Cannot Include**:
1. **Self-Reference (Non-Recursive CTEs)**: Only recursive CTEs can reference themselves.
2. **ORDER BY Without TOP/OFFSET-FETCH**: In some SQL dialects (e.g., SQL Server), `ORDER BY` requires `TOP`, `OFFSET`, or `FOR XML`.
3. **Aggregates in Recursive Members**: Some databases restrict aggregate/window functions in the recursive part of a CTE.
4. **Schema Modifications**: CTEs cannot contain `INSERT`, `UPDATE`, or `DELETE` statements (though they can be used in such statements).

---

### Recursive CTE Example: Employee Hierarchy
Assume a table `Employees` with `EmployeeID`, `Name`, and `ManagerID`:

```sql
WITH RECURSIVE EmployeeHierarchy AS (
    -- Anchor Member: Top-level manager (no manager)
    SELECT 
        EmployeeID, 
        Name, 
        ManagerID, 
        1 AS Level
    FROM Employees
    WHERE ManagerID IS NULL

    UNION ALL

    -- Recursive Member: Join employees to their managers
    SELECT 
        e.EmployeeID, 
        e.Name, 
        e.ManagerID, 
        eh.Level + 1 AS Level
    FROM Employees e
    INNER JOIN EmployeeHierarchy eh ON e.ManagerID = eh.EmployeeID
)
SELECT * FROM EmployeeHierarchy;
```

**Output**:
```
EmployeeID | Name    | ManagerID | Level
-----------------------------------------
1          | Alice   | NULL      | 1
2          | Bob     | 1         | 2
3          | Charlie | 2         | 3
```

---

### Key Uses of Recursive CTEs:
1. **Hierarchical Data Traversal**:
   - Organizational charts, folder structures, or bill-of-materials (BOM).
2. **Sequence Generation**:
   - Create number/date series (e.g., days between two dates).
3. **Path Enumeration**:
   - Track paths in tree structures (e.g., `root > child > grandchild`).
4. **Cycle Detection**:
   - Identify loops in graphs (e.g., using a `path` column to track visited nodes).
5. **Tree Aggregation**:
   - Sum values from leaf nodes up to the root (e.g., total cost in a BOM).

---

### Recursive CTE Structure:
1. **Anchor Member**: The initial query (base case).
2. **Recursive Member**: References the CTE and joins with the anchor.
3. **Termination Condition**: Stops recursion when no new rows are added (e.g., `WHERE Level < 10`).

---

### Example 2: Generate a Number Series (1 to 10)
```sql
WITH RECURSIVE Numbers AS (
    -- Anchor Member: Start at 1
    SELECT 1 AS n

    UNION ALL

    -- Recursive Member: Increment until n = 10
    SELECT n + 1
    FROM Numbers
    WHERE n < 10
)
SELECT * FROM Numbers;
```

**Output**:
```
n
---
1
2
...
10
```

---

### Best Practices:
- Use `UNION ALL` (not `UNION`) for recursion to avoid deduplication overhead.
- Include a termination condition to prevent infinite loops.
- Use cycle detection clauses (e.g., `CYCLE` in PostgreSQL) or manual tracking for graph traversal.

Recursive CTEs are powerful for hierarchical queries but require careful design to avoid performance pitfalls.


Here are more examples of **CTEs** (Common Table Expressions) and **recursive CTEs** to illustrate their versatility:

---

### **1. Regular CTE: Sales Report by Category**
**Scenario**: Calculate total sales per product category and filter top categories.

```sql
WITH SalesByCategory AS (
    SELECT 
        c.CategoryName,
        SUM(od.Quantity * od.UnitPrice) AS TotalSales
    FROM OrderDetails od
    JOIN Products p ON od.ProductID = p.ProductID
    JOIN Categories c ON p.CategoryID = c.CategoryID
    GROUP BY c.CategoryName
)
SELECT 
    CategoryName,
    TotalSales
FROM SalesByCategory
WHERE TotalSales > 10000
ORDER BY TotalSales DESC;
```

**Output**:
```
CategoryName | TotalSales
-------------------------
Beverages    | 150000
Dairy        | 120000
```

---

### **2. Regular CTE: Data Transformation**
**Scenario**: Identify employees with above-average salaries.

```sql
WITH AverageSalary AS (
    SELECT AVG(Salary) AS AvgSal
    FROM Employees
)
SELECT 
    EmployeeID,
    Name,
    Salary
FROM Employees
WHERE Salary > (SELECT AvgSal FROM AverageSalary);
```

**Output**:
```
EmployeeID | Name   | Salary
----------------------------
101        | Alice  | 95000
102        | Bob    | 110000
```

---

### **3. Recursive CTE: Product Category Hierarchy**
**Scenario**: Traverse nested product categories (e.g., parent-child relationships).

**Table**: `Categories`  
| CategoryID | CategoryName | ParentCategoryID |
|------------|--------------|-------------------|
| 1          | Electronics  | NULL              |
| 2          | Laptops      | 1                 |
| 3          | Smartphones  | 1                 |
| 4          | Gaming       | 2                 |

```sql
WITH RECURSIVE CategoryTree AS (
    -- Anchor: Root categories (no parent)
    SELECT 
        CategoryID,
        CategoryName,
        ParentCategoryID,
        1 AS Level
    FROM Categories
    WHERE ParentCategoryID IS NULL

    UNION ALL

    -- Recursive: Join child categories to parent
    SELECT 
        c.CategoryID,
        c.CategoryName,
        c.ParentCategoryID,
        ct.Level + 1 AS Level
    FROM Categories c
    INNER JOIN CategoryTree ct ON c.ParentCategoryID = ct.CategoryID
)
SELECT * FROM CategoryTree;
```

**Output**:
```
CategoryID | CategoryName | ParentCategoryID | Level
----------------------------------------------------
1          | Electronics  | NULL              | 1
2          | Laptops      | 1                 | 2
3          | Smartphones  | 1                 | 2
4          | Gaming       | 2                 | 3
```

---

### **4. Recursive CTE: Path Enumeration (Tree Path)**
**Scenario**: Show the full path of a folder hierarchy (e.g., `Electronics > Laptops > Gaming`).

**Table**: `Folders`  
| FolderID | FolderName | ParentFolderID |
|----------|------------|----------------|
| 1        | Root       | NULL           |
| 2        | Documents  | 1              |
| 3        | Projects   | 2              |

```sql
WITH RECURSIVE FolderPath AS (
    -- Anchor: Root folders
    SELECT 
        FolderID,
        FolderName,
        ParentFolderID,
        CAST(FolderName AS VARCHAR(1000)) AS Path
    FROM Folders
    WHERE ParentFolderID IS NULL

    UNION ALL

    -- Recursive: Build the path
    SELECT 
        f.FolderID,
        f.FolderName,
        f.ParentFolderID,
        CONCAT(fp.Path, ' > ', f.FolderName) AS Path
    FROM Folders f
    INNER JOIN FolderPath fp ON f.ParentFolderID = fp.FolderID
)
SELECT * FROM FolderPath;
```

**Output**:
```
FolderID | FolderName | ParentFolderID | Path
----------------------------------------------
1        | Root       | NULL           | Root
2        | Documents  | 1              | Root > Documents
3        | Projects   | 2              | Root > Documents > Projects
```

---

### **5. Recursive CTE: Generate Date Series**
**Scenario**: Create a sequence of dates between `2023-01-01` and `2023-01-07`.

```sql
WITH RECURSIVE DateSeries AS (
    -- Anchor: Start date
    SELECT CAST('2023-01-01' AS DATE) AS Date

    UNION ALL

    -- Recursive: Increment date by 1 day
    SELECT DATE_ADD(Date, INTERVAL 1 DAY)
    FROM DateSeries
    WHERE Date < '2023-01-07'
)
SELECT Date FROM DateSeries;
```

**Output**:
```
Date
-----------
2023-01-01
2023-01-02
...
2023-01-07
```

---

### **6. Recursive CTE: Cycle Detection in a Graph**
**Scenario**: Detect cycles in a social network (e.g., followers).

**Table**: `Friendships`  
| UserID | FriendID |
|--------|----------|
| 1      | 2        |
| 2      | 3        |
| 3      | 1        | (Cycle: 1 → 2 → 3 → 1)

```sql
WITH RECURSIVE FriendshipPath AS (
    SELECT 
        UserID,
        FriendID,
        CAST(UserID AS VARCHAR(1000)) AS Path,
        FALSE AS IsCycle
    FROM Friendships

    UNION ALL

    SELECT 
        fp.UserID,
        f.FriendID,
        CONCAT(fp.Path, ' → ', f.FriendID),
        f.FriendID = ANY(string_to_array(fp.Path, ' → ')::INT[]) AS IsCycle
    FROM FriendshipPath fp
    JOIN Friendships f ON fp.FriendID = f.UserID
    WHERE NOT fp.IsCycle
)
SELECT * FROM FriendshipPath WHERE IsCycle = TRUE;
```

**Output**:
```
UserID | FriendID | Path      | IsCycle
----------------------------------------
1      | 1        | 1 → 2 → 3 → 1 | TRUE
```

---

### **7. Recursive CTE: Bill of Materials (BOM)**
**Scenario**: Calculate the total cost of a product including nested components.

**Table**: `Components`  
| ComponentID | ComponentName | ParentComponentID | Cost |
|-------------|---------------|--------------------|------|
| 1           | Car           | NULL               | 5000 |
| 2           | Engine        | 1                  | 2000 |
| 3           | Turbo         | 2                  | 500  |

```sql
WITH RECURSIVE BOMCost AS (
    -- Anchor: Root component
    SELECT 
        ComponentID,
        ComponentName,
        ParentComponentID,
        Cost
    FROM Components
    WHERE ParentComponentID IS NULL

    UNION ALL

    -- Recursive: Sum child component costs
    SELECT 
        c.ComponentID,
        c.ComponentName,
        c.ParentComponentID,
        c.Cost + bc.Cost AS Cost
    FROM Components c
    INNER JOIN BOMCost bc ON c.ParentComponentID = bc.ComponentID
)
SELECT * FROM BOMCost;
```

**Output**:
```
ComponentID | ComponentName | ParentComponentID | Cost
-------------------------------------------------------
1           | Car           | NULL               | 5000
2           | Engine        | 1                  | 7000 (5000 + 2000)
3           | Turbo         | 2                  | 7500 (7000 + 500)
```

---

### Key Takeaways:
1. **Regular CTEs** simplify complex queries by breaking them into modular parts.
2. **Recursive CTEs** are ideal for:
   - Hierarchical/tree traversal (employees, folders, BOM).
   - Generating sequences (dates, numbers).
   - Cycle detection in graphs.
3. Always include a **termination condition** (e.g., `WHERE Level < N` or `WHERE Date < 'YYYY-MM-DD'`) to prevent infinite loops.

Let me know if you want to dive deeper into any specific use case! 🚀
