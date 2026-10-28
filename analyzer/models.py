from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ParameterMetadata(BaseModel):
    name: str
    type_hint: Optional[str] = "Any"
    default_value: Optional[str] = None

class MethodMetadata(BaseModel):
    name: str
    parameters: List[ParameterMetadata] = Field(default_factory=list)
    return_type: Optional[str] = "void"
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    is_async: bool = False
    is_static: bool = False
    visibility: str = "public"

class ClassMetadata(BaseModel):
    name: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    inherits: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    fields: List[str] = Field(default_factory=list)
    methods: List[MethodMetadata] = Field(default_factory=list)
    docstring: Optional[str] = None
    raw_code: str = ""

class ClassExplanation(BaseModel):
    class_name: str
    purpose: str
    design_rationale: str
    responsibilities: List[str] = Field(default_factory=list)
    dependencies_explained: Dict[str, str] = Field(default_factory=dict)
    key_methods_explained: Dict[str, str] = Field(default_factory=dict)
    evidence_citations: List[str] = Field(default_factory=list)
    potential_limitations: List[str] = Field(default_factory=list)

class FileAnalysisResult(BaseModel):
    file_path: str
    language: str
    classes: List[ClassMetadata] = Field(default_factory=list)
