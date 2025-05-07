# AI Assistant Guidelines for "Used Car Lead Generation Agent" Project

## 1. Overarching Principles (Derived from User Instructions)

*   **Proactive Problem Solving:** Think thoroughly before coding. Anticipate potential issues and offer solutions.
*   **Simplicity and Clarity:**
    *   Implement features in the simplest possible way that meets requirements.
    *   Write clean, simple, readable, and modular code.
    *   Use clear, concise, and easy-to-understand language in all communications and code comments.
    *   Employ short sentences for better comprehension.
*   **Modularity and File Size:** Keep files small and focused (ideally <200 lines, though this is a guideline and may be exceeded for e.g. extensive configuration or comprehensive manager classes if it maintains clarity).
*   **Iterative Development & Testing:** Test after every meaningful change. Verify each new feature works and explain to the USER how to test it.
*   **Focus on Core Functionality:** Prioritize core features before optimization or non-essential enhancements.
*   **Naming Conventions:** Use clear, consistent naming for variables, functions, classes, and files.
*   **Existing Code First:** Always look for existing code to modify or extend before creating new code from scratch.
*   **File System Navigation (Windows):** If unsure about file/directory structures, use PowerShell (Windows) commands for discovery (e.g., `Get-ChildItem` instead of `ls`, `Set-Location` instead of `cd`).

## 2. Code Development & Modification

*   **Code Style:** Python (PEP 8 where applicable). Clean, well-formatted.
*   **Comments:**
    *   **Abundant and Explanatory:** Include LOTS of helpful and explanatory comments. Document all changes and their reasoning within comments.
    *   **No Obvious Comments:** Avoid comments that merely restate what the code clearly does.
    *   **Preserve Useful Old Comments:** Do not delete old comments unless they are demonstrably wrong or obsolete.
    *   **Clarity in Comments:** Use clear, easy-to-understand language and short sentences.
*   **Error Handling:**
    *   **Thorough Analysis:** DO NOT JUMP TO CONCLUSIONS. Consider multiple possible causes for errors.
    *   **Plain English Explanation:** Explain the problem in plain English to the USER.
    *   **Minimal Changes:** Make the minimal necessary changes to fix errors, affecting as few lines as possible.
    *   **Web Search for Strange Errors:** For unusual or undocumented errors, suggest the USER perform a Perplexity web search for up-to-date information.
    *   **PowerShell Scripting (if applicable for .ps1 files):**
        *   Use PowerShell 7.x (`pwsh.exe`).
        *   `Set-Location` for directory changes.
        *   UTF-8 encoding for scripts.
        *   Replace special characters (✓, ✗) with ASCII (OK, X).
        *   Include `try/catch` blocks for error handling.
        *   Log unfixable errors to `C:\Logs\cursor-agent.log` (if relevant to a PS script I'm writing).
        *   Integrate with BrowserTools MCP at `http://localhost:3000` (if applicable to a task).
        *   Reference `@docs/technical.md` for conventions (Note: current project uses `Technical Design Document.md`).
        *   (Assume `check-paths.ps1` is handled by user environment if relevant).
*   **Dependencies:** Add necessary imports. Update `requirements.txt` after installing new packages (`pip freeze > requirements.txt`).

## 3. Tool Usage (Specific to AI Assistant Capabilities)

*   **`edit_file`:**
    *   Provide sufficient context around changes.
    *   Use `// ... existing code ...` (or language-appropriate equivalent like `# ... existing code ...` for Python) to denote unchanged sections.
    *   For new files, provide the complete content.
    *   Ensure instructions are clear and unambiguous for the applying model.
*   **`read_file`:** Use to gather context before editing. Read entire files if recently changed or if partial view is insufficient.
*   **`codebase_search` / `grep_search`:** Use to find relevant existing code before writing anew. Prefer `grep_search` for known exact strings/regex, `codebase_search` for semantic similarity.
*   **`run_terminal_cmd`:**
    *   Explain *why* a command is needed.
    *   For `git`, `less`, `head`, `tail`, `more`, append `| cat` or equivalent to avoid pager issues.
    *   Use `Set-Location` in PowerShell commands if providing them for the user to run.
*   **`list_dir`:** Use for discovery of file structure.
*   **General Tool Rules:**
    *   Explain tool usage before calling.
    *   Do not ask for permission to use tools.
    *   If a tool call fails or gives unexpected results, analyze and retry or try an alternative approach.

## 4. Project-Specific Guidance

*   **Follow `Master Development Guide.md`:** Adhere to the phases, tasks, and objectives outlined in this guide.
*   **Refer to Design Documents:** Regularly consult `Project Specification.md` and `Technical Design Document.md` for requirements, architecture, and data schemas.
*   **Risk Mitigation:** Be aware of risks in `Risk Assessment.md` and incorporate mitigation strategies into development (e.g., robust error handling for website changes).
*   **Testing:** Follow the `Testing Plan.md`. After implementing features, describe how the USER can test them. Write unit tests where appropriate (and if requested or part of the plan).
*   **Communication:** Adhere to `Communication Plan.md`. Provide updates as defined.

## 5. Interaction Style

*   **Pair Programming Mentality:** Act as a collaborative partner.
*   **Reasoning:** Provide 2-3 paragraphs of reasoning before significant code generation or complex tool use, explaining the approach.
*   **Guidance, Not Assumption:** If unsure about a specific implementation detail not covered in documents, propose options or ask clarifying questions, rather than making a potentially incorrect assumption.
*   **User Guidance for External Searches:** If truly stuck on a technical issue that seems very current or specific (e.g. a brand new API behavior), explicitly ask the user to perform a web search (e.g. Perplexity) and share the findings.

By adhering to these guidelines, I aim to provide effective and efficient assistance throughout the development of the "Used Car Lead Generation Agent" project. 