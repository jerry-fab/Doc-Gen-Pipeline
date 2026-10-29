# 📘 Automated Code Documentation Pipeline: Complete Architecture & Flow Guide

---

## 1. Executive Summary

The **Automated Code Documentation Pipeline (`Doc-Gen-Pipeline`)** is an enterprise-grade, zero-configuration CI/CD solution that converts source code changes into clean, structured Markdown documentation with interactive Mermaid class architecture diagrams. 

It is designed as a **Reusable GitHub Composite Action**, allowing any consumer repository (e.g., `Sample-Project-GP`, `Sample-Project-GP-2`) to inherit automated documentation capabilities with a simple 2-step workflow file and zero local dependency overhead.

---

## 2. Technology Stack Breakdown

| Layer | Technology | Purpose & Implementation Details |
| :--- | :--- | :--- |
| **AST Parsing Engine** | **Tree-sitter** (C-based parser generators) | Multi-language syntax parsing without executing untrusted code. Supports **8 language targets**: Python, C#, Java, JavaScript, JSX (React), TypeScript, TSX, Go, and Rust. |
| **AI Explanation Engine** | **Google Gemini 3.5 Flash** (`gemini-3.5-flash`) | Analyzes AST metadata and raw code to generate structured architectural rationale, component responsibilities, and parameter explanations. |
| **Deterministic Fallback Engine** | **Grounded Heuristic Engine** | In-house rule-based AST explainer that automatically activates if API rate limits (HTTP 429), quota exhaustion, or network timeouts occur. Ensures 100% pipeline reliability with zero downtime. |
| **Data Validation & Schemas** | **Pydantic v2** | Enforces strict type schemas (`ClassMetadata`, `MethodMetadata`, `ClassExplanation`, `AppConfig`) for clean data serialization between AST, AI, and Markdown generators. |
| **Visualization & Diagrams** | **Mermaid.js** | Generates class inheritance, method signatures, properties, and relationship diagrams embedded directly inside Markdown artifacts. |
| **CI/CD Orchestration** | **GitHub Actions (Composite Action)** | Runs in isolated cloud Ubuntu runners. Self-contained environment that auto-provisions Python 3.11, installs Tree-sitter packages, parses diffs, and commits documentation. |
| **Git Automation** | **Git CLI & GitHub Actions Bot** | Incremental scanning via `git diff HEAD~1 HEAD`, automated authoring by `github-actions[bot]`, and loop prevention using `[skip ci]`. |
| **Storage & Log Management** | **PipelineLogger (Multi-Channel)** | Multi-directory logging (`err_log`, `fn_log`, `quota_complete_log`) featuring dual-threshold automatic cleanup (1-hour time window + 10MB size ceiling). |

---

## 3. End-to-End Background Lifecycle & Communication Flow

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer (Local Laptop)
    participant GH as GitHub Cloud (Working Repo)
    participant Runner as GitHub Actions Runner (Ubuntu VM)
    participant PipelineRepo as Reusable Action (Doc-Gen-Pipeline)
    participant Gemini as Google Gemini AI API

    Dev->>GH: 1. git push origin master (code change, e.g. App.jsx)
    Note over GH: GitHub Event: "push" triggered
    GH->>Runner: 2. Spin up Ubuntu VM & run documentation.yml
    
    Runner->>GH: 3. actions/checkout@v4 (fetch-depth: 2)
    Note over Runner: Target repo code cloned into ./
    
    Runner->>PipelineRepo: 4. Download Doc-Gen-Pipeline@master
    Note over Runner: Action code cloned into github.action_path
    
    Runner->>Runner: 5. Setup Python 3.11 & Install Tree-sitter packages
    Runner->>Runner: 6. Run git diff to isolate modified files
    Runner->>Runner: 7. Tree-sitter AST extracts Classes, Functions, Methods
    
    Runner->>Gemini: 8. HTTPS POST (AST metadata & raw code snippet)
    Gemini-->>Runner: 9. JSON Response (Purpose, Design Rationale, Responsibilities)
    
    Runner->>Runner: 10. Generate Markdown & Mermaid diagram in ./docs/
    Runner->>Runner: 11. Write docs/PIPELINE_STATUS.md & execution logs
    
    Runner->>GH: 12. git commit -m "... [skip ci]" & git push
    Note over GH: Commit added to origin/master by github-actions[bot]
    
    Dev->>GH: 13. git pull origin master (or git ppush)
    GH-->>Dev: 14. Download docs/ to local laptop
```

---

## 4. Phase-by-Phase Execution Details

### Phase 1: The Push Event & Trigger
1. The developer pushes code to GitHub (`git push origin master`).
2. GitHub's webhook engine catches the push event.
3. Because the commit modifies files outside the ignored paths (`paths-ignore`), GitHub launches the workflow defined in `.github/workflows/documentation.yml`.

### Phase 2: Target Repository Checkout
* **Action**: `actions/checkout@v4` with `fetch-depth: 2`.
* **Why `fetch-depth: 2`?**: Default git checkout fetches only the current commit (`depth: 1`). Fetching depth 2 ensures git diff (`git diff HEAD~1 HEAD`) can compare the current commit against its parent to identify exactly which files were modified.

### Phase 3: Composite Action Resolution
* **Directive**: `uses: jerry-fab/Doc-Gen-Pipeline@master`.
* The runner pulls the reusable pipeline repository into a dedicated action directory (`github.action_path`).
* Target projects do **not** need to maintain Python dependencies or parser scripts in their own codebase.

### Phase 4: AST Extraction (Tree-sitter)
* The parser scans source files without compiling or executing them:
  - **React JSX/TSX**: Discovers functional components (`function App()`, `const Home = () => ...`) and ES6 classes.
  - **Python, Java, C#**: Discovers classes, inheritance hierarchies, method signatures, parameter types, and docstrings.
  - **Go & Rust**: Discovers structs, receiver methods, trait implementations, and public modules.

### Phase 5: AI Explanation Engine (Gemini 3.5 Flash)
* AST metadata and source code are sent to Google Gemini via:
  - **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
  - **Model**: `gemini-3.5-flash`
  - **Prompt Engineering**: Instructs the model to output strict JSON covering:
    - Primary purpose
    - Inferred design rationale
    - Architectural responsibilities
    - Key methods and injected dependencies
* **Fault Tolerance**: If Google returns HTTP 429, 404, or 503, the pipeline automatically falls back to the internal `GROUNDED_HEURISTIC` engine.

### Phase 6: Documentation Synthesis & Status Logging
* **Output Path**: `./docs/architecture/<Language>/<ClassName>.md`
* **Root Index**: Updated at `./docs/README.md`.
* **Execution Logs**:
  - `docs/PIPELINE_STATUS.md`: Live Markdown status dashboard (Start time, completion duration, components documented, engine used).
  - `docs/pipeline_execution.log`: Historical audit log of every pipeline execution.

### Phase 7: Automated Commit & Infinite Loop Prevention
* Git stages all artifacts in `docs/`.
* The commit is authored by:
  ```text
  Author: github-actions[bot] <github-actions[bot]@users.noreply.github.com>
  Message: docs: auto-update class architecture documentation [skip ci]
  ```
* 🛡️ **Loop Prevention Architecture**:
  1. **`[skip ci]` tag**: Tells GitHub Actions runner to skip triggering builds on this commit.
  2. **`paths-ignore: - 'docs/**'`**: Tells the workflow to ignore any push that only alters documentation.

### Phase 8: Local Workspace Synchronization
* The commit lands on GitHub remote repository (`origin/master`).
* When the developer runs `git pull origin master` (or uses the automated alias `git ppush`), the newly generated `docs/` folder transfers from GitHub cloud directly into the local IDE workspace.

---

## 5. Storage & Log Retention System

To prevent disk saturation during high-frequency CI/CD runs, the pipeline features a **Dual-Threshold Automatic Purge Engine** inside `analyzer/utils/logger.py`:

```json
"logging": {
  "max_age_hours": 1,
  "max_size_mb": 10
}
```

1. **Time-Based Purge (`max_age_hours: 1`)**:
   - Inspects timestamped logs across `logs/err_log/`, `logs/fn_log/`, and `logs/quota_complete_log/`.
   - Any log file older than 1 hour (3,600 seconds) is automatically removed upon pipeline initialization.
2. **Size-Based Purge (`max_size_mb: 10`)**:
   - If total log directory volume exceeds the configured MB threshold (default: 10MB), older logs are purged starting from the oldest until total volume drops beneath the threshold.
   - Actively running session log files are always protected.

---

## 6. Key Developer Takeaways & Best Practices

1. **Why `git pull` is required**:
   - Git is a distributed version control system. Remote commits generated by cloud bots on GitHub.com remain in the cloud until `git pull` is executed locally.
2. **Push & Auto-Pull Shortcut (`git ppush`)**:
   - To avoid waiting and typing `git pull` manually, configure this single-command alias:
     ```bash
     git config --global alias.ppush "!f() { git push origin master && echo '[Doc-Gen] Waiting 25s for cloud docs...' && sleep 25 && git pull; }; f"
     ```
   - Running `git ppush` automatically pushes your code, waits for the cloud action, and pulls down generated docs in one step.
3. **Status Verification**:
   - Always check `docs/PIPELINE_STATUS.md` in your project to verify the exact duration, trigger commit, and AI engine used for every run.
