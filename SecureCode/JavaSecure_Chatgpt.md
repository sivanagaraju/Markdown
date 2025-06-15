You're participating in the 2025 Secure Code Prompt Engineering Hackathon.

Use the following methodology to analyze the current file open in the editor (`VulnerableService.java`) and fix any **in-scope vulnerabilities**:

---

🛡️ IN-SCOPE VULNERABILITIES:
- Command Injection (CWE-77, CWE-78)
- Insecure Deserialization (CWE-502)
- Insecure Direct Object Reference (IDOR) (CWE-639)
- Insecure Session Identifier (CWE-330, CWE-384)
- Server-Side Request Forgery (SSRF) (CWE-918)
- Secrets Exposure (CWE-200, CWE-312, CWE-522)
- SQL Injection (SQLi) (CWE-89)
- Cross-Site Scripting (XSS) (CWE-79)
- Cross-Site Request Forgery (CSRF) (CWE-352)
- XML External Entity (XXE) Injection (CWE-611)

---

🔐 SECURE FIX PROCESS:

Follow this 4-step process:

1. **Secure Design Reasoning**
   - Identify the vulnerability.
   - Explain how it manifests.
   - Outline the mitigation.
   - Justify the security control.

2. **Initial Code Generation**
   - Provide a secure version of the vulnerable code.

3. **Recursive Criticism and Improvement (RCI)**
   - Critique the fix and suggest improvements if any.

4. **Final Hardened Code**
   - Output the most robust, secure version with comments.

---

Analyze and secure: `VulnerableService.java` (or the current file in the editor).
Only apply **localized, surgical fixes** — avoid adding new frameworks, large components, or logging unless needed for the fix.
