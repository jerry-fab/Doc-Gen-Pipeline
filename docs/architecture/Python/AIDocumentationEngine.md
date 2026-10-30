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

Coordinates the generation of architectural documentation explanations for Python classes by dispatching metadata to external LLM APIs (OpenAI-compatible or Anthropic native) or falling back to a deterministic rule-based heuristic explainer.

### Why this class exists (Design Rationale)
INFERRED: Implements a resilient Strategy/Fallback pattern for AI documentation generation. By encapsulating configuration loading, vendor-specific HTTP client payload formatting (OpenAI vs. Anthropic), and deterministic rule-based heuristics, the engine guarantees documentation synthesis even during API rate limits, network failures, or disabled configurations.

---

## 3. Key Responsibilities

- Initializes engine properties and enablement flags from a provided or default `ProfileConfig` (Lines 31-48).
- Orchestrates explanation generation and catches network or runtime exceptions to handle rate limits and fallbacks (Lines 50-107).
- Formats AST metadata and raw source code into standardized prompts with strict schema constraints (Lines 109-138).
- Executes HTTP POST requests against OpenAI-compatible chat completion endpoints (Lines 140-173).
- Executes HTTP POST requests against native Anthropic Messages endpoints (Lines 175-202).
- Generates structured rule-based documentation using naming conventions, docstrings, and parameter signatures without external API calls (Lines 204-277).

---

## 4. Method Signatures & Behavioral Analysis

| Method Name | Parameters | Return Type | Lines | Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **`__init__`** | `self: Any`, `profile: Optional[ProfileConfig]` | `Any` | L31-L47 | Initializes engine settings (`provider`, `api_key`, `api_base`, `model`, `temperature`, `timeout`, `is_enabled`) using `profile` or default config, and logs initialization status. Returns None. |
| **`explain_class`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L49-L110 | Accepts `ClassMetadata`, routes execution to an LLM provider if enabled, catches HTTP and general errors to trigger heuristic fallback, and returns a `ClassExplanation`. |
| **`_build_prompt`** | `self: Any`, `metadata: ClassMetadata` | `str` | L112-L143 | Accepts `ClassMetadata` and returns a formatted prompt string specifying strict JSON documentation requirements. |
| **`_call_openai_compatible`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L145-L178 | Accepts `ClassMetadata`, sends a POST request to an OpenAI-compatible endpoint, parses JSON output, and returns a `ClassExplanation`. |
| **`_call_anthropic_native`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L180-L208 | Accepts `ClassMetadata`, sends a POST request to the Anthropic Messages API, parses JSON content, and returns a `ClassExplanation`. |
| **`_grounded_heuristic_explainer`** | `self: Any`, `metadata: ClassMetadata` | `ClassExplanation` | L210-L277 | Accepts `ClassMetadata` and deterministically constructs a fallback `ClassExplanation` based on method signatures, inheritance, docstrings, and naming conventions. |

---

## 5. Injected Dependencies & Collaborators

- **`profile: Optional[ProfileConfig]`**: Injected configuration object supplying active provider details, API key, base URL, model name, temperature, and timeout limits.
- **`logger`**: Observed module used for logging operational status, quota exhaustion events, engine selection, and API call errors.
- **`requests`**: Observed external HTTP client library used to issue synchronous POST requests to remote LLM endpoints.
- **`load_config`**: Observed function called during initialization to fetch global application configuration if no profile is explicitly provided.
- **`ClassMetadata`**: Data structure containing parsed AST details and source code passed as input to explanation methods.
- **`ClassExplanation`**: Data model instantiated and returned containing structured architectural explanations.

---

## 6. Verifiable Code Citations

- Lines 31-48: `__init__` sets configuration attributes and evaluates `self.is_enabled` based on config state and API key presence.
- Lines 59-63: `explain_class` routes requests to `_call_anthropic_native` or `_call_openai_compatible` based on `api_base` or `provider` name.
- Lines 68-96: `explain_class` catches `RequestException`, checks status codes (429, 402, 403) or error text for quota exhaustion, logs details, and triggers `_grounded_heuristic_explainer`.
- Lines 100-107: `explain_class` routes directly to `_grounded_heuristic_explainer` when `is_enabled` is False.
- Lines 161-163: `_call_openai_compatible` posts payload to endpoint ending in `/chat/completions` using `requests.post`.
- Lines 193-195: `_call_anthropic_native` posts payload to endpoint ending in `/messages` using `requests.post`.
- Lines 204-277: `_grounded_heuristic_explainer` constructs and returns `ClassExplanation` with deterministic text based on AST metadata.

---

## 7. Known Architectural Boundaries & Limitations

- ⚠️ Cross-file inspection required to verify the implementation details of `load_config`, `logger`, `ClassMetadata`, and `ClassExplanation`.
- ⚠️ Assumes external HTTP calls return expected JSON payloads; unexpected API payload formats will cause unhandled `KeyError` or `json.JSONDecodeError` inside provider methods.
- ⚠️ No explicit schema validation is performed on the raw JSON dict returned by LLMs before instantiating `ClassExplanation(**data)`.

---
*Auto-generated by GitHub Pipeline Code Documentation Engine.*
