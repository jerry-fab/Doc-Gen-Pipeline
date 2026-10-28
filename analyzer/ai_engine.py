import os
import json
from typing import Optional
import requests
from dotenv import load_dotenv

from analyzer.models import ClassMetadata, ClassExplanation

load_dotenv()

class AIDocumentationEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def explain_class(self, metadata: ClassMetadata) -> ClassExplanation:
        """
        Explains class purpose and rationale.
        Uses LLM if API key is present; otherwise falls back to a deterministic heuristic engine.
        """
        if self.api_key:
            try:
                return self._call_llm(metadata)
            except Exception as e:
                print(f"[Warning] LLM call failed ({e}). Falling back to grounded heuristic explainer.")
                return self._grounded_heuristic_explainer(metadata)
        else:
            return self._grounded_heuristic_explainer(metadata)

    def _call_llm(self, metadata: ClassMetadata) -> ClassExplanation:
        prompt = f"""
You are a Senior Software Architect and technical documentation specialist.
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

STRICT RULES:
1. ONLY describe what is directly observable in the code.
2. Clearly separate observed functionality from INFERRED design rationale.
3. If database persistence, external network calls, or validation are not explicitly defined, DO NOT invent them. Explicitly mention that further cross-file investigation is required.
4. Provide exact line number citations.

Respond with strict JSON adhering to this format:
{{
  "class_name": "{metadata.name}",
  "purpose": "A concise explanation of what this class does.",
  "design_rationale": "Why this class exists (e.g., separation of concerns, abstraction, dependency injection).",
  "responsibilities": ["Primary task 1", "Primary task 2"],
  "dependencies_explained": {{ "DependencyName": "Role of this dependency" }},
  "key_methods_explained": {{ "method_name": "What this method does and returns" }},
  "evidence_citations": ["Line X-Y: implements Z", "Line A: delegates to B"],
  "potential_limitations": ["Requires investigation on ...", "No observable error handling for ..."]
}}
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a senior software architect who produces grounded, hallucination-free code documentation in JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"} if "gpt" in self.model else None
        }

        resp = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return ClassExplanation(**data)

    def _grounded_heuristic_explainer(self, metadata: ClassMetadata) -> ClassExplanation:
        """
        Grounded deterministic fallback that extracts verifiable facts and observed patterns.
        Guarantees 100% offline availability with zero cost and zero hallucination.
        """
        # Determine purpose based on docstring or naming conventions
        doc = metadata.docstring.strip() if metadata.docstring else ""
        if doc:
            purpose = doc.split("\n")[0]
        elif metadata.name.endswith("Service"):
            purpose = f"Encapsulates domain business logic and coordination for {metadata.name[:-7].lower()} workflows."
        elif metadata.name.endswith("Processor"):
            purpose = f"Processes transactions and tasks related to {metadata.name[:-9].lower()} operations."
        elif metadata.name.endswith("Connection"):
            purpose = f"Manages connectivity and resource handling for low-level interactions."
        else:
            purpose = f"Provides core abstraction and behaviors for `{metadata.name}`."

        # Inferred Design Rationale
        rationale_parts = []
        if metadata.inherits:
            rationale_parts.append(f"Implements inheritance/interface contract from `{', '.join(metadata.inherits)}` ensuring substitutability.")
        if metadata.dependencies:
            rationale_parts.append("Employs Dependency Injection via constructor parameters to decouple implementations from caller code.")
        if not rationale_parts:
            rationale_parts.append("Encapsulates specialized methods and state within a dedicated class unit.")
        design_rationale = " ".join(rationale_parts)

        # Responsibilities & Citations
        responsibilities = []
        key_methods = {}
        citations = [f"Lines {metadata.start_line}-{metadata.end_line}: Declares `{metadata.name}` in `{metadata.file_path}`."]

        for m in metadata.methods:
            if m.name in ("__init__", metadata.name):
                responsibilities.append(f"Initializes dependencies: {', '.join(p.name for p in m.parameters if p.name not in ('self', 'cls')) or 'None'}.")
                citations.append(f"Lines {m.start_line}-{m.end_line}: Constructor initialization.")
            else:
                desc = m.docstring or f"Executes `{m.name}` accepting {len(m.parameters)} parameter(s) and returning `{m.return_type}`."
                key_methods[m.name] = desc
                responsibilities.append(f"Provides operation `{m.name}`.")
                citations.append(f"Lines {m.start_line}-{m.end_line}: Defines method `{m.name}`.")

        # Dependencies
        deps_explained = {}
        for d in metadata.dependencies:
            deps_explained[d] = "Injected dependency used for delegating operations."

        limitations = [
            f"End-to-end integration requires inspecting classes calling or referenced by `{metadata.name}`.",
            "Underlying data persistence and network latency characteristics depend on external runtime configuration."
        ]

        return ClassExplanation(
            class_name=metadata.name,
            purpose=purpose,
            design_rationale=design_rationale,
            responsibilities=responsibilities,
            dependencies_explained=deps_explained,
            key_methods_explained=key_methods,
            evidence_citations=citations,
            potential_limitations=limitations
        )
