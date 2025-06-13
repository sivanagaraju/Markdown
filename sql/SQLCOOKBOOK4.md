Below is a **comprehensive, section-by-section** rewrite of **Chapter 4: Inserting, Updating, and Deleting**, capturing **all key details and examples** without omitting information. The content is presented in **summary form** (not verbatim), but includes **every important concept, solution, and discussion point** mentioned in the original text.

---

## **Chapter 4: Inserting, Updating, and Deleting**

### **Overview**
- Previous chapters covered **querying data** (i.e., `SELECT`).
- This chapter covers **writing** operations:
  1. **Inserting** new rows into tables
  2. **Updating** existing rows in tables
  3. **Deleting** rows you no longer want
- Recipes are grouped by topic:
  - **Insertion recipes** (4.1–4.7)
  - **Update recipes** (4.8–4.11)
  - **Deletion recipes** (4.12–4.17)
- Highlights:
  - You can insert a single row or **sets** of rows at a time.
  - You can update rows individually or entire sets in sophisticated ways.
  - You can delete single rows or sets of rows, including rows in one table that depend on conditions in another table.
  - **`MERGE`** (Recipe 4.11) can handle insert, update, and delete logic all in one statement, which is useful for synchronizing data from external sources.

---

## **4.1 Inserting a New Record**

### **Problem**
- Insert a **single row** into a table.
- Example: Insert `(deptno=50, dname='PROGRAMMING', loc='BALTIMORE')` into `DEPT`.

### **Solution**
- Use an `INSERT ... VALUES` statement:
  ```sql
  INSERT INTO dept (deptno, dname, loc)
       VALUES (50, 'PROGRAMMING', 'BALTIMORE');
  ```
- **DB2, SQL Server, PostgreSQL, MySQL** support inserting multiple rows at once:
  ```sql
  INSERT INTO dept (deptno, dname, loc)
       VALUES (1, 'A', 'B'),
              (2, 'B', 'C');
  ```

### **Discussion**
- The **basic syntax** for inserting one row is consistent across RDBMSs.
- You can **omit the column list** if you provide **all columns** in order:
  ```sql
  INSERT INTO dept
       VALUES (50, 'PROGRAMMING', 'BALTIMORE');
  ```
- Be mindful of column constraints (e.g., `NOT NULL`) and column order.  
- If you do not insert a value for each column, any omitted columns might become `NULL` or take a default if defined.

---

## **4.2 Inserting Default Values**

### **Problem**
- A table has columns with **default** definitions. You want to explicitly insert rows that rely on these defaults.
- Example: Table `D (id INTEGER DEFAULT 0)`. Insert a row so that `id` is set to `0` (the default) **without** typing `0`.

### **Solution**
- **All vendors** let you use the `DEFAULT` keyword:
  ```sql
  INSERT INTO D
       VALUES (DEFAULT);
  ```
  Or explicitly list columns:
  ```sql
  INSERT INTO D (id)
       VALUES (DEFAULT);
  ```
- **Oracle 8i or earlier**: Does **not** support `DEFAULT` keyword explicitly.
- **MySQL**: If all columns have defaults, you can use **empty values list**:
  ```sql
  INSERT INTO D
       VALUES ();
  ```
- **PostgreSQL, SQL Server**: Support **`DEFAULT VALUES`** syntax:
  ```sql
  INSERT INTO D
       DEFAULT VALUES;
  ```

### **Discussion**
- `DEFAULT` in the values list inserts the default defined on the column (e.g., `id=0`).
- If **all** columns in the table have defaults, MySQL’s empty `VALUES ()` or PostgreSQL/SQL Server’s `DEFAULT VALUES` can be used to create an entire row of defaults.
- For tables with a mix of default and nondefault columns, you can simply **exclude** the column from the insert if you want the column’s default to be used.

---

## **4.3 Overriding a Default Value with NULL**

### **Problem**
- A column has a default, but you want to explicitly insert `NULL` instead.
- Example: Table `D (id INTEGER DEFAULT 0, foo VARCHAR(10))`. You want to insert `(id=NULL, foo='Brighten')`.

### **Solution**
- **Specify `NULL`** directly:
  ```sql
  INSERT INTO d (id, foo)
       VALUES (NULL, 'Brighten');
  ```

### **Discussion**
- If you omit `id` entirely, `id` becomes `0` (the default).  
- Specifying `NULL` in the `VALUES` list forcibly overrides the default (assuming the column allows `NULL`).  
- This is crucial for columns with defaults if you specifically need them to be `NULL`.

---

## **4.4 Copying Rows from One Table into Another**

### **Problem**
- You want to insert rows from a **source table** (or query) into a **destination table**.
- Example: Insert rows from `DEPT` into `DEPT_EAST` for only certain `loc` values.

### **Solution**
- `INSERT` + `SELECT`:
  ```sql
  INSERT INTO dept_east (deptno, dname, loc)
       SELECT deptno, dname, loc
         FROM dept
        WHERE loc IN ('NEW YORK','BOSTON');
  ```

### **Discussion**
- **`INSERT ... SELECT`** is the standard approach to copy data.  
- You can filter or transform rows in the `SELECT`.  
- If you omit the target column list, you must insert into **all** columns in the same order they appear in the `SELECT`.

---

## **4.5 Copying a Table Definition**

### **Problem**
- Create a new empty table that has the **same columns** (structure) as an existing table, **without** copying the data.

### **Solution (By RDBMS)**

- **DB2**:  
  ```sql
  CREATE TABLE dept_2
        LIKE dept;
  ```
- **Oracle, MySQL, PostgreSQL**:
  ```sql
  CREATE TABLE dept_2
  AS
  SELECT *
    FROM dept
   WHERE 1 = 0;
  ```
- **SQL Server**:
  ```sql
  SELECT *
    INTO dept_2
    FROM dept
   WHERE 1 = 0;
  ```

### **Discussion**
- DB2 has a dedicated `LIKE` clause for copying structure.  
- Oracle/MySQL/PostgreSQL use **Create Table As Select** (`CTAS`), with `WHERE 1=0` to produce zero rows, thus an **empty** table with the same column definitions.  
- SQL Server uses `SELECT ... INTO`, also restricted to zero rows by `WHERE 1=0`.

---

## **4.6 Inserting into Multiple Tables at Once**

### **Problem**
- You want to run **one statement** that inserts rows returned by a query into **different target tables** based on row conditions.
- Example: From `DEPT`, if `loc` in `('NEW YORK','BOSTON')`, insert into `DEPT_EAST`; if `CHICAGO`, insert into `DEPT_MID`; else insert into `DEPT_WEST`.

### **Solution**

- **Oracle**: `INSERT ALL` or `INSERT FIRST`:
  ```sql
  INSERT ALL
     WHEN loc IN ('NEW YORK','BOSTON') THEN
       INTO dept_east (deptno, dname, loc)
       VALUES (deptno, dname, loc)
     WHEN loc = 'CHICAGO' THEN
       INTO dept_mid (deptno, dname, loc)
       VALUES (deptno, dname, loc)
     ELSE
       INTO dept_west (deptno, dname, loc)
       VALUES (deptno, dname, loc)
  SELECT deptno, dname, loc
    FROM dept;
  ```
  - **INSERT ALL**: All matching conditions can apply, possibly inserting a single source row into multiple target tables.  
  - **INSERT FIRST**: Stops evaluating further conditions once one is true.

- **DB2**: A workaround using constraints plus a UNION ALL “view”:
  1. Create each table (e.g., `dept_east`) with a `CHECK` constraint limiting permissible `loc` values.
  2. Insert into a **union** of these tables:
     ```sql
     INSERT INTO (
       SELECT * FROM dept_west
       UNION ALL
       SELECT * FROM dept_east
       UNION ALL
       SELECT * FROM dept_mid
     )
     SELECT * FROM dept;
     ```
  3. DB2’s check constraints route each row to the correct table if the row’s `loc` meets that table’s constraint.

- **MySQL, PostgreSQL, SQL Server**: No native multi-table insert in one statement. Must insert multiple times or write app logic.

### **Discussion**
- **Oracle** approach is straightforward: you can conditionally direct rows to multiple tables in a single insert.
- **DB2** approach is more indirect, reliant on constraints to filter rows into the correct base table.  
- Other systems lack direct multi-table insert syntax at time of writing.

---

## **4.7 Blocking Inserts to Certain Columns**

### **Problem**
- You want to **deny** the ability to insert values into some columns, while still allowing inserts into others.  
- Example: Only `(empno, ename, job)` can be inserted, not the rest of `EMP`’s columns.

### **Solution**
- **Create a view** that exposes only `(empno, ename, job)` from `EMP`:
  ```sql
  CREATE VIEW new_emps AS
  SELECT empno, ename, job
    FROM emp;
  ```
- Grant the application/user insert privileges on `new_emps`, **not** on `EMP`.
- When they insert into `new_emps`, the DB translates it to an insert on those three columns in `EMP`.

### **Discussion**
- Inserting into a **simple** (updatable) view is typically allowed if the DB can map columns back to a single base table.  
- You can also do an inline view insert (Oracle-specific syntax) but it’s less common.  
- More complex views (joins, groups) might not be updatable in the same way.

---

## **4.8 Modifying Records in a Table**

### **Problem**
- You want to **update** values in one or more rows.
- Example: Increase everyone’s `sal` in `deptno=20` by 10%.

### **Solution**
```sql
UPDATE emp
   SET sal = sal * 1.10
 WHERE deptno = 20;
```

### **Discussion**
- `UPDATE ... SET ... WHERE ...` changes existing rows.  
- If no `WHERE`, **all** rows are updated.  
- Pre-check with a `SELECT` showing `sal * 1.10` to confirm the updated values are correct before issuing the actual `UPDATE`.

---

## **4.9 Updating When Corresponding Rows Exist**

### **Problem**
- Update rows in a table **only** if they have a matching row in another table.
- Example: If an employee is in `EMP_BONUS`, increase that employee’s salary by 20%.

### **Solution**
- Use a subquery:
  ```sql
  UPDATE emp
     SET sal = sal * 1.20
   WHERE empno IN (SELECT empno
                     FROM emp_bonus);
  ```
- Or use `EXISTS` with a correlated condition:
  ```sql
  UPDATE emp
     SET sal = sal * 1.20
   WHERE EXISTS (
     SELECT 1
       FROM emp_bonus
      WHERE emp_bonus.empno = emp.empno
   );
  ```

### **Discussion**
- The `IN` variant: returns all `empno` from `emp_bonus`; any matching `emp.empno` is updated.  
- The `EXISTS` variant: for each `emp` row, checks if a matching `emp_bonus` row exists.  
- Specifying `SELECT NULL` or `SELECT 1` in `EXISTS` subqueries is typical; the actual selected value is irrelevant.

---

## **4.10 Updating with Values from Another Table**

### **Problem**
- You want to update certain columns in one table based on values from a matching row in another table.
- Example: A table `NEW_SAL(deptno, sal)` contains new salary data by department. You want to update `emp.sal` to `NEW_SAL.sal`, and set `emp.comm` to `(new_sal.sal / 2)` for employees who match on `deptno`.

### **Solution (By RDBMS)**

1. **DB2** (correlated subqueries in both `SET` and `WHERE`):
   ```sql
   UPDATE emp e
      SET (e.sal, e.comm) = (
        SELECT ns.sal, ns.sal/2
          FROM new_sal ns
         WHERE ns.deptno = e.deptno
      )
    WHERE EXISTS (
      SELECT 1
        FROM new_sal ns
       WHERE ns.deptno = e.deptno
    );
   ```

2. **MySQL** (multi-table update syntax):
   ```sql
   UPDATE emp e, new_sal ns
      SET e.sal  = ns.sal,
          e.comm = ns.sal / 2
    WHERE e.deptno = ns.deptno;
   ```

3. **Oracle** (either a correlated subquery approach or an inline view update):
   ```sql
   UPDATE (
     SELECT e.sal AS emp_sal, e.comm AS emp_comm,
            ns.sal AS ns_sal, ns.sal/2 AS ns_comm
       FROM emp e, new_sal ns
      WHERE e.deptno = ns.deptno
   )
   SET emp_sal = ns_sal,
       emp_comm = ns_comm;
   ```

4. **PostgreSQL** (JOIN in the `UPDATE`):
   ```sql
   UPDATE emp
      SET sal  = ns.sal,
          comm = ns.sal / 2
     FROM new_sal ns
    WHERE ns.deptno = emp.deptno;
   ```

5. **SQL Server** (similar to PostgreSQL):
   ```sql
   UPDATE e
      SET e.sal  = ns.sal,
          e.comm = ns.sal / 2
     FROM emp e, new_sal ns
    WHERE ns.deptno = e.deptno;
   ```

### **Discussion**
- Using subqueries or join-based syntax ensures rows are matched properly.
- If you fail to restrict rows (e.g., no `WHERE` for employees not in `NEW_SAL`), some employees could get `NULL`.
- Oracle’s inline view approach can only work if the updated table is “key-preserved.”

---

## **4.11 Merging Records**

### **Problem**
- You want to **insert, update, or delete** rows in one table based on rows in another table, all in **one** statement:
  - If a row already exists, **update** it.
  - If it does not exist, **insert** it.
  - Optionally, after updating, conditionally **delete** it if certain criteria are met.
- Example: `EMP_COMMISSION` is to be synchronized with `EMP`:
  1. If `EMP_COMMISSION` row matches `EMP` row on `empno`, set `comm=1000`.
  2. If after that update the employee’s `sal` is `<2000`, delete that row from `EMP_COMMISSION`.
  3. If no match, insert `(empno, ename, deptno, comm)` from `EMP`.

### **Solution**
- Use **`MERGE`** (not supported in MySQL, but supported by most others):
  ```sql
  MERGE INTO emp_commission ec
  USING (SELECT * FROM emp) emp
     ON (ec.empno = emp.empno)
  WHEN MATCHED THEN
       UPDATE SET ec.comm = 1000
       DELETE WHERE (sal < 2000)
  WHEN NOT MATCHED THEN
       INSERT (ec.empno, ec.ename, ec.deptno, ec.comm)
       VALUES (emp.empno, emp.ename, emp.deptno, emp.comm);
  ```

### **Discussion**
- `ON (ec.empno = emp.empno)` determines if rows are “matched.”
- **`WHEN MATCHED`** clause updates the existing row in `EMP_COMMISSION`. Then, if the updated row fails a condition, you can do a “conditional delete.”
- **`WHEN NOT MATCHED`** inserts new rows.  
- `MERGE` is ideal for upsert logic (update or insert) and can also handle conditional deletions.

---

## **4.12 Deleting All Records from a Table**

### **Problem**
- You want to remove **every row** from a table, making it empty.

### **Solution**
- **Use `DELETE`** without a `WHERE`:
  ```sql
  DELETE FROM emp;
  ```
- Or some databases have **`TRUNCATE TABLE`** for faster, possibly irreversible deletion.

### **Discussion**
- `DELETE FROM table` removes rows one by one (fully logged).  
- `TRUNCATE` is often more efficient but can’t typically be undone or rolled back.  
- Check your DB’s docs for differences in performance, rollback, constraints, etc.

---

## **4.13 Deleting Specific Records**

### **Problem**
- You want to remove only rows matching a specific criterion.
- Example: Remove employees in `deptno=10`.

### **Solution**
- `DELETE` with a `WHERE` clause:
  ```sql
  DELETE FROM emp
   WHERE deptno = 10;
  ```

### **Discussion**
- Any condition in the `WHERE` restricts which rows to delete.
- If you skip `WHERE`, you’ll delete **all** rows.  
- Always verify your logic so you don’t delete unintended rows.

---

## **4.14 Deleting a Single Record**

### **Problem**
- You want to remove **exactly one** row, often identified by its unique or primary key.
- Example: Delete employee `(empno=7782)`.

### **Solution**
- A narrower version of 4.13:
  ```sql
  DELETE FROM emp
   WHERE empno = 7782;
  ```

### **Discussion**
- Using the **primary key** ensures you remove only that row.
- Without a unique key in the condition, you risk removing multiple rows.

---

## **4.15 Deleting Referential Integrity Violations**

### **Problem**
- Some rows in a table reference nonexistent rows in another table; these are “invalid references.” You want to delete them.
- Example: `EMP.deptno` references `DEPT.deptno`, but some `EMP` rows have invalid deptno. You want to remove those employees whose `deptno` is not found in `DEPT`.

### **Solution**
- Use `NOT EXISTS` or `NOT IN`:
  ```sql
  DELETE FROM emp
   WHERE NOT EXISTS (
     SELECT *
       FROM dept
      WHERE dept.deptno = emp.deptno
   );
  ```
  or
  ```sql
  DELETE FROM emp
   WHERE deptno NOT IN (
     SELECT deptno FROM dept
   );
  ```

### **Discussion**
- Deletion is controlled by the `WHERE` clause logic.  
- `NOT EXISTS` uses a correlated check to see if a matching `deptno` exists.  
- `NOT IN` approach can fail or produce unexpected results if subquery returns `NULL`. So `NOT EXISTS` is often safer.

---

## **4.16 Deleting Duplicate Records**

### **Problem**
- A table has multiple “duplicate” rows for some column(s). You want to keep exactly **one** row per set of duplicates and remove the extras.
- Example: Table `dupes`, with duplicates determined by matching `NAME`. The `ID` column is distinct. You want to keep the row with the smallest `ID` for each `NAME` and delete all others.

### **Solution**
- Use a subquery that picks the `MIN(id)` per `name`, then delete rows that are not in that set:
  ```sql
  DELETE FROM dupes
   WHERE id NOT IN (
     SELECT MIN(id)
       FROM dupes
      GROUP BY name
   );
  ```
- **MySQL**: You must nest the subquery so the same table can be referenced in a `DELETE`. For instance:
  ```sql
  DELETE FROM dupes
   WHERE id NOT IN (
     SELECT min_id
       FROM (
         SELECT MIN(id) AS min_id
           FROM dupes
          GROUP BY name
       ) tmp
   );
  ```

### **Discussion**
- **Define** your notion of “duplicate” (e.g., same `NAME`).  
- Use an aggregate like `MIN(id)` (or `MAX(id)`) to identify the “keeper” row.  
- The main `DELETE` removes any row whose `id` is not in that set of keepers.  
- Double-check your grouping logic to ensure you only retain the row you want.

---

## **4.17 Deleting Records Referenced from Another Table**

### **Problem**
- You have a table whose rows are “flagged” by some condition in another table, and you want to remove them.
- Example: A table `dept_accidents` logs each accident for each dept. You want to delete employees in departments that have ≥3 accidents.

### **Solution**
1. Identify which departments have at least 3 accidents:
   ```sql
   SELECT deptno
     FROM dept_accidents
    GROUP BY deptno
    HAVING COUNT(*) >= 3;
   ```
2. Delete employees in those departments:
   ```sql
   DELETE FROM emp
    WHERE deptno IN (
      SELECT deptno
        FROM dept_accidents
       GROUP BY deptno
      HAVING COUNT(*) >= 3
    );
   ```

### **Discussion**
- The subquery groups accidents by `deptno` and uses `HAVING COUNT(*) >= 3` to find departments.  
- Those deptno values are used in `WHERE deptno IN (...)` to delete employees in those high-accident departments.

---

## **4.18 Summing Up**

### **Key Points and Best Practices**
1. **INSERT**  
   - Insert single or multiple rows at once (where supported).  
   - `DEFAULT` or `DEFAULT VALUES` can simplify use of default column values.  
   - `INSERT ... SELECT` copies data from one table to another.  
   - Some RDBMSs (Oracle) support multi-table insert in one statement (`INSERT ALL/INSERT FIRST`).

2. **UPDATE**  
   - Update specific rows with `WHERE`.  
   - Update all rows (caution) by omitting `WHERE`.  
   - Use subqueries or join-based syntax to update with values from another table.  
   - `MERGE` can conditionally update, insert, or even delete in one go, especially helpful for “upsert” logic.

3. **DELETE**  
   - `DELETE` with no `WHERE` removes every row.  
   - Use `WHERE` to delete only matching rows (e.g., a single row by primary key).  
   - You can correlate deletes with conditions in other tables (`IN`, `EXISTS`, `NOT EXISTS`).  
   - Deleting duplicates often involves an aggregate subquery that identifies which row(s) to keep.

4. **Caution**  
   - Always verify `WHERE` conditions before large-scale updates or deletes. A stray or missing condition can cause major data loss or unwanted changes.  
   - Some statements (e.g., `TRUNCATE`) might not be rollback-able.  
   - Key columns or constraints (like a primary key) are crucial to controlling which rows are updated or deleted.

By mastering **insertion**, **updating**, and **deletion** techniques, you can maintain and manipulate database data effectively. While queries (`SELECT`) are more frequent in daily work, these data modification commands are **critical** for keeping your database accurate and up to date.