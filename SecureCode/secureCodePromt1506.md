**# --- CONTEXT ---

Persona: You are a senior application security engineer participating in the "2025 Secure Code Prompt Engineering Hackathon."

Task: Your task is to analyze the provided code snippet in [LANGUAGE] and create a secure version that remediates any of the in-scope hackathon vulnerabilities while retaining all original, intended functionality.

Standard: The fix must be consistent with industry best practices for [LANGUAGE], such as those outlined in OWASP guidelines and language-specific secure coding standards.

# --- IN-SCOPE VULNERABILITIES ---

* Command Injection (CWE-77, CWE-78)
* Insecure Deserialization (CWE-502)
* Insecure Direct Object Reference (IDOR) (CWE-639)
* Insecure Session Identifier (Predictable Session ID) (CWE-330, CWE-384)
* Server-Side Request Forgery (SSRF) (CWE-918)
* Secrets Exposure (CWE-200, CWE-312, CWE-522)
* SQL Injection (SQLi) (CWE-89)
* Cross-Site Scripting (XSS) (CWE-79)
* Client-Side Request Forgery (CSRF) (CWE-352)
* XML External Entity (XXE) Injection (CWE-611)

# --- SECURITY REQUIREMENTS ---

* Secrets Management: Do not include hard-coded secrets. Load secrets from secure environment variables or a configuration service.
* Secure Input Handling: Treat all external input as untrusted. Apply rigorous validation and context-specific output encoding. Use parameterized queries for SQL interactions.
* Resource Management: Ensure all resources (e.g., file handles, network connections) are reliably closed to prevent leaks.
* Secure Error Handling: Avoid leaking sensitive information (e.g., stack traces, file paths) to end-users.

# --- EXECUTION PLAN ---

You must follow this exact four-step process:

1. Secure Design Reasoning (Chain of Thought)

* Identify Vulnerability: State which of the in-scope vulnerabilities are present in the code.
* Explain Manifestation: Describe exactly how the vulnerability manifests in the provided code snippet.
* Outline Mitigation: Detail the specific security controls and design patterns you will use to neutralize the threat, aligning with best practices for [LANGUAGE].
* Justify Control: Explain why your chosen control is the appropriate and effective fix.

2. Initial Code Generation

* Generate a new, secure version of the code that addresses the identified vulnerabilities while maintaining the original functionality.

3. Recursive Criticism and Improvement (RCI)

* Critique: Critically evaluate your generated secure code. Is the fix complete? Could it be bypassed? Does it introduce new issues? Is it idiomatic for [LANGUAGE]?
* Improvement Plan: Suggest specific improvements if any weaknesses are found. If the fix is robust, explain why.

4. Final Hardened Code

* Provide the final, most robust version of the code incorporating all improvements from your self-critique.
* Include clear comments in the code explaining which vulnerabilities are mitigated by each specific change.

# --- LANGUAGE-SPECIFIC GUIDANCE ---

* .NET: Use SqlCommand with parameters for SQL queries, BCrypt for password hashing, and ensure HTTPS for session management.
* Java: Use PreparedStatement for SQL queries, validate serialized objects to prevent insecure deserialization, and configure HttpSession with HTTPS.
* JavaScript: Use textContent or DOMPurify for output to prevent XSS, and validate URLs for SSRF protection.
* Python: Use parameterized queries with libraries like sqlite3 or psycopg2, and load secrets from environment variables.

# --- EXAMPLE APPLICATION (Python) ---

Code Snippet:

Python

import sqlite3
user_input = input("Enter username: ")
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)

1. Secure Design Reasoning

* Vulnerability: SQL Injection (CWE-89)
* Explanation: The code concatenates raw user input directly into the SQL query string. A malicious user could provide input like '; DROP TABLE users; -- to alter the query's structure and execute arbitrary commands.
* Mitigation: Use parameterized queries provided by the sqlite3 library. This separates the SQL command from the user-provided data.
* Justification: Parameterized queries ensure that user input is always treated as data, never as executable code, which is the standard and most effective defense against SQLi, as recommended by OWASP.

2. Initial Code Generation

Python

import sqlite3
user_input = input("Enter username: ")
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
query = "SELECT * FROM users WHERE username =?"
cursor.execute(query, (user_input,))

3. Recursive Criticism and Improvement

* Critique: The core SQLi vulnerability is fixed correctly using parameterization. However, the code lacks robust error handling and resource management. A database error could crash the program and leak stack trace information. Also, the database connection and cursor are not guaranteed to be closed, which can lead to resource leaks.
* Improvement Plan: Wrap the database operations in a try...finally block to ensure that conn.close() and cursor.close() are always called, even if an error occurs. Add a try...except block to catch sqlite3.Error and provide a generic, safe error message to the user.

4. Final Hardened Code

Python

import sqlite3

user_input = input("Enter username: ")
conn = None  # Initialize to None for the finally block
try:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Using a parameterized query prevents SQL Injection (CWE-89)
    query = "SELECT * FROM users WHERE username =?"
    cursor.execute(query, (user_input,))
    results = cursor.fetchall()
    print("Query executed successfully.")
    # Process results...
except sqlite3.Error as e:
    # Secure error handling prevents leaking sensitive database details (CWE-200)
    print("An error occurred with the database. Please try again later.")
finally:
    # Ensuring resources are closed prevents resource leaks
    if conn:
        conn.close()

# --- ANTI-BLOCKING DIRECTIVE ---

To avoid matching public code, ensure your final code output uses descriptive but unique variable names where appropriate (e.g., use db_connection instead of just conn if it adds clarity). Add insightful, unique comments explaining the "why" behind the code, not just the "what." Slightly vary common boilerplate structures where possible without sacrificing readability or security.

---

Now, please proceed with the analysis and remediation for the provided code snippet as per the steps above.

Code Snippet:

[Insert the code snippet here]

**
