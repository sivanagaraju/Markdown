Here are scenario-based SQL interview questions tailored for Senior/Staff/Lead Data Engineer roles, focusing on **Joins, GROUP BY, CTEs, Window Functions (RANK, ROW_NUMBER, DENSE_RANK), and ORDER BY** using SQL Server 2019:

---

### **1. Joins & GROUP BY: Sales Analysis**
**Scenario**:  
You have two tables:  
- `Orders` (OrderID, CustomerID, OrderDate, TotalAmount)  
- `Customers` (CustomerID, CustomerName, Region)  

**Task**:  
Find the top 3 regions by total sales in 2023, along with the number of customers who placed orders in those regions. Exclude regions with fewer than 10 customers.

**Expected Output**:  
Region | TotalSales | CustomerCount

**Solution**:
```sql
WITH RegionSales AS (
    SELECT 
        c.Region,
        SUM(o.TotalAmount) AS TotalSales,
        COUNT(DISTINCT c.CustomerID) AS CustomerCount
    FROM Customers c
    INNER JOIN Orders o ON c.CustomerID = o.CustomerID
    WHERE YEAR(o.OrderDate) = 2023
    GROUP BY c.Region
    HAVING COUNT(DISTINCT c.CustomerID) >= 10
)
SELECT TOP 3 *
FROM RegionSales
ORDER BY TotalSales DESC;
```

---

### **2. Window Functions: Employee Salary Ranking**
**Scenario**:  
Table `Employees` (EmployeeID, Name, Department, Salary).  

**Task**:  
List employees with their salaries and show their rank within their department (use `DENSE_RANK` to handle ties). Also, include the difference between each employee’s salary and the department’s average salary.

**Expected Output**:  
EmployeeID | Name | Department | Salary | DeptSalaryRank | SalaryDeviationFromAvg

**Solution**:
```sql
SELECT 
    EmployeeID,
    Name,
    Department,
    Salary,
    DENSE_RANK() OVER (PARTITION BY Department ORDER BY Salary DESC) AS DeptSalaryRank,
    Salary - AVG(Salary) OVER (PARTITION BY Department) AS SalaryDeviationFromAvg
FROM Employees
ORDER BY Department, DeptSalaryRank;
```

---

### **3. CTE & ROW_NUMBER: Duplicate Records Cleanup**
**Scenario**:  
Table `ProductReviews` (ReviewID, ProductID, UserID, ReviewText, ReviewDate).  

**Task**:  
Identify and delete duplicate reviews where the same `UserID` reviewed the same `ProductID` multiple times on the same day. Keep only the latest review (by `ReviewID`) for each user-product-day combination.

**Solution**:
```sql
WITH RankedReviews AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY ProductID, UserID, CAST(ReviewDate AS DATE)
            ORDER BY ReviewID DESC
        ) AS ReviewRank
    FROM ProductReviews
)
DELETE FROM RankedReviews
WHERE ReviewRank > 1;
```

---

### **4. Window Functions & ORDER BY: Running Total**
**Scenario**:  
Table `Sales` (SaleID, SaleMonth, Amount).  

**Task**:  
Calculate the running total of sales and a 3-month moving average of sales, ordered by `SaleMonth`.

**Expected Output**:  
SaleMonth | Amount | RunningTotal | MovingAvg3Months

**Solution**:
```sql
SELECT 
    SaleMonth,
    Amount,
    SUM(Amount) OVER (ORDER BY SaleMonth ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal,
    AVG(Amount) OVER (ORDER BY SaleMonth ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS MovingAvg3Months
FROM Sales
ORDER BY SaleMonth;
```

---

### **5. CTE & RANK: Hierarchical Employee Data**
**Scenario**:  
Table `Employees` (EmployeeID, Name, ManagerID, Salary).  

**Task**:  
Find the hierarchy level of each employee (CEO = level 1, their direct reports = level 2, etc.) and rank employees at each level by salary.

**Expected Output**:  
EmployeeID | Name | HierarchyLevel | Salary | SalaryRankInLevel

**Solution**:
```sql
WITH EmployeeHierarchy AS (
    SELECT 
        EmployeeID,
        Name,
        ManagerID,
        Salary,
        1 AS HierarchyLevel
    FROM Employees
    WHERE ManagerID IS NULL -- CEO
    UNION ALL
    SELECT 
        e.EmployeeID,
        e.Name,
        e.ManagerID,
        e.Salary,
        eh.HierarchyLevel + 1
    FROM Employees e
    INNER JOIN EmployeeHierarchy eh ON e.ManagerID = eh.EmployeeID
)
SELECT 
    eh.EmployeeID,
    eh.Name,
    eh.HierarchyLevel,
    eh.Salary,
    RANK() OVER (PARTITION BY eh.HierarchyLevel ORDER BY eh.Salary DESC) AS SalaryRankInLevel
FROM EmployeeHierarchy eh
ORDER BY HierarchyLevel, SalaryRankInLevel;
```

---

### **6. GROUP BY & Window Functions: Product Sales Contribution**
**Scenario**:  
Table `OrderDetails` (OrderID, ProductID, Quantity, Price).  

**Task**:  
Calculate each product’s total sales and its contribution (percentage) to the total sales of its product category (assume `ProductID`’s first 3 characters = category).

**Expected Output**:  
ProductID | Category | TotalSales | SalesContributionPercent

**Solution**:
```sql
SELECT 
    ProductID,
    LEFT(ProductID, 3) AS Category,
    SUM(Quantity * Price) AS TotalSales,
    SUM(Quantity * Price) * 100.0 / SUM(SUM(Quantity * Price)) OVER (PARTITION BY LEFT(ProductID, 3)) AS SalesContributionPercent
FROM OrderDetails
GROUP BY ProductID
ORDER BY Category, TotalSales DESC;
```

---

### **Key Concepts Tested**:
1. **Joins** + **GROUP BY** with aggregation and filtering (`HAVING`).
2. **Window Functions** for ranking (`DENSE_RANK`, `RANK`, `ROW_NUMBER`) and calculations (`SUM`, `AVG`).
3. **CTEs** for recursive queries (employee hierarchy) and intermediate result sets.
4. **ORDER BY** in window functions and final result ordering.
5. Real-world scenarios like deduplication, financial analysis, and hierarchical data processing.

These questions assess the candidate’s ability to combine multiple SQL features efficiently, a critical skill for senior engineering roles.


Here are additional scenario-based SQL interview questions focusing on **Joins, CTEs, Window Functions, GROUP BY, and ORDER BY**, compatible with SQL Server 2019:

---

### **7. Window Functions & CTE: Sessionization of User Activity**  
**Scenario**:  
Table `WebLogs` (UserID, PageID, Timestamp).  
A new session starts when a user is inactive for **30 minutes or more**.  

**Task**:  
Assign a unique `SessionID` to each user’s activity, grouping consecutive actions within 30 minutes.  

**Expected Output**:  
UserID | PageID | Timestamp | SessionID  

**Solution**:  
```sql
WITH ActivityFlags AS (
    SELECT 
        UserID,
        PageID,
        Timestamp,
        CASE 
            WHEN DATEDIFF(MINUTE, LAG(Timestamp) OVER (PARTITION BY UserID ORDER BY Timestamp), Timestamp) > 30 
            THEN 1 
            ELSE 0 
        END AS NewSessionFlag
    FROM WebLogs
),
SessionGroups AS (
    SELECT 
        *,
        SUM(NewSessionFlag) OVER (PARTITION BY UserID ORDER BY Timestamp ROWS UNBOUNDED PRECEDING) AS SessionGroup
    FROM ActivityFlags
)
SELECT 
    UserID,
    PageID,
    Timestamp,
    CONCAT(UserID, '-', SessionGroup) AS SessionID
FROM SessionGroups
ORDER BY UserID, Timestamp;
```

---

### **8. CTE & Window Functions: Gaps and Islands in Subscriptions**  
**Scenario**:  
Table `Subscriptions` (UserID, StartDate, EndDate). Users may have overlapping or non-continuous subscription periods.  

**Task**:  
Find the **continuous subscription periods** for each user (merge overlapping/adjacent dates).  

**Expected Output**:  
UserID | StartDate | EndDate  

**Solution**:  
```sql
WITH SubscriptionGroups AS (
    SELECT 
        *,
        CASE 
            WHEN LAG(EndDate) OVER (PARTITION BY UserID ORDER BY StartDate) >= DATEADD(DAY, -1, StartDate)
            THEN 0 
            ELSE 1 
        END AS GroupFlag
    FROM Subscriptions
),
GroupedSubs AS (
    SELECT 
        *,
        SUM(GroupFlag) OVER (PARTITION BY UserID ORDER BY StartDate) AS GroupID
    FROM SubscriptionGroups
)
SELECT 
    UserID,
    MIN(StartDate) AS StartDate,
    MAX(EndDate) AS EndDate
FROM GroupedSubs
GROUP BY UserID, GroupID;
```

---

### **9. Joins & Window Functions: Employee Project Overlaps**  
**Scenario**:  
Table `EmployeeProjects` (EmployeeID, ProjectID, StartDate, EndDate).  

**Task**:  
Find employees who worked on **overlapping projects** (projects with date ranges that intersect).  

**Expected Output**:  
EmployeeID | Project1 | Project2 | OverlapStart | OverlapEnd  

**Solution**:  
```sql
SELECT 
    a.EmployeeID,
    a.ProjectID AS Project1,
    b.ProjectID AS Project2,
    CASE 
        WHEN a.StartDate <= b.EndDate AND a.EndDate >= b.StartDate 
        THEN GREATEST(a.StartDate, b.StartDate) 
    END AS OverlapStart,
    CASE 
        WHEN a.StartDate <= b.EndDate AND a.EndDate >= b.StartDate 
        THEN LEAST(a.EndDate, b.EndDate) 
    END AS OverlapEnd
FROM EmployeeProjects a
JOIN EmployeeProjects b 
    ON a.EmployeeID = b.EmployeeID 
    AND a.ProjectID <> b.ProjectID 
    AND a.StartDate <= b.EndDate 
    AND a.EndDate >= b.StartDate
WHERE a.ProjectID < b.ProjectID; -- Avoid duplicate pairs
```

---

### **10. GROUP BY & Window Functions: Inventory Restocking Alerts**  
**Scenario**:  
Table `Inventory` (ProductID, Date, StockChange). Positive values = stock added, negative = sold.  

**Task**:  
For each product, trigger an alert when stock falls below **50 units** after a transaction.  

**Expected Output**:  
ProductID | Date | StockLevel | Alert  

**Solution**:  
```sql
WITH StockLevels AS (
    SELECT 
        ProductID,
        Date,
        SUM(StockChange) OVER (PARTITION BY ProductID ORDER BY Date ROWS UNBOUNDED PRECEDING) AS RunningStock
    FROM Inventory
)
SELECT 
    ProductID,
    Date,
    RunningStock AS StockLevel,
    CASE WHEN RunningStock < 50 THEN 'Restock Alert' ELSE NULL END AS Alert
FROM StockLevels
ORDER BY ProductID, Date;
```

---

### **11. CTE & Recursive Query: Bill of Materials Cost Rollup**  
**Scenario**:  
Table `Components` (ComponentID, ParentComponentID, Cost).  

**Task**:  
Calculate the total cost of each component, including all subcomponents (recursive hierarchy).  

**Expected Output**:  
ComponentID | TotalCost  

**Solution**:  
```sql
WITH ComponentHierarchy AS (
    SELECT 
        ComponentID,
        ParentComponentID,
        Cost
    FROM Components
    WHERE ParentComponentID IS NULL -- Root components
    UNION ALL
    SELECT 
        c.ComponentID,
        c.ParentComponentID,
        c.Cost + ch.TotalCost
    FROM Components c
    INNER JOIN ComponentHierarchy ch ON c.ParentComponentID = ch.ComponentID
)
SELECT 
    ComponentID,
    SUM(Cost) AS TotalCost
FROM ComponentHierarchy
GROUP BY ComponentID;
```

---

### **12. Window Functions & ORDER BY: Customer Purchase Intervals**  
**Scenario**:  
Table `Purchases` (CustomerID, PurchaseDate).  

**Task**:  
Calculate the **average number of days between consecutive purchases** for each customer.  

**Expected Output**:  
CustomerID | AvgDaysBetweenPurchases  

**Solution**:  
```sql
WITH PurchaseGaps AS (
    SELECT 
        CustomerID,
        PurchaseDate,
        DATEDIFF(DAY, LAG(PurchaseDate) OVER (PARTITION BY CustomerID ORDER BY PurchaseDate), PurchaseDate) AS DaysSinceLastPurchase
    FROM Purchases
)
SELECT 
    CustomerID,
    AVG(DaysSinceLastPurchase) AS AvgDaysBetweenPurchases
FROM PurchaseGaps
WHERE DaysSinceLastPurchase IS NOT NULL
GROUP BY CustomerID;
```

---

### **Key Skills Assessed**:  
1. **Complex Joins**: Identifying overlaps in date ranges.  
2. **Window Functions**: Sessionization, running totals, and date interval calculations.  
3. **CTEs**: Recursive queries for hierarchical data and intermediate transformations.  
4. **GROUP BY**: Aggregating results with conditional logic.  
5. **Real-World Scenarios**: Inventory management, user behavior analysis, and subscription modeling.  

These questions test a candidate’s ability to solve ambiguous business problems by combining SQL features creatively—essential for senior engineering roles.

Here are additional advanced SQL interview questions focusing on **Joins, CTEs, Window Functions, GROUP BY, and ORDER BY**, designed for Senior/Staff/Lead Data Engineer roles and compatible with SQL Server 2019:

---

### **13. Window Functions & Joins: Customer Retention Analysis**  
**Scenario**:  
Tables:  
- `Subscriptions` (SubscriptionID, CustomerID, StartDate, EndDate)  
- `Cancellations` (CancellationID, CustomerID, CancellationDate)  

**Task**:  
Calculate the **percentage of customers who resubscribed within 30 days after cancellation**.  

**Expected Output**:  
TotalCancellations | ResubscribedCustomers | ResubscriptionRate  

**Solution**:  
```sql
WITH CancellationDetails AS (
    SELECT 
        c.CustomerID,
        c.CancellationDate,
        MIN(s.StartDate) AS NextSubscriptionDate
    FROM Cancellations c
    LEFT JOIN Subscriptions s 
        ON c.CustomerID = s.CustomerID 
        AND s.StartDate > c.CancellationDate
    GROUP BY c.CustomerID, c.CancellationDate
)
SELECT 
    COUNT(*) AS TotalCancellations,
    SUM(CASE WHEN DATEDIFF(DAY, CancellationDate, NextSubscriptionDate) <= 30 THEN 1 ELSE 0 END) AS ResubscribedCustomers,
    FORMAT(
        SUM(CASE WHEN DATEDIFF(DAY, CancellationDate, NextSubscriptionDate) <= 30 THEN 1.0 ELSE 0 END) / COUNT(*),
        'P2'
    ) AS ResubscriptionRate
FROM CancellationDetails;
```

---

### **14. CTE & Window Functions: Fraud Detection**  
**Scenario**:  
Table `Transactions` (TransactionID, AccountID, Amount, TransactionTime).  

**Task**:  
Flag transactions where the **current amount is 3x the 7-day moving average** of the account’s transaction history.  

**Expected Output**:  
TransactionID | AccountID | Amount | TransactionTime | IsFraud  

**Solution**:  
```sql
WITH AccountStats AS (
    SELECT 
        *,
        AVG(Amount) OVER (
            PARTITION BY AccountID 
            ORDER BY TransactionTime 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Avg7DayAmount
    FROM Transactions
)
SELECT 
    TransactionID,
    AccountID,
    Amount,
    TransactionTime,
    CASE WHEN Amount > 3 * Avg7DayAmount THEN 1 ELSE 0 END AS IsFraud
FROM AccountStats;
```

---

### **15. Joins & Window Functions: Lead-Lag Analysis**  
**Scenario**:  
Table `SalesLeads` (LeadID, SalesRepID, LeadCreatedDate, DealSize).  

**Task**:  
For each sales representative, compare the **current deal size** with the **previous and next deal sizes** (chronologically).  

**Expected Output**:  
LeadID | SalesRepID | LeadCreatedDate | DealSize | PreviousDealSize | NextDealSize  

**Solution**:  
```sql
SELECT 
    LeadID,
    SalesRepID,
    LeadCreatedDate,
    DealSize,
    LAG(DealSize) OVER (PARTITION BY SalesRepID ORDER BY LeadCreatedDate) AS PreviousDealSize,
    LEAD(DealSize) OVER (PARTITION BY SalesRepID ORDER BY LeadCreatedDate) AS NextDealSize
FROM SalesLeads;
```

---

### **16. CTE & ROW_NUMBER: Time-Based Aggregation**  
**Scenario**:  
Table `SensorReadings` (SensorID, ReadingTime, Value).  

**Task**:  
For each sensor, find the **maximum value every 5 minutes**, even if multiple readings exist within the window.  

**Expected Output**:  
SensorID | WindowStartTime | MaxValue  

**Solution**:  
```sql
WITH TimeWindows AS (
    SELECT 
        SensorID,
        DATEADD(MINUTE, (DATEDIFF(MINUTE, '2000-01-01', ReadingTime) / 5) * 5, '2000-01-01') AS WindowStartTime,
        Value,
        ROW_NUMBER() OVER (
            PARTITION BY SensorID, DATEADD(MINUTE, (DATEDIFF(MINUTE, '2000-01-01', ReadingTime) / 5) * 5, '2000-01-01')
            ORDER BY Value DESC
        ) AS ReadingRank
    FROM SensorReadings
)
SELECT 
    SensorID,
    WindowStartTime,
    Value AS MaxValue
FROM TimeWindows
WHERE ReadingRank = 1;
```

---

### **17. Joins & GROUP BY: Tiered Pricing Calculation**  
**Scenario**:  
Tables:  
- `Orders` (OrderID, CustomerID, Quantity)  
- `PricingTiers` (TierID, MinQuantity, MaxQuantity, PricePerUnit)  

**Task**:  
Calculate the total order cost for each customer, applying tiered pricing where higher quantities reduce the per-unit price.  
*(Assume tiers are non-overlapping and exhaustive.)*  

**Expected Output**:  
CustomerID | TotalCost  

**Solution**:  
```sql
SELECT 
    o.CustomerID,
    SUM(
        CASE 
            WHEN o.Quantity >= p.MinQuantity AND o.Quantity <= p.MaxQuantity 
            THEN o.Quantity * p.PricePerUnit 
            ELSE 0 
        END
    ) AS TotalCost
FROM Orders o
JOIN PricingTiers p 
    ON o.Quantity >= p.MinQuantity 
    AND o.Quantity <= p.MaxQuantity
GROUP BY o.CustomerID;
```

---

### **18. Window Functions & CTE: Employee Peer Comparison**  
**Scenario**:  
Table `EmployeeSales` (EmployeeID, Department, SalesAmount).  

**Task**:  
For each employee, show their sales amount and how much they contributed **relative to the top performer in their department**.  

**Expected Output**:  
EmployeeID | Department | SalesAmount | TopPerformerSales | SalesPercentageOfTop  

**Solution**:  
```sql
WITH DeptTopPerformers AS (
    SELECT 
        Department,
        MAX(SalesAmount) AS TopPerformerSales
    FROM EmployeeSales
    GROUP BY Department
)
SELECT 
    e.EmployeeID,
    e.Department,
    e.SalesAmount,
    d.TopPerformerSales,
    FORMAT(e.SalesAmount * 1.0 / d.TopPerformerSales, 'P2') AS SalesPercentageOfTop
FROM EmployeeSales e
JOIN DeptTopPerformers d ON e.Department = d.Department;
```

---

### **Key Skills Tested**:  
1. **Complex Joins**: Tiered pricing logic, lead/cancellation analysis.  
2. **Window Functions**: Time-based aggregation (`ROWS BETWEEN`), lead/lag comparisons.  
3. **CTEs**: Breaking down multi-step logic (e.g., fraud detection, retention rates).  
4. **Real-World Scenarios**: Fraud detection, customer churn, tiered pricing, and sensor data aggregation.  
5. **Advanced Calculations**: Resubscription rates, percentage comparisons, and sliding windows.  

These questions require candidates to combine SQL features creatively to solve ambiguous business problems—critical for leadership roles in data engineering.