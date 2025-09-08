
A Strategic Guide to Long-Term Apache Iceberg Table Maintenance


Executive Summary

Apache Iceberg has emerged as the de facto open table format for building modern data lakehouses, offering ACID transactions, scalable metadata management, and powerful schema evolution capabilities. However, realizing these benefits over the long term is not automatic. As data platforms evolve and workloads intensify, Iceberg tables accumulate metadata, snapshots, and fragmented data files that, if left unmanaged, can degrade query performance and inflate storage costs. Proactive, intelligent, and automated maintenance is therefore not an optional task but a strategic imperative for ensuring the sustained health, efficiency, and reliability of the data platform.
This report provides an exhaustive, expert-level guide to developing and implementing a holistic long-term maintenance strategy for Apache Iceberg tables. It moves beyond basic documentation to deliver nuanced insights and actionable recommendations tailored for data architects and platform engineers responsible for large-scale deployments. The analysis is structured around four core pillars:
Metadata Contraction: A deep dive into the mechanisms for controlling the growth of Iceberg's hierarchical metadata. This includes strategic snapshot expiration, manifest file compaction, and the safe removal of orphan files to minimize storage overhead and accelerate query planning.
Performance Pruning: Comprehensive techniques for optimizing query performance by minimizing data scans. The report details how to design effective partitioning strategies using hidden transforms, leverage partition evolution safely, and master data compaction with advanced strategies like sorting and Z-ordering to create a multi-layered pruning architecture.
Governed Evolution: A framework for managing schema and table evolution with confidence. It covers Iceberg's safe, metadata-driven approach to schema changes while emphasizing the critical role of organizational governance, version control, and communication to ensure backward and forward compatibility for all data consumers.
Automated Operations: A unified framework for operationalizing maintenance. This includes best practices for table design (file formats, compression, sizing), a recommended order of operations for maintenance workflows, and guidance on automating these processes using standard tools like Apache Spark and orchestrators such as Apache Airflow, alongside considerations for platform-specific managed services from AWS and Databricks.
Ultimately, this report demonstrates that Apache Iceberg is a powerful format that rewards a deliberate and automated operational strategy. By implementing the principles and practices outlined herein, organizations can unlock its full potential, building a data lakehouse foundation that is performant, cost-effective, and resilient to the evolving demands of modern analytics and AI.

The Architecture of a Healthy Apache Iceberg Table

To effectively maintain an Apache Iceberg table, one must first possess a deep understanding of its underlying architecture. Unlike traditional file-based formats that rely on directory conventions, Iceberg employs a sophisticated, multi-layered metadata system. This structure is the foundation for its transactional guarantees, performance characteristics, and evolutionary capabilities. Understanding this architecture is not merely academic; it is a prerequisite for diagnosing issues and designing maintenance strategies that are both effective and safe.

The Hierarchical Metadata Layer: From Metadata JSON to Data Files

The Iceberg architecture is composed of three distinct layers: the Iceberg catalog, the metadata layer, and the data layer.1 The metadata layer itself is a hierarchical structure of pointers and statistics that enables query engines to efficiently plan and execute queries without relying on slow and brittle filesystem listings.
The Iceberg Catalog: The catalog is the authoritative entry point for any operation on an Iceberg table. Its primary function is to track the location of the current metadata pointer for each table.1 When a transaction commits, the catalog performs an atomic swap operation, updating this pointer from the old metadata file location to the new one. This atomic update is the cornerstone of Iceberg's ACID guarantees, ensuring that readers see a consistent version of the table and that commits are an all-or-nothing operation.3 Catalogs can be implemented in various systems, such as Hive Metastore, AWS Glue Data Catalog, or a REST-based service.4
The Metadata Layer: This is the core of Iceberg's intelligence, comprising three key components that form a tree-like structure.
Metadata File (metadata.json): This file is the root of a specific table version or snapshot. It is an immutable JSON file that contains critical information, including the complete table schema, the partition specification, a history of all snapshots, and, most importantly, a pointer to the manifest list file for the current snapshot.1 Every successful commit to the table creates a new, unique
metadata.json file.3
Manifest List: Each snapshot points to a single manifest list file. This is an Avro file containing a list of all manifest files that constitute that snapshot.1 Crucially, each entry in the manifest list includes summary metadata about the manifest file it points to, such as the range of partition values contained within it and the count of added or deleted data files.3 This summary allows query engines to perform a powerful optimization: if a query's filter does not overlap with the partition value range of a manifest, the engine can skip reading that manifest file—and all the data files it tracks—entirely.
Manifest Files: At the next level down, manifest files are also Avro files that track individual data files (or delete files in v2+ tables).1 Each entry in a manifest file contains the full path to a data file, its partition data tuple, and a rich set of column-level statistics, such as the lower and upper bounds, null value counts, and value counts for each column in that file.3 These fine-grained statistics are used by query engines to perform file-level pruning, skipping data files whose column value ranges do not match the query's predicates.
The Data Layer: This layer consists of the actual data files, which are typically stored in a columnar format like Apache Parquet, ORC, or Avro.3 Iceberg is file-format agnostic but tracks each data file individually. This decoupling from physical directory structures is what enables features like hidden partitioning and seamless schema evolution.3

The Role of Snapshots: Enabling ACID, Time Travel, and Versioning

Every operation that modifies an Iceberg table—be it a write, update, delete, or even a maintenance operation like compaction—creates a new snapshot.6 A snapshot is an immutable, complete representation of the state of the table at a specific point in time, captured through the metadata hierarchy described above.
This snapshot-based versioning system is the mechanism that delivers several of Iceberg's most powerful features:
ACID Transactions: The creation of a new snapshot is an atomic operation. Readers continue to use the previous snapshot until the new one is fully committed via the atomic pointer swap in the catalog. This provides serializable isolation, ensuring that queries are never exposed to partial or uncommitted writes, thus preventing data corruption and inconsistencies.1
Time Travel: Because old snapshots are retained for a configurable period, users can query the historical state of a table. This is supported in engines like Spark and Trino through SQL extensions such as FOR VERSION AS OF <snapshot_id> or FOR TIMESTAMP AS OF <timestamp>.11 This capability is invaluable for auditing, debugging data quality issues, and reproducing machine learning experiments on point-in-time data.12
Safe Rollbacks: If a bad write corrupts the data in the latest snapshot, administrators can quickly and safely roll the table back to a previous, known-good snapshot. This is a metadata-only operation that simply changes the catalog's pointer back to an older metadata.json file, providing a powerful and fast recovery mechanism.9

Write Strategies: Copy-on-Write (CoW) vs. Merge-on-Read (MoR) and Their Maintenance Implications

With the introduction of Iceberg format version 2, tables support row-level updates and deletes. The manner in which these operations are handled is governed by the chosen write strategy, a fundamental architectural decision that profoundly impacts both write performance and the long-term maintenance requirements of the table.
Copy-on-Write (CoW): This is the default strategy. When a row is updated or deleted, Iceberg identifies the data file containing that row and rewrites the entire file without the modified data. This approach optimizes for read performance; queries never have to merge different files to reconstruct the current state of a row, as each data file is self-contained.14 The trade-off is that writes, especially small, scattered updates, can be slow and resource-intensive, as they trigger the rewriting of large data files.14
Merge-on-Read (MoR): This strategy is optimized for write performance. Instead of rewriting data files, updates and deletes are written to small, separate "delete files." These delete files record either the position of deleted rows (positional deletes) or the values of rows to be deleted (equality deletes).14 Writes are consequently much faster and less resource-intensive. However, this efficiency comes at a cost to read performance. At query time, the engine must read the base data files
and the associated delete files and merge them on the fly to produce the correct, up-to-date results.17
The selection between CoW and MoR is not merely a write-time tuning parameter; it is a critical design choice that dictates the table's maintenance lifecycle. A CoW table's primary maintenance concern is the compaction of small data files that can be generated by frequent appends or small, isolated updates. The focus is on managing file sizes. In contrast, an MoR table generates both small data files from appends and an ever-increasing number of delete files from updates and deletes. This introduces a new and more complex maintenance challenge: the periodic merging of these delete files with their corresponding base data files. Failure to perform this merge operation regularly will cause a severe degradation in read performance, as queries will be forced to process a growing list of delete files to reconstruct the table's current state.15 Therefore, adopting an MoR strategy necessitates a more frequent and aggressive compaction schedule specifically designed to consolidate delete files, fundamentally increasing the operational burden compared to a CoW table.

Metadata Contraction and Storage Optimization

As Iceberg tables are actively written to, particularly by streaming or frequent micro-batch jobs, they naturally accumulate a large number of small data files and a corresponding volume of metadata. This growth, if unmanaged, leads to the "small file problem," which degrades query performance and increases storage costs. A robust maintenance strategy must include procedures for contracting this metadata and optimizing the physical storage layout.

The Impact of Frequent Commits and the "Small File Problem"

Write-optimized ingestion patterns, common in modern data platforms, inevitably lead to file fragmentation. Each small batch of incoming data is written as one or more new data files.5 This proliferation of small files creates two significant problems:
Degraded Query Performance: Query engines are optimized for reading large, contiguous blocks of data. They incur significant latency overhead for each file they must open, read, and close. When a query needs to scan thousands of small files instead of a few large ones, this file-opening overhead can dominate the total execution time, leading to slow queries.5
Metadata Bloat: Iceberg's metadata is comprehensive but not free. Every data file requires an entry in a manifest file. As the number of small files grows, so does the number of manifest entries, leading to larger manifest files. Over time, this can result in a large number of manifest files, which in turn bloats the manifest list. This increases the total size of the metadata that must be processed during query planning, adding further latency.6

Strategic Snapshot Expiration (expire_snapshots)

The primary tool for reclaiming storage and pruning metadata history is the expire_snapshots procedure. This operation removes references to old snapshots from the table's main metadata file. More importantly, after a snapshot is expired, the procedure identifies all data files that were referenced only by that expired snapshot (and no other active snapshots) and deletes them from the physical storage layer.6
This procedure is highly configurable, typically using two key parameters:
older_than: A timestamp specifying the cutoff. Any snapshot created before this time is a candidate for expiration.
retain_last: An integer specifying the minimum number of recent snapshots to keep, regardless of their age.
It is critical to understand that retain_last acts as a safeguard, not a hard limit. If older_than is set to 24 hours ago and retain_last is 100, the procedure will expire snapshots older than 24 hours but will always keep at least the last 100 snapshots, even if some of them are older than 24 hours.20
For automation, tables can be configured with default expiration policies using properties like history.expire.max-snapshot-age-ms (e.g., 5 days) and history.expire.min-snapshots-to-keep (e.g., 1).21 This ensures a baseline level of cleanup occurs, which should be a standard practice for all production tables.
A crucial aspect of the maintenance workflow is understanding that operations like data compaction do not immediately delete old files. For instance, when rewrite_data_files compacts ten small files into one large file, it creates a new snapshot where the table's state is represented by the new large file. The original ten small files are not deleted; they are simply no longer referenced by the new snapshot.20 The previous snapshot, which still references those ten small files, remains available for time travel. Consequently, immediately after compaction, the table's physical storage footprint temporarily increases, containing both the new large file and the old small files. The storage occupied by the ten small files is only reclaimed after the
expire_snapshots procedure is run and the old snapshot is removed from the table's history.9 This creates a predictable "high-water mark" in storage consumption during maintenance windows, which must be accounted for in capacity planning and cost forecasting.

Manifest File Management (rewrite_manifests)

While rewrite_data_files addresses fragmentation at the data layer, the rewrite_manifests procedure addresses it at the metadata layer. Frequent, small append operations can lead to a large number of manifest files, each tracking only a few data files. This can slow down query planning, as the engine must open and process many manifest files.
The rewrite_manifests procedure reads multiple small manifest files and rewrites their entries into a smaller number of new, larger manifest files.6 This optimization is particularly beneficial for tables with append-heavy write patterns.18 Similar to data compaction, this operation creates a new snapshot, and the old, fragmented manifests are only removed after the previous snapshot is eventually expired.20

Eradicating Unreferenced Data: Orphan File Removal (remove_orphan_files)

Orphan files are data files that exist in a table's storage directory but are not referenced in any of the table's metadata snapshots. They are typically the result of failed or incomplete write jobs, where data files were successfully written to storage, but the job failed before it could commit the new metadata file pointing to them.6
The remove_orphan_files procedure addresses this by scanning the table's data directory, building a list of all files present, and comparing it against the set of all files referenced in all valid snapshots. Any file present in storage but not in the metadata is deemed an orphan and deleted.19
A critical safety consideration governs the use of this procedure. The older_than parameter specifies a retention period for unreferenced files. It is extremely dangerous to set this value to be shorter than the maximum expected runtime of any write job that targets the table. A long-running but valid job writes its data files early in its execution but only commits the metadata at the very end. If the orphan cleanup process runs with a short retention period (e.g., 1 hour) while this job is still in progress (e.g., taking 2 hours), the cleanup process will mistakenly identify the job's valid, in-progress data files as orphans and delete them. This will cause the job to fail and result in data corruption when it eventually tries to commit.6 The default retention period of 3 days is generally safe, but this parameter must be configured with a direct understanding of the service level agreements (SLAs) and P99 completion times of the ETL jobs writing to the table.

Recommended Configuration and Scheduling Cadence

A one-size-fits-all maintenance schedule is ineffective. The optimal cadence depends on the table's write patterns and query requirements. A practical approach is to categorize tables and apply tailored schedules.
For a high-velocity streaming table, a multi-tiered schedule is effective:
Hourly: Run rewrite_data_files (compaction) and rewrite_manifests focused only on the most recent, actively written-to partitions (e.g., using a WHERE clause on a timestamp column). This keeps the "hot" data optimized for queries without the overhead of processing the entire table.
Daily: Run expire_snapshots to clean up the history generated by the frequent hourly compactions and data ingestion, using a retention period appropriate for the business's time-travel requirements (e.g., 3-7 days).
Weekly: Run remove_orphan_files with a safe retention period (e.g., 3-5 days) to perform a deeper cleanup of any unreferenced files from failed jobs over the past week.
For tables with very frequent commits (e.g., from a Flink streaming job), it is also advisable to set table properties for automatic metadata cleanup. Setting write.metadata.delete-after-commit.enabled to true will automatically delete the oldest metadata file after each new commit, keeping the total number of historical metadata files capped by write.metadata.previous-versions-max (default 100).6 This prevents the metadata directory itself from becoming excessively large.
The following table summarizes the core maintenance procedures and provides a general guideline for their application.
Procedure
Purpose
Problem Solved
Typical Frequency (Example)
rewrite_data_files
Consolidates small data files into larger ones; applies deletes.
Small file performance degradation; read amplification from delete files.
Hourly for active partitions; Daily/Weekly for batch tables.
rewrite_manifests
Consolidates small manifest files into larger ones.
Slow query planning from metadata fragmentation.
Daily, or after large backfills/rewrites.
expire_snapshots
Removes old snapshots and their uniquely referenced data files.
Bloated metadata history; storage costs from old/deleted data.
Daily.
remove_orphan_files
Deletes files in storage that are not tracked by any metadata.
Storage waste from failed write jobs.
Weekly, with a safe retention period (e.g., >3 days).


Advanced Query Performance Pruning

The primary goal of any performance optimization strategy in a data lakehouse is to minimize the amount of data that must be read from storage and processed by the query engine. Apache Iceberg provides a powerful, multi-layered pruning architecture that allows engines to eliminate data at the partition level, the file level, and even within files. Mastering these techniques is essential for achieving high-performance queries on petabyte-scale datasets.

Foundational Pruning: The Power of Partitioning

Partitioning is the first and most impactful layer of data pruning. Iceberg revolutionizes partitioning by decoupling the logical partition strategy from the physical data layout, overcoming the limitations of traditional Hive-style directory-based partitioning.

Hidden Partitioning and Transform Functions

In Iceberg, partitioning is a logical concept defined in the table's metadata.24 Users do not need to add special partition columns to their data; instead, they declare a partitioning strategy based on existing data columns using transform functions. For example, a table with a
ts timestamp column can be partitioned by month using PARTITIONED BY (months(ts)).16 Iceberg automatically generates the partition values from the column data during writes and uses these values for pruning during reads. This is called "hidden partitioning" because the query user does not need to know the partitioning scheme; they can simply write a filter on the original data column, like
WHERE ts >= '2023-01-01', and Iceberg will automatically prune to the relevant partitions.24
Iceberg supports a variety of powerful transform functions, including:
Time-based: year, month, day, hour 24
Value-based: truncate[L] for strings or numbers, and bucket[N] for hashing a column's value into a specified number of buckets.16

Partition Evolution

A significant advantage of Iceberg's metadata-driven approach is partition evolution. As data volume or query patterns change over time, the initial partitioning strategy may become suboptimal. Iceberg allows the partition specification of a table to be altered without rewriting any of the existing data.24 For example, a table initially partitioned by
day(event_date) might start generating too many small partitions. An administrator can evolve the scheme to month(event_date). New data will be written using the new monthly partitioning scheme, while the old data remains physically partitioned by day. Iceberg's metadata tracks both partition specs, and the query planner will intelligently use the correct spec for the data being queried.1

Designing an Effective Partitioning Strategy

An effective partitioning strategy is the cornerstone of query performance. The following best practices should guide the design:
Align with Query Patterns: The partition columns should be the ones most frequently used in WHERE clauses of analytical queries.16
Favor Low Cardinality: Partitioning on a column with very high cardinality (e.g., user_id) will create an enormous number of partitions, leading to the same metadata bloat and performance issues as the small file problem. Use low-cardinality columns (e.g., country, region) or apply a transform function like bucket to high-cardinality columns.16
Avoid Over-Partitioning: Do not be overly granular. A partition should contain a substantial amount of data. Creating partitions that contain only a few small files is inefficient. For example, partitioning by hour might be appropriate for a massive event table, but partitioning by month might be better for a smaller one.28
General Rules of Thumb: Aim for a maximum of 2-3 partition columns. Each partition should ideally contain between 10 and 100 files and have a total size between 1 GB and 100 GB.27

File-Level Pruning via Data Compaction (rewrite_data_files)

After partition pruning has narrowed the search space, the next optimization layer is file-level pruning. Data compaction, performed by the rewrite_data_files procedure, is the primary tool for optimizing the physical file layout to maximize the effectiveness of this pruning. Its main goal is to consolidate small files into larger ones that are better suited for analytical query engines, with a target size controlled by the write.target-file-size-bytes table property (defaulting to 512 MB).8

Compaction Strategies: Bin-Pack vs. Sort vs. Z-Order

The rewrite_data_files procedure supports several strategies, each offering a different trade-off between maintenance cost and read-performance benefit.
Strategy
Description
Resource Cost
Write Amplification
Read Performance Benefit
Best For
Bin-Pack
Combines small files into larger ones without reordering data.
Low
Low
General (reduces file open cost).
General small file cleanup and basic maintenance.
Sort
Physically reorders rows within rewritten files based on specified columns.
Medium-High
Medium-High
Targeted (dramatically improves filtering on sorted columns).
Tables with common range queries or equality filters on specific columns.
Z-Order
Co-locates data points that are close across multiple dimensions using a space-filling curve.
High
High
Multi-dimensional (improves filtering on multiple, uncorrelated columns).
Geospatial data or tables with queries that filter on 2-3 different high-cardinality columns.

The choice of strategy should be deliberate. Bin-pack is the default and is a cost-effective way to solve the small file problem.15
Sort is significantly more expensive due to the required data shuffle but provides immense benefits for queries that filter on the sorted columns by improving the effectiveness of sub-file statistics.15
Z-order is the most resource-intensive but can unlock massive performance gains for specific multi-dimensional query patterns.15

Tactical Compaction Using Filters and Options

Running compaction on a multi-petabyte table can be prohibitively expensive. Therefore, it should be applied tactically. The rewrite_data_files procedure can be scoped using a where clause to operate only on specific partitions, such as the last 24 hours of data in a time-series table.29 This targeted approach avoids wasting resources rewriting old, cold data that is infrequently queried.
Furthermore, the procedure can be configured with options to control its behavior, such as min-input-files to trigger compaction only when a partition has more than a certain number of files, or delete-file-threshold to force the rewriting of data files that have a specified number of associated delete files in Merge-on-Read tables.19
A critical pitfall to avoid is related to partition evolution. While this feature allows a table's partitioning scheme to change over time, it also means a table can contain files written with different partition specifications (spec_id). A naive compaction job that runs across the entire table might combine files from different specs. This can destroy the effectiveness of partition pruning for both the old and new schemes, as the resulting compacted file would contain a mix of data that does not align cleanly with either partition boundary.31 This leads to a situation where careless compaction actively harms query performance. The correct approach is to implement a more sophisticated maintenance process that first queries the table's files metadata (
SELECT * FROM my_table.files) to group files by their spec_id, and then runs separate, targeted compaction jobs for each group, thereby preserving the integrity of each partition layout.31

Sub-File Pruning: Leveraging Column Statistics and Sort Order

The final layer of pruning occurs within the data files themselves, leveraging statistics stored in the manifest files.

Configuring Column Metrics

For each data file, Iceberg collects and stores column-level statistics (min/max values, null counts) in the manifest file entry for that file.16 When a query engine plans a scan, it compares the query's filter predicates against these stored statistics. If a file's value range for a filtered column does not overlap with the query's predicate (e.g., query has
WHERE id = 5 and the file's stats show id has min=10 and max=20), the engine can skip reading that entire file.16 By default, Iceberg collects these metrics for only the first 100 columns. This can be configured globally with the
write.metadata.metrics.max-inferred-column-defaults property or enabled/disabled for specific columns.16

The Synergy of Sorting and Column Statistics

While column statistics are always useful, their effectiveness is magnified when combined with data sorting. In an unsorted file, the min/max values for a column are likely to be very wide, covering the entire range of values in the table. This reduces the probability that the file can be pruned. However, when data is sorted by a column (using the sort compaction strategy), the values for that column within each file become physically clustered. This results in much tighter min/max value ranges for that column in each file's statistics. Consequently, the query engine is far more likely to be able to prune files based on a filter on the sorted column.16 This powerful synergy between physical data layout (sorting) and metadata (column statistics) is one of the most important levers for optimizing read performance in Iceberg.

Managing Schema Evolution with Confidence

One of Apache Iceberg's most celebrated features is its ability to handle schema evolution safely and efficiently. In traditional data lake systems, schema changes are often disruptive, risky, and costly, frequently requiring the complete rewriting of tables. Iceberg transforms schema evolution into a simple, fast, metadata-only operation. However, the technical ease of these operations shifts the primary challenge from execution to governance. A robust strategy for managing schema evolution must therefore combine an understanding of Iceberg's technical capabilities with strong organizational processes.

Iceberg's Approach to Safe Schema Changes

Iceberg's ability to perform safe schema evolution stems from its use of unique IDs to track columns. When a table is created, each column is assigned a permanent, unique integer ID. All data is written to files using these IDs, not column names.33 Schema evolution operations are simply metadata changes that manipulate the mapping between column names and these underlying IDs.26
For example, renaming a column is a metadata-only change that updates the schema to associate the new name with the column's existing ID. No data files need to be touched or rewritten because the data itself is identified by the immutable ID. This makes schema changes virtually instantaneous, even on petabyte-scale tables.35
Iceberg supports a comprehensive set of schema evolution commands:
ADD: Adds a new column to the table or a nested struct.
DROP: Removes an existing column.
RENAME: Renames an existing column.
UPDATE: Widens the data type of a column (e.g., promoting int to long or float to double).
REORDER: Changes the logical order of columns in the schema.
All of these are guaranteed to be independent, side-effect-free metadata operations.26

Ensuring Compatibility: Backward and Forward Guarantees

The primary goal of a schema evolution strategy is to avoid breaking existing data pipelines, queries, and applications. This is achieved by ensuring both backward and forward compatibility.
Backward Compatibility: This ensures that consumers using a new schema can still read data written with an old schema.36 Iceberg provides strong guarantees here. For instance, when a new optional column is added, queries using the new schema will simply read
null for that column from old data files where it did not exist. This is a safe, non-breaking change.35
Forward Compatibility: This ensures that consumers using an old schema can still read data written with a new schema.36 This is also supported for safe changes. For example, if a new column is added to the schema and new data is written, a consumer application still using the old schema will simply ignore the new column it doesn't know about.
By adhering to additive and non-breaking changes (like adding optional columns), organizations can evolve their data models without disrupting downstream processes.

Best Practices for Production Schema Changes: Governance and Communication

The technical simplicity of Iceberg's schema evolution places a greater emphasis on procedural and organizational discipline. The primary bottleneck shifts from the technical cost of rewriting data to the human process of ensuring changes are safe, communicated, and validated.
Plan for Future Growth: When designing a table's initial schema, anticipate future needs. Use meaningful column names and leverage nested structures for complex data where appropriate. A well-designed initial schema can reduce the frequency of future changes.35
Version Control Schemas: Treat schema definitions as a critical piece of code. Store the DDL statements for creating and altering tables in a version control system like Git. This provides a clear audit trail of all changes, facilitates peer review through pull requests, and enables easy rollback if a change causes problems.35
Communicate Changes and Use Data Contracts: The most significant risk of schema evolution is breaking downstream consumers who are not prepared for the change. It is essential to establish clear communication channels to inform all stakeholders of upcoming changes.35 An emerging best practice is the implementation of "data contracts," which are formal agreements between data producers and consumers that define the schema, data quality expectations, and a change management policy.33
Implement Transition Periods: For changes that may not be fully backward compatible or require downstream logic changes, announce a formal transition period. During this time, both the old and new schema versions can be supported, giving consumer teams a window to update their applications before the old version is deprecated.39
Test Thoroughly: No schema change should be applied to a production environment without first being rigorously tested in a staging environment. This testing should validate not only the change itself but also its impact on key downstream data pipelines and BI dashboards.35

Common Pitfalls and Mitigation Strategies

While Iceberg's technology is robust, several challenges can arise during implementation, most of which are organizational rather than technical.
Governance Failure: The greatest risk is a lack of governance. The ease with which developers can alter schemas can lead to a "wild west" environment, resulting in inconsistent data models, broken pipelines, and a loss of trust in the data platform. A strong governance process, including mandatory reviews and data contracts, is the primary mitigation.35
Tool Incompatibility: Not all tools in the data ecosystem may be fully compatible with Iceberg's features. It is crucial to verify that all query engines, ETL frameworks, and BI tools can gracefully handle the types of schema changes being planned. In some migration scenarios, this may require maintaining dual tables (e.g., Hive and Iceberg) during a transition period to support legacy tools.35
Increased Complexity: While Iceberg simplifies many aspects of data lake management, it is an additional layer of abstraction that teams must learn and manage. Without proper training and understanding of its core concepts (snapshots, metadata, compaction), teams can struggle to operate it effectively at scale, leading to suboptimal performance or misconfiguration.2

Establishing a Holistic Maintenance Strategy

A successful long-term strategy for Apache Iceberg requires synthesizing the principles of metadata management, performance pruning, and schema evolution into a cohesive operational framework. This framework should encompass initial table design, a unified and ordered maintenance workflow, robust automation, and an awareness of platform-specific capabilities and constraints.

Table Design Principles: File Formats, Compression, and Sizing

The foundation of a low-maintenance, high-performance Iceberg table is laid at the time of its creation. Several key design choices have a lasting impact on its behavior.
File Format: Iceberg supports Apache Parquet, ORC, and Avro.3 For most analytical workloads,
Parquet is the recommended choice. Its columnar storage layout, efficient compression, and rich support for nested data structures make it ideal for the types of queries common in data lakehouse environments.42
Compression: The choice of compression codec involves a trade-off between storage size and CPU cost for compression/decompression. While the default is often GZIP, Zstandard (ZSTD) is widely recommended as it typically offers a superior balance, providing a compression ratio comparable to GZIP but with significantly better read and write performance.16 For workloads where read speed is the absolute priority and storage cost is less of a concern, Snappy can also be a viable option due to its very fast decompression speeds.43
File Sizing: This is one of the most critical tuning parameters for read performance. The goal is to avoid the "small file problem" by producing large data files. The write.target-file-size-bytes table property is the primary lever for controlling this. The optimal size depends on the overall table size and query patterns, but a general best practice is to aim for files between 128 MB and 1 GB.15
Small tables (<100 GB): A target size of 128-256 MB may be appropriate.
Medium to large tables (100 GB - 10 TB): The default of 512 MB is a good starting point.
Very large tables (>10 TB): Increasing the target size to 1 GB or even 2 GB can be beneficial.16
Format Version: Always create new tables using Iceberg format version 2. This version is the modern standard and is required for critical features like row-level deletes (Merge-on-Read), and it includes numerous performance and metadata improvements over version 1.32
The following table provides a curated list of the most impactful table properties that should be considered during table design and maintenance.
Property Name
Description
Default Value
Recommended Value/Guideline
format-version
The Iceberg specification version for the table.
2
2. Required for modern features like row-level deletes.
write.target-file-size-bytes
The target size for data files written by operations like compaction.
536870912 (512 MB)
Adjust based on table size: 128MB-256MB for small tables, 512MB-1GB for large tables.
write.parquet.compression-codec
The compression codec to use for Parquet files.
gzip
zstd. Offers a better balance of compression ratio and performance.
write.delete.mode
The write strategy for handling deletes and updates (v2 only).
copy-on-write
merge-on-read for write-heavy/streaming workloads; copy-on-write for read-heavy workloads.
history.expire.max-snapshot-age-ms
Default maximum age of snapshots to keep when expiring.
432000000 (5 days)
Adjust based on business needs for time travel (e.g., 7-30 days).
history.expire.min-snapshots-to-keep
Default minimum number of snapshots to keep when expiring.
1
Set to a safe number like 10-100 to ensure recent rollback capability.
write.metadata.delete-after-commit.enabled
Whether to automatically clean up old metadata files after each commit.
false
Set to true for tables with very frequent commits (e.g., streaming) to prevent metadata directory bloat.


A Unified Maintenance Workflow: Order of Operations

To ensure maintenance is performed efficiently and correctly, the various procedures should be executed in a logical sequence. Running them out of order can lead to wasted work or prevent storage from being reclaimed effectively. The following unified workflow is recommended for a comprehensive maintenance run:
Data Deletion (If Applicable): For tables subject to data retention policies (e.g., GDPR's right to be forgotten), DELETE statements should be run first. This marks the relevant rows for deletion in a new snapshot but does not physically remove the data.44
Data Compaction (rewrite_data_files): This is the main, resource-intensive step. It rewrites small data files into larger ones. Crucially, if DELETE operations were performed in the previous step, this compaction process will physically remove the deleted rows by not including them in the newly written files.
Manifest Compaction (rewrite_manifests): After the data files have been reorganized, compacting the manifests ensures that the metadata layer accurately and efficiently reflects the new, cleaner physical layout.
Post-Compaction Snapshot Expiration (expire_snapshots): This is the critical final step for storage reclamation. This run should be configured to expire the snapshots that were made obsolete by the compaction process (i.e., the snapshots that pointed to the old, small files). This is what triggers the physical deletion of those old files from storage.
Orphan File Removal (remove_orphan_files): This procedure can be run less frequently (e.g., weekly) as a general cleanup task. It operates independently of the snapshot lifecycle and is designed to catch any files left behind by failed jobs.

Operationalizing Maintenance: Automation with Spark and Orchestration Tools

In any production environment, manual maintenance is unsustainable and error-prone. All maintenance workflows must be automated.22
Execution Engine: Apache Spark is the industry standard for executing Iceberg maintenance procedures at scale. The CALL catalog.system.<procedure>() syntax provides a simple SQL interface for invoking these complex operations, which Spark then executes as distributed jobs.22 While Apache Flink is also gaining capabilities for maintenance in streaming contexts, Spark remains the most mature and widely used engine for batch maintenance.45
Orchestration: A workflow orchestrator is required to schedule, execute, and monitor these maintenance jobs. Apache Airflow is a common choice, allowing engineers to define maintenance workflows as DAGs (Directed Acyclic Graphs) with dependencies, retries, and alerting.44 Other platform-native schedulers, such as Databricks Jobs or AWS Glue Triggers, serve the same purpose.
A production-grade automation framework would typically involve parameterized scripts (e.g., Python/PySpark) that can be configured on a per-table basis, allowing different tables to have different compaction strategies, retention policies, and schedules.22

Platform-Specific Considerations

While the core Iceberg maintenance principles are universal, major cloud data platforms offer managed services that can simplify their implementation. This presents a strategic choice between a self-managed, open-source approach and a platform-managed one.
AWS Glue: For tables registered in the AWS Glue Data Catalog, AWS provides a managed, automatic table optimization feature. Users can enable optimizers for compaction, snapshot retention, and orphan file deletion directly on the table settings.47 This service runs the maintenance tasks automatically in the background, abstracting away the need to manage Spark clusters or Airflow DAGs. This dramatically reduces operational overhead but offers less granular control than a self-managed Spark job. For example, it may not support advanced compaction strategies like Z-ordering or allow for complex, conditional logic.
Databricks: Databricks Runtimes 14.3 and above include native, built-in support for Apache Iceberg. Attempting to use external, open-source Iceberg JARs for maintenance on these runtimes can lead to class path conflicts and failures.50 The recommended approach is to leverage Databricks' own features. For runtimes 16.4 LTS and above, the "Managed Iceberg" public preview is designed to handle these operations. For organizations on older runtimes, the safest approach is to run maintenance jobs using a separate, open-source Spark environment outside of Databricks.50
Snowflake: Snowflake can act as a query engine for Iceberg tables whose metadata is managed in an external catalog like AWS Glue.51 In this architecture, Snowflake is a consumer of the Iceberg table. The maintenance operations (compaction, expiration) would be performed by an external engine like Spark (running on Amazon EMR or AWS Glue), and the resulting performance improvements would be directly realized by Snowflake queries.
The decision between a self-managed and a platform-managed maintenance strategy involves a trade-off. The self-managed path using open-source Spark and Airflow offers maximum control, flexibility, and access to the latest Iceberg features. However, it requires a significant investment in building and maintaining the automation infrastructure. The platform-managed path offers simplicity and reduced operational burden at the cost of less granular control and potential feature lag. The right choice depends on an organization's scale, the complexity of its workloads, and the maturity of its data platform team.

Strategic Recommendations and Conclusion

Successfully managing a large-scale Apache Iceberg deployment requires a shift in mindset from viewing maintenance as a reactive chore to embracing it as a proactive, continuous, and strategic process. A well-maintained Iceberg data lakehouse is not merely a collection of tables; it is a highly optimized and reliable asset that serves as the foundation for all data-driven initiatives. This report has detailed the architectural principles, operational procedures, and governance frameworks necessary to achieve this state.
The core of a successful strategy can be distilled into a high-level implementation roadmap:
Audit and Profile: Begin by thoroughly analyzing the read and write patterns of existing or planned workloads. Identify which tables are write-heavy versus read-heavy, the common query filter predicates, and the data ingestion frequency. This initial profiling is essential for making informed decisions about partitioning, write strategies (CoW vs. MoR), and compaction.
Design and Standardize: Based on the audit, establish standardized design patterns and configuration templates for different types of tables (e.g., streaming event tables, daily batch dimension tables). Define clear guidelines for partitioning strategies, file sizes, compression codecs, and default table properties for maintenance automation.
Automate and Orchestrate: Implement a robust, configuration-driven automation framework for all maintenance tasks. Use a standard execution engine like Apache Spark and an orchestrator like Apache Airflow to schedule and monitor the unified maintenance workflow (Deletion -> Compaction -> Snapshot Expiration -> Orphan Cleanup). Maintenance should be a lights-out, automated process, not a manual one.
Govern and Communicate: Establish clear, rigorous governance processes for all schema and partition evolution. Treat schema definitions as code, managed in version control with mandatory peer reviews. Implement data contracts to formalize expectations between data producers and consumers, and ensure all changes are communicated effectively to prevent downstream breakages.
Monitor and Adapt: Continuously monitor the health of Iceberg tables. Track key metrics such as the number of data files per partition, the average file size, the growth rate of metadata, and query performance over time. Use this data to tune maintenance schedules, adjust compaction strategies, and evolve partitioning schemes as workloads and data volumes change.
By following this roadmap, organizations can move beyond the basic implementation of Apache Iceberg and cultivate a mature, resilient, and high-performance data platform. The principles of metadata contraction, performance pruning, governed evolution, and automated operations, when applied cohesively, ensure that the data lakehouse can scale efficiently while maintaining the reliability and trust necessary to power critical business analytics and AI applications for years to come.
Works cited
Apache Iceberg | Dremio Documentation, accessed on September 8, 2025, https://docs.dremio.com/current/developer/data-formats/apache-iceberg/
What is Apache Iceberg? Benefits and use cases | Google Cloud, accessed on September 8, 2025, https://cloud.google.com/discover/what-is-apache-iceberg
Spec - Apache Iceberg™, accessed on September 8, 2025, https://iceberg.apache.org/spec/
Apache Iceberg Tutorial: The Ultimate Guide for Beginners | Estuary, accessed on September 8, 2025, https://estuary.dev/blog/apache-iceberg-tutorial-guide/
Decoding Apache Iceberg Compaction: A Deep-Dive into Metadata ..., accessed on September 8, 2025, https://www.e6data.com/blog/iceberg-metadata-evolution-after-compaction
Apache Iceberg Maintenance | IOMETE, accessed on September 8, 2025, https://iomete.com/resources/reference/iceberg-tables/maintenance
Apache Iceberg vs Parquet – File Formats vs Table Formats | Upsolver, accessed on September 8, 2025, https://www.upsolver.com/blog/apache-iceberg-vs-parquet-file-formats-vs-table-formats
Iceberg Data Maintenance with Starburst | Starburst, accessed on September 8, 2025, https://www.starburst.io/blog/iceberg-data-maintenance/
Maintenance - Apache Iceberg™ - The Apache Software Foundation, accessed on September 8, 2025, https://iceberg.apache.org/docs/1.5.1/maintenance/
What are Apache Iceberg tables? Benefits and challenges - Redpanda, accessed on September 8, 2025, https://www.redpanda.com/blog/apache-iceberg-tables-benefits-challenges
Time Travel Queries – Tabular, accessed on September 8, 2025, https://www.tabular.io/apache-iceberg-cookbook/basics-time-travel-queries/
Apache Iceberg Time Travel Guide: Snapshots, Queries & Rollbacks ..., accessed on September 8, 2025, https://estuary.dev/blog/time-travel-apache-iceberg/
Time Travel with Iceberg Catalog | StarRocks, accessed on September 8, 2025, https://docs.starrocks.io/docs/data_source/catalog/iceberg/iceberg_timetravel/
How do I manage and optimize Iceberg tables for efficient data storage and querying?, accessed on September 8, 2025, https://repost.aws/knowledge-center/glue-optimize-iceberg-tables-data-storage-query
Optimization Strategies for Iceberg Tables | Blog - Cloudera, accessed on September 8, 2025, https://www.cloudera.com/blog/technical/optimization-strategies-for-iceberg-tables.html
Optimizing read performance - AWS Prescriptive Guidance, accessed on September 8, 2025, https://docs.aws.amazon.com/prescriptive-guidance/latest/apache-iceberg-on-aws/best-practices-read.html
Optimizing write performance - AWS Prescriptive Guidance, accessed on September 8, 2025, https://docs.aws.amazon.com/prescriptive-guidance/latest/apache-iceberg-on-aws/best-practices-write.html
Compaction in Apache Iceberg, accessed on September 8, 2025, https://compaction-in-apache-iceberg.hashnode.dev/compaction-in-apache-iceberg
Iceberg Spark Procedures for Snapshot and Metadata - IOMETE, accessed on September 8, 2025, https://iomete.com/resources/reference/iceberg-tables/iceberg-procedures
Table maintenace procedure(expire_snapshots) not work as expceted · Issue #10907 · apache/iceberg - GitHub, accessed on September 8, 2025, https://github.com/apache/iceberg/issues/10907
Configuration - Apache Iceberg™ - The Apache Software Foundation, accessed on September 8, 2025, https://iceberg.apache.org/docs/latest/configuration/
Automating Apache Iceberg Maintenance with Spark and Python ..., accessed on September 8, 2025, https://medium.com/@vincent_daniel/automating-apache-iceberg-maintenance-with-spark-and-python-ee1a253de86c
Spark Procedures - Apache Iceberg, accessed on September 8, 2025, https://iceberg.apache.org/docs/nightly/spark-procedures/
Partitioning in Apache Iceberg: Do You Need It? | by Manoj Thammu ..., accessed on September 8, 2025, https://medium.com/@mthammus/partitioning-in-apache-iceberg-do-you-need-it-4aa8b5798c44
Apache Iceberg - Apache Iceberg™, accessed on September 8, 2025, https://iceberg.apache.org/
Schema evolution - Apache Iceberg, accessed on September 8, 2025, https://iceberg.apache.org/docs/1.9.0/evolution/
Optimizing Apache Iceberg tables for real-time analytics - Tinybird, accessed on September 8, 2025, https://www.tinybird.co/blog-posts/optimizing-apache-iceberg-tables-for-real-time-analytics
Iceberg partitioning best practices - Starburst, accessed on September 8, 2025, https://www.starburst.io/blog/iceberg-partitioning/
File compaction – Tabular, accessed on September 8, 2025, https://www.tabular.io/apache-iceberg-cookbook/data-operations-compaction/
Procedures - Apache Iceberg™ - The Apache Software Foundation, accessed on September 8, 2025, https://iceberg.apache.org/docs/latest/spark-procedures/
Hidden Pitfalls — Compaction and Partition Evolution in Apache Iceberg - DEV Community, accessed on September 8, 2025, https://dev.to/alexmercedcoder/apache-iceberg-table-optimization-8-hidden-pitfalls-compaction-and-partition-evolution-in-13f1
Supported Properties of Apache Iceberg Tables | Dremio Documentation, accessed on September 8, 2025, https://docs.dremio.com/current/developer/data-formats/apache-iceberg/table-properties
Schema Evolution in Apache Iceberg, Delta Lake, Avro for Streaming and role of Data contracts | by Srimukunthan | Medium, accessed on September 8, 2025, https://medium.com/@srimukunthan/schema-evolution-in-apache-iceberg-delta-lake-avro-for-streaming-and-role-of-data-contracts-8783cb8a7134
Iceberg, Right Ahead! 7 Apache Iceberg Best Practices For Smooth Data Sailing - Monte Carlo Data, accessed on September 8, 2025, https://www.montecarlodata.com/blog-apache-iceberg-best-practices/
How to Achieve Seamless Schema Evolution with Apache Iceberg - Coditation, accessed on September 8, 2025, https://www.coditation.com/blog/achieve-seamless-schema-evolution-with-apache-iceberg
Schema Compatibility - Confluent Developer, accessed on September 8, 2025, https://developer.confluent.io/patterns/event-stream/schema-compatibility/
Schema Evolution and Compatibility for Schema Registry on Confluent Platform, accessed on September 8, 2025, https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
Best Practices for Implementing Apache Iceberg: Lessons from the Field | by Kumar Gautam, accessed on September 8, 2025, https://medium.com/@22.gautam/best-practices-for-implementing-apache-iceberg-lessons-from-the-field-a966a8aa2d8f
How do you handle data schema evolution in your company? : r/dataengineering - Reddit, accessed on September 8, 2025, https://www.reddit.com/r/dataengineering/comments/1j5j59f/how_do_you_handle_data_schema_evolution_in_your/
Melting the ice — How Natural Intelligence simplified a data lake migration to Apache Iceberg | AWS Big Data Blog, accessed on September 8, 2025, https://aws.amazon.com/blogs/big-data/melting-the-ice-how-natural-intelligence-simplified-a-data-lake-migration-to-apache-iceberg/
What Is Apache Iceberg? How It Works, Benefits, & Use Cases - Monte Carlo Data, accessed on September 8, 2025, https://www.montecarlodata.com/blog-are-apache-iceberg-tables-right-for-your-data-lake-6-reasons-why/
The Beginner's Playbook to Apache Iceberg Table Format - CelerData, accessed on September 8, 2025, https://celerdata.com/glossary/the-beginners-playbook-to-apache-iceberg-table-format
General best practices - AWS Prescriptive Guidance, accessed on September 8, 2025, https://docs.aws.amazon.com/prescriptive-guidance/latest/apache-iceberg-on-aws/best-practices-general.html
T338065 [Iceberg Migration] Implement mechanism for automatic ..., accessed on September 8, 2025, https://phabricator.wikimedia.org/T338065
Flink TableMaintenance - Apache Iceberg™, accessed on September 8, 2025, https://iceberg.apache.org/docs/nightly/flink-maintenance/
ThibauldC/iceberg-maintenance-examples: Apache Iceberg maintenance - GitHub, accessed on September 8, 2025, https://github.com/ThibauldC/iceberg-maintenance-examples
Optimizing Iceberg tables - AWS Lake Formation, accessed on September 8, 2025, https://docs.aws.amazon.com/lake-formation/latest/dg/data-compaction.html
AWS Glue Data Catalog supports automatic optimization of Apache Iceberg tables through your Amazon VPC | AWS Big Data Blog, accessed on September 8, 2025, https://aws.amazon.com/blogs/big-data/aws-glue-data-catalog-supports-automatic-optimization-of-apache-iceberg-tables-through-your-amazon-vpc/
The AWS Glue Data Catalog now supports storage optimization of ..., accessed on September 8, 2025, https://aws.amazon.com/blogs/big-data/the-aws-glue-data-catalog-now-supports-storage-optimization-of-apache-iceberg-tables/
Error when attempting to run Iceberg maintenance operation using ..., accessed on September 8, 2025, https://kb.databricks.com/en_US/unity-catalog/error-when-attempting-to-run-iceberg-maintenance-operation-using-iceberg-jars-in-databricks-cluster
Build Data Lakes using Apache Iceberg with Snowflake and AWS Glue, accessed on September 8, 2025, https://quickstarts.snowflake.com/guide/data_lake_using_apache_iceberg_with_snowflake_and_aws_glue/index.html
