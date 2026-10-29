# Pure Git Client-Side Integration Guide
### For Lumina Git Server (`git.luminad.com`) & Enterprise Git Repositories

---

## 1. Executive Summary

This architecture enables **automatic code documentation generation** for repositories hosted on **`git.luminad.com` (e.g., `Flexpub2.0.git`)** without requiring:
- ❌ Any admin permissions on `git.luminad.com`
- ❌ Any changes or webhooks on the Lumina Gogs server
- ❌ Any dedicated server-side CI/CD runners

Everything executes **locally on the developer's laptop** using standard Git hooks. When developers commit and push code, the architecture documentation is automatically generated, bundled, and pushed directly to the remote repository.

The existing **GitHub Actions pipeline remains 100% untouched** and fully operational for GitHub repositories.

---

## 2. Architecture Diagram

```
+-------------------------------------------------------------------------------+
|                           DEVELOPER WORKSTATION                               |
|                                                                               |
|  1. Developer edits code (.cs, .py, .java) in Flexpub2.0                     |
|                                                                               |
|  2. Developer runs:                                                           |
|     $ git add src/Service.cs                                                  |
|     $ git commit -m "feat: update service logic"                             |
|                                                                               |
|  3. [LOCAL PRE-COMMIT HOOK FIRES]:                                           |
|     +--> Reads staged files: git diff --cached                                |
|     +--> Executes: python analyzer/main.py --staged                           |
|     +--> AST Parser extracts classes & methods                                |
|     +--> AI Engine (Gemini / Local LLM) generates explanations                |
|     +--> Creates docs/csharp/Service.md & updates docs/README.md              |
|     +--> Stages documentation: git add docs/                                  |
|                                                                               |
|  4. Git completes single unified commit containing [Code + Docs]              |
|                                                                               |
|  5. Developer runs:                                                           |
|     $ git push origin master                                                  |
+-------------------------------------------------------------------------------+
                                      |
                                      | Pure HTTPS / SSH Git Push
                                      v
+-------------------------------------------------------------------------------+
|                       LUMINA GIT SERVER (git.luminad.com)                     |
|                                                                               |
|  Repository: Lumina-Internal/Flexpub2.0.git                                  |
|  Status: 100% UNTOUCHED / ZERO CONFIGURATION REQUIRED                         |
|  Result: Remote repository receives code AND updated docs in one go!          |
+-------------------------------------------------------------------------------+
```

---

## 3. Quick Setup (1-Click Installation)

Open your terminal on your laptop and run either the PowerShell or Bash installer:

### Option A: Windows PowerShell (Recommended)
```powershell
# Run from Github-Pipeline folder:
.\hooks\install-git-hook.ps1 -TargetRepo "D:\path\to\your\Flexpub2.0"
```

### Option B: Git Bash / Linux / macOS
```bash
# Run from Github-Pipeline folder:
./hooks/install-git-hook.sh /path/to/your/Flexpub2.0
```

---

## 4. Daily Developer Workflow

Once installed, developers work completely naturally:

```bash
# Step 1: Work on your project
git checkout -b feature/new-logic
# (edit your C#, Python, or Java files)

# Step 2: Stage your changes
git add src/MyClass.cs

# Step 3: Commit
git commit -m "feat: implement payment processing"

# Output:
# ============================================================
# [Doc-Gen Hook] Detected staged code changes:
# src/MyClass.cs
# [Doc-Gen Hook] Generating class architecture documentation...
# ============================================================
# [*] Deployment Mode: 'PRODUCTION' | Provider: 'google-genai' | Model: 'gemini-2.5-flash'
# [Mode] Git Staged diff detection (pre-commit staged index only)
# [*] Discovered 1 source file(s) for architectural analysis.
#   -> Parsing: src/MyClass.cs
#      Found Class: PaymentProcessor (Lines 10-95)
#      [Engine Used]: Google Gemini API (gemini-2.5-flash)
# [Success] Generated documentation for 1 class(es). Catalog index updated at 'docs/README.md'.
# [Doc-Gen Hook] Class documentation staged into current commit.
# ============================================================

# Step 4: Push to Lumina server
git push origin feature/new-logic
```

Both the code and its auto-generated documentation arrive on `git.luminad.com` seamlessly!

---

## 5. Key Advantages

| Feature | Git Hook Solution | Server Webhook / Runner |
| :--- | :--- | :--- |
| **Server Changes** | **0% (Zero server access required)** | Requires admin server setup |
| **Lumina Git Security** | **100% Safe (Client-only)** | Requires token/webhook permissions |
| **Git Server Compatibility** | **Universal (Gogs, GitLab, GitHub, Bitbucket)** | Platform-dependent |
| **Offline / Local Testing** | **Yes** | No |
| **Sync Guarantee** | **Code & Docs bundled in same commit** | Separate commits created after push |
