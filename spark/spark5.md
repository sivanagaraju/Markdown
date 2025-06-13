# Mindmap: Spark Structured API Foundation (with Code Highlights)

Below is a **detailed** mindmap capturing **all information** from the transcripts, **including** the **code snippets** presented for RDD and Spark SQL examples. It covers **RDD basics**, **DataFrames**, **Spark SQL**, and the **Catalyst Optimizer** in the Spark SQL Engine, with **no details omitted**.

---

## 1. Introduction to Spark APIs

1. **Origins & Evolution**  
   - Spark introduced to **simplify/improve** MapReduce.  
   - **RDD (Resilient Distributed Dataset)** was Spark’s first abstraction.  
   - Evolved into higher-level APIs: **DataFrame**, **Dataset**, and **Spark SQL**.

2. **API Stack Diagram**  
   - **RDD** at the core (low-level).  
   - **Catalyst Optimizer** powers DataFrame, Dataset, and SQL on top.  
   - **Recommended usage**:
     1. **Spark SQL** if you can solve tasks easily with SQL queries.  
     2. **DataFrame** for more extensive code or pipeline logic (especially with Python).  
     3. **Dataset** (strongly typed) for Scala/Java only.

3. **Section Overview**  
   - Show how **RDD** works (legacy, low-level).  
   - Demonstrate **Spark SQL** approach.  
   - Reiterate DataFrame usage (main focus in Python).  
   - **Dataset** not covered in detail because it’s not used in Python.

---

## 2. Introduction to Spark RDD API

### 2.1 What Is an RDD?

- **RDD** = **Resilient Distributed Dataset**:
  - **Resilient**: fault-tolerant (can re-create lost partitions from lineage).  
  - **Distributed**: partitioned across executors for parallel processing.  
  - **Dataset**: no row/column structure by default (unlike DataFrame with a schema).
- RDD requires **manual** data parsing/logic.

### 2.2 Comparing RDD to DataFrame

- **RDD**:
  - Raw data objects (no built-in schema).  
  - Minimal built-in file readers (e.g., `textFile`, etc.).  
  - No automatic optimizations (Catalyst doesn’t optimize RDD code).
- **DataFrame**:
  - Tabular structure (columns + types).  
  - Automatic Catalyst optimizations (projection pushdown, filters, etc.).  
  - Built-in CSV/JSON/Parquet readers.

### 2.3 HelloRDD Example (Code Snippet)

#### Project Setup
- Project name: **HelloRDD**.  
- `sample.csv` (no header row).  
- `log4j.properties` for logging.  
- Minimal or no `spark.conf` usage for simplicity.

#### Main Python File (Pseudo-Code)

```python
from pyspark.sql import SparkSession
from lib.logger import Log4J  # a custom logger if you have it
from collections import namedtuple

def main():
    # 1. Create SparkSession
    spark = (SparkSession.builder
                        .appName("HelloRDD")
                        .master("local[2]")  # or any config
                        .getOrCreate())

    logger = Log4J(spark)
    logger.info("Starting RDD Example...")

    # 2. Obtain SparkContext from SparkSession
    sc = spark.sparkContext

    # 3. Read data as RDD (lines of text)
    rdd = sc.textFile("sample.csv")

    # 4. (Optional) Repartition for local parallelism
    rdd_part = rdd.repartition(2)

    # 5. Parse each line: remove quotes, split by comma
    #    => produce a list of strings (columns)
    rdd_cols = rdd_part.map(lambda line: line.replace('"', '').split(','))

    # 6. Create a namedtuple to simulate a schema
    SurveyRecord = namedtuple("SurveyRecord", ["Timestamp", "Age", "Country", "State"])

    # 7. Convert each list of strings into SurveyRecord,
    #    also do 'select' by picking only needed columns
    rdd_records = rdd_cols.map(lambda cols: SurveyRecord(
        cols[0],  # Timestamp
        int(cols[1]),  # Age
        cols[2],       # Country
        cols[3]        # State
    ))

    # 8. Filter for Age < 40
    rdd_filtered = rdd_records.filter(lambda rec: rec.Age < 40)

    # 9. Group by Country => use (key, value) => reduceByKey
    #    Each record => (rec.Country, 1)
    kv_rdd = rdd_filtered.map(lambda rec: (rec.Country, 1))
    rdd_count = kv_rdd.reduceByKey(lambda a, b: a + b)

    # 10. Collect results & log
    results = rdd_count.collect()
    for (country, cnt) in results:
        logger.info(f"Country={country}, Count={cnt}")

    logger.info("Finished RDD Example.")
    spark.stop()

if __name__ == "__main__":
    main()
```

#### Observations
- Must **manually parse** CSV lines, remove quotes, cast to int.  
- Must **hand-code** group logic (reduceByKey).  
- No direct Catalyst optimizations.

---

## 3. Working with Spark SQL

### 3.1 Motivation

- **Spark SQL** is ideal for those comfortable with SQL syntax.  
- Performance = same as DataFrame approach (both use Catalyst).  
- Minimizes code if the transformations can be expressed in SQL.

### 3.2 HelloSparkSQL Example (Code Snippet)

```python
from pyspark.sql import SparkSession
from lib.logger import Log4J

def main():
    spark = (SparkSession.builder
                         .appName("HelloSparkSQL")
                         .master("local[2]")
                         .getOrCreate())

    logger = Log4J(spark)
    logger.info("Starting Spark SQL Example...")

    # 1. Read CSV as a DataFrame
    df = (spark.read
              .option("header", True)
              .option("inferSchema", True)
              .csv("sample.csv"))

    # 2. Register DataFrame as a temporary view
    df.createOrReplaceTempView("survey")

    # 3. Execute SQL query -> returns new DataFrame
    sqlDF = spark.sql("""
        SELECT Country, COUNT(*) AS cnt
        FROM survey
        WHERE Age < 40
        GROUP BY Country
    """)

    # 4. Print or process results
    sqlDF.show()

    logger.info("Finished Spark SQL Example.")
    spark.stop()

if __name__ == "__main__":
    main()
```

#### Observations
- Single SQL statement can handle **filter** + **group** logic.  
- Effortless CSV reading (header, schema inference).  
- **Creates** a new DataFrame as the query result.

---

## 4. Spark SQL Engine & Catalyst Optimizer

1. **Unified Engine**  
   - DataFrame & SQL → compiled by **Spark SQL Engine**.  
   - The **Catalyst Optimizer** does rule-based + cost-based optimizations automatically.

2. **Four Phases**  
   1. **Analysis**  
      - Parse SQL/DataFrame → abstract syntax tree.  
      - Resolve columns, tables, functions. Analysis errors if missing references.
   2. **Logical Optimization**  
      - Rule-based transformations (predicate pushdown, projection pruning, etc.).  
      - Cost-based selection for best plan.
   3. **Physical Planning**  
      - Convert logical plan → RDD operations (defining shuffles, partitioning).  
   4. **Whole-Stage Code Generation**  
      - Part of **Project Tungsten** → compile to efficient JVM bytecode.  
      - Minimizes overhead, uses CPU optimizations.

3. **Key Benefit for Developers**  
   - Just write SQL or DataFrame transformations.  
   - Spark automatically handles advanced optimizations.  
   - No manual tuning at the RDD level needed.

---

## 5. Section Summary

1. **API Layers Recap**  
   - **RDD**: lower-level, requires manual parsing & transformations, no automatic optimization.  
   - **DataFrame**: structured columns + Catalyst.  
   - **Dataset**: strongly typed version for Scala/Java.  
   - **Spark SQL**: SQL queries on top of DataFrames/tables, equally optimized.

2. **Recommended Usage**  
   - **Avoid** RDD unless you need extreme custom logic.  
   - For typical data engineering:
     - Combine **SQL** + **DataFrame**.  
     - SQL for straightforward queries.  
     - DataFrame API for more complex pipelines, application logs, unit tests, etc.  
   - Both rely on Catalyst → same optimizations & performance.

3. **Catalyst Optimizer**  
   - Automates analysis, logical optimization, physical planning, code generation.  
   - Freed from writing the grunt code as in RDD approach.

4. **Next Steps**  
   - Deeper exploration of **DataFrame** transformations, actions, and advanced usage.  
   - Understand how to best combine SQL and DataFrame in real pipelines.

> **“Keep learning and keep growing!”**
