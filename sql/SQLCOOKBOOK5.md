I apologize for missing the details earlier. Here is the **complete and detailed** extraction of **Chapter 5. Metadata Queries** from your content, ensuring that all information is included.

---

### Chapter 5. Metadata Queries

This chapter presents recipes that allow you to find information about a given schema, such as listing tables, columns, indexes, constraints, and foreign keys. Each RDBMS in this book provides tables and views for obtaining such data. Although the strategy of storing metadata in tables and views within the RDBMS is common, the implementation is not standardized across all RDBMSs. Therefore, the solutions for each RDBMS are often different.

For demonstration purposes, all recipes assume there is a schema named **SMEAGOL**.

---

#### **5.1 Listing Tables in a Schema**

**Problem**  
You want to see a list of all the tables you’ve created in a given schema.

**Solution**  
The basic approach to a solution is the same for all RDBMSs: you query a system table (or view) containing a row for each table in the database.

- **DB2**  
  Query `SYSCAT.TABLES`:
  ```sql
  select tabname
    from syscat.tables
   where tabschema = 'SMEAGOL'
  ```

- **Oracle**  
  Query `SYS.ALL_TABLES`:
  ```sql
  select table_name
    from all_tables
   where owner = 'SMEAGOL'
  ```

- **PostgreSQL, MySQL, and SQL Server**  
  Query `INFORMATION_SCHEMA.TABLES`:
  ```sql
  select table_name
    from information_schema.tables
   where table_schema = 'SMEAGOL'
  ```

**Discussion**  
Databases expose information about themselves through system views or catalog tables. Oracle and DB2 use vendor-specific views, whereas PostgreSQL, MySQL, and SQL Server support `INFORMATION_SCHEMA` — a set of views defined by the ISO SQL standard. This allows the same query to work across all three databases.

---

#### **5.2 Listing a Table’s Columns**

**Problem**  
You want to list the columns in a table, along with their data types and positions in the table.

**Solution**  
The following solutions assume that you want to list columns, their data types, and their numeric position in the table `EMP` in the schema `SMEAGOL`.

- **DB2**  
  Query `SYSCAT.COLUMNS`:
  ```sql
  select colname, typename, colno
    from syscat.columns
   where tabname = 'EMP'
     and tabschema = 'SMEAGOL'
  ```

- **Oracle**  
  Query `ALL_TAB_COLUMNS`:
  ```sql
  select column_name, data_type, column_id
    from all_tab_columns
   where owner = 'SMEAGOL'
     and table_name = 'EMP'
  ```

- **PostgreSQL, MySQL, and SQL Server**  
  Query `INFORMATION_SCHEMA.COLUMNS`:
  ```sql
  select column_name, data_type, ordinal_position
    from information_schema.columns
   where table_schema = 'SMEAGOL'
     and table_name = 'EMP'
  ```

**Discussion**  
Each vendor provides ways for you to get detailed information about columns. In the examples, only the column name, data type, and position are returned. However, other useful details such as length, nullability, and default values can also be retrieved.

---

#### **5.3 Listing Indexed Columns for a Table**

**Problem**  
You want to list indexes, their columns, and the column position (if available) in the index for a given table.

**Solution**  
- **DB2**  
  Query `SYSCAT.INDEXES` and `SYSCAT.INDEXCOLUSE`:
  ```sql
  select a.tabname, b.indname, b.colname, b.colseq
    from syscat.indexes a,
         syscat.indexcoluse b
   where a.tabname = 'EMP'
     and a.tabschema = 'SMEAGOL'
     and a.indschema = b.indschema
     and a.indname = b.indname
  ```

- **Oracle**  
  Query `SYS.ALL_IND_COLUMNS`:
  ```sql
  select table_name, index_name, column_name, column_position
    from sys.all_ind_columns
   where table_name = 'EMP'
     and table_owner = 'SMEAGOL'
  ```

- **PostgreSQL**  
  Query `PG_CATALOG.PG_INDEXES` and `INFORMATION_SCHEMA.COLUMNS`:
  ```sql
  select a.tablename, a.indexname, b.column_name
    from pg_catalog.pg_indexes a,
         information_schema.columns b
   where a.schemaname = 'SMEAGOL'
     and a.tablename = b.table_name
  ```

- **MySQL**  
  Use the `SHOW INDEX` command:
  ```sql
  show index from emp
  ```

- **SQL Server**  
  Query `SYS.TABLES`, `SYS.INDEXES`, `SYS.INDEX_COLUMNS`, and `SYS.COLUMNS`:
  ```sql
  select a.name table_name,
         b.name index_name,
         d.name column_name,
         c.index_column_id
    from sys.tables a,
         sys.indexes b,
         sys.index_columns c,
         sys.columns d
   where a.object_id = b.object_id
     and b.object_id = c.object_id
     and b.index_id = c.index_id
     and c.object_id = d.object_id
     and c.column_id = d.column_id
     and a.name = 'EMP'
  ```

**Discussion**  
Indexes are important for performance, particularly for queries involving filters or joins. By knowing which columns are indexed, you can anticipate performance issues.

---

#### **5.4 Listing Constraints on a Table**

**Problem**  
You want to list the constraints defined for a table and the columns they are defined on.

**Solution**  
- **DB2**  
  Query `SYSCAT.TABCONST` and `SYSCAT.COLUMNS`:
  ```sql
  select a.tabname, a.constname, b.colname, a.type
    from syscat.tabconst a,
         syscat.columns b
   where a.tabname = 'EMP'
     and a.tabschema = 'SMEAGOL'
     and a.tabname = b.tabname
     and a.tabschema = b.tabschema
  ```

- **Oracle**  
  Query `SYS.ALL_CONSTRAINTS` and `SYS.ALL_CONS_COLUMNS`:
  ```sql
  select a.table_name,
         a.constraint_name,
         b.column_name,
         a.constraint_type
    from all_constraints a,
         all_cons_columns b
   where a.table_name = 'EMP'
     and a.owner = 'SMEAGOL'
     and a.table_name = b.table_name
     and a.owner = b.owner
     and a.constraint_name = b.constraint_name
  ```

- **PostgreSQL, MySQL, and SQL Server**  
  Query `INFORMATION_SCHEMA.TABLE_CONSTRAINTS` and `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`:
  ```sql
  select a.table_name,
         a.constraint_name,
         b.column_name,
         a.constraint_type
    from information_schema.table_constraints a,
         information_schema.key_column_usage b
   where a.table_name = 'EMP'
     and a.table_schema = 'SMEAGOL'
     and a.table_name = b.table_name
     and a.table_schema = b.table_schema
     and a.constraint_name = b.constraint_name
  ```

**Discussion**  
Constraints are critical for ensuring data integrity. This query helps you find information about primary keys, foreign keys, and check constraints.

---

#### **5.5 Listing Foreign Keys Without Corresponding Indexes**

**Problem**  
You want to list tables with foreign key columns that are not indexed.

**Solution**  
- **DB2**  
  Query `SYSCAT.TABCONST`, `SYSCAT.KEYCOLUSE`, `SYSCAT.INDEXES`, and `SYSCAT.INDEXCOLUSE`:
  ```sql
  select fkeys.tabname,
         fkeys.constname,
         fkeys.colname,
         ind_cols.indname
    from (
      select a.tabschema, a.tabname, a.constname, b.colname
        from syscat.tabconst a,
             syscat.keycoluse b
       where a.tabname = 'EMP'
         and a.tabschema = 'SMEAGOL'
         and a.type = 'F'
         and a.tabname = b.tabname
         and a.tabschema = b.tabschema
    ) fkeys
    left join (
      select a.tabschema,
             a.tabname,
             a.indname,
             b.colname
        from syscat.indexes a,
             syscat.indexcoluse b
       where a.indschema = b.indschema
         and a.indname = b.indname
    ) ind_cols
    on (fkeys.tabschema = ind_cols.tabschema
        and fkeys.tabname = ind_cols.tabname
        and fkeys.colname = ind_cols.colname)
   where ind_cols.indname is null
  ```

- **Oracle**  
  Query `SYS.ALL_CONS_COLUMNS`, `SYS.ALL_CONSTRAINTS`, and `SYS.ALL_IND_COLUMNS`:
  ```sql
  select a.table_name,
         a.constraint_name,
         a.column_name,
         c.index_name
    from all_cons_columns a,
         all_constraints b,
         all_ind_columns c
   where a.table_name = 'EMP'
     and a.owner = 'SMEAGOL'
     and b.constraint_type = 'R'
     and a.owner = b.owner
     and a.table_name = b.table_name
     and a.constraint_name = b.constraint_name
     and a.owner = c.table_owner (+)
     and a.table_name = c.table_name (+)
     and a.column_name = c.column_name (+)
     and c.index_name is null
  ```

- **PostgreSQL**  
  Query `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`, `INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS`, `INFORMATION_SCHEMA.COLUMNS`, and `PG_CATALOG.PG_INDEXES`:
  ```sql
  select fkeys.table_name,
         fkeys.constraint_name,
         fkeys.column_name,
         ind_cols.indexname
    from (
      select a.constraint_schema,
             a.table_name,
             a.constraint_name,
             a.column_name
        from information_schema.key_column_usage a,
             information_schema.referential_constraints b
       where a.constraint_name = b.constraint_name
         and a.constraint_schema = b.constraint_schema
         and a.constraint_schema = 'SMEAGOL'
         and a.table_name = 'EMP'
    ) fkeys
    left join (
      select a.schemaname, a.tablename, a.indexname, b.column_name
        from pg_catalog.pg_indexes a,
             information_schema.columns b
       where a.tablename = b.table_name
         and a.schemaname = b.table_schema
    ) ind_cols
    on (fkeys.constraint_schema = ind_cols.schemaname
        and fkeys.table_name = ind_cols.tablename
        and fkeys.column_name = ind_cols.column_name)
   where ind_cols.indexname is null
  ```

- **MySQL**  
  Use `SHOW INDEX` and `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`.

- **SQL Server**  
  Query `SYS.TABLES`, `SYS.FOREIGN_KEYS`, `SYS.COLUMNS`, `SYS.INDEXES`, and `SYS.INDEX_COLUMNS`:
  ```sql
  select fkeys.table_name,
         fkeys.constraint_name,
         fkeys.column_name,
         ind_cols.index_name
    from (
      select a.object_id,
             d.column_id,
             a.name table_name,
             b.name constraint_name,
             d.name column_name
        from sys.tables a
             join sys.foreign_keys b on a.name = 'EMP' and a.object_id = b.parent_object_id
             join sys.foreign_key_columns c on b.object_id = c.constraint_object_id
             join sys.columns d on c.constraint_column_id = d.column_id
                            and a.object_id = d.object_id
    ) fkeys
    left join (
      select a.name index_name,
             b.object_id,
             b.column_id
        from sys.indexes a,
             sys.index_columns b
       where a.index_id = b.index_id
    ) ind_cols
    on (fkeys.object_id = ind_cols.object_id
        and fkeys.column_id = ind_cols.column_id)
   where ind_cols.index_name is null
  ```

**Discussion**  
Foreign keys are essential for ensuring referential integrity. Indexing foreign key columns can reduce locking and improve performance when querying tables with parent-child relationships.

---

#### **5.6 Using SQL to Generate SQL**

**Problem**  
You want to create dynamic SQL statements, perhaps to automate maintenance tasks like counting rows, disabling foreign key constraints, and generating insert scripts.

**Solution**  
SQL can generate other SQL statements dynamically.

- To count the number of rows in all tables:
  ```sql
  select 'select count(*) from ' || table_name || ';' cnts
    from user_tables;
  ```

- To disable foreign keys from all tables:
  ```sql
  select 'alter table ' || table_name ||
         ' disable constraint ' || constraint_name || ';' cons
    from user_constraints
   where constraint_type = 'R';
  ```

- To generate insert scripts from the `EMP` table:
  ```sql
  select 'insert into emp(empno,ename,hiredate) ' || chr(10) ||
         'values( ' || empno || ',' || '''' || ename || '''' ||
         ', to_date(' || '''' || hiredate || '''' || ') );' inserts
    from emp
   where deptno = 10;
  ```

**Discussion**  
Using SQL to generate SQL is a simple and powerful technique, especially useful for automation and creating maintenance scripts for batch tasks.

---

#### **5.7 Describing the Data Dictionary Views in an Oracle Database**

**Problem**  
You are using Oracle and cannot remember the available data dictionary views or their column definitions.

**Solution**  
Oracle provides data dictionary views that document the data dictionary views themselves. You can query `DICTIONARY` and `DICT_COLUMNS` to retrieve descriptions of the data dictionary views.

- To list data dictionary views:
  ```sql
  select table_name, comments
    from dictionary
   order by table_name;
  ```

- To describe the columns in a data dictionary view:
  ```sql
  select column_name, comments
    from dict_columns
   where table_name = 'ALL_TAB_COLUMNS';
  ```

**Discussion**  
Oracle's `DICTIONARY` and `DICT_COLUMNS` views provide self-referencing documentation for the data dictionary, which helps you discover all available views and their descriptions. This is particularly helpful when you need to understand system views and their functionality.

---

#### **5.8 Summing Up**

Metadata queries are essential tools that open up a range of possibilities for automating tasks and managing databases. These queries relieve some of the need to manually inspect your database and can help you ensure data integrity, performance, and scalability. With the techniques in this chapter, you can explore your schema, understand how objects are related, and generate scripts for maintenance.

---

This is the complete extraction of the **Chapter 5** contents, ensuring all relevant details are included. Let me know if you'd like more clarification on any section!