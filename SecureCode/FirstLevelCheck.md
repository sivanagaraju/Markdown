###Instruction###
You are a Senior Security Analyst. Your task is to perform a comprehensive scan of the entire codebase provided in the @workspace context.

Your objective is to identify all potential instances of the following vulnerability: ****.

For each potential instance you find, you MUST:
1.  Identify the full file path.
2.  Identify the specific method or function name where the vulnerability occurs.
3.  Provide a brief justification using Vulnerability-Semantics-guided Prompting (VSP), explaining how data flows from an external source to a vulnerable sink.

You MUST format your entire output as a single JSON array of objects. Each object in the array must contain the keys: "file_path", "method_name", and "justification". Do not include any other text or explanations in your response.

###Vulnerability Type###

Command Injection (CWE-77, CWE-78)
Insecure Deserialization (CWE-502)
Insecure Direct Object Reference (IDOR) (CWE-639)
Insecure Session Identifier (Predictable Session ID) (CWE-330, CWE-384)
Server-Side Request Forgery (SSRF) (CWE-918)
Secrets Exposure (CWE-200, CWE-312, CWE-522)
SQL Injection (SQLi) (CWE-89)
Cross-Site Scripting (XSS) (CWE-79)
Client-Side Request Forgery (CSRF) (CWE-352)
XML External Entity (XXE) Injection (CWE-611)


------


###Instruction###
You are an expert Principal Security Code Reviewer acting as a judge. I will provide you with a JSON array of potential vulnerabilities that were identified in a codebase.

Your task is to critically evaluate and rank these candidates from most to least critical. The #1 ranked candidate should be the single most clear, unambiguous, and textbook example of the vulnerability.

You MUST use the following criteria for your ranking, in this order of importance:
1.  **Exploitability:** How directly is the vulnerable code reachable by an external, unauthenticated user? A direct path from an HTTP request is more critical than a path requiring deep, authenticated access.
2.  **Clarity & Canonical Representation:** How well does this code snippet serve as a textbook example of the vulnerability? A simple, clear-cut case is preferred over a complex or convoluted one.
3.  **Impact:** How critical is the data or functionality affected by the potential exploit? A vulnerability affecting user authentication is more critical than one affecting a minor display feature.

Your output MUST be a numbered list, starting with the #1 ranked candidate. For each item in the list, you MUST provide the file path, method name, and a detailed rationale explaining why it received its rank based on the specified criteria.

###Candidate Vulnerabilities###



-----------


###Instruction###
Based on the ranked list you just provided, your final task is to select ONLY the #1 ranked candidate as the single canonical example.

**To robustly confirm your choice, you must perform a final justification. Instead of only comparing #1 and #2, you will briefly summarize why the #1 candidate is superior to the other top-ranked candidates (e.g., #2 and #3). Explicitly reference your original ranking criteria (Exploitability, Clarity, Impact) in your summary.**

For example, your justification might look like: "#1 is the definitive choice because its exploit path is unauthenticated, making it more exploitable than #2, and its implementation is a more direct and canonical example of the vulnerability than #3."

After this final justification, you MUST conclude with the exact phrase: "The definitive canonical instance is:" followed by the file path and method name of the #1 ranked candidate. Do not list any other candidates.

###Ranked List###
<Ranked List from Stage 2>

------

###Instruction###
Based on your final selection of the definitive canonical instance, you MUST provide the information in the following JSON format.

Your response MUST ONLY contain the JSON object and nothing else. Do not include any explanatory text, apologies, or markdown formatting like ```json.

###JSON Schema###
{
  "vulnerability_type": "",
  "cwe_identifier": "[CWE Identifier]",
  "canonical_instance": {
    "file_path": "[File path of #1 method]",
    "method_name": "[Name of #1 method]",
    "justification_for_selection": ""
  }
}