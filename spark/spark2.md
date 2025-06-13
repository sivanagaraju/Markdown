# Mindmap: Installing & Using Apache Spark – Comprehensive Guide

Below is a **detailed** mindmap consolidating **all** information from the transcripts about different Spark development environments, including **Mac** and **Windows** setups (local mode, IDE), **Databricks Community Edition**, and **Jupyter/Anaconda** usage. Every step and detail mentioned in the lectures is captured here.

---

## 1. Spark Development Environments – Overview

- **Primary Ways to Access Spark**  
  1. **Local Mode (Command Line REPL)**  
     - Simplest approach, all Spark processes on a **single machine** or VM.  
     - Access Spark via CLI tools: `spark-shell` (Scala), `pyspark` (Python).  
     - Useful for quick examples & small-scale data processing.  
  2. **Local Mode (IDE Integration)**  
     - Example: **PyCharm** or any Python-friendly IDE.  
     - Great for **iterative development**, debugging, code navigation, unit tests.  
     - Most course examples use PyCharm with Python.  
  3. **Databricks Cloud Environment**  
     - Managed Spark service on AWS/Azure/GCP.  
     - **Community Edition** offers a free single-node 6 GB cluster + notebooks.  
     - Popular commercial offering from Databricks, user-friendly notebooks.  
  4. **Jupyter Notebooks (Anaconda)**  
     - Common among data scientists for **step-by-step** exploration.  
     - Runs on local machine, bridging Python + Spark via `findspark`.  
  5. **Commercial Cloud Options**  
     - Amazon EMR, Google Dataproc, Azure HDInsight, etc.  
     - Often used in real-world production, but not deeply covered in the course.  
  6. **Multi-Node Cluster Environments**  
     - True distributed mode on multiple machines (e.g., Cloudera, GCP).  
     - For learning, single-machine setups suffice, but exposure to clusters is useful.  

---

## 2. Mac Users – Apache Spark in Local Mode (Command Line REPL)

### 2.1 Prerequisites

- **JDK 8 or 11**  
  - Spark requires **Java 8** or **Java 11** (other versions not recommended).  
  - Check current Java version:  
    ```bash
    java -version
    ```
  - If older or incompatible, remove it and install the correct version.

- **Setting `JAVA_HOME`**  
  - For JDK installed via **Homebrew**:  
    1. Install Homebrew (if missing) from [brew.sh](https://brew.sh).  
    2. `brew install openjdk@11` (or JDK 8 if needed).  
    3. `export JAVA_HOME="/usr/local/Cellar/openjdk@11/..."` (actual path may vary).  
    4. Add the above export line to your shell startup (`~/.zshrc`, `~/.bashrc`, etc.).  
  - For a **pre-installed** JDK in `/Library/Java/JavaVirtualMachines/...`:  
    1. Use command substitution:
       ```bash
       export JAVA_HOME=$(/usr/libexec/java_home -v 11)
       ```
    2. Place in the same startup script.

### 2.2 Download & Install Spark

1. **Download Spark** tar file from [spark.apache.org](https://spark.apache.org/).
2. Extract (untar) into a chosen directory, e.g.:
   ```bash
   mkdir ~/spark-install
   mv ~/Downloads/spark-3.x-bin-hadoop2.7.tgz ~/spark-install
   cd ~/spark-install
   tar -xvf spark-3.x-bin-hadoop2.7.tgz
   ```
3. **Set `SPARK_HOME`**:
   ```bash
   export SPARK_HOME="~/spark-install/spark-3.x-bin-hadoop2.7"
   ```
4. Place that export in `.zshrc`, `.bashrc`, or equivalent.

### 2.3 Update `PATH`

- Add Spark binaries to `PATH`:
  ```bash
  export PATH="$SPARK_HOME/bin:$PATH"
  ```
- Again, add it to your startup script.

### 2.4 Test Spark Shell

- **Scala REPL**:  
  ```bash
  spark-shell
  ```
  - Quit with `:q`.
- **PySpark**:
  ```bash
  pyspark
  ```
  - If it defaults to Python 2.7, install Python 3:
    ```bash
    brew install python@3
    export PYSPARK_PYTHON="/usr/local/bin/python3"
    ```
  - Add to your startup scripts so it persists.

### 2.5 Summary (Mac Local)

1. Confirm **Java** version (8 or 11), remove older Java if needed.  
2. Configure `JAVA_HOME`.  
3. Download & untar **Spark**.  
4. Set `SPARK_HOME` and update `PATH`.  
5. (For Python) ensure **Python 3** → set `PYSPARK_PYTHON`.  
6. Launch `spark-shell` or `pyspark`.

---

## 3. Windows Users – Apache Spark in Local Mode (Command Line REPL)

### 3.1 Download & Extract Spark

1. From [spark.apache.org](https://spark.apache.org/) or course materials, get Spark 3.x.  
2. Unzip or untar into a folder, e.g., `C:\spark3`.  
3. Inside `C:\spark3\bin`, you’ll see `.cmd` files for Windows usage.

### 3.2 Handling `winutils.exe` Error

- Spark on Windows may throw:
  ```
  Could not locate winutils.exe in the Hadoop binary path
  ```
- **Solution**:
  1. Download (or use provided) `winutils.exe` from the course resources or GitHub.  
  2. Create a folder, e.g., `C:\hdp\bin`.
  3. Place `winutils.exe` in `C:\hdp\bin`.
  4. **Set `HADOOP_HOME`**:
     ```bat
     setx HADOOP_HOME "C:\hdp"
     ```
     (Close & reopen cmd prompt for changes to apply.)

### 3.3 Python Environment

- **PySpark** requires Python 3 on Windows:
  - Install **Anaconda** or standard Python 3.  
  - If `pyspark.cmd` says “Python not recognized”, or uses Python 2.7, specify location:
    ```bat
    set PYSPARK_PYTHON="C:\Users\YourName\Anaconda3\python.exe"
    ```
  - Then run `pyspark.cmd` again.

### 3.4 Test Spark

- **Scala Shell**:
  ```bat
  cd C:\spark3\bin
  spark-shell.cmd
  ```
- **PySpark**:
  ```bat
  pyspark.cmd
  ```
  - Confirm it uses the correct Python 3 environment.

---

## 4. Windows Users – Apache Spark in the IDE (PyCharm)

### 4.1 Prerequisites

- **PyCharm** (Community or Pro).  
- **Anaconda** (or another Python 3 environment).  
- Spark extracted at e.g. `C:\spark3`.  
- `winutils.exe` if needed → `HADOOP_HOME`.

### 4.2 Example Project Setup

1. **Get Example Code from GitHub**  
   - A repository containing `HelloSpark.py` and other examples.  
   - Extract it to `C:\spark-examples` (or any directory).
2. **Open in PyCharm**  
   - PyCharm might auto-detect an interpreter incorrectly.  
   - Go to **File → Settings → Project → Python Interpreter**:
     - Set to **No Interpreter** first, then configure.  
     - Create or pick a **Conda environment** (Python 3).  
   - In PyCharm’s environment settings, **Install `pyspark`** from the package list.

### 4.3 Running a Spark Program

- **Open `HelloSpark.py`**.  
- Some scripts expect command-line **arguments** (e.g., data file paths).  
  - Go to **Run → Edit Configurations → Parameters**.  
- If you see a log warning: “Using Spark default log4j profile”:
  1. Check `SPARK_HOME` is set.  
  2. Rename `spark-defaults.conf.template` → `spark-defaults.conf` in `SPARK_HOME\conf`.  
  3. Add lines from the example GitHub config to point Spark to custom `log4j.properties`.  
- **Run** the script:
  - Verify output in PyCharm console.  
  - Possibly see an `app-logs` directory with log files.

### 4.4 Running Unit Tests

- Some examples include test files (e.g. `test_HelloSpark.py`).  
- Right-click → **Run** → check if tests pass.  

---

## 5. Apache Spark in Cloud – Databricks Community Edition

### 5.1 Introduction to Databricks

- **Managed Spark** environment with extensive features.  
- Community Edition: free single-node cluster with **6 GB** memory.  
- All code runs in a **browser-based** Notebook interface.  
- Some commercial/enterprise features are restricted in Community Edition.

### 5.2 Getting Access

1. Go to [databricks.com](https://databricks.com/) → **Try Databricks** → **Community Edition**.  
2. Register using email; verify link in inbox.  
3. On first login, you’ll see the **Databricks UI** with options for clusters, notebooks, etc.

### 5.3 Creating a Cluster

- **Clusters** → **Create Cluster** → name it, pick Spark version.  
- For Community Edition, Databricks provisions a **single VM** (6 GB).  
- Inactive clusters auto-terminate after ~2 hours.  

### 5.4 Working with Notebooks

1. Create a new **Notebook**.  
   - Choose default language (Python, Scala, SQL, or R).  
   - Attach notebook to the running cluster.  
2. **Write Spark code** in notebook cells. Example:
   - Use `%python` or `%scala` if needed, or directly in chosen notebook language.  
   - Access data from **DBFS** (Databricks File System).  
3. Run code cells with Shift+Enter or the “Run” button.  
4. **Visualizations**: Databricks notebooks offer built-in charting from query results.  
5. **Terminate/Delete** your cluster when done.  
   - Data remains stored in DBFS or associated tables, so you can re-create the cluster later.  

---

## 6. Apache Spark in Anaconda – Jupyter Notebook

### 6.1 Installing Anaconda

- Download **Anaconda** Individual Edition from [anaconda.com](https://www.anaconda.com/products/individual).  
- Choose Python 3 Installer for your OS (Windows/Mac/Linux).  
- Installation is straightforward (Graphical Installer or CLI).

### 6.2 Steps to Enable Spark in Jupyter

1. **Set `SPARK_HOME`**  
   - Point it to your local Spark install, e.g. `C:\spark3` or `~/spark-install/spark-3.x`.
2. **Install `findspark`**  
   - Open an **Anaconda Prompt** (or terminal if on Mac/Linux):
     ```bash
     pip install findspark
     ```
   - Then close the prompt.
3. **Initialize in Jupyter**  
   - Launch **Jupyter Notebook** from Anaconda.  
   - Create a new **Python 3** notebook.  
   - In the first cell:
     ```python
     import findspark
     findspark.init()
     ```
   - Then import Spark libraries:
     ```python
     from pyspark.sql import SparkSession
     spark = SparkSession.builder.appName("MyApp").getOrCreate()
     df = spark.read.json("path/to/jsonfile")
     df.show()
     ```
   - This **bridges** Python and the local Spark runtime.

### 6.3 Typical Use Cases

- **Interactive** data exploration and ML experiments.  
- Step-by-step approach to transformations.  
- Full Python ecosystem from Anaconda for scientific computing.

---

## 7. Additional Notes & Best Practices

1. **Local vs. Cluster**  
   - All these local setups (command line, IDE, Jupyter) essentially run Spark on a **single machine** (no actual distribution).  
   - Real production often uses **multi-node** clusters (Hadoop YARN, Kubernetes, or Databricks jobs).
2. **Environment Variables**  
   - Keep track of `JAVA_HOME`, `SPARK_HOME`, `HADOOP_HOME` (Windows), `PYSPARK_PYTHON`.  
   - Add them to your shell or system environment for consistency.
3. **Python Versions**  
   - Always prefer **Python 3**; Spark does not recommend Python 2.7 anymore.  
   - Using **Anaconda** simplifies library management.
4. **Log Configuration**  
   - Custom `log4j.properties` can reduce excessive console logs.  
   - Place relevant configs in `SPARK_HOME/conf/spark-defaults.conf` or pass them as arguments.
5. **Databricks**  
   - Great for quickly **prototyping** or learning.  
   - Auto-managed environment, no manual cluster config or environment variables needed.
6. **Testing & Debugging**  
   - Use IDEs like PyCharm for robust debugging & unit testing.  
   - Notebooks for incremental development & data exploration.


