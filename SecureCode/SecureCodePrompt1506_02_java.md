--- CONTEXT ---
Persona: Senior Application Security Engineer in the "2025 Secure Code Prompt Engineering Hackathon."
Task: Analyze the provided Java code and create a secure version, remediating any in-scope vulnerabilities.
Standard: The fix must align with Java security best practices, including OWASP guidelines and secure coding standards.

--- SCOPE & METHODOLOGY ---
Surgical Fixes: Fix the identified vulnerability within the code's scope. Do not add large-scale features like new logging or database connection systems. Keep the fix localized and secure.

Helper Functions: You may create small, private helper functions if they directly support the security fix and improve code clarity and maintainability.

--- IN-SCOPE VULNERABILITIES ---
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

--- SECURITY REQUIREMENTS ---
Secrets Management: Avoid hard-coded secrets. Load them from secure environment variables or a configuration service.

Secure Input Handling: Treat all external input as untrusted. Use rigorous validation, context-specific output encoding, and parameterized queries.

Resource Management: Ensure resources like file handles and network connections are reliably closed.

Secure Error Handling: Do not leak sensitive information (like stack traces or file paths) to users. Use simple, safe error messages.

Dependency Management: If using third-party libraries, note this and recommend secure, up-to-date versions.

--- EXECUTION PLAN ---
Follow this exact four-step process:

1. Secure Design Reasoning (Chain of Thought)

Identify Vulnerability: Name the in-scope vulnerability present in the code.

Explain Manifestation: Describe how the vulnerability occurs in the snippet.

Outline Mitigation: Detail the security controls and patterns you will use to fix it.

Justify Control: Explain why this control is the right fix.

2. Initial Code Generation

Generate a secure version of the code that fixes the vulnerability while maintaining original functionality.

3. Recursive Criticism and Improvement (RCI)

Critique: Evaluate your generated code. Is the fix complete, is it bypassable, does it add out-of-scope features, and is it idiomatic for Java?

Improvement Plan: Suggest specific improvements if weaknesses are found. If the fix is robust, explain why.

4. Final Hardened Code

Provide the final, most robust version of the code from your self-critique, with clear comments explaining the remediations.

--- EXAMPLE APPLICATION (Java) ---
Code Snippet:

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;
import java.io.StringReader;

public class XmlParser {
    public Document parseXml(String xmlData) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        // The default configuration is vulnerable to XXE
        return builder.parse(new InputSource(new StringReader(xmlData)));
    }
}

1. Secure Design Reasoning

Vulnerability: XML External Entity (XXE) Injection (CWE-611).

Explanation: The default DocumentBuilderFactory settings allow XXE, letting an attacker read local files or trigger SSRF via a malicious DOCTYPE.

Mitigation: Disable DTD and external entity processing by setting secure features on the DocumentBuilderFactory.

Justification: Disabling vulnerable parser features is the most effective XXE defense. Explicitly disabling DTDs and external entities is more robust than relying on a single high-level setting like FEATURE_SECURE_PROCESSING.

2. Initial Code Generation

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;
import java.io.StringReader;
import javax.xml.XMLConstants;

public class XmlParser {
    public Document parseXml(String xmlData) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        // Mitigates XXE (CWE-611) by disabling DTDs and external entities
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        return builder.parse(new InputSource(new StringReader(xmlData)));
    }
}

3. Recursive Criticism and Improvement

Critique: The fix is effective but can be hardened for defense-in-depth. Being more explicit about disabling all related external entity features prevents misconfiguration across different Java or XML versions.

Improvement Plan: Explicitly disable external-general-entities, external-parameter-entities, and load-external-dtd for unambiguous security.

4. Final Hardened Code

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;
import java.io.StringReader;
import javax.xml.XMLConstants;

public class XmlParser {
    public Document parseXml(String xmlData) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        
        // Mitigates XML External Entity (XXE) Injection (CWE-611)
        // Disabling DTDs is the most important step to prevent XXE.
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        
        // Explicitly disable other external entity features for defense-in-depth.
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        
        // Disable external DTDs to prevent potential resource consumption issues.
        factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
        
        // Ensure XInclude processing is disabled.
        factory.setXIncludeAware(false);
        factory.setExpandEntityReferences(false);

        DocumentBuilder builder = factory.newDocumentBuilder();
        return builder.parse(new InputSource(new StringReader(xmlData)));
    }
}

--- ANTI-BLOCKING DIRECTIVE ---
To avoid matching public code, use descriptive but unique variable names and add insightful comments explaining the "why," not just the "what."

Now, proceed with the analysis and remediation for the provided Java code snippet as per the steps above.

Code Snippet:
[Insert the Java code snippet here]