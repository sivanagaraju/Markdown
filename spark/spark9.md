# Mindmap: Aggregations in Apache Spark

Below is a **comprehensive** mindmap of **all details** from the transcripts on *Spark DataFrame Aggregations*, including **simple** (global) aggregations, **grouping** (groupBy) aggregations, **windowing** (running totals, etc.), **challenge/solution** code snippets, and **all references** to functions (`coalesce`, `round`, etc.). **No details are omitted**.

---

## 1. Introduction to Aggregations

1. **Context & Types of Aggregations**  
   - In Apache Spark, we perform **aggregations** to produce summaries from DataFrames.  
   - **Three categories** in the transcripts:
     1. **Simple (Global) Aggregations** → entire DataFrame summarized into **one** row.  
     2. **Grouping Aggregations** → `groupBy` columns, produce summary stats per group.  
     3. **Windowing Aggregations** → define a partition + ordering, then apply running totals, ranks, lead/lag, etc.

2. **Built-In Functions**  
   - **Spark** provides **aggregate** (e.g. `count`, `sum`, `avg`, `countDistinct`) and **window** (`row_number`, `rank`, `dense_rank`, `lead`, `lag`, `sum(...) over ...`) functions in `pyspark.sql.functions`.
   - Use them in **DataFrame** column expressions or **Spark SQL**.

3. **Invoice Data Example**  
   - The transcripts use **Invoice line items** CSV with columns:
     - `InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country`.
   - We will load this into a DataFrame, then demonstrate **simple** and **grouping** aggregates, plus **window** aggregates.

---

## 2. Simple (Global) Aggregations

1. **Definition**  
   - Summaries of the **entire** DataFrame → returns **one** row.
   - E.g.: `count(*)`, `sum(Quantity)`, `avg(UnitPrice)`, `countDistinct(...)`.

2. **Code Example**  
   ```python
   # from pyspark.sql.functions import count, sum, avg, countDistinct                                                                                           

   # Suppose df is loaded from the invoice CSV
   simple_df = df.select(
       count("*").alias("rowCount"),
       sum("Quantity").alias("totalQty"),
       avg("UnitPrice").alias("avgPrice"),
       countDistinct("InvoiceNo").alias("uniqueInvoices")
   )
   simple_df.show()
   ```
   - Produces one-row DataFrame.

3. **SQL-Like Expression**  
   ```python
   from pyspark.sql.functions import expr

   simple_expr_df = df.selectExpr(
       "count(1) as rowCount",
       "sum(Quantity) as totalQty",
       "avg(UnitPrice) as avgPrice",
       "count(distinct InvoiceNo) as uniqueInvoices"
   )
   simple_expr_df.show()
   ```
   - `count(1)` is effectively same as `count(*)`; but `count("StockCode")` excludes null StockCode rows.

---

## 3. Grouping Aggregations

1. **Concept**  
   - Use **groupBy** (or Spark SQL `GROUP BY`) to produce multiple aggregates **per group**.  
   - E.g. Summarize `(Country, InvoiceNo)` groups → sum of quantity, total invoice value, etc.

2. **Code Example**  
   ```python
   from pyspark.sql.functions import round, sum, expr

   grouped_df = df.groupBy("Country", "InvoiceNo").agg(
       sum("Quantity").alias("totalQty"),
       round(sum(expr("Quantity * UnitPrice")), 2).alias("invoiceValue")
   )
   grouped_df.show()
   ```
   - The same in **Spark SQL**:
     ```python
     df.createOrReplaceTempView("invoices")
     result_sql = spark.sql("""
       SELECT
         Country,
         InvoiceNo,
         SUM(Quantity) AS totalQty,
         ROUND(SUM(Quantity * UnitPrice), 2) AS invoiceValue
       FROM invoices
       GROUP BY Country, InvoiceNo
     """)
     result_sql.show()
     ```

3. **Exercise** (from transcripts)  
   - **Challenge**:  
     - Group by **Country** and **weekofyear(InvoiceDate)**.  
     - **Aggregations**:
       1. `countDistinct(InvoiceNo)` = unique invoice count  
       2. `sum(Quantity)` = total quantity  
       3. `sum(Quantity * UnitPrice)` = total value  
   - Must parse `InvoiceDate` from string → date, then `weekofyear()`.

4. **Solution**  
   ```python
   from pyspark.sql.functions import to_date, weekofyear, sum, countDistinct, expr, round

   # 1) Convert InvoiceDate (string) to date, possibly filtering year=2010
   df2 = df.withColumn("InvoiceDate", to_date("InvoiceDate", "M/d/yy H:mm")) \
           .filter(expr("year(InvoiceDate) = 2010"))

   # 2) Create WeekNumber column
   df2 = df2.withColumn("WeekNumber", weekofyear("InvoiceDate"))

   # 3) Group & aggregate
   #    - uniqueInvoices = countDistinct(InvoiceNo)
   #    - totalQty = sum(Quantity)
   #    - totalValue = sum(Quantity*UnitPrice) => maybe round
   grouped_agg = df2.groupBy("Country", "WeekNumber").agg(
       countDistinct("InvoiceNo").alias("uniqueInvoices"),
       sum("Quantity").alias("TotalQuantity"),
       round(sum(expr("Quantity * UnitPrice")), 2).alias("TotalValue")
   )

   # 4) Optional: coalesce, sort, or write to disk
   grouped_agg = grouped_agg.coalesce(1).sort("Country","WeekNumber")
   grouped_agg.show()

   # grouped_agg.write.mode("overwrite").parquet("/path/to/output")
   ```
   - The transcripts mention `.coalesce(...)` to reduce partitions in final output, and `.sort(...)` for clarity.

---

## 4. Windowing Aggregations

1. **Why Window Aggregates?**  
   - Needed for advanced computations like **running total**, rank, lead/lag.  
   - You define a **partition** (like Country), an **ordering** (like WeekNumber), and a **frame** (range/rowsBetween) for each row.

2. **Example**: Running Total of `invoiceValue` Per Week  
   - We start with a DataFrame that already has `(Country, WeekNumber, invoiceValue)` from grouping.  
   - We want a cumulative sum (week by week) for each country.

3. **Defining a Window**  
   ```python
   from pyspark.sql.window import Window
   from pyspark.sql.functions import sum

   running_total_window = Window.partitionBy("Country") \
                                .orderBy("WeekNumber") \
                                .rowsBetween(Window.unboundedPreceding, Window.currentRow)
   ```
   - **partitionBy("Country")** → separate each country’s data.  
   - **orderBy("WeekNumber")** → each partition sorted by ascending WeekNumber.  
   - **rowsBetween(Window.unboundedPreceding, Window.currentRow)** → from first row in partition up to current row (cumulative).

4. **Applying the Window**  
   ```python
   df_with_running = df.withColumn(
       "RunningTotal",
       sum("invoiceValue").over(running_total_window)
   )
   df_with_running.show()
   ```
   - Produces a new column `RunningTotal` = sum of all previous rows + current row in that partition ordering.

5. **Adjusting the Frame**  
   - For a “3-week rolling sum,” for example:
     ```python
     df.withColumn(
       "ThreeWeekSum",
       sum("invoiceValue").over(
         running_total_window.rowsBetween(-2, Window.currentRow)
       )
     )
     ```
   - Or `rangeBetween` for numeric ordering columns.

6. **Other Window Functions**  
   - `rank`, `dense_rank`, `row_number`, `lead`, `lag` can be used similarly:
     ```python
     from pyspark.sql.functions import row_number

     df.withColumn("rowNum", row_number().over(running_total_window))
     ```
   - Each function is applied via `.over(windowSpec)` in the column expression.

---

## 5. Summary & Next Steps

1. **Aggregations Overview**  
   - **Simple**: single-row summary of the entire DataFrame (e.g. `count(*)`, `sum(...)`).  
   - **Grouping**: `groupBy(...)` + multiple aggregates or `Spark SQL GROUP BY`.  
   - **Window**: partition + ordering + frame. E.g. running totals, ranking, lead/lag.

2. **Key Built-In Functions**  
   - **Aggregate**: `count, sum, avg, min, max, countDistinct, approx_count_distinct`, etc.  
   - **Window**: `sum(...).over(...)`, `rank`, `dense_rank`, `row_number`, `lead`, `lag`, plus specifying partition, ordering, and frame.

3. **Practical Tips**  
   - Often **clean/cast** data first (e.g. `InvoiceDate` to `date`).  
   - **Filter** if needed to reduce volume or focus on certain segments (like year=2010).  
   - For final output, you might **coalesce** to reduce file partitions, or **sort** for readability.  
   - Understand difference between `rowsBetween` vs. `rangeBetween` for window frames.  
   - Windowing does not replace groupBy—it’s for row-level advanced analytics within partitions.

4. **Where to Go Next**  
   - More advanced topics:
     - **Cube** / **Rollup** for multi-level grouping.  
     - Performance considerations (shuffle, partitioning, caching).  
     - Combining window functions with grouping or sub-DataFrames.

