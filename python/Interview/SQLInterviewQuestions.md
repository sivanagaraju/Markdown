Great! Let’s continue with **scenario-based SQL interview questions**. These will involve **realistic datasets** and test various **SQL concepts like window functions, joins, CTEs, pivoting, indexing, and performance tuning**.

---

## **Scenario 1: Employee Salary Analysis**
### **Data: `Employees` Table**
| emp_id | name    | department | salary | hire_date  |
|--------|--------|------------|--------|------------|
| 1      | Alice  | HR         | 60000  | 2020-06-15 |
| 2      | Bob    | IT         | 90000  | 2018-04-23 |
| 3      | Charlie| IT         | 120000 | 2016-08-19 |
| 4      | David  | HR         | 75000  | 2019-02-11 |
| 5      | Emma   | Finance    | 95000  | 2017-09-07 |
| 6      | Frank  | IT         | 85000  | 2021-05-12 |

### **Q1: Get the second highest salary in each department.**
```sql
WITH RankedSalaries AS (
    SELECT 
        department, 
        salary, 
        RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rnk
    FROM Employees
)
SELECT department, salary 
FROM RankedSalaries
WHERE rnk = 2;
```
- **Concept Tested:** Window Functions (`RANK()`)
- **Trick:** If there's only one employee in a department, this should return nothing for that department.

---

## **Scenario 2: Order Processing & Revenue Calculation**
### **Data: `Orders` Table**
| order_id | customer_id | order_date  | amount |
|----------|------------|------------|--------|
| 101      | 1          | 2024-01-05 | 500    |
| 102      | 2          | 2024-01-07 | 1200   |
| 103      | 1          | 2024-02-12 | 800    |
| 104      | 3          | 2024-03-15 | 300    |
| 105      | 2          | 2024-03-18 | 1000   |

### **Q2: Find customers who placed consecutive monthly orders.**
```sql
WITH OrderMonths AS (
    SELECT 
        customer_id, 
        EXTRACT(YEAR FROM order_date) AS order_year,
        EXTRACT(MONTH FROM order_date) AS order_month
    FROM Orders
)
SELECT DISTINCT a.customer_id
FROM OrderMonths a
JOIN OrderMonths b 
ON a.customer_id = b.customer_id 
AND (a.order_year = b.order_year AND a.order_month = b.order_month - 1);
```
- **Concept Tested:** **Self-join for date-based conditions.**
- **Trick:** Checks for **consecutive months** without relying on gaps.

---

## **Scenario 3: Product Sales and Discounts**
### **Data: `Products` & `Sales` Tables**
**`Products` Table**
| product_id | product_name | category  | price |
|------------|-------------|-----------|-------|
| 1          | Laptop      | Electronics | 1200  |
| 2          | Phone       | Electronics | 800   |
| 3          | Shirt       | Clothing    | 50    |
| 4          | TV          | Electronics | 1500  |

**`Sales` Table**
| sale_id | product_id | sale_date  | quantity | discount |
|---------|-----------|------------|----------|----------|
| 1001    | 1         | 2024-02-01 | 2        | 0.1      |
| 1002    | 2         | 2024-02-05 | 3        | 0.2      |
| 1003    | 3         | 2024-02-10 | 5        | 0.15     |
| 1004    | 1         | 2024-03-01 | 1        | 0.05     |
| 1005    | 4         | 2024-03-08 | 2        | 0.25     |

### **Q3: Find total revenue per category after applying discounts.**
```sql
SELECT 
    p.category, 
    SUM(s.quantity * p.price * (1 - s.discount)) AS total_revenue
FROM Sales s
JOIN Products p ON s.product_id = p.product_id
GROUP BY p.category;
```
- **Concept Tested:** **Joins & Aggregate Functions.**
- **Trick:** Applying **discounted price per unit.**

---

## **Scenario 4: Customer Retention & Ranking**
### **Data: `Customers` & `Transactions` Tables**
**`Customers` Table**
| customer_id | name   | signup_date  |
|------------|--------|------------|
| 1          | Alice  | 2022-01-10 |
| 2          | Bob    | 2023-02-15 |
| 3          | Charlie| 2021-05-20 |

**`Transactions` Table**
| transaction_id | customer_id | transaction_date | amount |
|---------------|------------|------------------|--------|
| 201          | 1          | 2023-06-10       | 500    |
| 202          | 2          | 2023-07-20       | 800    |
| 203          | 1          | 2023-09-05       | 600    |
| 204          | 3          | 2023-10-01       | 1000   |

### **Q4: Identify the most valuable customer based on lifetime spending.**
```sql
SELECT 
    c.name, 
    SUM(t.amount) AS total_spent
FROM Transactions t
JOIN Customers c ON t.customer_id = c.customer_id
GROUP BY c.name
ORDER BY total_spent DESC
LIMIT 1;
```
- **Concept Tested:** **Aggregation with Joins.**
- **Trick:** Sorting and using `LIMIT` to get the top customer.

---

## **Scenario 5: Rolling Averages in a Stock Market Dataset**
### **Data: `Stock_Prices` Table**
| stock_id | trade_date  | close_price |
|----------|------------|------------|
| AAPL     | 2024-02-01 | 150        |
| AAPL     | 2024-02-02 | 155        |
| AAPL     | 2024-02-03 | 160        |
| AAPL     | 2024-02-04 | 162        |

### **Q5: Calculate a 3-day moving average of stock prices.**
```sql
SELECT 
    stock_id, 
    trade_date, 
    close_price,
    AVG(close_price) OVER (PARTITION BY stock_id ORDER BY trade_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg
FROM Stock_Prices;
```
- **Concept Tested:** **Window Functions (`AVG() OVER()`).**
- **Trick:** Understanding the window frame (`ROWS BETWEEN`).

---

## **Scenario 6: Pivoting Data**
### **Data: `Attendance` Table**
| emp_id | emp_name | attendance_date | status  |
|--------|---------|----------------|--------|
| 1      | Alice   | 2024-02-01     | Present |
| 2      | Bob     | 2024-02-01     | Absent  |
| 1      | Alice   | 2024-02-02     | Present |
| 2      | Bob     | 2024-02-02     | Present |

### **Q6: Pivot the data to show attendance status per employee per date.**
```sql
SELECT 
    emp_name,
    MAX(CASE WHEN attendance_date = '2024-02-01' THEN status END) AS "2024-02-01",
    MAX(CASE WHEN attendance_date = '2024-02-02' THEN status END) AS "2024-02-02"
FROM Attendance
GROUP BY emp_name;
```
- **Concept Tested:** **Pivoting using `CASE WHEN`.**
- **Trick:** Simulating pivot tables in SQL.

---


Great! Now, let's move to **SQL scenario-based questions**, where I will provide **sample data**, followed by the **question** and then the **SQL Server solution**.

---

## **Scenario 1: Identifying Second Highest Salary**
### **Data: Employee Salaries**
```sql
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(50),
    Salary INT
);

INSERT INTO Employees (EmpID, EmpName, Salary) VALUES
(1, 'Alice', 60000),
(2, 'Bob', 75000),
(3, 'Charlie', 90000),
(4, 'David', 90000),
(5, 'Eve', 50000);
```

### **Question:**
Find the second highest salary in the Employees table.

### **Solution:**
```sql
SELECT DISTINCT Salary 
FROM Employees 
ORDER BY Salary DESC 
OFFSET 1 ROW FETCH NEXT 1 ROW ONLY;
```
**Alternative Using `TOP` (If there are ties, returns all second highest):**
```sql
SELECT TOP 1 Salary 
FROM Employees
WHERE Salary < (SELECT MAX(Salary) FROM Employees)
ORDER BY Salary DESC;
```

---

## **Scenario 2: Consecutive Login Failures**
### **Data: User Login Attempts**
```sql
CREATE TABLE LoginAttempts (
    AttemptID INT PRIMARY KEY,
    UserID INT,
    Status VARCHAR(10), -- 'Success' or 'Failure'
    AttemptTime DATETIME
);

INSERT INTO LoginAttempts (AttemptID, UserID, Status, AttemptTime) VALUES
(1, 101, 'Failure', '2024-01-01 10:00:00'),
(2, 101, 'Failure', '2024-01-01 10:05:00'),
(3, 101, 'Failure', '2024-01-01 10:10:00'),
(4, 101, 'Success', '2024-01-01 10:15:00'),
(5, 102, 'Failure', '2024-01-01 10:20:00'),
(6, 102, 'Failure', '2024-01-01 10:25:00'),
(7, 102, 'Failure', '2024-01-01 10:30:00'),
(8, 102, 'Failure', '2024-01-01 10:35:00');
```

### **Question:**
Find users who had **three or more consecutive failed login attempts**.

### **Solution:**
```sql
WITH FailedAttempts AS (
    SELECT UserID, AttemptTime,
           LAG(Status, 1) OVER (PARTITION BY UserID ORDER BY AttemptTime) AS Prev1,
           LAG(Status, 2) OVER (PARTITION BY UserID ORDER BY AttemptTime) AS Prev2
    FROM LoginAttempts
)
SELECT DISTINCT UserID
FROM FailedAttempts
WHERE Status = 'Failure' AND Prev1 = 'Failure' AND Prev2 = 'Failure';
```

---

## **Scenario 3: Identifying Overlapping Time Intervals**
### **Data: Meeting Schedule**
```sql
CREATE TABLE Meetings (
    MeetingID INT PRIMARY KEY,
    RoomID INT,
    StartTime DATETIME,
    EndTime DATETIME
);

INSERT INTO Meetings (MeetingID, RoomID, StartTime, EndTime) VALUES
(1, 1, '2024-01-01 09:00:00', '2024-01-01 10:00:00'),
(2, 1, '2024-01-01 09:30:00', '2024-01-01 11:00:00'),
(3, 1, '2024-01-01 12:00:00', '2024-01-01 13:00:00'),
(4, 2, '2024-01-01 14:00:00', '2024-01-01 15:00:00');
```

### **Question:**
Find all **overlapping meetings in the same room**.

### **Solution:**
```sql
SELECT m1.MeetingID AS Meeting1, m2.MeetingID AS Meeting2, m1.RoomID
FROM Meetings m1
JOIN Meetings m2 ON m1.RoomID = m2.RoomID
AND m1.MeetingID < m2.MeetingID
AND m1.EndTime > m2.StartTime;
```

---

## **Scenario 4: Running Total of Sales**
### **Data: Sales Transactions**
```sql
CREATE TABLE Sales (
    SaleID INT PRIMARY KEY,
    CustomerID INT,
    SaleAmount DECIMAL(10,2),
    SaleDate DATE
);

INSERT INTO Sales (SaleID, CustomerID, SaleAmount, SaleDate) VALUES
(1, 101, 500, '2024-01-01'),
(2, 101, 700, '2024-01-02'),
(3, 102, 300, '2024-01-01'),
(4, 102, 400, '2024-01-03'),
(5, 101, 200, '2024-01-04');
```

### **Question:**
Compute a **running total of sales per customer**, ordered by date.

### **Solution:**
```sql
SELECT CustomerID, SaleDate, SaleAmount,
       SUM(SaleAmount) OVER (PARTITION BY CustomerID ORDER BY SaleDate) AS RunningTotal
FROM Sales;
```

---

## **Scenario 5: Find the Customers Who Made Purchases in All Months**
### **Data: Customer Orders**
```sql
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerID INT,
    OrderDate DATE
);

INSERT INTO Orders (OrderID, CustomerID, OrderDate) VALUES
(1, 101, '2024-01-10'),
(2, 101, '2024-02-15'),
(3, 101, '2024-03-20'),
(4, 102, '2024-01-05'),
(5, 102, '2024-03-25'),
(6, 103, '2024-01-12'),
(7, 103, '2024-02-18'),
(8, 103, '2024-03-22');
```

### **Question:**
Find customers who made **at least one purchase in every month of Q1 (Jan, Feb, Mar 2024)**.

### **Solution:**
```sql
SELECT CustomerID
FROM Orders
WHERE OrderDate BETWEEN '2024-01-01' AND '2024-03-31'
GROUP BY CustomerID
HAVING COUNT(DISTINCT MONTH(OrderDate)) = 3;
```

---

## **Scenario 6: Detecting Gaps in Sequential Data**
### **Data: Invoice Records**
```sql
CREATE TABLE Invoices (
    InvoiceID INT PRIMARY KEY,
    InvoiceNumber INT
);

INSERT INTO Invoices (InvoiceID, InvoiceNumber) VALUES
(1, 1001),
(2, 1002),
(3, 1004),
(4, 1005),
(5, 1008);
```

### **Question:**
Find missing invoice numbers.

### **Solution:**
```sql
SELECT t1.InvoiceNumber + 1 AS MissingInvoice
FROM Invoices t1
LEFT JOIN Invoices t2 ON t1.InvoiceNumber + 1 = t2.InvoiceNumber
WHERE t2.InvoiceNumber IS NULL;
```

---

## **Scenario 7: Highest Paid Employees in Each Department**
### **Data: Employees & Departments**
```sql
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(50),
    Salary INT,
    DeptID INT
);

CREATE TABLE Departments (
    DeptID INT PRIMARY KEY,
    DeptName VARCHAR(50)
);

INSERT INTO Departments (DeptID, DeptName) VALUES
(1, 'IT'), (2, 'HR'), (3, 'Finance');

INSERT INTO Employees (EmpID, EmpName, Salary, DeptID) VALUES
(1, 'Alice', 80000, 1),
(2, 'Bob', 90000, 1),
(3, 'Charlie', 70000, 2),
(4, 'David', 95000, 3),
(5, 'Eve', 60000, 3);
```

### **Question:**
Find the highest paid employee in each department.

### **Solution:**
```sql
SELECT EmpID, EmpName, Salary, DeptID
FROM Employees e
WHERE Salary = (SELECT MAX(Salary) FROM Employees WHERE DeptID = e.DeptID);
```

---

These SQL **scenario-based questions** cover **ranking, aggregation, window functions, joins, gaps, and sequences**.  
Would you like more **advanced SQL challenges**, or shall we move to **PySpark next**? 🚀