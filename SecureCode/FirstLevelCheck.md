The Precision Prompting Framework: A Step-by-Step Guide
Here is the complete, corrected framework designed for higher accuracy. Follow these three stages sequentially for each vulnerability you need to find.

Stage 1: Comprehensive Identification (The Broad Scan)
Goal: To find all potential instances of a single, specific vulnerability across your entire workspace. This stage prioritizes finding every possible candidate.

Instructions:
Copy and paste the following prompt into your chat. Replace <VULNERABILITY NAME> and [CWE Identifier] with the specific vulnerability from your hackathon list.

Prompt for Stage 1:

###Instruction###
You are a Senior Security Analyst. Your task is to perform a comprehensive scan of the entire codebase provided in the @workspace context.

Your objective is to identify all potential instances of the following vulnerability: **<VULNERABILITY NAME> ([CWE Identifier])**.

For each potential instance you find, you MUST:
1.  Identify the full file path.
2.  Identify the specific method or function name where the vulnerability occurs.
3.  Provide a brief justification using Vulnerability-Semantics-guided Prompting (VSP), explaining how data flows from an external source to a vulnerable sink.

You MUST format your entire output as a single JSON array of objects. Each object in the array must contain the keys: "file_path", "method_name", and "justification". Do not include any other text or explanations in your response.

Stage 2: Comparative Analysis and Ranking (The Judgment)
Goal: To take the list of candidates from Stage 1 and force the AI to act as a judge, ranking them from most to least critical.

Instructions:
Take the entire JSON output from Stage 1 and use it to replace the <JSON Output from Stage 1> placeholder in the prompt below.

Prompt for Stage 2:

###Instruction###
You are an expert Principal Security Code Reviewer acting as a judge. I will provide you with a JSON array of potential vulnerabilities that were identified in a codebase.

Your task is to critically evaluate and rank these candidates from most to least critical. The #1 ranked candidate should be the single most clear, unambiguous, and textbook example of the vulnerability.

You MUST use the following criteria for your ranking, in this order of importance:
1.  **Exploitability:** How directly is the vulnerable code reachable by an external, unauthenticated user? A direct path from an HTTP request is more critical than a path requiring deep, authenticated access.
2.  **Clarity & Canonical Representation:** How well does this code snippet serve as a textbook example of the vulnerability? A simple, clear-cut case is preferred over a complex or convoluted one.
3.  **Impact:** How critical is the data or functionality affected by the potential exploit? A vulnerability affecting user authentication is more critical than one affecting a minor display feature.

Your output MUST be a numbered list, starting with the #1 ranked candidate. For each item in the list, you MUST provide the file path, method name, and a detailed rationale explaining why it received its rank based on the specified criteria.

###Candidate Vulnerabilities###
<JSON Output from Stage 1>

Stage 3: Final Selection and Formatted Output (The Extraction)
Goal: To take the ranked list from Stage 2 and extract only the #1 candidate into the final, clean JSON format. This stage replaces the unreliable "justification summary" and "forced choice" steps with a direct and reliable extraction task.

Instructions:
Take the entire ranked list from Stage 2 and use it to replace the <Ranked List from Stage 2> placeholder in the prompt below. Also fill in the vulnerability name and CWE ID.

Prompt for Stage 3:

###Instruction###
You are a data formatting specialist. Your task is to process a ranked list of vulnerabilities and extract ONLY the #1 ranked candidate into a specific JSON format.

From the ranked list provided below, you MUST identify ONLY the #1 candidate.

You will then use the information from that #1 candidate to populate the following JSON schema. You MUST extract the 'rationale' text for the #1 candidate verbatim and use it as the value for the 'justification_for_selection' key.

Your response MUST ONLY contain the final JSON object. Do not include any other text, apologies, or markdown formatting.

###Ranked List###
<Ranked List from Stage 2>

###JSON Schema to Populate###
{
  "vulnerability_type": "<VULNERABILITY NAME>",
  "cwe_identifier": "[CWE Identifier]",
  "canonical_instance": {
    "file_path": "[File path of #1 method]",
    "method_name": "[Name of #1 method]",
    "justification_for_selection": "[The verbatim rationale for the #1 ranked candidate from the list above]"
  }
}
