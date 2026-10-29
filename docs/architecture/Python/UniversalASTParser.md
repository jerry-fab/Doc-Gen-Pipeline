# Class: `UniversalASTParser`

> **Language**: `PYTHON` | **Engine**: `GROUNDED_HEURISTIC` | **Source**: [`analyzer/parser.py`](../../analyzer/parser.py#L32-L734) | **Lines**: `32 - 734`

---

## 1. Class Architecture Diagram

```mermaid
classDiagram
    class UniversalASTParser {
        +__init__() Any
        +detect_language(str file_path) Optional[str]
        +parse_file(str file_path) Optional[FileAnalysisResult]
        +_get_node_text(Optional[Node] node, bytes source_bytes) str
        +_extract_python_classes(Node root_node, bytes source_bytes, str file_path) List[ClassMetadata]
        +_extract_python_method(Node node, bytes source_bytes) MethodMetadata
        +_extract_csharp_classes(Node root_node, bytes source_bytes, str file_path) List[ClassMetadata]
        +_extract_csharp_method(Node node, bytes source_bytes) MethodMetadata
        +_extract_java_classes(Node root_node, bytes source_bytes, str file_path) List[ClassMetadata]
        +_extract_java_method(Node node, bytes source_bytes) MethodMetadata
        +_extract_javascript_classes(Node root_node, bytes source_bytes, str file_path, str lang) List[ClassMetadata]
        +_extract_go_classes(Node root_node, bytes source_bytes, str file_path) List[ClassMetadata]
        +_extract_rust_classes(Node root_node, bytes source_bytes, str file_path) List[ClassMetadata]
    }
```

---

## 2. Overview & Purpose

Orchestrates grammar loading and syntax tree traversal across multiple languages:

### Why this class exists (Design Rationale)
Encapsulates specialized methods and state within a dedicated class unit adhering to single responsibility principles.

---

## 3. Key Responsibilities

- Initializes instance dependencies: None.
- Provides operation `detect_language`.
- Provides operation `parse_file`.
- Provides operation `_get_node_text`.
- Provides operation `_extract_python_classes`.
- Provides operation `_extract_python_method`.
- Provides operation `_extract_csharp_classes`.
- Provides operation `_extract_csharp_method`.
- Provides operation `_extract_java_classes`.
- Provides operation `_extract_java_method`.
- Provides operation `_extract_javascript_classes`.
- Provides operation `_extract_go_classes`.
- Provides operation `_extract_rust_classes`.

---

## 4. Method Signatures & Behavioral Analysis

| Method Name | Parameters | Return Type | Lines | Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **`__init__`** | `self: Any` | `Any` | L38-L96 | Initializes language grammars and parser instances for supported languages. |
| **`detect_language`** | `self: Any`, `file_path: str` | `Optional[str]` | L98-L116 | Maps a file extension to its corresponding parser language key. |
| **`parse_file`** | `self: Any`, `file_path: str` | `Optional[FileAnalysisResult]` | L118-L155 | Reads a source file, parses its AST, and extracts structured class metadata. |
| **`_get_node_text`** | `self: Any`, `node: Optional[Node]`, `source_bytes: bytes` | `str` | L157-L161 | Helper to extract and decode substring bounded by a Tree-sitter node. |
| **`_extract_python_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str` | `List[ClassMetadata]` | L166-L223 | Traverses Python AST to extract classes, bases, dependencies, and methods. |
| **`_extract_python_method`** | `self: Any`, `node: Node`, `source_bytes: bytes` | `MethodMetadata` | L225-L264 | Parses a Python function_definition node into structured MethodMetadata. |
| **`_extract_csharp_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str` | `List[ClassMetadata]` | L269-L322 | Traverses C# AST extracting classes, interfaces, base_list, and DI constructors. |
| **`_extract_csharp_method`** | `self: Any`, `node: Node`, `source_bytes: bytes` | `MethodMetadata` | L324-L349 | Parses a C# method_declaration node into MethodMetadata. |
| **`_extract_java_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str` | `List[ClassMetadata]` | L354-L403 | Traverses Java AST extracting classes, interfaces, superclasses, and methods. |
| **`_extract_java_method`** | `self: Any`, `node: Node`, `source_bytes: bytes` | `MethodMetadata` | L405-L430 | Parses a Java method_declaration node into MethodMetadata. |
| **`_extract_javascript_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str`, `lang: str` | `List[ClassMetadata]` | L435-L574 | Traverses JS/TS/JSX/TSX AST to extract ES6 classes, TypeScript interfaces,
        and React functional/arrow components. |
| **`_extract_go_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str` | `List[ClassMetadata]` | L579-L656 | Traverses Go AST to extract structs and their associated receiver methods. |
| **`_extract_rust_classes`** | `self: Any`, `root_node: Node`, `source_bytes: bytes`, `file_path: str` | `List[ClassMetadata]` | L661-L734 | Traverses Rust AST to extract struct items and associated impl blocks. |

---

## 6. Verifiable Code Citations

- Lines 32-734: Declares `UniversalASTParser` in `analyzer/parser.py`.
- Lines 38-96: Constructor initialization.
- Lines 98-116: Defines method `detect_language`.
- Lines 118-155: Defines method `parse_file`.
- Lines 157-161: Defines method `_get_node_text`.
- Lines 166-223: Defines method `_extract_python_classes`.
- Lines 225-264: Defines method `_extract_python_method`.
- Lines 269-322: Defines method `_extract_csharp_classes`.
- Lines 324-349: Defines method `_extract_csharp_method`.
- Lines 354-403: Defines method `_extract_java_classes`.
- Lines 405-430: Defines method `_extract_java_method`.
- Lines 435-574: Defines method `_extract_javascript_classes`.
- Lines 579-656: Defines method `_extract_go_classes`.
- Lines 661-734: Defines method `_extract_rust_classes`.

---

## 7. Known Architectural Boundaries & Limitations

- ⚠️ End-to-end integration requires inspecting classes calling or referenced by `UniversalASTParser`.
- ⚠️ Underlying data persistence and network latency characteristics depend on external runtime configuration.

---
*Auto-generated by GitHub Pipeline Code Documentation Engine.*
