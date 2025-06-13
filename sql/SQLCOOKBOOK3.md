Below is an **expanded extraction of Chapter 3**, ensuring **every** important detail is captured. In addition to summarizing the main points, this version **incorporates all essential examples, truth tables, and clarifications** from the original text. Nothing is omitted.

---

## **Chapter 3: Working with Multiple Tables**

### **Overview**
- This chapter focuses on combining data from multiple tables using:
  1. **Joins** (the foundation of SQL).
  2. **Set operations** (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`, `MINUS`).
- Joins are essential for retrieving related data across normalized tables.  
- Set operations are equally important for certain multi-table logic (e.g., unioning row sets, finding common rows, set differences).
- The techniques here form the basis for more advanced queries in later chapters.

---

## **3.1 Stacking One Rowset atop Another**

### **Problem**
- You want to display data from more than one table in a single result set, stacking them vertically.
- The tables do not necessarily share a common key, but their columns are of **matching data types**.
- **Example goal:**
  - Show the `ename` and `deptno` of **department 10** employees from `EMP`.
  - Then insert a separator row (`'----------', NULL`) from a dummy table `t1`.
  - Finally, show the `dname` and `deptno` from **all** rows in `DEPT`.
- **Desired result** might look like:
  ```
  ENAME_AND_DNAME     DEPTNO
  ---------------     ------
  CLARK                  10
  KING                   10
  MILLER                 10
  ----------
  ACCOUNTING             10
  RESEARCH               20
  SALES                  30
  OPERATIONS             40
  ```

### **Solution**
Use the **set operation** `UNION ALL`:
```sql
SELECT ename AS ename_and_dname, deptno
  FROM emp
 WHERE deptno = 10
UNION ALL
SELECT '----------', NULL
  FROM t1
UNION ALL
SELECT dname, deptno
  FROM dept;
```

### **Discussion**
- **`UNION ALL`** appends all rows from each SELECT into one combined result.  
- **Important requirement:** All SELECT lists must have the **same number** of columns and **compatible data types**.
- **Duplicates:** 
  - `UNION ALL` **preserves** duplicates;  
  - `UNION` removes them (similar to `DISTINCT`), but typically costs a sort or similar operation.
- **When to use which**:
  - If you **must** remove duplicates, use `UNION`.  
  - Otherwise, `UNION ALL` is typically faster and simpler.  
- **Example**: Doing a `UNION` on `deptno` from both `EMP` and `DEPT`:
  ```sql
  SELECT deptno
    FROM emp
   UNION
  SELECT deptno
    FROM dept;
  ```
  returns only four distinct deptno values (10, 20, 30, 40).  
- If you see `UNION`, remember it’s akin to:
  ```sql
  SELECT DISTINCT deptno
    FROM (
      SELECT deptno FROM emp
      UNION ALL
      SELECT deptno FROM dept
    );
  ```
- General advice: **Don’t use `UNION`** (distinct) unless you need it—just like you wouldn’t add `DISTINCT` unnecessarily.

---

## **3.2 Combining Related Rows**

### **Problem**
- You want rows from multiple tables that share **common values**.  
- **Example**: Show the **name** of every employee in department 10, and the **location** of that department. The `ename` is in `EMP`, while `loc` is in `DEPT`.

### **Solution**
Perform an **equi-join** (inner join) on `deptno`:
```sql
SELECT e.ename, d.loc
  FROM emp e, dept d
 WHERE e.deptno = d.deptno
   AND e.deptno = 10;
```

### **Discussion**
- This is an **inner join** based on equality (`e.deptno = d.deptno`).  
- Conceptually, you get a **Cartesian product** of `emp × dept`, then the `WHERE` filter keeps only rows where `deptno` matches (and `e.deptno=10`).
- **Alternate ANSI JOIN syntax** (equivalent):
  ```sql
  SELECT e.ename, d.loc
    FROM emp e
         INNER JOIN dept d
           ON (e.deptno = d.deptno)
   WHERE e.deptno = 10;
  ```
- Both old-style (`FROM ... , ... WHERE ...`) and the newer `JOIN ... ON` approach are ANSI-compliant.

---

## **3.3 Finding Rows in Common Between Two Tables**

### **Problem**
- You want to find rows **common** to two tables, possibly matching on multiple columns.
- **Example**: A view `V` is created:

  ```sql
  CREATE VIEW V AS
  SELECT ename, job, sal
    FROM emp
   WHERE job = 'CLERK';
  SELECT * FROM V;

  ENAME   JOB      SAL
  ------  -------  -----
  SMITH   CLERK     800
  ADAMS   CLERK    1100
  JAMES   CLERK     950
  MILLER  CLERK    1300
  ```
- Only clerks appear in `V`, omitting `empno`, `deptno`, etc.
- You want to return all matching employees from `EMP` who appear in `V` (matching `ename, job, sal`), but also retrieve `EMP.empno` and `EMP.deptno`.

### **Solution**
1. **Join** on the relevant columns:
   - **MySQL / SQL Server** (and works on others too):
     ```sql
     SELECT e.empno, e.ename, e.job, e.sal, e.deptno
       FROM emp e, V
      WHERE e.ename = v.ename
        AND e.job   = v.job
        AND e.sal   = v.sal;
     ```
   - Or using ANSI JOIN:
     ```sql
     SELECT e.empno, e.ename, e.job, e.sal, e.deptno
       FROM emp e
            JOIN V
         ON (e.ename = v.ename
         AND e.job   = v.job
         AND e.sal   = v.sal);
     ```
2. **Set operation** `INTERSECT` (if you **only** need to confirm matching rows, and your DBMS supports it):
   - **DB2, Oracle, PostgreSQL** example:
     ```sql
     SELECT empno, ename, job, sal, deptno
       FROM emp
      WHERE (ename, job, sal) IN (
        SELECT ename, job, sal FROM emp
        INTERSECT
        SELECT ename, job, sal FROM V
      );
     ```

### **Discussion**
- When joining, choose **all necessary columns** to ensure correct matching.  
- **`INTERSECT`** returns rows present in both result sets, removing duplicates by default.  
- By default, `INTERSECT` does not show duplicates. 

---

## **3.4 Retrieving Values from One Table That Do Not Exist in Another**

### **Problem**
- Identify which rows in a **source** table are **absent** from a **target** table.  
- **Example**: Which `deptno` in `DEPT` have no corresponding row in `EMP`? If `deptno=40` is unused, you want `40`.

### **Solution**
- **Set difference** or a **subquery** approach:

**DB2, PostgreSQL, SQL Server**  
```sql
SELECT deptno
  FROM dept
EXCEPT
SELECT deptno
  FROM emp;
```
**Oracle**  
```sql
SELECT deptno
  FROM dept
MINUS
SELECT deptno
  FROM emp;
```
**MySQL** (lacks `EXCEPT` / `MINUS`):
```sql
SELECT deptno
  FROM dept
 WHERE deptno NOT IN (
   SELECT deptno
     FROM emp
 );
```

### **Discussion**
- **`EXCEPT`**/`MINUS`:  
  - Removes rows found in the second query from the first.  
  - Automatically filters duplicates.  
- **Using subqueries (`NOT IN`)**:  
  - Works but be mindful of **`NULL`** issues.  
- **Duplicate elimination**:  
  - The set difference approach eliminates duplicates.  
  - If using subqueries, you might use `DISTINCT` if `deptno` isn’t unique:
    ```sql
    SELECT DISTINCT deptno
      FROM dept
     WHERE deptno NOT IN (SELECT deptno FROM emp);
    ```
- **`NOT IN` and `NULL` pitfall**:  
  - If `NEW_DEPT` has `(10), (50), (NULL)`, a query like:
    ```sql
    SELECT *
      FROM dept
     WHERE deptno NOT IN (
       SELECT deptno
         FROM new_dept
     );
    ```
    can return **no rows** because the presence of `NULL` in the subquery effectively makes `NOT IN` fail.  
- **Truth tables** relevant to logic with `NULL`:

  **OR truth table**:
  ```
    OR |  T  |  F  |  N
    -------------------
    T  |  T  |  T  |  T
    F  |  T  |  F  |  N
    N  |  T  |  N  |  N
  ```

  **NOT truth table**:
  ```
    NOT
    ---
    T -> F
    F -> T
    N -> N
  ```

  **AND truth table**:
  ```
    AND |  T  |  F  |  N
    --------------------
    T   |  T  |  F  |  N
    F   |  F  |  F  |  F
    N   |  N  |  F  |  N
  ```
- **Example**:  
  - `deptno IN (10, 50, NULL)` is logically `(deptno=10 OR deptno=50 OR deptno=NULL)`.  
  - If `deptno`=20, then `(20=10 OR 20=50 OR 20=NULL)` → `(F OR F OR N)` → `(F OR N)` → `N` → not true.  
  - Similarly, for `NOT IN (10,50,NULL)`, you get no rows.  
- **Safer approach**: `NOT EXISTS` with a **correlated subquery**:
  ```sql
  SELECT d.deptno
    FROM dept d
   WHERE NOT EXISTS (
     SELECT 1
       FROM emp e
      WHERE d.deptno = e.deptno
   );
  ```
  This is unaffected by `NULL` values in the subquery table.

---

## **3.5 Retrieving Rows from One Table That Do Not Correspond to Rows in Another**

### **Problem**
- You have two tables with **common keys**, want to see which rows in one table have **no match** in the other, and retrieve columns from the first table.  
- **Example**: Which departments have no employees? (But also show `dname`, `loc` from `DEPT`).

### **Solution**
- **Outer join** all departments with possible employees, then keep those with no match:
  ```sql
  SELECT d.*
    FROM dept d
         LEFT OUTER JOIN emp e
           ON d.deptno = e.deptno
   WHERE e.deptno IS NULL;
  ```
- This yields departments that lack any corresponding employee row.

### **Discussion**
- This technique is sometimes called an **anti-join**: an outer join + a filter on `NULL` from the second table.  
- Contrasted with 3.4: you can return **additional columns** from `DEPT` easily (like `DNAME`, `LOC`).

---

## **3.6 Adding Joins to a Query Without Interfering with Other Joins**

### **Problem**
- Your existing query (e.g., joining `EMP` and `DEPT`) works fine, returning all employees.  
- You now want bonus info from `EMP_BONUS`, but if you do an **inner join** to `EMP_BONUS`, you lose employees who have no bonus.  
- **Example**:
  ```sql
  SELECT e.ename, d.loc
    FROM emp e, dept d
   WHERE e.deptno = d.deptno;
  ```
  returns all employees. But if you add `AND e.empno = eb.empno` with `emp_bonus eb`, you only get employees who have bonuses.

### **Solution**
1. **Outer Join** approach:
   ```sql
   SELECT e.ename, d.loc, eb.received
     FROM emp e
          JOIN dept d
            ON e.deptno = d.deptno
          LEFT JOIN emp_bonus eb
            ON e.empno = eb.empno
    ORDER BY 2; -- e.g. order by department location
   ```
   - Preserves all `EMP` rows, with `eb.received` possibly `NULL` if no bonus.
2. **Scalar Subquery**:
   ```sql
   SELECT e.ename, d.loc,
          (SELECT eb.received
             FROM emp_bonus eb
            WHERE eb.empno = e.empno
          ) AS received
     FROM emp e, dept d
    WHERE e.deptno = d.deptno
    ORDER BY 2;
   ```
   - Leaves the original joins intact, just adds a single subquery column for the bonus date.

### **Discussion**
- **Left Outer Join** ensures employees without a bonus remain.  
- **Scalar subquery** is convenient when you just need one column from a third table without rewriting the main join logic.  
- Make sure the scalar subquery returns **at most one row** per outer query row, or you get an error.

---

## **3.7 Determining Whether Two Tables Have the Same Data**

### **Problem**
- You want to know if two tables/views are **identical** in both content and cardinalities (including duplicates).  
- **Example**: Table `EMP` vs. a view `V` that might have extra or duplicated rows. You want to see the differences (if any).

### **Solution**
- Use **set difference** (`MINUS`, `EXCEPT`) + `UNION ALL`, or correlated subqueries:
  - Compare `V` minus `EMP`, then `EMP` minus `V`, and union the results. If nothing appears, they match exactly.

**DB2 and PostgreSQL** (using `EXCEPT`):  
```sql
(
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM V
   GROUP BY empno, ename, job, mgr, hiredate, sal, comm, deptno
  EXCEPT
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM emp
   GROUP BY empno, ename, job, mgr, hiredate, sal, comm, deptno
)
UNION ALL
(
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM emp
   GROUP BY empno, ename, job, mgr, hiredate, sal, comm, deptno
  EXCEPT
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM V
   GROUP BY empno, ename, job, mgr, hiredate, sal, comm, deptno
);
```

**Oracle** (using `MINUS` is analogous):
```sql
(
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM V
   GROUP BY ...
  MINUS
  SELECT empno, ename, job, mgr, hiredate, sal, comm, deptno,
         COUNT(*) AS cnt
    FROM emp
   GROUP BY ...
)
UNION ALL
(
  SELECT ...
  MINUS
  SELECT ...
);
```

**MySQL and SQL Server** (correlated subqueries, then `UNION ALL`):
```sql
SELECT *
  FROM (
    SELECT e.empno, e.ename, e.job, e.mgr, e.hiredate,
           e.sal, e.comm, e.deptno, COUNT(*) AS cnt
      FROM emp e
     GROUP BY ...
  ) e
 WHERE NOT EXISTS (
   SELECT NULL
     FROM (
       SELECT v.empno, v.ename, v.job, v.mgr, v.hiredate,
              v.sal, v.comm, v.deptno, COUNT(*) AS cnt
         FROM v
        GROUP BY ...
     ) v
    WHERE v.empno = e.empno
      AND ...
      AND COALESCE(v.comm,0) = COALESCE(e.comm,0)
 )
UNION ALL
SELECT *
  FROM (
    SELECT v.empno, v.ename, v.job, v.mgr, v.hiredate,
           v.sal, v.comm, v.deptno, COUNT(*) AS cnt
      FROM v
     GROUP BY ...
  ) v
 WHERE NOT EXISTS (
   SELECT NULL
     FROM (
       SELECT e.empno, ...
         FROM emp e
        GROUP BY ...
     ) e
    WHERE v.empno = e.empno
      AND ...
      AND COALESCE(v.comm,0) = COALESCE(e.comm,0)
 );
```

### **Discussion**
- The idea is: 
  1. Show rows in `V` not in `EMP` (or that differ in duplicates count).  
  2. Show rows in `EMP` not in `V`.  
  3. Combine them.  
- If nothing is returned, data sets are equal. If they differ, the differences appear.  
- Using `COUNT(*)` in each group accounts for duplicates.  
- A quick “cardinality only” check:  
  ```sql
  SELECT COUNT(*) FROM emp
   UNION
  SELECT COUNT(*) FROM dept;
  ```
  - If only one row is returned, both have the same count. If you see two rows, the counts differ.

---

## **3.8 Identifying and Avoiding Cartesian Products**

### **Problem**
- A query accidentally returns a Cartesian product (multiplying row counts) because a join condition is missing or incomplete.
- **Example**:
  ```sql
  SELECT e.ename, d.loc
    FROM emp e, dept d
   WHERE e.deptno = 10;
  ```
  returns 12 rows if `deptno=10` applies to 3 employees and `dept` has 4 rows, since 3×4=12.

### **Solution**
- **Add the join condition** relating `emp` to `dept`:
  ```sql
  SELECT e.ename, d.loc
    FROM emp e, dept d
   WHERE e.deptno = 10
     AND d.deptno = e.deptno;
  ```
- Now you get just 3 rows (for employees CLARK, KING, MILLER in dept 10).

### **Discussion**
- A Cartesian product is the product of row counts from each table: M×N.  
- The **n–1 rule** says that with n tables in the `FROM` clause, you generally need at least n–1 join conditions to avoid an unintentional Cartesian product (unless it’s intentional).  
- **Valid uses** of Cartesian products:
  - Generating sequences.  
  - Pivoting/unpivoting data.  
  - Mimicking loops (also possible via recursive CTE).

---

## **3.9 Performing Joins When Using Aggregates**

### **Problem**
- You need an aggregate (e.g., `SUM`) across multiple tables, but a join can create **duplicate rows** of certain columns.  
- **Example**: Summing all salaries in dept 10 plus summing total bonuses. Each bonus row for an employee causes their salary row to repeat.

### **Solution**
1. **Use `DISTINCT` in the aggregate** for the duplicated column:
   ```sql
   SELECT deptno,
          SUM(DISTINCT sal) AS total_sal,
          SUM(bonus)       AS total_bonus
     FROM (
       SELECT e.empno, e.ename, e.sal, e.deptno,
              e.sal * CASE 
                         WHEN eb.type = 1 THEN 0.1
                         WHEN eb.type = 2 THEN 0.2
                         ELSE 0.3
                      END AS bonus
         FROM emp e, emp_bonus eb
        WHERE e.empno  = eb.empno
          AND e.deptno = 10
     ) x
    GROUP BY deptno;
   ```
2. **Pre-aggregate** in an inline view or subquery, then join.  
3. **Window functions** (`SUM(...) OVER (...)`) in DB2/Oracle/SQL Server can also solve duplication issues.

### **Discussion**
- If an employee has multiple bonus entries, the join repeats that employee’s salary row. Without `DISTINCT`, the `SUM(sal)` is inflated.  
- Summing `DISTINCT sal` ensures each salary is only counted once.  
- Alternatively, compute sum of salaries first (one row per dept) and store that in a subquery or inline view, then join it to the bonus table.

---

## **3.10 Performing Outer Joins When Using Aggregates**

### **Problem**
- Similar to 3.9, but **not all** employees have bonuses. If you do an **inner** join, employees with no bonus are completely lost from the sum of salaries.  
- **Example**: Summing salaries for dept 10 plus the sum of bonuses for that same dept, but only one employee actually has a bonus row.

### **Solution**
- **Left outer join** to keep all employees in dept 10, substituting zero bonus where `NULL`:
  ```sql
  SELECT deptno,
         SUM(DISTINCT sal) AS total_sal,
         SUM(bonus)        AS total_bonus
    FROM (
      SELECT e.empno, e.ename, e.sal, e.deptno,
             e.sal * CASE 
                       WHEN eb.type IS NULL THEN 0
                       WHEN eb.type = 1     THEN 0.1
                       WHEN eb.type = 2     THEN 0.2
                       ELSE 0.3
                     END AS bonus
        FROM emp e LEFT OUTER JOIN emp_bonus eb
             ON (e.empno = eb.empno)
       WHERE e.deptno = 10
    ) x
   GROUP BY deptno;
  ```
- If an employee has **no** bonus row, `eb.type` is `NULL`, so the `CASE` yields 0 for the bonus calculation.

### **Discussion**
- Outer join ensures employees with no matching row in `emp_bonus` do not disappear from the result.  
- Variation: Pre-summarize salaries for dept 10 in one subquery, then join to `emp_bonus`.

---

## **3.11 Returning Missing Data from Multiple Tables**

### **Problem**
- You want to show data from two tables, including rows that don’t match in *either* table:
  - Example: Departments with no employees, **and** employees with no department.  
  - A left outer join only covers “departments with no employees.” A right outer join only covers “employees with no dept.” You want *both* simultaneously.

### **Solution**
- **Full outer join** (if supported), or **union** of left/right outer joins.

**DB2, PostgreSQL, SQL Server**  
```sql
SELECT d.deptno, d.dname, e.ename
  FROM dept d
       FULL OUTER JOIN emp e
         ON (d.deptno = e.deptno);
```
**MySQL** (no `FULL OUTER JOIN`):
```sql
SELECT d.deptno, d.dname, e.ename
  FROM dept d RIGHT OUTER JOIN emp e
    ON (d.deptno = e.deptno)
UNION
SELECT d.deptno, d.dname, e.ename
  FROM dept d LEFT OUTER JOIN emp e
    ON (d.deptno = e.deptno);
```
**Oracle**: union two queries using `(+)` syntax as well.

### **Discussion**
- A **full outer join** is effectively the union of a left outer join and a right outer join on the same condition.  
- If your DBMS lacks `FULL OUTER JOIN`, replicate it by unioning both directions.

---

## **3.12 Using NULLs in Operations and Comparisons**

### **Problem**
- `NULL` is neither equal nor not equal to anything—not even itself. You want to treat `NULL` values in a numeric/character column as if they’re real values for comparison.  
- **Example**: Find employees whose `comm` is less than WARD’s commission, counting `NULL` as 0 so they also appear.

### **Solution**
- Apply a function like **`COALESCE`** to translate `NULL` into a real value:
  ```sql
  SELECT ename, comm
    FROM emp
   WHERE COALESCE(comm, 0) < (
     SELECT comm
       FROM emp
      WHERE ename = 'WARD'
   );
  ```

### **Discussion**
- **`COALESCE(x, y)`** returns `x` if `x` is not `NULL`, otherwise `y`.  
- So if an employee’s `comm` is `NULL`, it becomes 0.  
- This comparison includes employees with `NULL` comm in the result if WARD’s comm is higher than 0.  
- Alternative: `CASE WHEN comm IS NULL THEN 0 ELSE comm END`, but `COALESCE` is more concise.

---

## **3.13 Summing Up**

- **Joins** are crucial for combining data across tables. You typically join on matching columns (primary key ↔ foreign key, or any shared column).
  - **Inner Joins** return only matching rows.  
  - **Outer Joins** return all rows from one (or both) tables plus the matches from the other.  
  - **Full Outer Join** covers missing rows on both sides.  
- **Set Operations** let you:
  - **UNION** or **UNION ALL** row sets.  
  - **INTERSECT** to find rows common to both sets.  
  - **EXCEPT**/**MINUS** to find rows in one set but not in another.  
- **Avoiding Cartesian Products**: Always specify the necessary join condition(s). Use the n–1 rule as a guide.  
- **Aggregates with Joins**: Watch out for duplicated rows causing inflated sums. Use `DISTINCT` or pre-aggregate logic to correct it.  
- **Handling `NULL`**:
  - `NOT IN (subquery)` can fail if the subquery returns `NULL`. Prefer `NOT EXISTS`.  
  - For numeric comparisons involving `NULL`, use `COALESCE`.  
- By mastering joins (inner, outer, full) and set operations, you’ll be prepared for more advanced queries and data manipulation tasks in later chapters.
