# Class: `AIDocumentationEngine`

> **Language**: `PYTHON` | **Engine**: `GEMINI` | **Source**: [`analyzer/ai_engine.py`](../../analyzer/ai_engine.py#L26-L277) | **Lines**: `26 - 277`

---

## 1. Class Architecture Diagram

```mermaid
classDiagram
    class AIDocumentationEngine {
        +__init__(Optional[ProfileConfig] profile) Any
        +explain_class(ClassMetadata metadata) ClassExplanation
        +_build_prompt(ClassMetadata metadata) str
        +_call_openai_compatible(ClassMetadata metadata) ClassExplanation
        +_call_anthropic_native(ClassMetadata metadata) ClassExplanation
        +_grounded_heuristic_explainer(ClassMetadata metadata) ClassExplanation
    }
    AIDocumentationEngine ..> Optional[ProfileConfig] : depends on
```

---

## 2. Overview & Purpose

Coordinates the synthesis of architectural class documentation by executing calls to external LLM APIs (OpenAI-compatible or Anthropic) or falling back to a deterministic rule-based heuristic generator.

### Why this class exists (Design Rationale)
INFERRED: The class employs a fallback pattern to ensure high availability of documentation generation. It abstracts specific API interaction protocols (OpenAI vs. Anthropic) behind a single entry point (`explain_class`), allowing callers to receive a standardized `ClassExplanation` regardless of API status, rate limits, or network connectivity.

---

## 3. Key Responsibilities

- Initializes API configuration settings, endpoint URLs, and feature enablement state from an injected ProfileConfig or application config.
- Routes explanation requests to provider-specific methods (`_call_anthropic_native` or `_call_openai_compatible`) based on provider name and endpoint URL.
- Handles HTTP exceptions, quota exhaustion errors, and unhandled exceptions by logging events and falling back to `_grounded_heuristic_explainer`.
- Constructs structured prompt strings incorporating class metadata and JSON schema instructions.
- Generates deterministic documentation summaries without network calls using metadata naming patterns and AST properties.

---

## 4. Method Signatures & Behavioral Analysis

| Method Name | Parameters | Return Type | Lines | Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **`__init__`** | `self: Any`, `profile: Optional[ProfileConfig]` | `Any` | L31-L47 | Loads application configuration, sets instance attributes for provider, API key, base URL, model, temperature, timeout, and enabled flag, and logs initialization parameters. Returns None. |
| **`explain_class`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L49-L110 | Accepts a ClassMetadata object, determines whether to execute an LLM API request or the heuristic explainer based on `is_enabled`, catches request/runtime exceptions to trigger fallbacks, and returns a ClassExplanation. |
| **`_build_prompt`** | `self: Any`, `metadata: ClassMetadata` | `str` | L112-L143 | Constructs and returns a formatted prompt string containing AST metadata, source code, and JSON output rules. |
| **`_call_openai_compatible`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L145-L178 | Sends an HTTP POST request using `requests.post` to an OpenAI-compatible endpoint, parses the returned JSON string, and returns a ClassExplanation instance. |
| **`_call_anthropic_native`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L180-L208 | Sends an HTTP POST request using `requests.post` to Anthropic's Messages endpoint, parses the text response, and returns a ClassExplanation instance. |
| **`_grounded_heuristic_explainer`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L210-L277 | Generates a ClassExplanation using rule-based heuristics derived from metadata class names, docstrings, parameters, and methods without invoking network services. |

---

## 5. Injected Dependencies & Collaborators

- **`profile: Optional[ProfileConfig]`**: Optional constructor parameter supplying provider credentials, API endpoints, model selection, temperature, and timeout parameters.
- **`load_config`**: Function called during initialization when no explicit profile is provided to obtain active configuration settings.
- **`logger`**: Module used to log initialization parameters, engine choices, quota exhaustion warnings, and execution exceptions.
- **`requests`**: HTTP library used to send POST requests to external LLM API endpoints.
- **`json`**: Module used to deserialize JSON content returned from API responses into Python dictionaries.
- **`ClassMetadata`**: Data structure containing class details (name, file_path, lines, methods, dependencies, docstring, raw_code) passed to explanation methods.
- **`ClassExplanation`**: Data structure instantiated and returned containing synthesized class documentation fields.

---

## 6. Verifiable Code Citations

- Lines 31-47: `__init__` initializes configuration properties and logs status via `logger.log_fn`.
- Lines 49-110: `explain_class` routes to LLM calls or `_grounded_heuristic_explainer`, handling `requests.exceptions.RequestException` and general `Exception`.
- Lines 112-140: `_build_prompt` formats AST metadata and JSON schema requirements into a single string.
- Lines 142-174: `_call_openai_compatible` sends HTTP POST requests to `/chat/completions` and parses `choices[0].message.content` into `ClassExplanation`.
- Lines 176-203: `_call_anthropic_native` sends HTTP POST requests to `/messages` with `x-api-key` header and parses `content[0].text` into `ClassExplanation`.
- Lines 205-277: `_grounded_heuristic_explainer` constructs purpose, rationale, responsibilities, and key method mappings based on metadata attributes.

---

## 7. Known Architectural Boundaries & Limitations

- ⚠️ Requires cross-file inspection to verify the precise implementations of `load_config`, `logger`, `ClassMetadata`, and `ClassExplanation`.
- ⚠️ No explicit handling for `json.JSONDecodeError` if an API returns non-JSON or malformed output beyond code-block stripping.
- ⚠️ Assumes `requests.post` responses strictly contain the expected nested dictionary structures (`choices[0].message.content` or `content[0].text`).

---
*Auto-generated by GitHub Pipeline Code Documentation Engine.*
