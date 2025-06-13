# Mindmap: Spark Data Sources and Sinks

Below is a **detailed** and **complete** mindmap capturing **all information** from the “Spark Data Sources and Sinks” transcripts. It includes **concepts**, **recommendations**, **code examples**, **DataFrameReader/Writer** mechanics, **partitioning**, **bucketing**, **Spark SQL managed/unmanaged tables**, and **metastore** details. **No details are omitted**.

---

## 1. Introduction: Spark Data Sources and Sinks

1. **Big-Picture Context**
   - Spark processes large-scale data by **reading** from sources and **writing** to sinks.
   - In a **Data Lake** environment, Spark typically works with files in **distributed storage** (e.g., HDFS, S3) or can connect directly to **external systems** (databases, message queues) if needed.

2. **Categories of Data Sources**
   - **External Data Sources** (outside Data Lake):
     - RDBMS (Oracle, SQL Server, MySQL, PostgreSQL)
     - NoSQL (Cassandra, MongoDB)
     - Cloud Data Warehouses (Snowflake, Redshift)
     - Streaming systems (Kafka, etc.)
     - Typically **ingest** them into the Lake with data integration tools (for batch).
   - **Internal Data Sources** (inside Data Lake):
     - Files in HDFS or cloud object storage (S3, GCS, Azure Blob).
     - Stored in formats like CSV, JSON, Parquet, ORC, Avro, etc.

3. **Recommended Approach**
   - For **batch**: Usually **import** external data first into the Lake, then let Spark read from those internal files. 
   - Spark *can* read from external systems (e.g., via JDBC or custom connectors) but that’s often used for *streaming* or specialized scenarios.
   - **Parquet** is the recommended default format for Spark due to built-in schema + performance advantages.

4. **Data Sinks**
   - Spark “sinks” are simply **where** the processed DataFrame is written out.
   - Could be:
     - **Files** in distributed storage (e.g., Parquet or Avro).
     - External systems (JDBC to RDBMS, NoSQL, etc.).
   - Similar to sources, typically recommended to store final output in **internal** Lake files or **Spark SQL tables** (discussed later).

---

## 2. Spark DataFrameReader API

1. **High-Level Mechanics**
   - Accessed via `spark.read`, where `spark` is a `SparkSession`.
   - The **DataFrameReader** follows a **standard structure**:
     ```python
     (spark.read
         .format("csv" | "json" | "parquet" | "jdbc" | ...)
         .option("header", True/False)           # or other source-specific options
         .option("mode", "...")                  # e.g. PERMISSIVE, DROPMALFORMED, FAILFAST
         .schema(...)                            # optional if we want explicit schema
         .load("path or directory"))
     ```

2. **Formats & Options**
   - **Built-In** formats: CSV, JSON, Parquet, ORC, JDBC.  
   - **Extended** formats: Avro, Cassandra, MongoDB, etc. (require additional packages).
   - **Key CSV/JSON options**:
     - `header` (for CSV).
     - `inferSchema` (sometimes inaccurate for date/time).
     - `mode` for malformed records:
       - `PERMISSIVE` (default), 
       - `DROPMALFORMED`, 
       - `FAILFAST`.
   - **Parquet/Avro** embed schema in files → typically no need to manually set schema.

3. **Usage Examples**
   - **CSV**:
     ```python
     df_csv = (spark.read
                  .format("csv")
                  .option("header", True)
                  .option("inferSchema", True)
                  .load("flightdata/*.csv"))
     ```
   - **JSON**:
     ```python
     df_json = (spark.read
                  .format("json")
                  # JSON automatically tries to infer schema
                  .load("flightdata/flights.json"))
     ```
   - **Parquet**:
     ```python
     df_parquet = spark.read.parquet("flightdata/flights.parquet")
     ```
     - Parquet already contains the schema → best synergy with Spark.

---

## 3. Reading CSV, JSON, and Parquet (Example)

1. **Sample Project** – *SparkSchemaDemo*
   - Includes three data files (same flight data) in CSV, JSON, and Parquet forms.
   - **Observations**:
     - CSV/JSON → typically yield `string` columns if no schema is specified.
     - Setting `inferSchema` might improve numeric columns but can fail on dates.
     - Parquet → includes correct schema, so Spark loads correct data types automatically.

2. **Behavior of `inferSchema`**:
   - Might interpret integers/floats well, but often leaves date/time as strings.
   - If you need accurate date/time, you must either:
     - Provide an **explicit schema**, or
     - Use a format that stores schema (Parquet/Avro).

3. **Conclusion**:
   - For critical data types, prefer **explicit** schema or a **schema-based** format (Parquet).
   - CSV/JSON are common ingestion formats but can be error-prone if the schema is complex (esp. for dates).

---

## 4. Creating Spark DataFrame Schema

1. **Why Define Schema Explicitly?**
   - CSV/JSON inference is often **inaccurate** (especially for date/time).
   - Provides full control (column names, data types, date patterns).
   - Reduces runtime errors and ensures correct data types.

2. **Spark Data Types**
   - Found in `pyspark.sql.types`: 
     - `StringType`, `IntegerType`, `DoubleType`, `DateType`, `TimestampType`, `BooleanType`, ...
   - Spark must track its own types for internal compilation & optimization (Catalyst).

3. **Two Methods**:
   1. **Programmatic StructType** 
      ```python
      from pyspark.sql.types import (StructType, StructField, StringType, IntegerType, DateType)

      flight_schema = StructType([
          StructField("FL_DATE", DateType(), True),
          StructField("OP_CARRIER", StringType(), True),
          StructField("ORIGIN", StringType(), True),
          StructField("DEST", StringType(), True),
          StructField("DISTANCE", IntegerType(), True)
      ])

      df = (spark.read
                .format("csv")
                .option("header", True)
                .option("mode", "FAILFAST")
                .option("dateFormat", "M/d/y")     # parse dates
                .schema(flight_schema)
                .load("flightdata/flights.csv"))
      ```
   2. **DDL String**  
      ```python
      ddl = "FL_DATE DATE, OP_CARRIER STRING, ORIGIN STRING, DEST STRING, DISTANCE INT"

      df_ddl = (spark.read
                    .format("json")
                    .option("dateFormat", "M/d/y")
                    .schema(ddl)
                    .load("flightdata/flights.json"))
      ```

4. **Handling Date Parsing** 
   - CSV might require `option("dateFormat", "M/d/y")`.
   - If Spark can’t parse a date correctly → error or null (depending on `mode`).

---

## 5. Spark DataFrameWriter API

1. **High-Level Mechanics**
   - Accessed via `df.write`.
   - Standard structure:
     ```python
     (df.write
         .format("csv" | "json" | "parquet" | "jdbc" | ...)
         .mode("append" | "overwrite" | "errorIfExists" | "ignore")
         .option("maxRecordsPerFile", N)  # if needed
         .partitionBy("col1", "col2")     # optional
         .bucketBy(N, "colA", "colB")     # for managed tables
         .sortBy("colA", "colB")          # also for bucketed data
         .save("output_path_or_table_name"))
     ```

2. **saveMode**  
   - `append` → add new files.  
   - `overwrite` → remove existing data, then write new.  
   - `errorIfExists` → fail if output path already has data.  
   - `ignore` → if target exists, do nothing; else write new.

3. **Controlling Output Layout**  
   - By default, 1 file per partition (the data is partitioned across executors).
   - **Repartitioning**:
     - `.repartition(N)` → random distribution into N partitions → N output files.
   - **partitionBy** (File-based partitioning):
     - e.g. `.partitionBy("OP_CARRIER", "ORIGIN")` → create subdirectories for each combination.  
     - Good for “partition pruning” in queries.
   - **bucketBy** + **sortBy** (only for Spark managed tables):
     - Hash data by some columns into fixed # of “buckets,” optionally sorted.  
     - Can improve performance for joins, etc.
   - **maxRecordsPerFile**:
     - Limit file sizes by capping record count per file.

4. **Example**: Writing Data to Avro
   ```python
   # Avro needs extra spark-avro package
   (df.write
      .format("avro")
      .mode("overwrite")
      .save("/path/to/avro_output"))
   ```
   - Overwrite mode → deletes existing data at the path, then writes new files.

---

## 6. Writing Your Data and Managing Layout (Example)

1. **Sample Project** – *DataSinkDemo*
   - Demonstrates how to write DataFrames in various ways (e.g., Avro output).
   - If using Avro with PySpark, set extra packages in `spark-defaults.conf`:
     ```bash
     spark.driver.extraClassPath  ...
     spark.jars.packages  org.apache.spark:spark-avro_2.11:2.4.5
     ```
   - Then in code:
     ```python
     (df.write
        .format("avro")
        .mode("overwrite")
        .save("/path/to/avro_out"))
     ```

2. **Partition Examples**  
   - Checking partition count:
     ```python
     num_partitions = df.rdd.getNumPartitions()
     ```
   - If 2 partitions → 2 output files (unless one is empty).
   - **Force Repartition**:
     ```python
     df5 = df.repartition(5)
     df5.write.overwrite().format("avro").save(...)
     # => 5 output files
     ```

3. **partitionBy** Example:
   ```python
   (df.write
      .mode("overwrite")
      .format("json")
      .partitionBy("OP_CARRIER", "ORIGIN")
      .save("/path/json_output"))
   ```
   - Creates nested directories:  
     - `OP_CARRIER=<value>/ORIGIN=<value>/part-... .json`
   - Good for partition pruning.  
   - Be mindful of columns with large cardinality → can result in thousands or millions of directories.

4. **maxRecordsPerFile**  
   ```python
   (df.write
      .mode("overwrite")
      .format("json")
      .partitionBy("OP_CARRIER", "ORIGIN")
      .option("maxRecordsPerFile", 10000)
      .save("/path/json_output"))
   ```
   - Splits large partitions into multiple files if partition has more than 10k rows.

5. **File Size Considerations**
   - Prefer moderate file sizes (e.g., 500 MB to a few GB).  
   - Very small files → overhead.  
   - Very large files → can hamper splitting performance.

---

## 7. Spark Databases and Tables

1. **Spark as a Database**  
   - Spark can manage **databases** + **tables** + **views** in a **metastore** (catalog).  
   - Table data is stored as files (often Parquet), while table metadata is in the catalog (commonly Hive Metastore).
   - Tools can query these tables via **SQL** or **JDBC/ODBC** → convenient for BI/reporting.

2. **Managed vs. Unmanaged (External) Tables**
   - **Managed Table**:
     - Spark manages **both** metadata and data.  
     - Data physically stored under `spark.sql.warehouse.dir` in `[database].db/[table]/...`.  
     - Dropping table → removes data files + metadata.
   - **Unmanaged/External Table**:
     - Spark only manages metadata; data remains in a custom location you specify.  
     - Dropping table → deletes metadata only, data files stay.  
     - Typically used if you already have data in place, want to register it for Spark SQL queries.

3. **Why Managed Tables?**
   - They allow advanced Spark features (like **bucketing**).  
   - Future Spark SQL improvements often target managed tables first.  
   - Great if you want Spark to “own” the data lifecycle.

---

## 8. Working with Spark SQL Tables (Example)

1. **Enable Hive Support**  
   - For a persistent metastore, use `.enableHiveSupport()`:
     ```python
     spark = (SparkSession.builder
                          .appName("SparkSQLTableDemo")
                          .enableHiveSupport()
                          .getOrCreate())
     ```
   - This links to an existing Hive Metastore or creates a local one.

2. **Creating a Database & Table**:
   ```python
   # create a DB if not exists
   spark.sql("CREATE DATABASE IF NOT EXISTS AIRLINE_DB")
   
   # set current DB
   spark.catalog.setCurrentDatabase("AIRLINE_DB")

   # read data (e.g. from parquet)
   df = spark.read.parquet("flightdata/flights.parquet")

   # save as a MANAGED TABLE
   df.write.mode("overwrite").saveAsTable("flight_data_tbl")
   ```
   - By default, it writes Parquet files in the warehouse directory at `.../AIRLINE_DB.db/flight_data_tbl`.

3. **Partitioned Managed Table**:
   ```python
   df.write
     .mode("overwrite")
     .partitionBy("OP_CARRIER", "ORIGIN")
     .saveAsTable("flight_data_tbl")
   ```
   - Creates subdirectories for each partition combination under the table folder.
   - Caution if columns have very high cardinality → thousands of partitions.

4. **Bucketing** Example**:
   ```python
   # Must do for a MANAGED table
   df.write.bucketBy(5, "OP_CARRIER", "ORIGIN") \
           .sortBy("OP_CARRIER", "ORIGIN") \
           .mode("overwrite") \
           .format("csv") \
           .saveAsTable("flight_data_bucketed_tbl")
   ```
   - Splits data into 5 hashed buckets, sorted by those columns. 
   - Produces exactly 5 files (no extra partition directories).
   - Can improve certain joins or queries.

5. **Accessing the Catalog**:
   ```python
   tables = spark.catalog.listTables("AIRLINE_DB")
   for t in tables:
       print(t.name, t.database, t.tableType)
   ```
   - `tableType`: `MANAGED`, `EXTERNAL`, or `VIEW`.
   - If we do `DROP TABLE AIRLINE_DB.flight_data_tbl`, the data + metadata is removed for a MANAGED table.

---

## 9. Section Summary

1. **Core Concepts**:
   - Spark can read data from **internal** (files in HDFS/S3) or **external** systems. 
   - For **batch** processes, recommended approach is to land data in the Lake first, then let Spark read from those files (e.g. Parquet).
2. **DataFrameReader**:
   - `.format(...)`, `.option(...)`, `.load(...)`. 
   - Common formats: CSV, JSON, Parquet (recommended), ORC, Avro, plus external plugins.
   - Potentially override/infer schema or define it explicitly (StructType/DDL).
3. **DataFrameWriter**:
   - `.format(...)`, `.mode(...)`, `.save(...)`. 
   - Partitioning via `repartition()` or `.partitionBy()`; bucketing with `.bucketBy()`.
   - Manage file layout (number of partitions, subdirectories, file size).
4. **Spark SQL Tables**:
   - Two-tier approach: 
     - **Managed** (Spark controls data location & deletes on drop). 
     - **Unmanaged** (external data location, only metadata in Spark).
   - Access via **SQL** or **JDBC/ODBC** → convenient for BI tools.
   - Powerful features: partitioning, **bucketing** (especially for managed tables).
5. **Practical Advice**:
   - Default to **Parquet** for best performance & schema correctness. 
   - Use **explicit schemas** if CSV/JSON are ambiguous. 
   - For repeated SQL or external tool usage, consider **Spark managed tables**. 
   - Be mindful of partition/bucket cardinalities to avoid too many small files or directories.

> **"Keep learning and keep growing!"**
