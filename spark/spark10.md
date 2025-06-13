# Mindmap: Spark DataFrame Joins

Below is a **complete** mindmap synthesizing **all details** from the transcripts on Spark DataFrame joins. It covers **inner vs. outer joins**, **column name ambiguity**, **shuffle sort merge** vs. **broadcast** joins, **bucketed** joins, and **relevant code** examples. **No details are omitted**.

---

## 1. Introduction to DataFrame Joins

1. **Context and Motivation**
   - Often in Spark, you have **multiple** DataFrames that must be **joined** on a matching key or condition.
   - Syntax:  
     ```python
     df_left.join(df_right, join_expr, joinType)
     ```
   - The **join_expr** is typically something like `df_left["key"] == df_right["key"]`.
   - The **joinType** can be `"inner"`, `"left"`, `"right"`, `"full"`, etc.

2. **Primary Join Types**
   1. **Inner Join**: Only matching rows (keys present in both DataFrames). Non-matching rows on either side are excluded.
   2. **Outer (Full) Join**: All rows from both sides. Unmatched rows get `null` for the missing side’s columns.
   3. **Left Outer**: All rows from the left DF + any matching rows from the right. Unmatched right rows excluded.
   4. **Right Outer**: All rows from the right DF + matched left. Unmatched left rows excluded.
   5. (Optional) **Semi**, **Anti** joins also exist but weren’t heavily discussed in the transcripts.

3. **Common Pitfalls: Column Name Ambiguity**
   - If both DataFrames share columns with **identical names**, referencing them after the join can cause “ambiguous column” errors in Spark.
   - Examples: If both sides have a column called `"quantity"`, a `.select("quantity")` is ambiguous.
   - **Solutions**:
     1. **Rename** one side’s column(s) pre-join using `withColumnRenamed`.
     2. **Drop** the duplicated column from the joined result.
     3. In SQL queries, you might qualify columns by table alias, but in DataFrame code, rename or drop is usually needed.

---

## 2. Inner Joins and Column Ambiguity: Example

1. **Sample Code**  
   Suppose we have two small DataFrames:

   ```python
   from pyspark.sql import SparkSession
   from pyspark.sql.functions import col

   spark = SparkSession.builder.appName("JoinExample").getOrCreate()

   # Left DF: order_df
   order_data = [
       (1, "01", 3),    # order_id=1, prod_id="01", qty=3
       (1, "02", 2),
       (2, "01", 1),
       (3, "03", 5),
       (4, "09", 3),    # This item may not exist in product_df
   ]
   order_df = spark.createDataFrame(order_data, ["order_id","prod_id","quantity"])

   # Right DF: product_df
   product_data = [
       ("01","Gaming Mouse",15, 39.99),    # (prod_id, prod_name, quantity, list_price)
       ("02","Wireless Mouse",10, 29.99),
       ("03","Mechanical KB",5, 79.99),
       ("04","Standard Keyboard",20, 19.99),
   ]
   product_df = spark.createDataFrame(product_data, ["prod_id","prod_name","quantity","list_price"])

   order_df.show()
   product_df.show()

   # Join expression
   join_expr = (order_df["prod_id"] == product_df["prod_id"])

   # Attempt an INNER join
   df_joined = order_df.join(product_df, join_expr, "inner")
   df_joined.show()  # only matching rows appear
   ```
   - The row with `prod_id="09"` is missing in the result, because no product with `"09"` is in `product_df`.

2. **Column Ambiguity**  
   - Notice both DFs have a `"quantity"` column. If you do:
     ```python
     df_joined.select("order_id","prod_name","quantity").show()
     ```
     Spark complains about ambiguity (“Reference ‘quantity’ is ambiguous”).
   - **Solution** #1: rename one side’s quantity:
     ```python
     product_renamed = product_df.withColumnRenamed("quantity","reorder_qty")
     joined_ok = order_df.join(product_renamed, "prod_id", "inner")
     joined_ok.select("order_id","prod_name","reorder_qty").show()
     ```
   - **Solution** #2: drop the right side’s “quantity” after join:
     ```python
     df_joined2 = order_df.join(product_df, "prod_id", "inner") \
                         .drop(product_df["quantity"])
     df_joined2.select("order_id","prod_name","quantity").show()
     # Here, 'quantity' is from the left side
     ```

---

## 3. Outer Joins

1. **Full Outer Join**  
   - Keeps **all** rows from both DFs. If one side is missing, columns become `null`.
   - Example:
     ```python
     df_full = order_df.join(product_df, "prod_id", "full_outer")
     df_full.show()
     ```
   - Observations:
     - The row with `prod_id="09"` appears with `null` for `product_df` columns (like `prod_name`).
     - The “Standard Keyboard” (`prod_id="04"`) also appears with `null` from left side’s columns.

2. **Left Outer**  
   - All rows from **left** + matched from right. If no match on right side, right columns are `null`.
   - Example:
     ```python
     df_lefted = order_df.join(product_df, "prod_id", "left")
     df_lefted.show()
     ```
   - The row `prod_id="09"` from order_df is included, but “Standard Keyboard” from the right side is excluded.

3. **Right Outer**  
   - Symmetrical: all rows from **right** + matched from left. Unmatched left rows get `null`.

4. **Filling `null`s with `coalesce()`**  
   - If you want to fill `null` values in an outer join result with fallback columns:
     ```python
     from pyspark.sql.functions import coalesce

     df_fix = df_lefted.withColumn("prod_name",
                 coalesce(col("prod_name"), col("prod_id"))
               ) \
               .withColumn("list_price",
                 coalesce(col("list_price"), col("unit_price"))
               )
     df_fix.show()
     ```
   - This ensures if `prod_name` is null, we show `prod_id` instead, etc.

---

## 4. Internals: Shuffle Sort Merge Join vs. Broadcast Join

1. **Shuffle Sort Merge Join** (default for large ↔ large)  
   - **Process**:
     1. Each DF is read in partitions.  
     2. A “map” phase tags each row by join key → “shuffle write”.  
     3. A “reduce” phase collects identical keys in the same partition → “shuffle read”.  
     4. Then merges matching keys → final DataFrame partitions.  
   - **Drawback**: The shuffle can be heavy on network/disk I/O.  
   - Spark UI shows multiple stages: two map exchange stages, then a final reduce exchange stage.

2. **Code Example**:  
   - Suppose we have two directories `d1` and `d2` each with 3 files:
     ```python
     from pyspark.sql import SparkSession

     spark = SparkSession.builder \
         .appName("ShuffleJoinDemo") \
         .config("spark.sql.shuffle.partitions", 3) \
         .master("local[3]") \
         .getOrCreate()

     df1 = spark.read.csv("path/to/d1", header=True, inferSchema=True)
     df2 = spark.read.csv("path/to/d2", header=True, inferSchema=True)

     join_expr = (df1["id"] == df2["id"])
     # Inner join
     df_join = df1.join(df2, join_expr, "inner")
     # Force an action so we can see Spark UI
     df_join.count()

     # Then check Spark UI => you'll see map exchange / reduce exchange for shuffle.
     ```
   - We can see in the Spark UI that it has stages for reading each DF, then a final stage for shuffle join.

3. **Optimizing Shuffle Joins**  
   - **Filter** early, **aggregate** early to reduce data size.  
   - Tune `spark.sql.shuffle.partitions` to match your cluster’s parallelism.  
   - Avoid data skew if one key is extremely popular. Possibly re-partition data or refine the key for more uniform distribution.  
   - If you have fewer unique keys than partitions, your parallelism might be limited by that key cardinality.

4. **Broadcast Join** (large ↔ small)  
   - If **one** DF is small enough (fits in memory per executor), Spark can **broadcast** it to each executor → no shuffle for the large DF.  
   - By default, Spark auto-broadcasts if the small DF is under `spark.sql.autoBroadcastJoinThreshold` (default ~10 MB).
   - Force broadcast:
     ```python
     from pyspark.sql.functions import broadcast

     df_bcast_join = large_df.join(broadcast(small_df), "join_key", "inner")
     df_bcast_join.show()
     ```
   - The Spark UI shows “**BroadcastHashJoin**” and no shuffle exchange for that join.

---

## 5. Bucketed Joins (Large ↔ Large, Repeated Joins)

1. **Motivation**  
   - If you have **two large** DataFrames frequently joined on the same key, you can *pre-bucket* them by that key.  
   - Then **subsequent joins** can be done **without** shuffle, as they are already partitioned by key in consistent buckets.

2. **Implementation Steps**  
   - **(1) Bucket** each DF at write time:
     ```python
     # e.g. for dfA
     dfA.write \
        .bucketBy(3, "joinKey").sortBy("joinKey") \
        .mode("overwrite") \
        .saveAsTable("mydb.dfA_bucketed")

     # similarly for dfB
     dfB.write \
        .bucketBy(3, "joinKey").sortBy("joinKey") \
        .mode("overwrite") \
        .saveAsTable("mydb.dfB_bucketed")
     ```
     - The `3` means 3 buckets. Both DFs must use the **same** number of buckets & same key.  
     - This initial bucketing does a shuffle once, but it’s done only once at data prep time.
   - **(2) Join** the tables:
     ```python
     spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)  # disable broadcast

     tableA = spark.table("mydb.dfA_bucketed")
     tableB = spark.table("mydb.dfB_bucketed")

     joined_df = tableA.join(tableB, "joinKey", "inner")
     joined_df.explain()
     # => Should show a "Bucketed" or "SortMergeJoin" *without* a new shuffle.
     ```
   - Thus you avoid shuffle at join time if Spark sees consistent bucketing.

3. **Trade-Off**  
   - Bucketing requires overhead once (the shuffle while creating buckets).  
   - But repeated joins on the same key => no shuffle in those queries → big performance gains.  
   - Must maintain consistent # of buckets + same key usage across data sets.

---

## 6. Summary and Best Practices

1. **Joins & Column Ambiguity**  
   - Rename or drop duplicated columns to avoid “Reference ‘colName’ is ambiguous” errors.

2. **Join Types**  
   - **Inner**: keep only matched rows.  
   - **Left** / **Right** Outer: keep all from left/right, fill unmatched with null.  
   - **Full Outer**: all from both sides, fill unmatched side with null.  
   - Optionally fix nulls with `coalesce(...)`.

3. **Shuffle Sort Merge Joins (Large ↔ Large)**  
   - You typically see 2 map (shuffle writes) + 1 reduce (shuffle read) stages in the Spark UI.  
   - **Tune** by filtering or aggregating early, adjusting `spark.sql.shuffle.partitions`, and avoiding skew.

4. **Broadcast Hash Joins (Large ↔ Small)**  
   - If small DF can fit in memory, **broadcast** it.  
   - Spark will replicate small DF → skip shuffle.  
   - Code: `df_large.join(broadcast(df_small), "key", "inner")`.

5. **Bucketed Joins (Large ↔ Large)**  
   - Pre-bucket each data set on the join key → no shuffle at join time.  
   - Good if you frequently re-join the same large data sets.  
   - Must keep consistent # of buckets, same partition key, and similar sort order.

6. **Final Recommendations**  
   - Understand your data sets’ sizes and usage patterns.  
   - For big ↔ big joins: either shuffle or try bucketing.  
   - For big ↔ small joins: broadcast if feasible.  
   - Always watch for **data skew** and **filter** data as early as possible.  
   - If repeated joins on same key, consider **bucketing** to avoid repeated shuffle cost.

> **"Keep learning and keep growing!"**
