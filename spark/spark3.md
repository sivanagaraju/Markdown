# Mindmap: Spark Execution Model & Architecture

Below is an **exhaustive** mindmap capturing **all details** from the transcripts about Spark’s distributed processing architecture, execution modes, and practical demos—covering everything from **interactive** usage and **spark-submit** to **local mode** vs. **cluster mode** on YARN, plus real-world examples (streaming, batch jobs, multi-node clusters, etc.). **No details are omitted.**

---

## 1. Running Spark Programs: Two Main Approaches

1. **Interactive Clients**  
   - **spark-shell** (Scala) & **pyspark** (Python)  
     - Allows running code **line-by-line**, immediate feedback in the console/REPL.  
     - Used heavily for **learning**, **development**, **exploratory data analysis**.  
   - **Notebooks**  
     - E.g., **Zeppelin**, **Databricks**, **Jupyter**.  
     - Web-based environment; can mix code with markdown/visualizations.  
   - Typically used in **Client Mode** (Driver on local/edge node; Executors on cluster or local threads).

2. **Submit Jobs**  
   - **spark-submit** utility  
     - Packages your Spark application (batch or streaming) for **production** or scheduled runs.  
     - Submits app to cluster → runs without interactive session.  
   - Examples of real jobs:  
     - **Stream Processing**: e.g., reading a news feed in real time, applying ML to route content to users.  
     - **Batch Processing**: e.g., daily YouTube stats job computing watch time over the last 24 hours.  
   - In **production** scenarios, this is the standard approach (Cluster Mode, driver + executors run on cluster).

> **Note**: Some vendors (e.g., **Databricks**) have specialized interfaces (REST APIs, web UI) to submit jobs, but `spark-submit` is **universal** across all distributions.

---

## 2. Spark’s Distributed Processing Model

- **Master-Slave Per Application**  
  - **Driver** = Master process for that specific app.  
    - Responsible for scheduling, task distribution, collecting results.  
  - **Executors** = Slave processes that run tasks in parallel.  
    - Each executor is allocated CPU cores + memory.

- **Separate from the Cluster’s Master/Slave Nodes**  
  - The **Cluster Manager** (YARN, etc.) manages resources across the entire cluster.  
  - Spark requests containers from the Cluster Manager to launch the Driver + Executors *for each application*.

- **Multiple Apps at Once**  
  - If you submit two apps (A1, A2), each gets its **own** Driver + separate Executors.  
  - Each Spark application is **isolated** from others (unless configured for resource sharing).

---

## 3. Cluster Managers & Execution Modes

### 3.1 Common Cluster Managers

1. **Local**  
   - No actual cluster; runs everything on a single machine with multi-threading.  
   - **local[3]** = 1 Driver thread + 2 Executor threads (total 3).  
   - **local** (no number) = single-threaded.  
   - Excellent for **development** and **testing** on your laptop/desktop.

2. **YARN** (Hadoop)  
   - Standard in on-premises Hadoop or cloud-based distributions (e.g., **Google Dataproc**, **Amazon EMR**, **Azure HDInsight**).  
   - Spark obtains containers from YARN for the Driver & Executors.  
   - Allows dynamic resource allocation (scale executors up/down).

3. **Other Managers**  
   - **Kubernetes**, **Mesos**, or **Databricks-managed** environments.  
   - All follow the same principle: Spark requests resources, obtains containers, launches Driver + Executors.

### 3.2 Execution Modes

1. **Client Mode**  
   - Driver runs **where you launch** the job (e.g., your local machine or edge node).  
   - Executors run on the cluster (or local threads if using local manager).  
   - Interactive usage: if the client closes, the Driver terminates → job ends.

2. **Cluster Mode**  
   - Driver **also** runs on the cluster nodes.  
   - You can close your client session; job continues independently.  
   - Ideal for **long-running** or production apps submitted via `spark-submit`.

---

## 4. Summarizing “When to Use What”

- **Local (Client Mode)**  
  - Single-node dev/test scenario on your machine or VM.  
  - Good for **learning, debugging**, small data tasks.

- **YARN (Client Mode)**  
  - Interactive exploration on a real multi-node cluster using notebooks or `spark-shell` from an edge node.  
  - Typically for **data scientists** who want direct access to cluster data and resources but prefer an interactive session.

- **YARN (Cluster Mode)**  
  - `spark-submit --master yarn --deploy-mode cluster`  
  - Common for **production** or scheduled jobs. The Driver and Executors remain active on cluster until completion (independent of client session).

> **Other**: The same logic applies if you use **Databricks** (its internal manager) or **Kubernetes**. The basic distinction between **Client** vs. **Cluster** mode remains.

---

## 5. Practical Demos & Examples

### 5.1 Local Client Mode Demo (spark-shell / pyspark)

1. **spark-shell** example:
   ```bash
   spark-shell --master local[3] --driver-memory 2g
   ```
   - Everything in **one JVM**: 1 driver thread + 2 executor threads (3 total).  
   - Ran a simple command like reading JSON with:
     ```scala
     val df = spark.read.json("/path/to/json")
     df.show()
     ```
   - **SparkContext Web UI** (often at `localhost:4040`) shows only one process because driver+executors share the same JVM.

2. **UI Note**:  
   - The Spark UI is available only **while** the application/shell is running.  
   - Once you exit the shell (`:q`), the UI is no longer accessible.

---

### 5.2 Installing a Multi-Node Spark Cluster (Google Cloud Demo)

1. **Google Cloud Dataproc**  
   - Created a **4-node** YARN cluster (1 master, 3 workers).  
   - Spark version 2.4, enabled components like **Anaconda**, **Zeppelin**.  
   - Configured minimal CPU/memory on each node to manage cost.  
   - Post-creation:
     - Access to **Spark History Server**, **YARN ResourceManager**, **Zeppelin** Notebook, etc.  
   - Clusters can be **deleted** after use to save money; re-created on demand.

2. **Storage**  
   - Created a **GCS bucket** for cluster storage.  
   - Must keep the bucket in the same region as the cluster for best performance.

---

### 5.3 YARN Client Mode Demo

- **spark-shell** on the master node:
  ```bash
  spark-shell \
    --master yarn \
    --deploy-mode client \
    --driver-memory 1g \
    --executor-memory 500m \
    --num-executors 2
  ```
- **Spark UI**:  
  - Current running job often viewed in **YARN ResourceManager** → “Application Master” link.  
  - **Spark History Server** shows finished or older jobs.  
- Observed dynamic resource allocation: if idle, YARN might kill extra executors.

---

### 5.4 Working with a Notebook in YARN

1. **Zeppelin Notebook**  
   - Access Zeppelin web UI (need cluster or admin-provided URL).  
   - By default, `%spark` or `%scala` interpreter cells.  
   - For Python, use `%pyspark`.  
   - After first cell execution, the Driver + Executors start on YARN in “Client Mode.”  
   - Inspect running job via **YARN ResourceManager** or after finishing in Spark History Server.

2. **Dynamic Allocation**  
   - If the Notebook is idle, one or more executors may be released.

---

### 5.5 `spark-submit` Demo (YARN Cluster Mode)

1. **spark-submit** is standard for production or scheduled Spark apps:
   ```bash
   spark-submit \
     --master yarn \
     --deploy-mode cluster \
     my_pyspark_script.py [app arguments...]
   ```
2. Example: *SparkPi* approximation
   - Copied `pi.py` onto the cluster node.
   - Ran:
     ```bash
     spark-submit \
       --master yarn \
       --deploy-mode cluster \
       pi.py 100
     ```
   - Received an **Application ID**; job continues on the cluster, driver runs in cluster node.  
   - Track progress in YARN or Spark History Server once it completes.

3. **Why** cluster mode?  
   - Freed from having to keep the client shell open.  
   - Suited for long/complex jobs or fully-automated pipelines.

---

## 6. Other Key Points & Observations

- **Stream vs. Batch** Examples  
  - **Stream**: continuous real-time data (e.g., news feed + ML classification).  
  - **Batch**: scheduled periodic job (e.g., daily YouTube watch-time stats).  
- **Spark UI & Logging**  
  - **SparkContext UI** (active) vs. **Spark History Server** (completed jobs).  
  - In secure enterprise setups, you often need permission from Ops to access these UIs.
- **Dynamic Resource Allocation**  
  - Executors can be scaled up/down automatically, especially under YARN.  
  - Unused executors may be killed if idle to release cluster resources.
- **Local Mode** is typically single-machine, **Cluster Mode** spans multiple servers.  
- Exiting the shell or Notebook in **Client Mode** kills the Driver → terminates the job.

---

## 7. Section Summary & What’s Next

- **We learned**:
  1. How to **execute** Spark programs: interactive tools (shell, notebooks) vs. `spark-submit`.
  2. The internal **Driver + Executors** model and the role of the **Cluster Manager**.
  3. **Client Mode** vs. **Cluster Mode** with demos on local machines and multi-node YARN clusters.
  4. Monitoring via **SparkContext UI**, **Spark History Server**, and **YARN ResourceManager**.

- **Next Steps**:
  - We’ll focus on **creating Spark programs**—understanding how to write efficient and correct code using Spark’s APIs.
  - The foundational knowledge of execution architecture helps ensure we know **where** our code runs and **how** it scales.

> **“Keep learning and keep growing!”**
