# APScheduler Complete Guide for FastAPI

## What is APScheduler?

**APScheduler** (Advanced Python Scheduler) is a lightweight, in-process task scheduler that lets you run Python functions:

- At specific times (like cron)
- At fixed intervals
- Once at a specific date/time
- Immediately in the background

Unlike Celery (which needs Redis/RabbitMQ), APScheduler runs **inside your Python application** with optional database persistence.

---

## How It Works with FastAPI

```mermaid
flowchart TB
    subgraph PROCESS["Single Python Process"]
        MAIN["Main Thread<br/>(FastAPI/Uvicorn)"]
        BG["Background Thread<br/>(APScheduler)"]
        EXECUTOR["ThreadPoolExecutor<br/>(Job execution)"]
    end
    
    subgraph EXTERNAL["External (Optional)"]
        JOBSTORE["Database<br/>(Job persistence)"]
    end
    
    MAIN -->|"Starts on app startup"| BG
    BG -->|"Runs jobs in"| EXECUTOR
    BG <-->|"Loads/saves jobs"| JOBSTORE
    
    MAIN -.->|"Same process"| BG
```

> [!IMPORTANT]
> APScheduler runs **in the same process** as FastAPI. When FastAPI stops, APScheduler stops. When FastAPI starts, APScheduler starts.

---

## Lifecycle: Start, Stop, Restart

### What Happens When You Start the App?

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Create scheduler with database persistence
scheduler = BackgroundScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
    }
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== STARTUP ==========
    # 1. APScheduler loads all saved jobs from database
    # 2. Jobs that were scheduled before restart are restored
    # 3. Scheduler thread starts running
    scheduler.start()
    print("✅ Scheduler started - resuming any pending jobs from DB")
    
    yield  # App is running here
    
    # ========== SHUTDOWN ==========
    # 1. Scheduler stops accepting new jobs
    # 2. Waits for running jobs to complete (graceful)
    # 3. Job state is already in DB, safe to stop
    scheduler.shutdown(wait=True)
    print("🛑 Scheduler stopped gracefully")

app = FastAPI(lifespan=lifespan)
```

### What Happens During Restart?

```mermaid
sequenceDiagram
    participant APP as FastAPI App
    participant SCHED as APScheduler
    participant DB as Database (JobStore)
    
    Note over APP,DB: === RUNNING STATE ===
    SCHED->>DB: Job state saved continuously
    
    Note over APP,DB: === STOP (Ctrl+C or restart) ===
    APP->>SCHED: shutdown(wait=True)
    SCHED->>SCHED: Wait for running jobs
    SCHED->>DB: Final state already persisted
    SCHED-->>APP: Shutdown complete
    APP->>APP: Process exits
    
    Note over APP,DB: === START AGAIN ===
    APP->>SCHED: scheduler.start()
    SCHED->>DB: Load all persisted jobs
    DB-->>SCHED: Jobs with next_run_time
    SCHED->>SCHED: Resume scheduling
    
    Note over SCHED: Missed jobs during downtime?<br/>Depends on misfire_grace_time
```

### Handling Missed Jobs (Misfire)

If your app was down when a job was supposed to run:

```python
scheduler = BackgroundScheduler(
    job_defaults={
        # If job was missed by less than 60 seconds, still run it
        'misfire_grace_time': 60,
        
        # If multiple runs were missed, combine into one run
        'coalesce': True
    }
)
```

---

## APScheduler Features

| Feature | Description |
|---------|-------------|
| **Multiple Trigger Types** | Interval, Cron, Date (one-time) |
| **Job Persistence** | SQLAlchemy, MongoDB, Redis backends |
| **Concurrency Control** | Limit concurrent instances of same job |
| **Timezone Support** | Schedule in any timezone |
| **Job Events** | Listen to job execution, errors, missed runs |
| **Thread/Process Pool** | Execute jobs in threads or processes |
| **Pause/Resume** | Pause and resume individual jobs |
| **Dynamic Scheduling** | Add/remove/modify jobs at runtime |

---

## Code Examples with Explanations

### Example 1: Basic Interval Job

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Create a scheduler that runs in a background thread
scheduler = BackgroundScheduler()

def check_pending_jobs():
    """This function will be called every 2 minutes"""
    print(f"[{datetime.now()}] Checking for pending jobs...")
    # Your logic here: query DB, check Spark status, etc.

# Add a job that runs every 2 minutes
# - 'interval': Run repeatedly at fixed intervals
# - id: Unique identifier (important for persistence)
# - replace_existing: If job with this ID exists, replace it
scheduler.add_job(
    check_pending_jobs,           # Function to call
    trigger='interval',           # Trigger type
    minutes=2,                    # Interval
    id='check_pending_jobs',      # Unique job ID
    replace_existing=True         # Replace if exists
)

scheduler.start()
```

### Example 2: Cron-style Scheduling

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def cleanup_old_logs():
    """Run daily at 2:30 AM to clean up old log entries"""
    print("Cleaning up logs older than 30 days...")

def generate_daily_report():
    """Run every weekday at 9 AM"""
    print("Generating daily report...")

# Cron-style: Run at 2:30 AM every day
scheduler.add_job(
    cleanup_old_logs,
    CronTrigger(hour=2, minute=30),
    id='daily_cleanup'
)

# Cron-style: Run at 9 AM, Monday-Friday
scheduler.add_job(
    generate_daily_report,
    CronTrigger(
        day_of_week='mon-fri',  # Monday to Friday
        hour=9,                  # 9 AM
        minute=0
    ),
    id='daily_report'
)

scheduler.start()
```

### Example 3: Database Persistence (Your Use Case)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Configure with database persistence
# Jobs survive app restarts!
jobstores = {
    'default': SQLAlchemyJobStore(
        url='postgresql://user:pass@localhost/mydb',
        tablename='apscheduler_jobs'  # Custom table name
    )
}

# Use a thread pool to run jobs concurrently
executors = {
    'default': ThreadPoolExecutor(max_workers=10)
}

# Default settings for all jobs
job_defaults = {
    'coalesce': True,           # Combine missed runs into one
    'max_instances': 1,         # Only one instance per job at a time
    'misfire_grace_time': 300   # 5 minutes grace for missed jobs
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

def poll_spark_status(request_id: str, spark_job_id: str):
    """
    Poll Spark for job status.
    This function will be called repeatedly until the job completes.
    """
    from your_app.services import get_spark_status, publish_to_kafka
    
    status = get_spark_status(spark_job_id)
    
    if status['state'] in ['COMPLETED', 'FAILED']:
        publish_to_kafka(request_id, status)
        # Remove this job since it's done
        scheduler.remove_job(request_id)
        return f"Job {request_id} completed"
    
    return f"Job {request_id} still running"

# When a POST request comes in, schedule polling for that specific job
def schedule_polling_for_request(request_id: str, spark_job_id: str):
    """Called from your FastAPI endpoint after submitting to Spark"""
    scheduler.add_job(
        poll_spark_status,
        trigger='interval',
        seconds=30,                          # Poll every 30 seconds
        id=request_id,                       # Use request_id as job ID
        args=[request_id, spark_job_id],     # Arguments to pass
        replace_existing=True,
        max_instances=1
    )
    print(f"Scheduled polling for {request_id}")
```

### Example 4: Event Listeners (Error Handling)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import (
    EVENT_JOB_EXECUTED,     # Job ran successfully
    EVENT_JOB_ERROR,        # Job raised an exception
    EVENT_JOB_MISSED,       # Job missed its scheduled time
    EVENT_JOB_ADDED,        # New job was added
    EVENT_JOB_REMOVED       # Job was removed
)

scheduler = BackgroundScheduler()

def job_executed_listener(event):
    """Called when a job runs successfully"""
    print(f"✅ Job {event.job_id} executed successfully")
    print(f"   Return value: {event.retval}")

def job_error_listener(event):
    """Called when a job raises an exception"""
    print(f"❌ Job {event.job_id} failed!")
    print(f"   Exception: {event.exception}")
    print(f"   Traceback: {event.traceback}")
    
    # Log to your database
    log_to_db(
        request_id=event.job_id,
        event_type="JOB_ERROR",
        error=str(event.exception)
    )

def job_missed_listener(event):
    """Called when a job was scheduled but missed"""
    print(f"⚠️ Job {event.job_id} missed its scheduled time")

# Register listeners
scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
scheduler.add_listener(job_missed_listener, EVENT_JOB_MISSED)

scheduler.start()
```

### Example 5: Dynamic Job Management

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# ===== ADD A JOB =====
scheduler.add_job(
    my_function,
    trigger='interval',
    seconds=60,
    id='my_job'
)

# ===== GET JOB INFO =====
job = scheduler.get_job('my_job')
print(f"Next run time: {job.next_run_time}")
print(f"Job function: {job.func}")

# ===== PAUSE A JOB =====
# Job stays in scheduler but won't run
scheduler.pause_job('my_job')
print("Job paused - won't run until resumed")

# ===== RESUME A JOB =====
scheduler.resume_job('my_job')
print("Job resumed - will run at next scheduled time")

# ===== MODIFY A JOB =====
# Change the interval from 60 to 120 seconds
scheduler.reschedule_job(
    'my_job',
    trigger='interval',
    seconds=120
)
print("Job interval changed to 120 seconds")

# ===== REMOVE A JOB =====
scheduler.remove_job('my_job')
print("Job removed from scheduler")

# ===== LIST ALL JOBS =====
for job in scheduler.get_jobs():
    print(f"Job: {job.id}, Next run: {job.next_run_time}")
```

### Example 6: One-Time Scheduled Job

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()
scheduler.start()

def send_reminder(user_id: str, message: str):
    """Send a reminder notification"""
    print(f"Sending reminder to {user_id}: {message}")

# Schedule a one-time job for 1 hour from now
run_time = datetime.now() + timedelta(hours=1)

scheduler.add_job(
    send_reminder,
    trigger='date',              # One-time trigger
    run_date=run_time,           # When to run
    args=['user123', 'Meeting in 5 minutes!'],
    id='reminder_user123'
)

print(f"Reminder scheduled for {run_time}")
```

---

## Full FastAPI Integration Example

```python
"""
Complete example: FastAPI + APScheduler with database persistence
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import uuid
from datetime import datetime

# ========== SCHEDULER SETUP ==========

DATABASE_URL = "sqlite:///./scheduler.db"

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

executors = {
    'default': ThreadPoolExecutor(max_workers=10)
}

job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 60
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

# ========== EVENT LISTENERS ==========

def on_job_executed(event):
    print(f"[{datetime.now()}] ✅ Job {event.job_id} completed")

def on_job_error(event):
    print(f"[{datetime.now()}] ❌ Job {event.job_id} failed: {event.exception}")

scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

# ========== JOB FUNCTIONS ==========

def poll_transfer_status(request_id: str):
    """
    Called by scheduler to check transfer status.
    This runs in a background thread, not blocking the API.
    """
    print(f"[{datetime.now()}] Polling status for {request_id}")
    
    # Simulate checking external API
    import random
    status = random.choice(['RUNNING', 'RUNNING', 'COMPLETED'])
    
    if status == 'COMPLETED':
        print(f"[{datetime.now()}] {request_id} completed! Removing job.")
        scheduler.remove_job(request_id)
        # Here you would publish to Kafka
    else:
        print(f"[{datetime.now()}] {request_id} still running...")

# ========== FASTAPI APP ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    scheduler.start()
    print(f"[{datetime.now()}] 🚀 Scheduler started")
    
    # Print existing jobs (recovered from DB)
    jobs = scheduler.get_jobs()
    if jobs:
        print(f"Recovered {len(jobs)} jobs from database:")
        for job in jobs:
            print(f"  - {job.id}: next run at {job.next_run_time}")
    
    yield
    
    # Shutdown: Stop the scheduler gracefully
    scheduler.shutdown(wait=True)
    print(f"[{datetime.now()}] 🛑 Scheduler stopped")

app = FastAPI(lifespan=lifespan)

# ========== API MODELS ==========

class SubmitRequest(BaseModel):
    data: dict

class SubmitResponse(BaseModel):
    request_id: str
    message: str

# ========== API ENDPOINTS ==========

@app.post("/submit", response_model=SubmitResponse)
async def submit_job(request: SubmitRequest):
    """
    Accept a job request, schedule background polling.
    """
    request_id = str(uuid.uuid4())
    
    # Schedule polling every 30 seconds for this request
    scheduler.add_job(
        poll_transfer_status,
        trigger='interval',
        seconds=30,
        id=request_id,
        args=[request_id],
        replace_existing=True
    )
    
    return SubmitResponse(
        request_id=request_id,
        message="Job scheduled. Polling will begin shortly."
    )

@app.get("/jobs")
async def list_jobs():
    """List all scheduled jobs"""
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        }
        for job in jobs
    ]

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a scheduled job"""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    scheduler.remove_job(job_id)
    return {"message": f"Job {job_id} cancelled"}

# Run with: uvicorn main:app --reload
```

---

## Comparison: Why APScheduler Over Alternatives

| Feature | APScheduler | Celery | Background Threads |
|---------|-------------|--------|-------------------|
| **External Dependencies** | None (optional DB) | Redis/RabbitMQ required | None |
| **Setup Complexity** | Low | High | Very Low |
| **Persistence** | Built-in | Via broker | Manual |
| **Distributed** | No (single process) | Yes (multiple workers) | No |
| **Cron Support** | Yes | Yes | Manual |
| **Best For** | Single-instance apps | Distributed systems | Simple tasks |

> [!TIP]
> APScheduler is perfect for your use case - single FastAPI app needing background polling with persistence.

---

## Summary

1. **APScheduler runs inside your FastAPI process** - starts and stops with your app
2. **With SQLAlchemy JobStore**, jobs survive app restarts
3. **When app restarts**, scheduler loads saved jobs and resumes polling
4. **Event listeners** let you log errors and successes
5. **Dynamic scheduling** lets you add/remove jobs based on API requests
