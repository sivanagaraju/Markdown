Below is a comprehensive extraction of **all key points** from **Chapter 2: Sorting Query Results**. This summary covers each sub-section, ensuring that no important detail is omitted.

---

## **Chapter 2: Sorting Query Results**

**Overview**  
- Focuses on customizing the organization of query results.  
- Mastery of the `ORDER BY` clause and other sorting techniques is essential for producing readable and meaningful output.

---

### **2.1 Returning Query Results in a Specified Order**

- **Problem:** Display the names, jobs, and salaries of employees in department 10, sorted by salary (lowest to highest).
- **Solution:** Use the `ORDER BY` clause to sort rows:
  ```sql
  SELECT ename, job, sal
    FROM emp
   WHERE deptno = 10
   ORDER BY sal ASC;
  ```
  - `ASC` sorts in ascending order (this is default).
  - To sort in descending order, use `DESC`:
    ```sql
    SELECT ename, job, sal
      FROM emp
     WHERE deptno = 10
     ORDER BY sal DESC;
    ```
- **Discussion:**
  - You can sort on **column names** or **column positions**:
    ```sql
    -- Column position example (3 corresponds to 'sal'):
    SELECT ename, job, sal
      FROM emp
     WHERE deptno = 10
     ORDER BY 3 DESC;
    ```
  - Sorting **by position** uses the **ordinal** of the columns in the `SELECT` list (starting at 1).

---

### **2.2 Sorting by Multiple Fields**

- **Problem:** Sort rows from `emp` first by `deptno` (ascending), then by `sal` (descending).
- **Desired Result:**  
  ```
  EMPNO  DEPTNO  SAL   ENAME   JOB
  -----  ------  ----  ------  ---------
  ...    10      5000  KING    PRESIDENT
  ...    10      2450  CLARK   MANAGER
  ...    10      1300  MILLER  CLERK
  ...    20      3000  SCOTT   ANALYST
  ...    20      3000  FORD    ANALYST
  ...    20      2975  JONES   MANAGER
  ...
  (etc.)
  ```
- **Solution:** List sort columns, separated by commas, specifying ascending or descending:
  ```sql
  SELECT empno, deptno, sal, ename, job
    FROM emp
   ORDER BY deptno, sal DESC;
  ```
- **Discussion:**
  - The **order of columns** in `ORDER BY` determines **primary sort first**, then **secondary sort**, and so on.
  - If using **numeric positions** in `ORDER BY`, the position number must be ≤ the number of columns in the `SELECT` list.
  - You can often order by a column **not in the SELECT list** if you specify its name (though some restrictions apply with `GROUP BY` or `DISTINCT`).

---

### **2.3 Sorting by Substrings**

- **Problem:** Sort the query results by **specific parts of a string**. For example, sort by the **last two characters** of the `job` column from the `emp` table.
- **Solution:** Use the substring function of your DBMS in the `ORDER BY` clause.

  **DB2, MySQL, Oracle, PostgreSQL**  
  ```sql
  SELECT ename, job
    FROM emp
   ORDER BY SUBSTR(job, LENGTH(job) - 1);
  ```
  
  **SQL Server**  
  ```sql
  SELECT ename, job
    FROM emp
   ORDER BY SUBSTRING(job, LEN(job) - 1, 2);
  ```

- **Discussion:**
  - **SUBSTR** (or **SUBSTRING**) can target any slice of a string.  
  - **SQL Server’s SUBSTRING** syntax requires three parameters: `(string, start_position, length)`.
  - To get the **last two characters**, start at `length(job) - 1` and extract 2 characters.

---

### **2.4 Sorting Mixed Alphanumeric Data**

- **Problem:** You have mixed alphanumeric data (e.g., `ENAME DEPTNO` combined into a single string) and you want to sort by either the **numeric** portion or the **text** portion.
- **Example View**:
  ```sql
  CREATE VIEW V AS
  SELECT ename || ' ' || deptno AS data
    FROM emp;
  ```
  **Sample Data:**  
  ```
  SMITH 20
  ALLEN 30
  WARD 30
  ...
  ```
- **Goal:** Sort by `deptno` *or* by `ename` within that single string.
- **Solution (Oracle, SQL Server, PostgreSQL):** Use `TRANSLATE` and `REPLACE` to remove unwanted parts (digits or letters) and then `ORDER BY`.
  ```sql
  -- ORDER BY DEPTNO
  SELECT data
    FROM V
   ORDER BY REPLACE(
             data,
             REPLACE(
               TRANSLATE(data, '0123456789', '##########'), 
               '#', 
               ''
             ), 
             ''
           );
  
  -- ORDER BY ENAME
  SELECT data
    FROM V
   ORDER BY REPLACE(
             TRANSLATE(data, '0123456789', '##########'),
             '#',
             ''
           );
  ```
- **DB2 Variation:**  
  - Must **CAST** `deptno` to `CHAR` if creating a view.  
  - Parameters in `TRANSLATE` differ in order, but logic remains the same.
- **MySQL:**  
  - `TRANSLATE` is **not supported**, so there is **no direct solution** shown.
- **Discussion:**
  - `TRANSLATE` (where supported) maps characters you want to remove or replace.  
  - `REPLACE` then removes placeholder characters.  
  - This approach effectively extracts numbers or text, making sorting possible.

---

### **2.5 Dealing with Nulls When Sorting**

- **Problem:** Sort rows by a nullable column (e.g., `comm`) and control how `NULL` values appear:  
  - Sort them **last** or **first**.  
- **Default Approaches:**
  ```sql
  SELECT ename, sal, comm
    FROM emp
   ORDER BY comm;         -- Ascending, DB-dependent null order
  SELECT ename, sal, comm
    FROM emp
   ORDER BY comm DESC;    -- Descending, DB-dependent null order
  ```
- **Challenge:** By default, some DBMSs put nulls **first** in ascending order, while others put them **last**—and vice versa for descending order. You might need finer control.
- **CASE Expression Approach (DB2, MySQL, PostgreSQL, SQL Server):**
  1. Create a **flag** to distinguish null vs. non-null.
  2. Sort by the flag first, then by the real column.
  ```sql
  SELECT ename, sal, comm
    FROM (
      SELECT ename, sal, comm,
             CASE WHEN comm IS NULL THEN 0 ELSE 1 END AS is_null
        FROM emp
    ) x
   ORDER BY is_null DESC, comm;  -- Example: non-null comm ascending, nulls last
  ```
  - Adjust the sorting of `is_null` (DESC/ASC) and `comm` (DESC/ASC) to achieve the desired null positioning.
- **Oracle-Only Feature:** `NULLS FIRST` or `NULLS LAST` in the `ORDER BY` clause:
  ```sql
  -- Sort by comm ascending, nulls last:
  SELECT ename, sal, comm
    FROM emp
   ORDER BY comm NULLS LAST;
  
  -- Sort by comm descending, nulls first:
  SELECT ename, sal, comm
    FROM emp
   ORDER BY comm DESC NULLS FIRST;
  ```
- **Discussion:**
  - Most databases **do not** provide `NULLS FIRST` or `NULLS LAST` outside window functions.  
  - If your DBMS lacks direct syntax, use an auxiliary **CASE** column to control the order of nulls.

---

### **2.6 Sorting on a Data-Dependent Key**

- **Problem:** Conditionally choose **which column** to sort on, based on data content.  
  - Example: If `job = 'SALESMAN'`, sort by `comm`; otherwise, sort by `sal`.
- **Solution:** Use a `CASE` expression inside `ORDER BY`:
  ```sql
  SELECT ename, sal, job, comm
    FROM emp
   ORDER BY CASE
              WHEN job = 'SALESMAN'
                   THEN comm
              ELSE sal
            END;
  ```
- **Discussion:**
  - The `CASE` expression dynamically returns **one value** for the `ORDER BY` based on the row’s data.  
  - This allows a single result set to be sorted differently on a **row-by-row** basis.

---

### **2.7 Summing Up**

- Sorting query results is a **core skill** in SQL.  
- **ORDER BY** can be combined with:
  - **Column positions** (e.g., `ORDER BY 2 DESC`).
  - **CASE expressions** to handle **conditional sorting**.  
  - **Substring functions** to sort based on specific parts of a string.  
  - **Special functions/techniques** to handle **NULL** positioning.  
  - **TRANSLATE/REPLACE** (or **CASE** logic) to sort **mixed alphanumeric** data.
- Proper mastery of these techniques ensures **clear, precise, and correct** presentation of query results.

---

## **Key Takeaways**
1. **Ascending vs. Descending Order**: Specify `ASC` or `DESC` (with or without column positions).  
2. **Multi-Column Sorting**: Order of columns (or expressions) in the `ORDER BY` clause defines priority.  
3. **Substring Sorting**: Use `SUBSTR` (or `SUBSTRING`) to sort by parts of string fields.  
4. **Mixed Data Sorting**: Combine `TRANSLATE` and `REPLACE` to strip out characters (or digits) before sorting.  
5. **Handling NULLs**:
   - Use **CASE** to group nulls first or last if your DBMS doesn’t support `NULLS FIRST/LAST`.  
   - In Oracle, leverage `NULLS FIRST` / `NULLS LAST` directly.  
6. **Conditional Sorting**: A **CASE** in `ORDER BY` lets you switch columns or sort rules based on row content.

By employing these techniques, you can produce well-ordered data tailored to your exact requirements.