# Mindmap: Spark Dataframe and Dataset Transformations

Below is a **comprehensive** mindmap that captures **all details** from the transcripts on “Spark Dataframe and Dataset Transformations.” This includes **introductions**, **working with rows and columns**, **unit testing**, **handling unstructured data**, **UDF creation**, and various **miscellaneous transformations** (adding/dropping columns, case expressions, casting, duplicates, sorting). **No details are omitted**, and **code references** are included.

---

## 1. Introduction to Data Transformation

1. **Core Idea & Context**
   - In Spark: **Read** → **Transform** → **Write** is the essential pipeline for data engineering.
   - We’ve covered reading/writing data in earlier sections; now we focus on **transformation** techniques.
   - Transformations occur on:
     - **DataFrames** (programmatic, e.g. PySpark code).
     - **Spark SQL Tables** (via SQL statements).

2. **What Are Transformations?**
   - Combining DataFrames: **joins**, **unions**.
   - Aggregations: **groupBy**, **windowing**, **rollup**, **cube**, etc.
   - Column-level transformations: **filter**, **sort**, **split**, **sample**, **distinct**.
   - Using **built-in functions** or **UDFs** for custom logic.
   - **Case** / **when** expressions, referencing row/column, creating custom expressions.
   - In short, any manipulation that produces a new DataFrame from an existing one is a transformation.

3. **Approach**
   - We will move **bottom-up**: first learning to handle **rows** (especially if data is unstructured or for testing).
   - Then we tackle **column** manipulations (the more common scenario in structured or semi-structured data).
   - Finally, we look at **misc** transformations (like casting, removing duplicates, sorting, etc.).

---

## 2. Working with DataFrame Rows

1. **Row Object Basics**
   - A Spark DataFrame is effectively a distributed collection of **Row** objects.
   - Typically, transformations revolve around **columns** rather than entire rows.
   - However, there are **three** situations to handle `Row` objects directly:
     1. **Manually creating rows** to build small DataFrames (common in **unit testing** or demos).
     2. **Collecting** DataFrame rows to the driver (`.collect()`, `.take()`) for debugging or test assertions.
     3. Working with **unstructured data** where each row is just a string or raw object—requiring parsing at the row level.

2. **Scenario 1: Manually Creating Rows**
   - For quick or small data sets, especially in **unit tests**.
   - **Example** (Databricks or any Spark environment):
     ```python
     from pyspark.sql import Row

     row_list = [
       Row(id=1, name="Alice", eventDate="2023-01-10"),
       Row(id=2, name="Bob", eventDate="2023-01-11"),
       ...
     ]
     # Convert to RDD then to DataFrame, or directly createDataFrame:
     rdd = spark.sparkContext.parallelize(row_list, 2)
     df = spark.createDataFrame(rdd)
     df.show()
     ```
   - Alternatively, `spark.createDataFrame(list_of_tuples).toDF("col1", "col2", ...)` also works.

3. **Scenario 2: Collecting Rows to the Driver**
   - **`.collect()`** or **`.take(n)`** returns a Python list of `Row` objects.
   - Common in **unit testing** to do row-by-row assertion:
     ```python
     rows = df.collect()
     for row in rows:
         assert row["eventDate"] is not None
         # or row.eventDate
     ```

4. **Scenario 3: Unstructured Data**  
   - If a file is truly **unstructured** (like logs), reading with `spark.read.text(...)` yields a single column `"value"` containing raw strings.
   - You parse each row (often using **regex** or splitting) to produce structured columns.
   - Once columns exist, you can use normal transformations (groupBy, filter, etc.).

---

## 3. DataFrame Rows and Unit Testing

1. **Motivation**
   - For example, a function that transforms a string date into a Spark date (or any custom transformation).
   - You want to test correctness with a **manually created DataFrame** + collecting rows for assertion.

2. **Full Example**
   - **Notebook** was shown converting a string `'EventDate'` to an actual date in Spark.
   - Code in **Databricks** or local environment to create rows, build DataFrame, apply function, visually inspect.
   - Then we do the **same** in a **PyCharm** project or any environment, but convert that logic to **unit tests**:
     ```python
     import unittest
     from pyspark.sql import SparkSession
     from datetime import date

     def myDateFunction(df, colName):
         # transforms colName from string to date
         # return new df

     class MyTestCase(unittest.TestCase):
         @classmethod
         def setUpClass(cls):
             cls.spark = SparkSession.builder.getOrCreate()
             rows = [...]
             cls.test_df = cls.spark.createDataFrame(rows, ["EventDate"])  # or with schema

         def test_date_type(self):
             result = myDateFunction(self.test_df, "EventDate")
             row_list = result.collect()
             for row in row_list:
                 self.assertTrue(isinstance(row["EventDate"], date))
     ```
   - Use `collect()` to compare row by row.

---

## 4. DataFrame Rows and Unstructured Data

1. **Apache Log File Example**  
   - A typical web server log is basically lines of text → `spark.read.text("weblogs.txt")`.
   - DataFrame has single column: `"value"` (raw string).
2. **Regex to Extract Fields**  
   - Example: IP address, timestamp, request, referrer, etc. each captured with `regexp_extract("value", pattern, group)`.
   - Then we do:
     ```python
     import pyspark.sql.functions as F

     logs_df = spark.read.text("apache_logs.txt")
     parsed_df = logs_df.select(
       F.regexp_extract("value", ipRegex, 1).alias("ip"),
       F.regexp_extract("value", dateRegex, 1).alias("dateTime"),
       ...
     )
     parsed_df.show()
     ```
3. **Subsequent Transformations**  
   - After columns are defined, you can do groupBy, filters, or further transformations (like `filter(referrer != '-')`).
   - Possibly normalizing or extracting partial strings from the referrer (like domain only).

---

## 5. Working with DataFrame Columns

1. **Referencing Columns**  
   - **Column String**: `"colName"`, used in `.select("colA")`, `.drop("colA")`, `.groupBy("colA")`, etc.
   - **Column Object**: `col("colName")` or `F.col("colName")` or `column("colName")`.
   - Most DataFrame methods accept **either** string or column object. Mix them as needed.

2. **Creating Column Expressions**
   - **String (SQL) style** → wrap in `expr("...")`.
     ```python
     df.select(
       "Year","Month","DayOfMonth",
       expr("to_date(concat(Year,'-',Month,'-',DayOfMonth)) as flightDate")
     )
     ```
   - **Column-object** style → chain built-in functions:
     ```python
     from pyspark.sql.functions import to_date, concat, lit, col

     df.select(
       col("Year"),
       to_date(
         concat(col("Year"), lit("-"), col("Month"), lit("-"), col("DayOfMonth"))
       ).alias("flightDate")
     )
     ```
   - Both produce the same result. 
   - `expr(...)` can incorporate built-in or user-defined function calls in string form.

3. **Docs & Built-In Functions**
   - **DataFrame** docs: methods like `filter()`, `select()`, `drop()`, etc. (they often mention “can be column or SQL expression”).
   - **Column** docs: methods like `alias()`, `cast()`, `when()`, etc.
   - **pyspark.sql.functions**: `lit()`, `concat()`, `to_date()`, `regexp_extract()`, `when()`, `col()`, `expr()`, `monotonically_increasing_id()`, etc.

---

## 6. Creating and Using UDF (User-Defined Function)

1. **Why UDF?**
   - If built-in transformations or expressions don’t handle specific logic, define a custom Python function → convert it to Spark **UDF**.
2. **Two Ways to Register**  
   1. **DataFrame UDF** (no catalog entry):
      ```python
      from pyspark.sql.functions import udf
      from pyspark.sql.types import StringType

      def parse_gender(gender_str):
          # custom logic => "Male"/"Female"/"Unknown"
          return ...

      parseGender_udf = udf(parse_gender, StringType())
      ```
      - Use in code:
        ```python
        df2 = df.withColumn("Gender", parseGender_udf(col("Gender")))
        ```
   2. **SQL UDF** (registered in catalog):
      ```python
      spark.udf.register("parse_gender_sql", parse_gender, StringType())
      ```
      - Then used in SQL expression or `expr("parse_gender_sql(Gender)")`.
3. **Catalog Visibility**
   - `udf()` → no catalog entry; purely for DataFrame column usage.
   - `spark.udf.register("funcName", ...)` → see it in `spark.catalog.listFunctions()`.

---

## 7. Misc Transformations

1. **Example Setup**  
   - Often done in local **Jupyter Notebook** or **PyCharm**.  
   - We create a small DataFrame, show how to do transformations like **adding columns**, **casting**, **dropping duplicates**, **sorting**, etc.

2. **Quick DataFrame Creation**  
   ```python
   data_list = [
       ("Alice","12","1","06"),
       ("Bob","1","1","63"),
       ("Bob","1","1","63"),  # duplicate row
       ...
   ]
   df = spark.createDataFrame(data_list).toDF("name","day","month","year")
   df.show()
   ```
   - `toDF()` quickly names columns, skipping the need for RDD, Row objects, or explicit schema.

3. **monotonically_increasing_id()**  
   - Built-in function that creates a unique (but not consecutive) 64-bit ID per row across partitions.  
   - Example:
     ```python
     from pyspark.sql.functions import monotonically_increasing_id

     df2 = df.withColumn("id", monotonically_increasing_id())
     df2.show()
     ```
   - Each partition => unique range of IDs.

4. **Case Expressions**  
   - **SQL style**:
     ```python
     df = df.withColumn("correctedYear", expr("""
       CASE 
         WHEN year < 21 THEN year + 2000
         WHEN year < 100 THEN year + 1900
         ELSE year
       END
     """))
     ```
   - **Column Object** style (using `when` / `otherwise`):
     ```python
     from pyspark.sql.functions import when, col

     df = df.withColumn("correctedYear",
           when(col("year") < 21, col("year") + 2000)
           .when(col("year") < 100, col("year") + 1900)
           .otherwise(col("year"))
       )
     ```

5. **Casting Columns**  
   - Often needed to fix column data types.  
   - Approach 1: cast inline in expressions:
     ```python
     expr("CASE WHEN CAST(year AS INT) < 21 THEN ... END")
     ```
   - Approach 2: use `.withColumn("year", col("year").cast("int"))`:
     ```python
     df = df.withColumn("year", col("year").cast("int"))
     ```
   - Inconsistent types can lead to unexpected results (e.g. decimal expansion).

6. **Adding & Dropping Columns**  
   - **Add**: `withColumn("newCol", expression)`.
   - **Remove**: `.drop("colA","colB")`.
   - Example:
     ```python
     from pyspark.sql.functions import to_date, concat, lit

     df = df.withColumn(
       "dob",
       to_date(concat(col("year"), lit("-"), col("month"), lit("-"), col("day")))
     ).drop("day", "month", "year")
     df.show()
     ```

7. **dropDuplicates()**
   - Remove duplicate rows:
     ```python
     df_no_dups = df.dropDuplicates(["name","dob"])
     ```
   - If no columns specified, deduplicates entire row.

8. **Sorting**  
   - `df.sort("dob")` or `df.orderBy("dob")` → ascending by default.  
   - For descending, either:
     - **Column object**: `.orderBy(col("dob").desc())`, or
     - **String** expression: `.sort(expr("dob desc"))`.

9. **Examples** in Jupyter / PyCharm**  
   - The transcripts mention a “MiscDemo” with code showing:
     1. `df.repartition(3)` to create multiple partitions.
     2. Adding ID with `monotonically_increasing_id()`.
     3. Using `case when col < 21 then ... else ... end`.
     4. Casting from string to int.
     5. Dropping duplicates on some columns.
     6. Sorting in descending order.

---

## 8. Summary & Next Steps

1. **Row-Level**:
   - Usually for **small** or **unstructured** data scenarios, or for **unit test** creation/collection.
   - E.g. `spark.read.text()` -> parse lines with regex to create columns.

2. **Column-Level**:
   - The most common Spark pattern: apply **built-in** or **UDF** transformations.
   - Use either string-based SQL expressions with `expr()` or column-object approach.

3. **UDF**:
   - If built-ins do not suffice, register a custom Python function as a UDF for your transformations.  
   - Different registration for DataFrame vs. SQL usage.

4. **Misc Tools**:
   - Quick DataFrame creation with `spark.createDataFrame(...)` + `.toDF()`.
   - **monotonically_increasing_id** for unique row IDs.
   - **Case** expressions, **when** and **otherwise** for branching logic.
   - Casting columns to correct data types avoids surprising decimal/float expansions.
   - **dropDuplicates**, **drop** columns, and sorting can further refine your DataFrame.

5. **Conclusion**:
   - This section covers the **foundational transformations** needed in typical Spark data engineering tasks.
   - Next steps might involve **advanced** transformations (joins, aggregations, window functions) or deeper **performance** considerations.

