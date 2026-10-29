"""
analyzer.ai_engine
~~~~~~~~~~~~~~~~~~

Grounded AI Explanation Engine supporting Multi-Environment Profiles:
    - Local: Fast/Free tier providers (Google Gemini Flash, Groq).
    - Production: Enterprise precision providers (Mistral Codestral, Anthropic Claude).
    - Offline Fallback: Zero-cost deterministic heuristic explainer.

Fault Tolerance & Observability:
    - Automatically detects API Quota Exhaustion (HTTP 429 / Rate Limits).
    - Logs quota failures to `logs/quota_complete_log/`.
    - Logs operational events to `logs/fn_log/`.
    - Logs unhandled exceptions to `logs/err_log/`.
    - Seamlessly falls back to the Grounded Heuristic Engine without crashing.
"""

import json
from typing import Optional
import requests

from analyzer.models import ClassMetadata, ClassExplanation
from analyzer.utils import load_config, ProfileConfig, logger


class AIDocumentationEngine:
    """
    Coordinates semantic analysis and documentation synthesis based on the active profile.
    """

    def __init__(self, profile: Optional[ProfileConfig] = None):
        """
        Initializes API credentials and endpoints from the chosen profile or config.json.
        """
        app_config = load_config()
        self.profile = profile or app_config.get_active_profile()
        self.provider = self.profile.provider.lower()
        self.api_key = self.profile.api_key.strip() if self.profile.api_key else ""
        self.api_base = self.profile.api_base.rstrip("/")
        self.model = self.profile.model
        self.temperature = self.profile.temperature
        self.timeout = self.profile.timeout_seconds
        self.is_enabled = self.profile.enabled and bool(self.api_key)

        logger.log_fn(
            f"Initialized AIDocumentationEngine | Provider: {self.provider.upper()} | Model: {self.model} | Enabled: {self.is_enabled}"
        )

    def explain_class(self, metadata: ClassMetadata) -> ClassExplanation:
        """
        Generates an architectural explanation for a given class.
        
        Strategy:
            - If active profile is enabled: Calls the designated LLM API.
            - If Quota / Rate-limit exhausted: Logs to quota_complete_log and switches to Heuristic.
            - If unexpected error occurs: Logs to err_log and switches to Heuristic.
            - If disabled: Runs Heuristic engine directly.
        """
        if self.is_enabled:
            try:
                logger.log_fn(f"Invoking {self.provider.upper()} API for Class '{metadata.name}' ({metadata.file_path})...")
                if "anthropic.com" in self.api_base or "claude" in self.provider:
                    explanation = self._call_anthropic_native(metadata)
                else:
                    explanation = self._call_openai_compatible(metadata)
                
                explanation.engine_used = self.provider.upper()
                logger.log_engine_used(metadata.name, explanation.engine_used)
                return explanation

            except requests.exceptions.RequestException as req_err:
                error_str = str(req_err).lower()
                status_code = getattr(req_err.response, "status_code", None)

                # Check for Quota or Rate-Limit exhaustion
                is_quota_issue = (
                    status_code in (429, 402, 403) or
                    any(keyword in error_str for keyword in ("quota", "rate limit", "resource_exhausted", "insufficient_quota"))
                )

                if is_quota_issue:
                    details = f"HTTP {status_code}: {req_err}"
                    print(f"[Notice] Quota/Rate-limit reached for {self.provider.upper()}. Switching to Heuristic Engine.")
                    logger.log_quota_exhausted(
                        provider=self.provider,
                        model=self.model,
                        class_name=metadata.name,
                        error_details=details
                    )
                    fallback_msg = f"Quota/Rate-limit exhausted for {self.provider.upper()} ({details})"
                else:
                    print(f"[Warning] {self.provider.upper()} API error ({req_err}). Switching to Heuristic Engine.")
                    logger.log_error(f"LLM API Call Error for Class '{metadata.name}'", exc=req_err)
                    fallback_msg = f"{self.provider.upper()} API Error: {req_err}"

                explanation = self._grounded_heuristic_explainer(metadata)
                logger.log_engine_used(metadata.name, explanation.engine_used, fallback_reason=fallback_msg)
                return explanation

            except Exception as unhandled_err:
                print(f"[Warning] Unexpected error during AI explanation ({unhandled_err}). Falling back to Heuristic Engine.")
                logger.log_error(f"Unexpected Error during explanation for Class '{metadata.name}'", exc=unhandled_err)
                explanation = self._grounded_heuristic_explainer(metadata)
                logger.log_engine_used(metadata.name, explanation.engine_used, fallback_reason=f"Exception: {unhandled_err}")
                return explanation
        else:
            logger.log_fn(f"LLM disabled in config. Running Grounded Heuristic Engine for Class '{metadata.name}'.")
            explanation = self._grounded_heuristic_explainer(metadata)
            logger.log_engine_used(metadata.name, explanation.engine_used, fallback_reason="LLM disabled in active profile")
            return explanation

    def _build_prompt(self, metadata: ClassMetadata) -> str:
        return f"""You are a Senior Software Architect and technical documentation specialist.
Analyze this {metadata.language.upper()} class: `{metadata.name}` from file `{metadata.file_path}` (Lines {metadata.start_line}-{metadata.end_line}).

AST METADATA:
- Inherits: {metadata.inherits}
- Injected Dependencies: {metadata.dependencies}
- Methods: {[m.name + ' (' + ', '.join(p.name + ': ' + (p.type_hint or '') for p in m.parameters) + ') -> ' + (m.return_type or '') for m in metadata.methods]}
- Existing Docstring: {metadata.docstring}

SOURCE CODE:
```{metadata.language}
{metadata.raw_code}
```

STRICT ARCHITECTURAL RULES:
1. ONLY describe what is directly observable in the code.
2. Clearly separate observed functionality from INFERRED design rationale.
3. If database persistence, external network calls, or validation are not explicitly defined, DO NOT invent them. Explicitly state that cross-file inspection is required.
4. Provide exact line number citations.

Respond with strict JSON adhering to this schema:
{{
  "class_name": "{metadata.name}",
  "purpose": "A concise explanation of what this class does.",
  "design_rationale": "Why this class exists (e.g., separation of concerns, abstraction, dependency injection).",
  "responsibilities": ["Primary task 1", "Primary task 2"],
  "dependencies_explained": {{ "DependencyName": "Role of this dependency" }},
  "key_methods_explained": {{ "method_name": "What this method does and returns" }},
  "evidence_citations": ["Line X-Y: implements Z", "Line A: delegates to B"],
  "potential_limitations": ["Requires investigation on ...", "No observable error handling for ..."]
}}"""

    def _call_openai_compatible(self, metadata: ClassMetadata) -> ClassExplanation:
        """Invokes OpenAI-compatible endpoints (Gemini, Groq, Mistral, OpenRouter)."""
        prompt = self._build_prompt(metadata)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior software architect who produces grounded, hallucination-free code documentation in JSON."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"} if any(x in self.model for x in ("gpt", "mistral", "codestral")) else None
        }

        endpoint = f"{self.api_base}/chat/completions" if not self.api_base.endswith("/chat/completions") else self.api_base
        response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # Clean markdown code block wraps if returned by some providers
        if content.strip().startswith("```"):
            lines = content.strip().splitlines()
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        data.setdefault("engine_used", self.provider.upper())
        return ClassExplanation(**data)

    def _call_anthropic_native(self, metadata: ClassMetadata) -> ClassExplanation:
        """Invokes native Anthropic Messages API for Claude."""
        prompt = self._build_prompt(metadata)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": self.temperature,
            "system": "You are a senior software architect who produces grounded, hallucination-free code documentation in JSON.",
            "messages": [
                {"role": "user", "content": prompt + "\nOutput strictly valid JSON with no markdown quotes."}
            ]
        }
        endpoint = f"{self.api_base}/messages" if not self.api_base.endswith("/messages") else self.api_base
        response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        content = response.json()["content"][0]["text"]

        if content.strip().startswith("```"):
            lines = content.strip().splitlines()
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        data.setdefault("engine_used", "CLAUDE")
        return ClassExplanation(**data)

    def _grounded_heuristic_explainer(self, metadata: ClassMetadata) -> ClassExplanation:
        """Deterministic, rule-based fallback generator."""
        doc = metadata.docstring.strip() if metadata.docstring else ""
        if doc:
            purpose = doc.split("\n")[0]
        elif metadata.name.endswith("Service"):
            purpose = f"Encapsulates domain business logic and coordination for {metadata.name[:-7].lower()} workflows."
        elif metadata.name.endswith("Processor"):
            purpose = f"Processes transactions and lifecycle tasks related to {metadata.name[:-9].lower()} operations."
        elif metadata.name.endswith("Connection"):
            purpose = f"Manages connectivity and resource handling for low-level system interactions."
        elif metadata.name.startswith("I") and metadata.name[1:2].isupper():
            purpose = f"Defines an interface contract for {metadata.name[1:].lower()} capabilities."
        else:
            purpose = f"Provides core abstraction and member behaviors for `{metadata.name}`."

        rationale_parts = []
        if metadata.inherits:
            rationale_parts.append(
                f"Implements inheritance/interface contract from `{', '.join(metadata.inherits)}` ensuring substitutability and polymorphism."
            )
        if metadata.dependencies:
            rationale_parts.append(
                "Employs Dependency Injection via constructor parameters to decouple implementations from caller code."
            )
        if not rationale_parts:
            rationale_parts.append(
                "Encapsulates specialized methods and state within a dedicated class unit adhering to single responsibility principles."
            )
        design_rationale = " ".join(rationale_parts)

        responsibilities = []
        key_methods = {}
        citations = [
            f"Lines {metadata.start_line}-{metadata.end_line}: Declares `{metadata.name}` in `{metadata.file_path}`."
        ]

        for m in metadata.methods:
            if m.name in ("__init__", metadata.name):
                params_desc = ", ".join(p.name for p in m.parameters if p.name not in ("self", "cls")) or "None"
                responsibilities.append(f"Initializes instance dependencies: {params_desc}.")
                citations.append(f"Lines {m.start_line}-{m.end_line}: Constructor initialization.")
            else:
                desc = m.docstring or f"Executes `{m.name}` accepting {len(m.parameters)} parameter(s) and returning `{m.return_type}`."
                key_methods[m.name] = desc
                responsibilities.append(f"Provides operation `{m.name}`.")
                citations.append(f"Lines {m.start_line}-{m.end_line}: Defines method `{m.name}`.")

        deps_explained = {}
        for d in metadata.dependencies:
            deps_explained[d] = "Injected collaborator utilized for delegating specialized operations."

        limitations = [
            f"End-to-end integration requires inspecting classes calling or referenced by `{metadata.name}`.",
            "Underlying data persistence and network latency characteristics depend on external runtime configuration."
        ]

        return ClassExplanation(
            class_name=metadata.name,
            engine_used="GROUNDED_HEURISTIC",
            purpose=purpose,
            design_rationale=design_rationale,
            responsibilities=responsibilities,
            dependencies_explained=deps_explained,
            key_methods_explained=key_methods,
            evidence_citations=citations,
            potential_limitations=limitations
        )
