

# Long-Term Maintenance Strategies for Apache Iceberg Tables

## 1. Core Maintenance Operations: Data and Metadata Contraction

Effective long-term management of Apache Iceberg tables hinges on a set of core maintenance operations designed to control storage costs and optimize query performance. These operations, often referred to as "contraction" tasks, systematically reduce the physical and metadata footprint of a table over time. The primary goals are to mitigate the "small file problem," manage metadata bloat, and ensure that the table remains performant and cost-effective as data volume and query patterns evolve. This involves a continuous cycle of compacting small data files into larger, more efficient ones, rewriting manifest files to optimize metadata access, and expiring old snapshots to reclaim storage and simplify metadata. For a data platform using Spark 3.4 and S3, these operations are typically orchestrated via Spark SQL procedures, which provide a powerful and flexible interface for automating table maintenance. Understanding and implementing these core contraction strategies is fundamental to building a sustainable and scalable data lakehouse architecture.

### 1.1. Data File Compaction (`rewrite_data_files`)

Data file compaction is arguably the most critical maintenance task for an Iceberg table, directly addressing the pervasive "small file problem" that can severely degrade query performance and inflate metadata overhead. In high-velocity data environments, such as those with streaming ingestion or frequent micro-batch writes, data is often written in small increments, resulting in a proliferation of tiny Parquet files on S3. Each of these files, regardless of its size, incurs a fixed cost during query execution, including I/O requests, metadata tracking, and scheduling overhead. When a table accumulates thousands or millions of these small files, the cumulative overhead can become a significant bottleneck, leading to slower query planning and execution times. Compaction, specifically through the `rewrite_data_files` procedure, is the process of merging these small files into a smaller number of larger, optimally-sized files. This bin-packing strategy not only reduces the file count but also improves data locality and makes more efficient use of columnar storage formats like Parquet, ultimately leading to faster and more cost-effective queries.

#### 1.1.1. Addressing the "Small File Problem"

The "small file problem" is a common challenge in data lake architectures, particularly those built on object storage like Amazon S3. When data is ingested frequently, especially from streaming sources, it often results in the creation of numerous small files. Each file, even if only a few kilobytes in size, requires a separate I/O operation to open and read, and its metadata must be tracked in the Iceberg manifest files. This leads to a cascade of performance issues. First, the sheer number of files increases the time required for query planning, as the query engine must process a large manifest to understand the table's layout. Second, the I/O overhead of opening and closing thousands of files can dominate the actual data processing time, especially for analytical queries that scan large portions of the table. Third, a high file count can lead to metadata bloat, where the manifest files themselves become large and unwieldy, further slowing down query planning. Compaction directly mitigates these issues by consolidating small files into larger ones, typically targeting a size of **128MB to 512MB**, which is a common sweet spot for balancing parallelism and I/O efficiency in distributed query engines like Spark and Dremio . By reducing the file count, compaction lowers metadata overhead, decreases I/O costs, and simplifies query planning, resulting in significant performance gains.

#### 1.1.2. Spark SQL Procedure for Compaction

Apache Iceberg provides a powerful and user-friendly stored procedure, `rewrite_data_files`, which can be executed directly from Spark SQL to perform compaction. This procedure is the recommended method for managing data file layout in Iceberg tables, as it handles the complexities of file selection, merging, and atomic commit. The procedure works by scanning the table to identify files that are candidates for compaction, typically those smaller than a specified threshold. It then reads the data from these files, combines it, and writes out new, larger files. Finally, it creates a new table snapshot that atomically replaces the old, small files with the newly compacted ones, ensuring that concurrent readers are not impacted. This approach is highly flexible and can be configured to target specific partitions, allowing for incremental compaction of "cold" data without interfering with active writes to "hot" partitions . The ability to execute this procedure via a simple SQL command makes it easy to integrate into automated maintenance workflows orchestrated by tools like Apache Airflow or AWS Step Functions.

The following example demonstrates how to call the `rewrite_data_files` procedure from Spark SQL to compact a table named `dev.default.events`. The `strategy => 'binpack'` option specifies that the procedure should use a bin-packing algorithm to merge small files. The `where` clause is used to filter the partitions that will be compacted, in this case, only targeting partitions for dates prior to the current day. This is a crucial best practice for avoiding conflicts with streaming ingestion jobs that may be writing to the current day's partition . The `options` map allows for further customization, such as setting the target file size and the maximum number of concurrent file group rewrites, which can be tuned to control the resource consumption of the compaction job.

```sql
CALL dev.system.rewrite_data_files(
  table => 'dev.default.events',
  strategy => 'binpack',
  where => 'event_time < current_date()',
  options => map(
      'target-file-size-bytes', '536870912', -- 512 MB
      'max-concurrent-file-group-rewrites', '10'
  )
);
```
*Source: Adapted from  and *

#### 1.1.3. Configuring Target File Size and Compaction Strategy

The effectiveness of a compaction job is heavily influenced by its configuration, particularly the target file size and the chosen compaction strategy. The `target-file-size-bytes` option allows you to specify the desired size for the output files. While the optimal size can vary depending on your specific workload and query engine, a common recommendation is to aim for files in the range of **128MB to 512MB** . Larger files can reduce the number of I/O operations and improve sequential read performance, but they may also reduce the granularity of parallelism. It's important to align this setting with the ideal scan size of your query engine (e.g., Dremio, Spark) to maximize efficiency. For instance, Dremio's `OPTIMIZE` command also allows for bin-packing and sorting strategies, and the choice of target size should be coordinated with Dremio's execution engine characteristics to ensure that reflections and direct queries are optimized .

The `strategy` parameter in the `rewrite_data_files` procedure determines how the files are rewritten. The `binpack` strategy is the most common and is designed to simply merge small files into larger ones without any specific data ordering. This is efficient for reducing file count and metadata overhead. However, for workloads that frequently filter or sort on specific columns, a sort-based compaction strategy can provide additional performance benefits. By sorting the data within the files according to the query patterns, you can improve data locality and make Iceberg's metadata pruning even more effective. For example, if queries often filter on a `customer_id` column, sorting the data by `customer_id` during compaction can allow the query engine to skip entire files or row groups that do not contain the desired customer, leading to significant I/O savings. Dremio's `OPTIMIZE` command explicitly supports a `SORT` option for this purpose, allowing you to specify the columns to sort by . The choice between bin-packing and sorting should be driven by a careful analysis of your query patterns and a cost-benefit analysis of the additional compute resources required for sorting.

### 1.2. Metadata File Optimization (`rewrite_manifests`)

While data file compaction addresses the physical layout of the data, optimizing the metadata layer is equally crucial for maintaining a high-performing Iceberg table. Iceberg's metadata is organized in a hierarchical tree structure, with a manifest list pointing to one or more manifest files, which in turn track the individual data files. This metadata tree acts as an index over the table's data, enabling efficient query planning and data file pruning . However, just like data files, manifest files can become fragmented and inefficient over time. Frequent writes, especially those that do not align with the table's partitioning scheme, can lead to the creation of many small manifest files. This "metadata bloat" can slow down query planning, as the engine needs to open and process a large number of manifests to build a complete picture of the table. The `rewrite_manifests` procedure is designed to address this issue by consolidating small or poorly organized manifest files into a smaller number of optimized ones, thereby speeding up metadata access and improving overall query performance.

#### 1.2.1. Managing Manifest File Overhead

The overhead associated with manifest files can become a significant performance bottleneck if not managed properly. Each manifest file contains metadata about a subset of the table's data files, including their location, partition information, and column-level statistics like min/max values. When a table has a large number of small manifest files, the query planning process becomes more complex and time-consuming. The query engine must read each manifest to determine which data files are relevant to the query, and a high manifest count increases the I/O and processing required for this step. This is particularly problematic for tables with a high write frequency or those that are not partitioned in a way that aligns with the write pattern. For example, if data is written in a random order across different partitions, each write operation may create a new manifest, leading to rapid fragmentation of the metadata layer. The `rewrite_manifests` procedure helps to mitigate this by rewriting the manifests to group data files more logically, for example, by partitioning them or by coalescing small manifests into larger ones. This reduces the number of manifests that need to be scanned during query planning, leading to faster and more efficient query execution .

#### 1.2.2. Spark SQL Procedure for Manifest Rewriting

Similar to data file compaction, Iceberg provides a stored procedure, `rewrite_manifests`, to optimize the manifest files. This procedure can be executed from Spark SQL and is designed to reorganize the metadata layer for better performance. The procedure works by reading the existing manifests, re-grouping the data file entries, and writing out new, optimized manifests. This process can be configured to target specific issues, such as consolidating small manifests or re-grouping data files by partition to align with common query patterns. By rewriting the manifests, you can ensure that the metadata layer remains lean and efficient, even in the face of high-volume or disorganized write operations. This is a crucial maintenance task for long-term table health, as it directly impacts the speed of query planning and the overall user experience.

The following example demonstrates how to use the `rewrite_manifests` action via the Iceberg Java API in a Spark environment. This code snippet shows how to rewrite manifests that are smaller than a specified size (10 MB in this case). This is a common use case for consolidating small, fragmented manifests into larger, more manageable ones. The `rewriteIf` method allows you to specify a predicate to determine which manifests should be rewritten, providing fine-grained control over the optimization process. While this example uses the Java API, the same functionality is often exposed through SQL procedures or other engine-specific commands, such as Dremio's `OPTIMIZE` command, which can also consolidate manifests as part of its table optimization process .

```java
import org.apache.iceberg.Table;
import org.apache.iceberg.spark.actions.SparkActions;
import org.apache.iceberg.relocated.com.google.common.collect.ImmutableList;

// Assuming 'table' is an instance of your Iceberg table
Table table = ...;

SparkActions
    .get()
    .rewriteManifests(table)
    .rewriteIf(file -> file.length() < 10 * 1024 * 1024) // 10 MB
    .execute();
```
*Source: *

### 1.3. Snapshot Lifecycle Management (`expire_snapshots`)

A core feature of Apache Iceberg is its support for time travel, which is enabled by the table's snapshot-based architecture. Every write operation on an Iceberg table creates a new snapshot, which is a point-in-time view of the table's data and metadata. This allows users to query historical versions of the table, roll back to a previous state, or audit changes over time. However, retaining all snapshots indefinitely can lead to significant storage and metadata overhead. Each snapshot references the data files that were active at that time, and as the table evolves, old snapshots can retain references to files that are no longer needed by the current version of the table. This can result in unbounded growth of storage costs and an ever-increasing metadata footprint, which can slow down query planning. Snapshot lifecycle management, primarily through the `expire_snapshots` procedure, is the process of systematically removing old snapshots to reclaim storage space and keep the metadata layer lean.

#### 1.3.1. Controlling Metadata and Storage Bloat

The accumulation of old snapshots is a primary driver of both storage and metadata bloat in an Iceberg table. While time travel is a powerful feature, it is rarely necessary to retain the entire history of a table forever. Most organizations have data retention policies that dictate how long historical data should be kept for compliance, auditing, or analytical purposes. By expiring snapshots that are older than a certain age or retaining only a specific number of recent snapshots, you can significantly reduce the amount of storage consumed by the table. This is because expiring a snapshot allows Iceberg to safely delete any data files that are no longer referenced by any active snapshot. This process not only reclaims storage space on S3 but also simplifies the metadata layer by removing the entries for the expired snapshots. A leaner metadata layer leads to faster query planning and a more responsive system. It is a critical maintenance task for controlling the long-term operational costs of a data lakehouse and ensuring that the system remains performant as it scales.

#### 1.3.2. Spark SQL Procedure for Expiring Snapshots

The `expire_snapshots` procedure is the standard mechanism for managing the lifecycle of snapshots in an Iceberg table. This procedure, which can be executed from Spark SQL, allows you to define a retention policy for your table's history. You can specify the expiration based on the age of the snapshots (e.g., expire all snapshots older than 30 days) or by retaining a specific number of the most recent snapshots. The procedure works by identifying the snapshots that meet the expiration criteria, removing their metadata entries, and then deleting any data files that are no longer referenced by any remaining snapshot. This process is atomic and ensures that no data is deleted that is still needed by an active snapshot. By regularly running the `expire_snapshots` procedure, you can automate the process of cleaning up old data and metadata, ensuring that your table remains efficient and cost-effective over the long term.

The following example shows how to call the `expire_snapshots` procedure from Spark SQL. In this case, the procedure is configured to retain the last 10 snapshots and to expire any snapshots that are older than 7 days. The `older_than` parameter takes a timestamp, allowing for precise control over the retention window. This type of configuration is common in production environments where a balance needs to be struck between the utility of time travel and the cost of storing historical data. By automating this process, you can ensure that your table's history is managed according to your organization's data governance policies without requiring manual intervention.

```sql
CALL catalog_name.system.expire_snapshots(
  table => 'db.table_name',
  retain_last => 10,
  older_than => TIMESTAMP '2025-01-01 00:00:00.000'
);
```
*Source: Adapted from *

#### 1.3.3. Automating with Table Properties

In addition to running the `expire_snapshots` procedure manually or as part of a scheduled job, it is also possible to automate the snapshot expiration process by setting table properties. Iceberg provides a number of table properties that can be used to control the lifecycle of snapshots, such as `history.expire.max-snapshot-age-ms` and `history.expire.min-snapshots-to-keep`. The `history.expire.max-snapshot-age-ms` property specifies the maximum age of a snapshot in milliseconds. Any snapshot that is older than this value will be automatically expired. The `history.expire.min-snapshots-to-keep` property specifies the minimum number of snapshots to retain. These properties can be set when the table is created, or they can be altered later using the `ALTER TABLE` statement. For example, to set the maximum snapshot age to 7 days and the minimum number of snapshots to retain to 10, you can use the following command:

```sql
ALTER TABLE mydb.sales_data SET TBLPROPERTIES (
  'history.expire.max-snapshot-age-ms' = '604800000',
  'history.expire.min-snapshots-to-keep' = '10'
);
```

With these properties set, Iceberg will automatically expire snapshots that are older than 7 days, but it will always retain at least 10 snapshots. This provides a simple and effective way to manage the snapshot lifecycle without the need for external automation.

### 1.4. Orphan File Cleanup (`remove_orphan_files`)

In addition to managing the lifecycle of tracked data and metadata files, it is also important to address the issue of untracked, or "orphan," files. Orphan files are data or metadata files that exist in the table's storage location (e.g., an S3 bucket) but are not referenced by any snapshot in the table's metadata. These files can accumulate for a variety of reasons, such as failed write operations, bugs in the ingestion pipeline, or manual interventions that did not properly clean up after themselves. While orphan files do not impact the correctness of queries (since they are not part of the table's logical state), they do consume storage space and can lead to unnecessary costs. The `remove_orphan_files` procedure is designed to identify and safely delete these untracked files, helping to keep the storage footprint of your table clean and cost-efficient.

#### 1.4.1. Identifying and Removing Untracked Files

The process of identifying orphan files involves comparing the list of files in the table's storage location with the list of files that are referenced in the table's metadata. The `remove_orphan_files` procedure performs this comparison and generates a list of files that are present in storage but not in the metadata. Before deleting these files, it is crucial to ensure that they are truly orphaned and not part of a recent write operation that has not yet been committed. To handle this, the procedure typically includes a safety mechanism, such as a time-based threshold, to only consider files that have not been modified for a certain period (e.g., older than 3 days). This helps to prevent the accidental deletion of files that are part of an in-progress transaction. Once the list of confirmed orphan files is generated, the procedure can safely delete them, reclaiming the associated storage space.

#### 1.4.2. Spark SQL Procedure for Orphan File Removal

The `remove_orphan_files` procedure is exposed as a stored procedure that can be executed from Spark SQL, making it easy to integrate into your regular maintenance workflows. This procedure is a critical tool for ensuring the long-term health and cost-efficiency of your Iceberg tables, as it helps to prevent the silent accumulation of untracked files. By periodically running this procedure, you can automate the process of cleaning up your storage location and ensure that you are not paying for storage that is not being used by your tables. This is particularly important in a cloud environment like AWS, where storage costs are a significant component of the overall operational expenditure.

The following example demonstrates how to call the `remove_orphan_files` procedure from Spark SQL. The `older_than` parameter is used to specify a safety window, ensuring that only files older than a certain timestamp are considered for removal. This is a critical safety feature that helps to prevent the deletion of files that may be part of a recent, uncommitted write operation. By setting this parameter appropriately, you can safely automate the cleanup of orphan files as part of your regular maintenance schedule.

```sql
CALL catalog_name.system.remove_orphan_files(
  table => 'db.table_name',
  older_than => TIMESTAMP '2025-01-01 00:00:00.000'
);
```
*Source: Adapted from *

## 2. Query Performance Optimization: Partitioning and Pruning

Optimizing query performance is a cornerstone of a successful data platform, and Apache Iceberg provides a powerful suite of features to achieve this. At the heart of Iceberg's performance model are partitioning and pruning, which work in tandem to minimize the amount of data that needs to be scanned for any given query. Partitioning is the process of organizing data into distinct, non-overlapping subsets based on the values of one or more columns. This allows a query engine to quickly identify and skip entire partitions that are not relevant to a query's filter criteria. Pruning is the broader mechanism by which Iceberg uses metadata to eliminate data files from a query's scan plan. This includes not only partition-based pruning but also file-level pruning based on column statistics stored in the manifest files. By designing effective partitioning strategies and leveraging Iceberg's advanced pruning capabilities, you can dramatically reduce query execution times and lower the computational cost of your analytics workloads.

### 2.1. Designing Effective Partitioning Strategies

The design of a table's partitioning scheme is one of the most critical decisions you will make when creating an Iceberg table, as it has a profound and lasting impact on query performance. A well-designed partitioning strategy can enable massive performance gains by allowing the query engine to skip vast amounts of irrelevant data. Conversely, a poorly designed partitioning scheme can lead to a proliferation of small files, metadata bloat, and minimal performance benefits. The key to designing an effective partitioning strategy is to have a deep understanding of your data and, more importantly, your query patterns. The goal is to partition the data in a way that aligns with the most common and selective filters used in your queries. This requires a careful balance between query performance and the practical considerations of file management, such as avoiding partitions that are too small or too large.

#### 2.1.1. Selecting High-Cardinality Filter Columns

The first step in designing a partitioning strategy is to identify the columns that are most frequently used in the `WHERE` clauses of your queries. These are the columns that offer the most potential for data pruning. However, not all filter columns are good candidates for partitioning. The ideal partitioning column has a high degree of selectivity, meaning that it can effectively divide the data into distinct and reasonably sized partitions. For example, a `timestamp` or `date` column is often an excellent choice for partitioning, especially for time-series data, as queries are frequently filtered by a specific time range. A column with a very low cardinality (i.e., a small number of unique values, such as a `status` column with only "active" and "inactive" values) is generally a poor choice for partitioning, as it will result in a small number of very large partitions, limiting the effectiveness of partition pruning. In some cases, a column with a very high cardinality (e.g., a `user_id` column with millions of unique values) can also be problematic, as it can lead to an explosion in the number of partitions, resulting in the "small file problem" and excessive metadata overhead. In such cases, it may be more effective to use a transformation, such as bucketing or truncation, to create a more manageable number of partitions.

#### 2.1.2. Balancing Query Performance and File Management

A successful partitioning strategy requires a delicate balance between optimizing for query performance and managing the practical implications of file and partition management. While a highly granular partitioning scheme (e.g., partitioning by hour instead of by day) can offer better query performance for time-based filters, it also increases the number of partitions and the potential for creating many small files. This can lead to metadata bloat and slower query planning, as the engine has to process a larger number of manifests. Therefore, it is important to choose a partitioning granularity that is appropriate for your data volume and query patterns. A good rule of thumb is to aim for partitions that are large enough to contain a reasonable number of files (e.g., at least a few hundred megabytes to a few gigabytes of data) but not so large that they cannot be effectively pruned. Regular monitoring of partition sizes and file counts is essential to ensure that your partitioning strategy remains effective as your data grows. If you find that your partitions are becoming too small or too numerous, it may be time to evolve your partitioning scheme to a coarser granularity.

#### 2.1.3. Utilizing Hidden Partitioning for Flexibility

One of the most innovative features of Apache Iceberg is its support for "hidden partitioning." In traditional table formats like Hive, the partition structure is exposed to the user, and queries must include the partition columns in the `WHERE` clause to enable pruning. This can be cumbersome and error-prone. With Iceberg's hidden partitioning, the partition structure is managed internally by the table's metadata. Users can query the table using the original column names (e.g., `event_time`), and Iceberg will automatically apply the partition transform (e.g., `day(event_time)`) to enable pruning. This makes queries simpler and more intuitive, and it also provides more flexibility in how the data is partitioned. For example, you can change the partition transform from `day(event_time)` to `month(event_time)` without having to rewrite the data or change your queries. This is a powerful feature that makes it easier to manage and optimize your tables over the long term .

### 2.2. Partition Evolution for Long-Term Adaptability

A key feature of Apache Iceberg that distinguishes it from older table formats like Hive is its support for **partition evolution**. This capability allows for the modification of a table's partitioning scheme over time without requiring a costly and disruptive full table rewrite . As data volumes and query patterns evolve, the initial partitioning strategy may become suboptimal. For instance, a table initially partitioned by `month(ts)` might become too large for efficient querying, necessitating a change to `day(ts)` or even `hour(ts)`. Iceberg's partition evolution handles this by treating the change as a metadata operation. When a partition spec is updated, a new spec is created and set as the default for future writes, while existing data files remain untouched in their original partition layout . This non-destructive approach ensures that historical data is preserved and remains queryable, while new data is organized according to the more efficient, updated scheme. This flexibility is crucial for long-term data platform evolution, as it allows for continuous optimization of table layout in response to changing analytical needs without incurring significant downtime or operational overhead.

The mechanism behind partition evolution is managed through Iceberg's metadata layer. Each snapshot of the table can reference a different partition spec. When a query is executed, Iceberg's query planner intelligently handles the different partition layouts. It uses "split planning," where it creates separate query plans for data written under each distinct partition spec . For each set of files, the planner derives the appropriate partition filter based on the spec that was active when those files were written. This process is entirely transparent to the end-user, who can continue to write standard SQL queries filtering on the source column (e.g., `WHERE ts > '2025-01-01'`), and Iceberg will automatically prune files from all partition layouts accordingly. This is a direct consequence of Iceberg's "hidden partitioning" design, which abstracts the physical partition structure from the logical query, allowing the physical layout to evolve independently . This ensures that even after evolving the partition strategy, queries remain efficient and correct across the entire dataset, both old and new.

#### 2.2.1. Evolving Partition Schemas with `ALTER TABLE`

In environments using Spark 3.4 with the Iceberg 1.3.0 runtime, partition evolution is primarily managed through Spark SQL extensions, which provide a set of `ALTER TABLE` commands specifically for this purpose. These commands allow for adding, dropping, and replacing partition fields in a declarative manner, making the process accessible and easy to integrate into data pipeline workflows . The core commands are `ADD PARTITION FIELD`, `DROP PARTITION FIELD`, and `REPLACE PARTITION FIELD`. These operations are metadata-only and do not trigger a rewrite of existing data files, making them lightweight and fast. For example, to add a new partition field, one can use the `ADD PARTITION FIELD` clause. This is particularly useful when a new column is added to the schema and it becomes a key filtering criterion for queries. By adding it as a partition field, future data writes will be organized by this new column, improving the performance of queries that filter on it.

The syntax for these commands is designed to be intuitive for those familiar with SQL. For instance, to add a new identity partition on a column named `category`, the command would be `ALTER TABLE prod.db.sample ADD PARTITION FIELD category;` . More complex transformations, such as bucketing or time-based partitioning, are also supported. For example, to partition by day from a timestamp column `ts`, the command is `ALTER TABLE prod.db.sample ADD PARTITION FIELD day(ts);` . This flexibility allows for sophisticated partitioning strategies to be implemented and modified as needed. It is important to note that these commands are part of the Iceberg SQL extensions and require the `iceberg-spark-extensions` JAR to be available in the Spark environment, which is confirmed to be part of the specified setup. This direct SQL support empowers data engineers and analysts to manage table partitioning directly from their SQL clients or notebooks, streamlining the process of adapting the data lake to new requirements.

##### 2.2.1.1. Adding New Partition Fields

The `ALTER TABLE ... ADD PARTITION FIELD` command is used to introduce a new partitioning criterion to a table. This operation is essential for adapting to new query patterns or incorporating new columns into the table's organization strategy. When a new partition field is added, it only affects data written after the change; existing data files remain in their original locations and are not reorganized . This is a critical aspect of Iceberg's non-destructive evolution model. For example, if a new column `region` is added to a `sales` table and queries frequently filter by this column, adding it as a partition field will significantly improve the performance of those queries for all future data. The command can be used with various partition transforms, including identity, bucket, truncate, and time-based functions like `year`, `month`, `day`, and `hour` .

The following table provides examples of adding partition fields using different transforms, which are supported in the specified Spark 3.4 and Iceberg 1.3.0 environment :

| Operation | Spark SQL Command | Description |
| :--- | :--- | :--- |
| **Add Identity Partition** | `ALTER TABLE prod.db.sample ADD PARTITION FIELD category;` | Creates a partition based on the distinct values in the `category` column. |
| **Add Bucket Partition** | `ALTER TABLE prod.db.sample ADD PARTITION FIELD bucket(16, id);` | Hashes the `id` column and partitions the data into 16 buckets. This is useful for high-cardinality columns to avoid creating too many small partitions. |
| **Add Truncate Partition** | `ALTER TABLE prod.db.sample ADD PARTITION FIELD truncate(4, data);` | Truncates the string values in the `data` column to the first 4 characters and partitions by these truncated values. |
| **Add Time-Based Partition** | `ALTER TABLE prod.db.sample ADD PARTITION FIELD year(ts);` | Extracts the year from the `ts` timestamp column and partitions the data by year. Other supported functions include `month(ts)`, `day(ts)`, and `hour(ts)`. |
| **Add with Custom Name** | `ALTER TABLE prod.db.sample ADD PARTITION FIELD bucket(16, id) AS shard;` | Adds a bucket partition on the `id` column but names the partition field `shard` in the metadata. This can be useful for providing more descriptive names in metadata queries. |

It is crucial to understand the implications of adding a new partition field, especially concerning dynamic partition overwrites. When the partitioning scheme changes, the behavior of `INSERT OVERWRITE` operations that rely on dynamic partitioning will also change. For example, if a table was previously partitioned by `day(ts)` and is changed to `hour(ts)`, an `INSERT OVERWRITE` will now overwrite individual hourly partitions rather than daily ones . This can lead to unexpected results if not managed carefully. To maintain control, it is recommended to use explicit overwrites or the `DataFrameWriterV2` API for more complex write operations after evolving the partition spec.

##### 2.2.1.2. Dropping Existing Partition Fields

The `ALTER TABLE ... DROP PARTITION FIELD` command allows for the removal of a partition criterion from a table's partitioning scheme. This is useful when a particular partition field is no longer beneficial for query performance or is causing an excessive number of small partitions. Similar to adding a field, dropping a partition field is a metadata-only operation and does not physically move or rewrite any existing data files . The data that was previously organized by the dropped partition field remains in its original directory structure, but new data will be written according to the new, simplified partition spec. It is important to note that dropping a partition field does not delete the column from the table's schema; it only removes it from the partitioning logic. The column remains available for querying and can be re-added as a partition field later if needed.

The command requires specifying the exact partition field to be dropped, including its transform if it is not an identity partition. For example, to drop an identity partition on the `category` column, the command would be `ALTER TABLE prod.db.sample DROP PARTITION FIELD category;` . If the partition was created with a transform, such as `bucket(16, id)`, the same transform must be specified in the `DROP` command: `ALTER TABLE prod.db.sample DROP PARTITION FIELD bucket(16, id);` . If a custom name was used when the partition was added (e.g., `AS shard`), the custom name should be used to drop it: `ALTER TABLE prod.db.sample DROP PARTITION FIELD shard;` . A significant consideration when dropping a partition field is its impact on metadata tables. The schema of metadata tables, such as `files`, includes a column for each partition field. Dropping a field will remove that column from the schema of new snapshots, which could cause existing queries against these metadata tables to fail or produce different results . Therefore, it is essential to audit any downstream processes or dashboards that rely on the structure of these metadata tables before dropping a partition field.

##### 2.2.1.3. Replacing Partition Fields

The `ALTER TABLE ... REPLACE PARTITION FIELD` command provides a powerful way to atomically change a partition field from one transform to another. This is particularly useful for scenarios like changing the granularity of time-based partitioning, such as moving from daily (`day(ts)`) to hourly (`hour(ts)`) partitions, or changing the number of buckets in a hash partition. The `REPLACE` command combines the `DROP` and `ADD` operations into a single, atomic metadata update, which is safer and more efficient than executing the two commands separately . This ensures that there is no intermediate state where the partition spec is incomplete or inconsistent. For example, to change a partition from `month(ts)` to `day(ts)`, the command would be `ALTER TABLE prod.db.sample REPLACE PARTITION FIELD month(ts) WITH day(ts);` .

This operation is non-destructive, meaning it does not rewrite existing data. Data written under the old partition spec (e.g., `month(ts)`) remains in place, while all new data will be written using the new spec (e.g., `day(ts)`) . This allows for a seamless transition, where the table can be queried efficiently across both old and new data layouts. As with other partition evolution commands, the `REPLACE` operation can also be used to specify a custom name for the new partition field using the `AS` keyword. For instance, `ALTER TABLE prod.db.sample REPLACE PARTITION FIELD ts_day WITH day(ts) AS day_of_ts;` would replace the old `ts_day` partition field with a new one based on `day(ts)` but named `day_of_ts` in the metadata . This atomic replacement is a key feature for maintaining data platform agility, as it allows for the continuous refinement of partitioning strategies to match evolving data and query characteristics without the need for complex and resource-intensive table rewrites.

#### 2.2.2. Non-Destructive Partition Changes

The fundamental principle behind Iceberg's partition evolution is that it is a **non-destructive** process. This means that when the partitioning scheme of a table is altered, the existing data files on storage (e.g., S3) are not moved, renamed, or rewritten . Instead, Iceberg creates a new partition specification in the table's metadata and applies it only to new data that is written to the table from that point forward. This approach has several significant advantages. First, it makes the evolution process extremely fast, as it only involves a metadata update rather than a massive data movement operation. Second, it preserves the history of the table, which is essential for time-travel queries. Because the old data files remain in their original locations, it is possible to query the table as it existed at any point in its history, using the partition spec that was active at that time .

This non-destructive nature is a stark contrast to traditional data lake architectures, such as those based on the Hive table format, where changing the partitioning scheme typically required creating a new table and migrating all the data, a process that is both time-consuming and error-prone. With Iceberg, the old and new partitioning schemes coexist harmoniously within the same table. The Iceberg query planner is intelligent enough to handle this hybrid layout. During query execution, it will use the appropriate partition spec for each set of data files to perform partition pruning, ensuring that queries are optimized regardless of which partitioning scheme the data was written under . This capability provides immense flexibility for data platform teams, allowing them to adapt their data layout to changing requirements over time without being locked into an initial design or facing prohibitive costs for making changes. It is a cornerstone of Iceberg's design for building robust, scalable, and maintainable data lakes.

#### 2.2.3. Impact on Existing Data and New Writes

When a partition spec is evolved in an Iceberg table, the impact is clearly delineated between existing data and new writes. **Existing data files**, which were written under the previous partition spec, are completely unaffected by the change. They remain in their original directory structure on S3, and their associated metadata in the manifests continues to reference the old partition values . This ensures that historical data is not altered and remains accessible for time-travel queries. When a query is executed that scans this older data, Iceberg's planner uses the old partition spec to understand the data layout and perform partition pruning correctly. This backward compatibility is a critical feature, as it guarantees that evolving the partition scheme will not break existing queries or data pipelines that may depend on the historical state of the table.

In contrast, **all new data written to the table** after the partition evolution will be organized according to the new, updated partition spec . Any `INSERT`, `UPDATE`, or `MERGE` operations will use the new partitioning logic to determine the directory structure for the new data files. This means that over time, the table will naturally become a hybrid, containing data files organized under multiple different partition specs. This is a normal and expected state for an evolving Iceberg table. The Iceberg query planner is designed to handle this hybrid state seamlessly. It will create a separate query plan for each partition spec present in the snapshot being queried, applying the correct partition filters for each set of files . This ensures that queries are always optimized, regardless of the age of the data being scanned. This clear separation of concerns between old and new data allows for a smooth and continuous evolution of the table's physical layout without any disruption to ongoing data processing or analytical workloads.

### 2.3. Maximizing Pruning Efficiency

While partitioning is a powerful tool for reducing the amount of data scanned by a query, its effectiveness can be further enhanced by maximizing the efficiency of data pruning. Pruning is the process of eliminating data files from a query's scan based on the query's filter predicates. In addition to partition pruning, which skips entire partitions, Iceberg supports file-level pruning, which skips individual data files within a partition. This is made possible by the rich metadata that Iceberg stores in its manifest files. Each manifest file contains detailed column-level statistics for every data file it tracks, including the minimum and maximum values, the number of null values, and the total number of records. When a query is executed, the query engine can use this information to determine whether a particular data file could possibly contain any records that match the query's filter. If the file's statistics indicate that it cannot contain any matching records, the file can be safely skipped, even if it is in a partition that is relevant to the query. This can lead to significant performance gains, especially for queries with highly selective filters.

#### 2.3.1. Leveraging Min/Max Statistics in Manifests

The min/max statistics stored in Iceberg's manifest files are a key enabler of efficient file-level pruning. For each column in a data file, Iceberg tracks the minimum and maximum values. When a query includes a filter on a column, the query engine can compare the filter value to the min/max range for that column in each data file. If the filter value falls outside the min/max range, the file can be pruned from the scan. For example, consider a query that filters for `customer_id = 12345`. If a data file has a min/max range for `customer_id` of `10000` to `20000`, the file can be safely skipped, as it cannot contain the value `12345`. This is a powerful optimization that can significantly reduce the amount of data that needs to be read from storage. The effectiveness of this technique depends on the data being well-clustered within the files. If the data is randomly distributed, the min/max ranges will be wide, and the pruning will be less effective. This is why sort-based compaction can be so beneficial, as it co-locates related data, resulting in tighter min/max ranges and more effective file pruning.

#### 2.3.2. Predicate Pushdown and Dynamic Partition Pruning

In addition to file-level pruning, Iceberg also supports more advanced pruning techniques, such as predicate pushdown and dynamic partition pruning. Predicate pushdown is the process of pushing filter predicates as close to the data source as possible. In the context of Iceberg, this means that the query engine will use the filter predicates to prune files and partitions before reading the data. This is a standard optimization in most modern query engines, and Iceberg's rich metadata makes it particularly effective. Dynamic partition pruning is a more advanced technique that is used when a query joins a large fact table with a smaller dimension table. If the query filters the dimension table, the filter can be dynamically applied to the fact table, pruning partitions that are not needed for the join. This can lead to significant performance gains, as it avoids scanning large portions of the fact table that are not relevant to the query. Iceberg's support for these advanced pruning techniques, combined with its rich metadata, makes it a highly efficient format for large-scale analytical workloads.

## 3. Schema Evolution and Compatibility

Apache Iceberg provides robust support for **schema evolution**, allowing table schemas to be modified over time without requiring expensive and disruptive data rewrites . This is a critical capability for modern data platforms, where business requirements and data sources are constantly changing. Iceberg's approach to schema evolution is based on a metadata-driven model that ensures changes are safe, correct, and backward-compatible. The system uses unique, stable column IDs to track each column in a table, rather than relying on column names or positions . This fundamental design choice is what enables safe evolution. When a new column is added, it is assigned a new, unique ID, ensuring that it will never be confused with existing data. Similarly, when a column is renamed or dropped, the underlying data is not touched; only the table's metadata schema is updated.

This approach guarantees that schema changes are **independent and free of side-effects** . For example, adding a new column will never cause existing values in other columns to be read or modified. Dropping a column does not affect the values in any other column. This is a significant improvement over older systems where such changes could lead to data corruption or correctness issues. Iceberg supports a wide range of schema evolution operations, including adding, dropping, renaming, and reordering columns, as well as widening the data types of existing columns (e.g., from `int` to `bigint`) . All of these operations are implemented as metadata changes, making them fast and efficient. This flexibility allows data teams to adapt their tables to new requirements with confidence, knowing that the integrity of their existing data will be preserved and that downstream applications will continue to function correctly.

### 3.1. Backward and Forward Compatibility Principles

Iceberg's schema evolution is designed to maintain both **backward and forward compatibility**. Backward compatibility ensures that new versions of the table schema can read data written with older schemas. This is achieved through the use of column IDs. When a data file is read, Iceberg uses the column IDs stored in the file's footer to map the data to the current table schema. If a column in the current schema does not exist in the data file (i.e., it was added after the file was written), Iceberg will simply return a `null` value for that column . This allows queries to run seamlessly across data files with different schemas. Forward compatibility, while less commonly a concern in analytical systems, is also supported to a degree. Iceberg can read data files that have columns which have since been dropped from the table schema, ignoring the dropped columns during the read process.

The principles of safe evolution are enforced by the Iceberg specification. For instance, **safe type promotions** are explicitly defined. It is safe to promote an `int` to a `bigint`, or a `float` to a `double`, but not the other way around, as that could lead to data loss or precision errors . Similarly, a `decimal(P, S)` can be widened to `decimal(P2, S)` where `P2 > P`, but the scale `S` cannot be changed . These rules ensure that data integrity is maintained throughout the evolution process. The use of column IDs also prevents issues that can arise from reusing column names. In systems that track columns by name, reusing the name of a previously dropped column could lead to "un-deleting" the old data, a problem that Iceberg's ID-based system inherently avoids . This robust framework for compatibility provides a solid foundation for building reliable and long-lived data lakes that can adapt to changing business needs over time.

#### 3.1.1. Safe Column Additions, Renames, and Drops

Iceberg provides a set of well-defined, safe operations for modifying the columns in a table. These operations are designed to be metadata-only, ensuring that the underlying data files are not rewritten, which makes them fast and efficient. The primary operations are adding, renaming, and dropping columns.

**Adding a new column** is a completely safe operation. When a new column is added to the table schema, it is assigned a unique, new column ID . Existing data files, which were written before this column existed, will not contain any data for this new column. When these old files are read by a query that references the new column, Iceberg will correctly return `null` values for that column, ensuring that the query executes without error and produces the expected results. This allows for the seamless introduction of new data points into the table without affecting historical data or requiring a backfill.

**Renaming a column** is also a safe and straightforward operation. When a column is renamed, its underlying column ID remains unchanged . Only the name associated with that ID in the table's metadata schema is updated. This means that all existing data files, which store data mapped to the column ID, remain perfectly valid. Queries can immediately use the new column name, and Iceberg will correctly map it to the data in the files. This is a significant advantage over systems that track columns by name, where renaming a column can be a complex and risky operation.

**Dropping a column** is handled by removing the column from the current table schema. The column's ID is not reused, and the data for that column in existing files is simply ignored during reads . This ensures that dropping a column does not have any unintended side effects on other columns or the overall structure of the data. It is a clean and safe way to remove obsolete or sensitive data fields from the table's logical schema. The combination of these safe operations provides a powerful and flexible toolkit for managing the evolution of table schemas over time.

#### 3.1.2. Type Promotion and Widening

Iceberg supports a specific set of **type promotion** rules that allow for the safe widening of column data types. This is a crucial aspect of schema evolution, as it enables tables to accommodate growing data ranges or increased precision requirements without breaking existing data. These promotions are considered "safe" because they do not result in the loss of data or precision. The supported type promotions are explicitly defined in the Iceberg specification and are enforced by the engine .

The following table summarizes the safe type promotions available in Iceberg, which are applicable to the Spark 3.4 and Iceberg 1.3.0 environment :

| Original Type | Promoted Type | Description |
| :--- | :--- | :--- |
| `int` | `bigint` | Widening a 32-bit integer to a 64-bit integer. This allows the column to store much larger values without risk of overflow. |
| `float` | `double` | Increasing the precision of a floating-point number from 32-bit to 64-bit. This reduces the potential for rounding errors in calculations. |
| `decimal(P, S)` | `decimal(P2, S)` | Increasing the precision (`P`) of a decimal number, while keeping the scale (`S`) constant. This allows for storing numbers with more digits before the decimal point. |

It is important to note that not all type changes are allowed. For example, it is not possible to promote a `string` to an `int`, or a `bigint` to an `int`, as these conversions could result in data loss or errors. The Iceberg engine will reject any `ALTER TABLE` command that attempts an unsafe type change. Furthermore, there are restrictions on type promotion for columns that are used as the source for partition fields. If a type promotion would cause the partition transform to produce a different result (e.g., promoting an `int` to a `string` for a `bucket` transform, which would change the hash value), the promotion is not allowed . This ensures that the integrity of the partitioning scheme is maintained even as the schema evolves. These carefully defined rules provide a safe and predictable framework for adapting the data types of columns to meet the changing needs of the business.

### 3.2. Implementing Schema Changes with Spark SQL

In the specified environment of Spark 3.4 and Iceberg 1.3.0, schema evolution is implemented using a rich set of `ALTER TABLE` SQL commands. These commands provide a declarative and user-friendly way to modify table schemas without writing any custom code. The Iceberg Spark extensions add support for a comprehensive range of schema modification operations, including adding, renaming, dropping, and altering the type of columns, as well as managing nested fields within structs, maps, and arrays. This SQL-based approach makes schema evolution accessible to a wider range of users, including data analysts and data scientists who may not be proficient in programming languages like Scala or Java. By leveraging these SQL commands, data teams can manage the evolution of their tables in a consistent and reproducible manner, ensuring that the data platform remains agile and responsive to changing business needs.

#### 3.2.1. `ALTER TABLE ... ADD COLUMN`

The `ALTER TABLE ... ADD COLUMN` command is used to add a new column to an existing table. This is one of the most common schema evolution operations, as it allows for the introduction of new data points into the table without disrupting existing data. The command is straightforward to use and can be combined with various options to specify the column's data type, whether it is nullable, and any default values. For example, to add a new string column named `customer_segment` to a `sales` table, the command would be:

```sql
ALTER TABLE sales ADD COLUMN customer_segment STRING;
```

This command will add the new column to the table's schema. As discussed earlier, this is a safe operation that will not affect existing data files. When old data files are queried, the new column will simply return `null` values. This allows for a seamless transition, where new data can be written with the new column, while old data remains accessible without any changes.

#### 3.2.2. `ALTER TABLE ... RENAME COLUMN`

The `ALTER TABLE ... RENAME COLUMN` command is used to change the name of an existing column. This is a useful operation for correcting naming inconsistencies, improving clarity, or aligning the schema with new business terminology. The command is simple to use and does not require any data to be rewritten. For example, to rename the `customer_segment` column to `customer_tier`, the command would be:

```sql
ALTER TABLE sales RENAME COLUMN customer_segment TO customer_tier;
```

This command will update the column name in the table's metadata. All existing queries and data pipelines that reference the old column name will need to be updated to use the new name. However, the underlying data remains unchanged, and the operation is performed instantly as a metadata-only change.

#### 3.2.3. `ALTER TABLE ... DROP COLUMN`

The `ALTER TABLE ... DROP COLUMN` command is used to remove a column from the table's schema. This is a useful operation for cleaning up obsolete or unused columns, which can help to simplify the schema and reduce confusion. The command is safe and does not delete any data from the underlying files. For example, to drop the `customer_tier` column, the command would be:

```sql
ALTER TABLE sales DROP COLUMN customer_tier;
```

This command will remove the column from the table's schema. The data for this column in existing files will be ignored during reads. It is important to note that this operation is irreversible, so it should be used with caution. It is a good practice to first check if the column is being used by any downstream applications before dropping it.

### 3.3. Coordinating Schema Changes with Dremio Reflections

When using Dremio as a query engine on top of Iceberg tables, it is important to consider the impact of schema evolution on Dremio's reflections. Reflections are pre-computed, materialized views that Dremio uses to accelerate query performance. When the schema of an underlying Iceberg table changes, the reflections that are based on that table may become invalid or outdated. This can lead to query failures or incorrect results if the reflections are not properly refreshed. Therefore, it is crucial to have a strategy for coordinating schema changes with the management of Dremio reflections.

#### 3.3.1. Impact of Schema Evolution on Reflections

Schema evolution can have a significant impact on Dremio reflections. When a column is added, dropped, or renamed in an Iceberg table, any reflections that include that column will need to be updated. If a column is added, the reflection will not include the new column until it is refreshed. If a column is dropped, the reflection will become invalid, as it will be referencing a column that no longer exists. If a column is renamed, the reflection will also become invalid, as it will be referencing the old column name. In all of these cases, it is necessary to refresh the reflection to ensure that it is consistent with the underlying table.

#### 3.3.2. Best Practices for Refreshing Reflections

To ensure that Dremio reflections remain consistent with the underlying Iceberg tables, it is a best practice to refresh the reflections after any schema changes are made. This can be done manually through the Dremio UI or programmatically using the Dremio REST API. For automated workflows, it is recommended to integrate the reflection refresh into the data pipeline that performs the schema evolution. For example, after running an `ALTER TABLE` command to add a new column, the pipeline can trigger a refresh of the relevant reflections. This ensures that the reflections are always up-to-date and that queries will continue to perform well. It is also a good practice to monitor the status of reflections and to set up alerts for any reflections that become invalid. This can help to quickly identify and resolve any issues that may arise from schema evolution.

## 4. Foundational Best Practices for Table Design and Management

Beyond the core maintenance operations, establishing a set of foundational best practices for table design and management is crucial for the long-term success of a data platform built on Apache Iceberg. These practices provide a framework for creating tables that are not only performant and cost-effective but also easy to manage and evolve over time. This includes setting sensible defaults for table properties, optimizing for the specific characteristics of the underlying storage system (in this case, S3), and implementing a robust strategy for automation and monitoring. By adopting these best practices from the outset, data teams can avoid common pitfalls and ensure that their Iceberg tables remain a valuable asset for the organization as the data platform grows and matures.

### 4.1. Establishing Table Design Guidelines

Creating a set of standardized table design guidelines is a critical first step in building a maintainable data platform. These guidelines should cover key aspects of table creation, such as setting appropriate target file sizes, configuring metadata retention policies, and enabling automatic cleanup of old metadata files. By establishing these standards, data teams can ensure that all tables are created with a consistent and optimized configuration, which simplifies management and reduces the risk of performance issues down the line. These guidelines should be documented and shared with all data engineers and analysts who are responsible for creating and managing tables, ensuring that everyone is following the same best practices.

#### 4.1.1. Setting Target File Sizes (`write.target-file-size-bytes`)

One of the most important table properties to set is the target file size. This property, `write.target-file-size-bytes`, determines the desired size of the data files that are written to the table. As discussed earlier, a good target file size is typically in the range of **128MB to 512MB**, as this provides a good balance between query performance and write efficiency. By setting this property at the table level, you can ensure that all new data files are written to an optimal size, which reduces the need for frequent compaction jobs. This can be set when the table is created or altered at any time. For example:

```sql
CREATE TABLE mydb.sales_data (
  id BIGINT,
  amount DECIMAL(10, 2),
  sale_date DATE
) USING iceberg
TBLPROPERTIES ('write.target-file-size-bytes' = '268435456'); -- 256MB
```

#### 4.1.2. Configuring Metadata Retention (`write.metadata.previous-versions-max`)

Another important table property is `write.metadata.previous-versions-max`, which controls the number of previous metadata files to retain. Each commit to an Iceberg table creates a new metadata file, and retaining too many of these files can lead to metadata bloat. By setting this property, you can limit the number of metadata files that are kept, which helps to keep the metadata layer lean and efficient. A common recommendation is to retain a reasonable number of versions, such as 10 or 20, to allow for debugging and auditing without consuming excessive storage. For example:

```sql
ALTER TABLE mydb.sales_data SET TBLPROPERTIES ('write.metadata.previous-versions-max' = '10');
```

#### 4.1.3. Enabling Automatic Metadata Cleanup (`write.metadata.delete-after-commit.enabled`)

To further automate the management of metadata files, you can enable the `write.metadata.delete-after-commit.enabled` property. When this property is set to `true`, Iceberg will automatically delete old metadata files after each new commit. This ensures that the number of metadata files is kept in check, even for tables with very frequent commits. This is a simple and effective way to prevent metadata bloat without the need for manual intervention. For example:

```sql
ALTER TABLE mydb.sales_data SET TBLPROPERTIES ('write.metadata.delete-after-commit.enabled' = 'true');
```

### 4.2. S3-Specific Optimizations

When using Amazon S3 as the storage backend for Iceberg tables, there are a number of specific optimizations that can be made to improve performance and reduce costs. S3 has some unique characteristics, such as request rate limits and a flat namespace, that can impact the performance of a data lakehouse. By understanding these characteristics and configuring Iceberg accordingly, you can ensure that your tables are optimized for the S3 environment.

#### 4.2.1. Mitigating S3 Request Rate Limits

Amazon S3 has a default request rate limit of **3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second per prefix**. While this is a high limit, it can be a bottleneck for very large and busy data platforms. To mitigate this, it is important to design your data layout to distribute the request load across multiple prefixes. This can be achieved by using a hash-based prefix for your data files, which is discussed in the next section. It is also important to monitor your S3 request rates and to request a limit increase from AWS if necessary.

#### 4.2.2. Using `ObjectStoreLocationProvider` for Hash-Based Prefixes

To help distribute the request load across multiple prefixes, Iceberg provides the `ObjectStoreLocationProvider`. This location provider automatically adds a hash-based prefix to the path of your data files, which helps to distribute the files across multiple S3 prefixes. This can significantly improve performance and reduce the risk of hitting S3's request rate limits. To use the `ObjectStoreLocationProvider`, you can set the `write.object-storage.enabled` table property to `true`. For example:

```sql
ALTER TABLE mydb.sales_data SET TBLPROPERTIES ('write.object-storage.enabled' = 'true');
```

### 4.3. Automation and Monitoring

To ensure that your Iceberg tables remain healthy and performant over the long term, it is essential to have a robust strategy for automation and monitoring. This includes scheduling regular maintenance tasks, monitoring key metrics, and balancing the costs of maintenance with the performance gains. By automating the maintenance process, you can ensure that it is performed consistently and reliably, without relying on manual intervention. By monitoring key metrics, you can proactively identify and address any issues that may arise, before they impact query performance.

#### 4.3.1. Scheduling Maintenance Tasks with Orchestration Tools

The core maintenance operations, such as compaction, snapshot expiration, and manifest rewriting, should be automated using an orchestration tool like Apache Airflow, AWS Step Functions, or a similar tool. This allows you to schedule these tasks to run on a regular basis, such as daily or weekly, ensuring that your tables are always in an optimal state. The orchestration tool can be configured to run the Spark SQL procedures for each of these tasks, and it can also be used to manage dependencies and handle failures. By automating the maintenance process, you can free up your data engineers to focus on more strategic tasks, while ensuring that your data platform remains healthy and performant.

#### 4.3.2. Monitoring Key Metrics: File Counts, Snapshot Growth, Query Performance

To proactively manage the health of your Iceberg tables, it is important to monitor a set of key metrics. This includes the number of files in the table, the number of snapshots, and query performance. A high file count can be an indicator of the "small file problem," while a high snapshot count can indicate that snapshot expiration is not running frequently enough. Query performance can be monitored by tracking metrics such as query execution time and the amount of data scanned. By monitoring these metrics, you can identify trends and potential issues, and you can use this information to tune your maintenance schedules and table configurations.

#### 4.3.3. Balancing Maintenance Costs and Performance Gains

While regular maintenance is essential for a healthy data platform, it is also important to balance the costs of maintenance with the performance gains. Maintenance tasks like compaction can be resource-intensive, and running them too frequently can lead to high compute costs. It is important to find a balance that provides a good return on investment. This may involve tuning the frequency of maintenance tasks, or using more targeted approaches, such as compacting only the partitions that are most in need of optimization. By carefully monitoring the costs and benefits of your maintenance strategy, you can ensure that you are getting the most value from your data platform.

## 5. Understanding "Contraction Pruning" in the Iceberg Ecosystem

The term "contraction pruning" is not a standard, formally defined term within the Apache Iceberg community or documentation. However, based on the context of your research, it can be understood as a conceptual framework that combines two of the most critical aspects of long-term Iceberg table management: **"contraction"** of the table's physical and metadata footprint, and **"pruning"** of data during query execution. This framework provides a holistic view of how to maintain a lean, efficient, and high-performing data lakehouse. "Contraction" refers to the set of maintenance operations designed to reduce the table's footprint, such as data file compaction, metadata optimization, and snapshot lifecycle management. "Pruning" refers to the query optimization techniques that leverage the table's metadata to skip irrelevant data files, such as partition pruning and file-level pruning based on column statistics. By understanding how these two concepts are related and how they have evolved, you can develop a more effective and comprehensive maintenance strategy for your Iceberg tables.

### 5.1. Deconstructing the Term: Contraction and Pruning

To fully appreciate the "contraction pruning" framework, it is helpful to deconstruct the two core concepts and understand their individual roles in the data platform ecosystem. While they are distinct concepts, they are deeply intertwined, and the effectiveness of one often depends on the proper implementation of the other. A well-maintained table (good contraction) enables more effective query optimization (good pruning), and a well-designed query optimization strategy (good pruning) can inform the priorities for table maintenance (contraction).

#### 5.1.1. "Contraction" as Table and Metadata Footprint Reduction

In the context of Iceberg table maintenance, **"contraction"** refers to the set of operations designed to reduce the physical and metadata footprint of a table. This is a proactive, preventative set of tasks aimed at keeping the table healthy and efficient over the long term. The primary goal of contraction is to counteract the natural tendency of a table to become bloated and fragmented as data is ingested, updated, and deleted. The key operations that fall under the umbrella of contraction include:

*   **Data File Compaction (`rewrite_data_files`):** Merging many small files into a smaller number of larger, more optimal files to reduce I/O overhead and metadata bloat.
*   **Metadata File Optimization (`rewrite_manifests`):** Consolidating small or fragmented manifest files to speed up query planning.
*   **Snapshot Lifecycle Management (`expire_snapshots`):** Removing old, unneeded snapshots to reclaim storage space and simplify the metadata layer.
*   **Orphan File Cleanup (`remove_orphan_files`):** Deleting untracked files that are consuming storage space but are not part of the table.

Together, these operations form a comprehensive maintenance strategy that ensures the table remains lean, efficient, and cost-effective.

#### 5.1.2. "Pruning" as Query Optimization via File Skipping

**"Pruning"** in the context of Iceberg refers to the set of query optimization techniques that leverage the table's rich metadata to skip irrelevant data files during query execution. This is a reactive, on-the-fly optimization that occurs every time a query is run. The goal of pruning is to minimize the amount of data that needs to be read from storage and processed by the query engine, thereby reducing query execution time and compute costs. The key techniques that fall under the umbrella of pruning include:

*   **Partition Pruning:** Using partition information to skip entire directories of data files that are not relevant to the query's filter predicates.
*   **File-Level Pruning:** Using column-level statistics (min/max values) stored in manifest files to skip individual data files that do not contain any data matching the query's filters.
*   **Predicate Pushdown:** Pushing filter predicates as close to the data source as possible to maximize the effectiveness of pruning.
*   **Dynamic Partition Pruning:** Using the results of a filter on a dimension table to dynamically prune partitions in a fact table during a join.

By effectively leveraging these pruning techniques, you can dramatically improve the performance of your analytical workloads.

### 5.2. Evolution of Maintenance Schemes

The strategies for maintaining Iceberg tables have evolved significantly since the project's inception. In the early days, maintenance was largely a manual process, requiring data engineers to write custom scripts to perform tasks like compaction and snapshot expiration. As the ecosystem has matured, more automated and integrated solutions have emerged, making it easier to manage tables at scale. This evolution has been driven by the need to reduce operational overhead and to make the power of Iceberg accessible to a wider range of users.

#### 5.2.1. From Manual Procedures to Automated Optimization

The evolution of Iceberg maintenance can be seen as a shift from manual, script-based procedures to automated, declarative optimization. In the early days, data engineers would have to write and maintain their own Spark jobs to perform compaction and other maintenance tasks. This was a time-consuming and error-prone process, and it required a deep understanding of the Iceberg internals. As the project matured, built-in procedures like `rewrite_data_files` and `expire_snapshots` were introduced, which could be called directly from Spark SQL. This was a major step forward, as it simplified the process of performing maintenance and made it more accessible to users who were not proficient in programming. More recently, the trend has been towards even more automated and declarative solutions, such as the use of table properties to automatically manage snapshot expiration and the introduction of engine-specific commands that handle optimization automatically.

#### 5.2.2. The Role of Engine-Specific Commands (e.g., Dremio `OPTIMIZE`)

A key trend in the evolution of Iceberg maintenance is the increasing role of engine-specific commands. Query engines like Dremio are starting to provide their own commands for table optimization, which are built on top of the core Iceberg procedures but are tailored to the specific characteristics of the engine. For example, Dremio's `OPTIMIZE` command provides a simple, one-stop solution for performing compaction, manifest rewriting, and other maintenance tasks. It also includes engine-specific optimizations, such as the ability to sort data based on the query patterns observed by the Dremio engine. This trend towards engine-specific optimization is a natural evolution of the ecosystem, as it allows for a tighter integration between the table format and the query engine, which can lead to better performance and a more seamless user experience.

### 5.3. A Unified Maintenance Strategy

A successful long-term maintenance strategy for Iceberg tables requires a unified approach that integrates the concepts of contraction and pruning. This means not only performing the core maintenance tasks but also doing so in a way that is aligned with the goals of query optimization. By understanding the relationship between the physical layout of the data and the effectiveness of pruning, you can make more informed decisions about how to prioritize and configure your maintenance tasks.

#### 5.3.1. Integrating Compaction, Snapshot Expiration, and Manifest Rewriting

A unified maintenance strategy should integrate all of the core contraction tasks into a single, cohesive workflow. This means scheduling regular jobs for data file compaction, snapshot expiration, and manifest rewriting, and ensuring that these jobs are run in the correct order. For example, it is generally recommended to run compaction before snapshot expiration, as this ensures that the old, small files are compacted before they are removed. Similarly, it is a good practice to run manifest rewriting after a period of frequent writes, to ensure that the metadata layer remains optimized. By integrating these tasks into a single, automated workflow, you can ensure that your tables are always in a healthy and performant state.

#### 5.3.2. Aligning Maintenance with Data Platform Evolution Goals

Finally, a unified maintenance strategy should be aligned with the overall goals of the data platform evolution. This means that the maintenance tasks should be prioritized based on the specific needs of the business. For example, if the primary goal is to reduce costs, then the focus should be on tasks like snapshot expiration and orphan file cleanup. If the primary goal is to improve query performance, then the focus should be on tasks like data file compaction and sort-based compaction. By aligning your maintenance strategy with your business goals, you can ensure that you are getting the most value from your data platform and that it continues to meet the needs of the organization as it grows and evolves.