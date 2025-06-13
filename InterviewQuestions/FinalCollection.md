## Python Coding Question: Data Validation and Loading to S3

**Scenario:**
You’re building a Python script to process order data from a local CSV file (`orders.csv`) with columns `order_id`, `customer_id`, `amount`, and `order_date`. Validate that the `amount` is positive, transform the `order_date` to a standard format (e.g., YYYY-MM-DD), and upload the cleaned data to an S3 bucket (`s3://my-bucket/cleaned_orders/`).

**Question:**
Write a Python script to solve this, and explain how you’d ensure the script is reliable for production use.

**Expected Solution:**

```python
import pandas as pd
import boto3
from datetime import datetime

# Read CSV file
df = pd.read_csv("orders.csv")

# Validate: Ensure amount is positive
df = df[df["amount"] > 0]

# Transform: Standardize order_date
df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d")

# Write cleaned data to a temporary CSV
cleaned_file = "cleaned_orders.csv"
df.to_csv(cleaned_file, index=False)

# Upload to S3
s3_client = boto3.client("s3")
bucket_name = "my-bucket"
s3_path = "cleaned_orders/cleaned_orders.csv"

try:
    s3_client.upload_file(cleaned_file, bucket_name, s3_path)
    print(f"Successfully uploaded to s3://{bucket_name}/{s3_path}")
except Exception as e:
    print(f"Error uploading to S3: {e}")
```

**Reliability Steps:**

- Add error handling for file reading and S3 upload using `try-except`.
- Log validation failures to a file for debugging.
- Use `boto3`’s retry configuration to handle transient S3 failures: `boto3.setup_default_session(config=Config(retries={'max_attempts': 3}))`.
- Test the script in a CI/CD pipeline (e.g., with Jenkins, as per Swathi’s resume) to catch issues early.

**Follow-Up Questions:**

- If this data were to be loaded into a data lake with Delta Lake tables, how would you modify the script to write the output as a Delta Lake table?
- How would you handle missing or malformed `order_date` values in the CSV file?
- What steps would you take to automate this script using a tool like Apache Airflow, and how would you monitor its execution?

--------------------------------------------------------------------------------------------------------------------
Certainly! Here’s a **shortened and concise version** of your refined **SQL Optimization in a Hive-based Data Warehouse** interview question for Swathi Chinthanippu. It retains all the core technical depth while removing repetition and tightening the language to fit better in a timed interview setting.

---

## ✅ **SQL Optimization Question: Financial Reporting in Hive**

### 🔹 Scenario

You’re working on a Hive-based data warehouse at Wells Fargo to support the Financial Data Operation (FDO) team. You have three tables:

* `transactions`: (`transaction_id`, `account_id`, `category_id`, `transaction_date`, `amount`) — 150M rows
* `accounts`: (`account_id`, `customer_id`, `account_type`) — 20M rows
* `categories`: (`category_id`, `category_name`) — 1,000 rows

You’re tasked with calculating the **total transaction amount per `account_type` and `category_name`** for **Q1 2025**.

Here is the current slow-performing query:

```sql
SELECT 
    a.account_type,
    c.category_name,
    SUM(t.amount) as total_amount
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN categories c ON t.category_id = c.category_id
WHERE YEAR(t.transaction_date) = 2025
  AND MONTH(t.transaction_date) BETWEEN 1 AND 3
GROUP BY a.account_type, c.category_name;
```

---

### 🧠 Questions

1. **Why is this query slow in Hive?**
2. **Rewrite it for better performance using Hive-specific features.**
3. **Explain your optimization steps and their benefits.**

---

### ✅ **What a Strong Answer Should Include**

* **Problems with the current query:**

  * `YEAR()` and `MONTH()` prevent partition pruning → full table scan
  * Joins without bucketing or broadcasting → costly shuffle
  * No filter pushdown or vectorization

* **Optimized Query (example):**

```sql
SELECT 
    a.account_type,
    c.category_name,
    SUM(t.amount) as total_amount
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN categories c /* broadcast */ ON t.category_id = c.category_id
WHERE t.transaction_date >= '2025-01-01' 
  AND t.transaction_date < '2025-04-01'
GROUP BY a.account_type, c.category_name;
```

* **Suggested Optimizations:**

  * Use **date range filter** for partition pruning
  * **Partition `transactions`** by `year`, `month`
  * **Bucket `transactions` and `accounts`** by `account_id` to optimize join
  * **Broadcast `categories` table** (small dimension)
  * Enable Hive configs:

    * `SET hive.optimize.ppd=true;`
    * `SET hive.vectorized.execution.enabled=true;`
    * `SET hive.auto.convert.join=true;`

---

### 🔄 Optional Follow-Ups (If Time Allows)

* How would you handle data skew in `account_type`?
* How would Delta Lake features (like Z-ordering) help here?
* How would this be integrated into a CI/CD pipeline for automated reporting?
* How would you stream this output to Kafka efficiently?

---

### ⏱️ Time Required: \~6–8 minutes

Would you like this compressed further to fit a 4-minute slot or keep this as a “deep dive” flagship question in the interview?

---

Let me know if you'd like a **PDF version**, a **candidate evaluation checklist**, or to turn this into a **Jupyter notebook-style demo**.

----------

## Python Coding Question: Efficient Data Processing with PySpark

**Scenario:**

You’re working on a critical data pipeline that processes a massive dataset of transaction data stored in S3 (`s3://my-bucket/trans_data/`) in Parquet format, with columns: `trans_id`, `user_id`, `amount`, `trans_date`, and `product_type`. This dataset contains over 10 billion transactions. The user data (`s3://my-bucket/users/`) has columns: `user_id`, `name`, and `city`, with around 50 million users. Your task is to calculate the total transaction amount per city and product type for transactions in 2024, and the pipeline must complete within 30 minutes on a cluster with limited resources. The data has uneven distribution—some users have millions of transactions while others have very few—causing delays in processing.

**Question:**  
Write a PySpark script to perform this analysis as efficiently as possible, ensuring the pipeline completes within 30 minutes. How would you handle the uneven distribution of data to avoid delays and ensure the pipeline runs smoothly?

**Solution:**  
Here’s a potential solution that incorporates optimization techniques without explicitly mentioning them in the question:

Let’s explore what an effective solution might look like. What steps would you take to process 10 billion transactions efficiently? How might you handle the join between transactions and users, given the data sizes (10 billion vs. 50 million)? What strategies could help balance the workload across the cluster when some users have significantly more transactions than others?

Here’s a solution that incorporates optimization techniques without explicitly mentioning them in the question:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, sum as _sum

# Initialize Spark session with balanced configurations
spark = SparkSession.builder \
    .appName("EfficientTransactionAnalysis") \
    .config("spark.sql.shuffle.partitions", "1000") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

# Read transaction data with early filtering
transactions = spark.read.parquet("s3://my-bucket/trans_data/") \
    .filter(year(col("trans_date")) == 2024)

# Read user data
users = spark.read.parquet("s3://my-bucket/users/")

# Add a temporary key to distribute data evenly for users with many transactions
transactions_distributed = transactions.withColumn("temp_key", (col("user_id") % 10).cast("string"))
users_distributed = users.withColumn("temp_key", (col("user_id") % 10).cast("string"))

# Organize transaction data to optimize join performance
transactions_distributed = transactions_distributed.repartition(1000, "user_id") \
    .write.bucketBy(1000, "user_id").mode("overwrite").saveAsTable("trans_distributed")
transactions_distributed = spark.table("trans_distributed")

# Join with the smaller user dataset efficiently
joined_df = transactions_distributed.join(
    users_distributed.hint("broadcast"),
    ["user_id", "temp_key"],
    "inner"
)

# Calculate total amount per city and product type
result = joined_df.groupBy("city", "product_type") \
    .agg(_sum("amount").alias("total_amount"))

# Reduce output partitions for writing
result = result.coalesce(50)
result.write.mode("overwrite").parquet("s3://my-bucket/output/")

# Clean up
spark.stop()
```

**Why This Solution is Effective:**  
- **Early Filtering:** Filters transactions for 2024 while reading Parquet, reducing the dataset size upfront (predicate pushdown).  
- **Data Distribution:** Adds a `temp_key` to handle uneven distribution (salting), ensuring more balanced processing across the cluster.  
- **Optimized Join:** Uses a broadcast join for the smaller `users` dataset (50 million rows), avoiding unnecessary data movement.  
- **Partitioning Strategy:** Repartitions and buckets transactions by `user_id` to align data for the join, minimizing data shuffling.  
- **Output Efficiency:** Uses `coalesce` to reduce the number of output partitions, speeding up the write operation.  
- **Adaptive Execution:** Enables adaptive query execution (AQE) to dynamically optimize the execution plan.

**Steps to Ensure Smooth Execution:**  
- Filter data as early as possible to reduce the amount of data processed.  
- Distribute the workload evenly by adding a temporary key for users with many transactions.  
- Organize the data before the join to ensure efficient processing.  
- Use the smaller dataset in a way that minimizes data movement during the join.  
- Adjust the number of output files to optimize the write operation.  
- Configure the cluster to dynamically adapt to the data size and distribution.


------

## 📊 **Scenario: Customer Profile Updates**

Wells Fargo maintains a `customer_profiles` table that contains the following fields:

* `customer_id` (unique per customer)
* `name`
* `address`
* `kyc_status` (e.g., `verified`, `pending`, `rejected`)
* `updated_date`

Every day, a new snapshot of customer data is received. The goal is to **retain the full history** of changes to customer profiles for compliance and audit purposes.

---

### 📊 Sample Incoming Data (Today’s Snapshot)

| customer\_id | name         | address          | kyc\_status | updated\_date |
| ------------ | ------------ | ---------------- | ----------- | ------------- |
| 101          | John Smith   | 123 Maple St, NY | verified    | 2025-06-13    |
| 102          | Sarah Connor | 45 Oak Rd, CA    | pending     | 2025-06-13    |
| 103          | Mike Johnson | 999 Pine St, TX  | verified    | 2025-06-13    |

Yesterday, the same customer 101 had a different address: "111 Elm St, NY". We need to **keep both versions**.

---

###  🧠 **SCD Type 2 Implementation in SQL Server**

We maintain a **history table** like this:

### `customer_profiles_history`

| surrogate\_key | customer\_id | name         | address          | kyc\_status | effective\_start\_date | effective\_end\_date | is\_current |
| -------------- | ------------ | ------------ | ---------------- | ----------- | ---------------------- | -------------------- | ----------- |
| 1              | 101          | John Smith   | 111 Elm St, NY   | verified    | 2024-01-01             | 2025-06-12           | 0           |
| 2              | 101          | John Smith   | 123 Maple St, NY | verified    | 2025-06-13             | 9999-12-31           | 1           |
| 3              | 102          | Sarah Connor | 45 Oak Rd, CA    | pending     | 2025-06-13             | 9999-12-31           | 1           |

### Key Ideas:

* `surrogate_key`: primary key (identity/autoincrement)
* `effective_start_date`: when the version became active
* `effective_end_date`: when the version became inactive
* `is_current`: flag for latest version (either 0 or 1)

---

### ❓ Follow-up Interview Questions

1. **What if two updates come for the same customer on the same day?**

   * Would you use `rowversion` or a timestamp to deduplicate?

2. **What’s the difference between SCD Type 1 vs Type 2 vs Type 3?**

   * Type 1 overwrites, Type 2 stores history, Type 3 stores limited change (e.g., previous value in another column)

3. **How would you design this if the volume grows to 1B+ rows?**

   * Talk about partitioning on `effective_start_date`, indexing `customer_id`, archiving old records.

4. **How to enforce uniqueness in `is_current = 1` per `customer_id`?**

   * You can use a filtered unique index:

     ```sql
     CREATE UNIQUE INDEX ux_customer_current ON customer_profiles_history(customer_id)
     WHERE is_current = 1
     ```

5. **What problems can arise with SCD2 during backfills or reprocessing?**

   * Data duplication, incorrect end dates, version gaps.

6. **What if KYC data comes late (backdated updates)? How do you handle retroactive corrections?**

   * You may need to **recalculate effective ranges** or even delete/re-insert affected versions.

---

