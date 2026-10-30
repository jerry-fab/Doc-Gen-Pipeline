"""
analyzer.parser
~~~~~~~~~~~~~~~

Universal Abstract Syntax Tree (AST) parser leveraging official Tree-sitter grammars.

Supported Languages:
    - Python (.py): Classes, inheritance, decorators, functions, types, and docstrings.
    - C# (.NET) (.cs): Classes, interfaces, records, constructor dependency injection, methods.
    - Java (.java): Classes, interfaces, superclasses, implements, formal parameters, methods.

Why Tree-sitter?
    Unlike simple regex or naive string matching, Tree-sitter builds a concrete syntax tree
    that understands nested blocks, syntax boundaries, and multiline declarations with 100%
    accuracy regardless of coding style.
"""

import os
from typing import Optional, List
from tree_sitter import Language, Parser, Node
import tree_sitter_python as tspython
import tree_sitter_c_sharp as tscsharp
import tree_sitter_java as tsjava

try:
    import tree_sitter_javascript as tsjs  # type: ignore
except ImportError:
    tsjs = None

try:
    import tree_sitter_typescript as tsts  # type: ignore
except ImportError:
    tsts = None

try:
    import tree_sitter_go as tsgo  # type: ignore
except ImportError:
    tsgo = None

try:
    import tree_sitter_rust as tsrs  # type: ignore
except ImportError:
    tsrs = None

from analyzer.models import ClassMetadata, MethodMetadata, ParameterMetadata, FileAnalysisResult


class UniversalASTParser:
    """
    Orchestrates grammar loading and syntax tree traversal across multiple languages:
    Python, C#, Java, JavaScript, TypeScript, TSX, Go, and Rust.
    """

    def __init__(self):
        """Initializes language grammars and parser instances for supported languages."""
        self.parsers = {}

        # 1. Initialize Python Grammar
        try:
            self.py_lang = Language(tspython.language())
            self.parsers["python"] = Parser(self.py_lang)
        except Exception as exc:
            print(f"[Warning] Failed to initialize Python grammar: {exc}")

        # 2. Initialize C# (.NET) Grammar
        try:
            self.cs_lang = Language(tscsharp.language())
            self.parsers["csharp"] = Parser(self.cs_lang)
        except Exception as exc:
            print(f"[Warning] Failed to initialize C# grammar: {exc}")

        # 3. Initialize Java Grammar
        try:
            self.java_lang = Language(tsjava.language())
            self.parsers["java"] = Parser(self.java_lang)
        except Exception as exc:
            print(f"[Warning] Failed to initialize Java grammar: {exc}")

        # 4. Initialize JavaScript / JSX Grammar
        if tsjs:
            try:
                self.js_lang = Language(tsjs.language())
                self.parsers["javascript"] = Parser(self.js_lang)
            except Exception as exc:
                print(f"[Warning] Failed to initialize JavaScript grammar: {exc}")

        # 5. Initialize TypeScript Grammar
        if tsts:
            try:
                self.ts_lang = Language(tsts.language_typescript())
                self.parsers["typescript"] = Parser(self.ts_lang)
            except Exception as exc:
                print(f"[Warning] Failed to initialize TypeScript grammar: {exc}")

        # 6. Initialize TSX Grammar
        if tsts:
            try:
                self.tsx_lang = Language(tsts.language_tsx())
                self.parsers["tsx"] = Parser(self.tsx_lang)
            except Exception as exc:
                print(f"[Warning] Failed to initialize TSX grammar: {exc}")

        # 7. Initialize Go Grammar
        if tsgo:
            try:
                self.go_lang = Language(tsgo.language())
                self.parsers["go"] = Parser(self.go_lang)
            except Exception as exc:
                print(f"[Warning] Failed to initialize Go grammar: {exc}")

        # 8. Initialize Rust Grammar
        if tsrs:
            try:
                self.rs_lang = Language(tsrs.language())
                self.parsers["rust"] = Parser(self.rs_lang)
            except Exception as exc:
                print(f"[Warning] Failed to initialize Rust grammar: {exc}")

    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Maps a file extension to its corresponding parser language key.
        """
        ext = os.path.splitext(file_path)[1].lower()
        extension_map = {
            ".py": "python",
            ".cs": "csharp",
            ".java": "java",
            ".js": "javascript",
            ".jsx": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".go": "go",
            ".rs": "rust",
        }
        return extension_map.get(ext)

    def parse_file(self, file_path: str) -> Optional[FileAnalysisResult]:
        """
        Reads a source file, parses its AST, and extracts structured class metadata.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()
        except Exception as exc:
            print(f"[Error] Failed to read source file '{file_path}': {exc}")
            return None

        return self.parse_code(file_path, source_code)

    def parse_code(self, file_path: str, source_code: str) -> Optional[FileAnalysisResult]:
        """
        Parses source code string, builds AST, and extracts structured class metadata.
        Used by both CLI and Centralized REST API server.
        """
        lang = self.detect_language(file_path)
        if not lang or lang not in self.parsers:
            return None

        source_bytes = source_code.encode("utf-8")
        parser = self.parsers[lang]
        tree = parser.parse(source_bytes)

        classes: List[ClassMetadata] = []
        if lang == "python":
            classes = self._extract_python_classes(tree.root_node, source_bytes, file_path)
        elif lang == "csharp":
            classes = self._extract_csharp_classes(tree.root_node, source_bytes, file_path)
        elif lang == "java":
            classes = self._extract_java_classes(tree.root_node, source_bytes, file_path)
        elif lang in ("javascript", "typescript", "tsx"):
            classes = self._extract_javascript_classes(tree.root_node, source_bytes, file_path, lang)
        elif lang == "go":
            classes = self._extract_go_classes(tree.root_node, source_bytes, file_path)
        elif lang == "rust":
            classes = self._extract_rust_classes(tree.root_node, source_bytes, file_path)

        return FileAnalysisResult(
            file_path=file_path,
            language=lang,
            classes=classes
        )

    def _get_node_text(self, node: Optional[Node], source_bytes: bytes) -> str:
        """Helper to extract and decode substring bounded by a Tree-sitter node."""
        if not node:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()

    # =========================================================================
    # PYTHON AST EXTRACTION
    # =========================================================================
    def _extract_python_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        """Traverses Python AST to extract classes, bases, dependencies, and methods."""
        classes = []

        def visit(node: Node):
            if node.type == "class_definition":
                # Class Name
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"

                # Inheritance: Base classes listed inside class Foo(Bar, Baz):
                inherits = []
                superclasses_node = node.child_by_field_name("superclasses")
                if superclasses_node:
                    for child in superclasses_node.children:
                        if child.type in ("identifier", "attribute"):
                            inherits.append(self._get_node_text(child, source_bytes))

                # Class Body: Methods, Docstrings, Injected Dependencies
                methods = []
                dependencies = []
                docstring = None
                body_node = node.child_by_field_name("body")
                if body_node:
                    for stmt in body_node.children:
                        # Extract top-level docstring if first statement is a string literal
                        if stmt.type == "expression_statement" and docstring is None:
                            first_child = stmt.children[0] if stmt.children else None
                            if first_child and first_child.type == "string":
                                docstring = self._get_node_text(first_child, source_bytes).strip("\"'\n ")
                        elif stmt.type == "function_definition":
                            method = self._extract_python_method(stmt, source_bytes)
                            methods.append(method)
                            # Constructor parameters represent injected dependencies
                            if method.name == "__init__":
                                for p in method.parameters:
                                    if p.name not in ("self", "cls"):
                                        dependencies.append(f"{p.name}: {p.type_hint}")

                classes.append(ClassMetadata(
                    name=class_name,
                    file_path=file_path,
                    language="python",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    inherits=inherits,
                    dependencies=dependencies,
                    methods=methods,
                    docstring=docstring,
                    raw_code=self._get_node_text(node, source_bytes)
                ))

            # Recurse into all child nodes
            for child in node.children:
                visit(child)

        visit(root_node)
        return classes

    def _extract_python_method(self, node: Node, source_bytes: bytes) -> MethodMetadata:
        """Parses a Python function_definition node into structured MethodMetadata."""
        name_node = node.child_by_field_name("name")
        method_name = self._get_node_text(name_node, source_bytes) if name_node else "unknown_func"

        return_type_node = node.child_by_field_name("return_type")
        return_type = self._get_node_text(return_type_node, source_bytes) if return_type_node else "Any"

        # Parameters
        params = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            for child in params_node.children:
                if child.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter"):
                    p_text = self._get_node_text(child, source_bytes)
                    p_name = p_text.split(":")[0].split("=")[0].strip()
                    p_type = "Any"
                    if ":" in p_text:
                        p_type = p_text.split(":")[1].split("=")[0].strip()
                    params.append(ParameterMetadata(name=p_name, type_hint=p_type))

        # Method Docstring
        docstring = None
        body_node = node.child_by_field_name("body")
        if body_node and len(body_node.children) > 0:
            first_stmt = body_node.children[0]
            if first_stmt.type == "expression_statement":
                fc = first_stmt.children[0] if first_stmt.children else None
                if fc and fc.type == "string":
                    docstring = self._get_node_text(fc, source_bytes).strip("\"'\n ")

        return MethodMetadata(
            name=method_name,
            parameters=params,
            return_type=return_type,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
            is_async=node.children[0].type == "async" if node.children else False
        )

    # =========================================================================
    # C# (.NET) AST EXTRACTION
    # =========================================================================
    def _extract_csharp_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        """Traverses C# AST extracting classes, interfaces, base_list, and DI constructors."""
        classes = []

        def visit(node: Node):
            if node.type in ("class_declaration", "interface_declaration", "record_declaration"):
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"

                # Inheritance & Interface Implementation: base_list node
                inherits = []
                for child in node.children:
                    if child.type == "base_list":
                        for base_child in child.children:
                            if base_child.type not in (":", ","):
                                inherits.append(self._get_node_text(base_child, source_bytes))

                # Members: Methods, Constructor Injected Dependencies, Fields
                methods = []
                dependencies = []
                fields = []
                body_node = node.child_by_field_name("body")
                if body_node:
                    for member in body_node.children:
                        if member.type == "method_declaration":
                            methods.append(self._extract_csharp_method(member, source_bytes))
                        elif member.type == "constructor_declaration":
                            param_list = member.child_by_field_name("parameters")
                            if param_list:
                                for p in param_list.children:
                                    if p.type == "parameter":
                                        p_text = self._get_node_text(p, source_bytes)
                                        dependencies.append(p_text)
                        elif member.type in ("field_declaration", "property_declaration"):
                            fields.append(self._get_node_text(member, source_bytes))

                classes.append(ClassMetadata(
                    name=class_name,
                    file_path=file_path,
                    language="csharp",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    inherits=inherits,
                    dependencies=dependencies,
                    fields=fields[:10],
                    methods=methods,
                    raw_code=self._get_node_text(node, source_bytes)
                ))

            for child in node.children:
                visit(child)

        visit(root_node)
        return classes

    def _extract_csharp_method(self, node: Node, source_bytes: bytes) -> MethodMetadata:
        """Parses a C# method_declaration node into MethodMetadata."""
        name_node = node.child_by_field_name("name")
        method_name = self._get_node_text(name_node, source_bytes) if name_node else "unknown_method"

        type_node = node.child_by_field_name("type")
        return_type = self._get_node_text(type_node, source_bytes) if type_node else "void"

        params = []
        param_list = node.child_by_field_name("parameters")
        if param_list:
            for p in param_list.children:
                if p.type == "parameter":
                    type_child = p.child_by_field_name("type")
                    name_child = p.child_by_field_name("name")
                    p_type = self._get_node_text(type_child, source_bytes) if type_child else "var"
                    p_name = self._get_node_text(name_child, source_bytes) if name_child else "arg"
                    params.append(ParameterMetadata(name=p_name, type_hint=p_type))

        return MethodMetadata(
            name=method_name,
            parameters=params,
            return_type=return_type,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1
        )

    # =========================================================================
    # JAVA AST EXTRACTION
    # =========================================================================
    def _extract_java_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        """Traverses Java AST extracting classes, interfaces, superclasses, and methods."""
        classes = []

        def visit(node: Node):
            if node.type in ("class_declaration", "interface_declaration", "record_declaration"):
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"

                # Inheritance: extends superclass and implements super_interfaces
                inherits = []
                for child in node.children:
                    if child.type in ("superclass", "super_interfaces", "extends_interfaces"):
                        for sub in child.children:
                            if sub.type not in ("extends", "implements", ","):
                                inherits.append(self._get_node_text(sub, source_bytes))

                # Members: Methods and Constructor Dependencies
                methods = []
                dependencies = []
                body_node = node.child_by_field_name("body")
                if body_node:
                    for member in body_node.children:
                        if member.type == "method_declaration":
                            methods.append(self._extract_java_method(member, source_bytes))
                        elif member.type == "constructor_declaration":
                            param_list = member.child_by_field_name("parameters")
                            if param_list:
                                for p in param_list.children:
                                    if p.type == "formal_parameter":
                                        p_text = self._get_node_text(p, source_bytes)
                                        dependencies.append(p_text)

                classes.append(ClassMetadata(
                    name=class_name,
                    file_path=file_path,
                    language="java",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    inherits=inherits,
                    dependencies=dependencies,
                    methods=methods,
                    raw_code=self._get_node_text(node, source_bytes)
                ))

            for child in node.children:
                visit(child)

        visit(root_node)
        return classes

    def _extract_java_method(self, node: Node, source_bytes: bytes) -> MethodMetadata:
        """Parses a Java method_declaration node into MethodMetadata."""
        name_node = node.child_by_field_name("name")
        method_name = self._get_node_text(name_node, source_bytes) if name_node else "unknown_method"

        type_node = node.child_by_field_name("type")
        return_type = self._get_node_text(type_node, source_bytes) if type_node else "void"

        params = []
        param_list = node.child_by_field_name("parameters")
        if param_list:
            for p in param_list.children:
                if p.type == "formal_parameter":
                    type_child = p.child_by_field_name("type")
                    name_child = p.child_by_field_name("name")
                    p_type = self._get_node_text(type_child, source_bytes) if type_child else "Object"
                    p_name = self._get_node_text(name_child, source_bytes) if name_child else "arg"
                    params.append(ParameterMetadata(name=p_name, type_hint=p_type))

        return MethodMetadata(
            name=method_name,
            parameters=params,
            return_type=return_type,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1
        )

    # =========================================================================
    # JAVASCRIPT, TYPESCRIPT & REACT JSX/TSX EXTRACTION
    # =========================================================================
    def _extract_javascript_classes(self, root_node: Node, source_bytes: bytes, file_path: str, lang: str) -> List[ClassMetadata]:
        """
        Traverses JS/TS/JSX/TSX AST to extract ES6 classes, TypeScript interfaces,
        and React functional/arrow components.
        """
        classes = []

        def visit(node: Node):
            # 1. ES6 Class or TypeScript Class
            if node.type in ("class_declaration", "class"):
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"
                
                inherits = []
                heritage = node.child_by_field_name("heritage") or node.child_by_field_name("super_class")
                if heritage:
                    for h_child in heritage.children:
                        if h_child.type in ("identifier", "type_identifier"):
                            inherits.append(self._get_node_text(h_child, source_bytes))

                body = node.child_by_field_name("body")
                methods = []
                dependencies = []
                fields = []

                if body:
                    for member in body.children:
                        if member.type == "method_definition":
                            m_name_node = member.child_by_field_name("name")
                            m_name = self._get_node_text(m_name_node, source_bytes)
                            m_params = []
                            param_list = member.child_by_field_name("parameters")
                            if param_list:
                                for p in param_list.children:
                                    if p.type in ("identifier", "required_parameter", "optional_parameter", "assignment_pattern"):
                                        p_name = self._get_node_text(p, source_bytes).split("=")[0].split(":")[0].strip()
                                        if p_name and p_name not in ("this",):
                                            m_params.append(ParameterMetadata(name=p_name, type_hint="Any"))
                            
                            methods.append(MethodMetadata(
                                name=m_name,
                                parameters=m_params,
                                return_type="any",
                                start_line=member.start_point[0] + 1,
                                end_line=member.end_point[0] + 1
                            ))
                            if m_name == "constructor":
                                for p in m_params:
                                    dependencies.append(p.name)

                        elif member.type in ("field_definition", "public_field_definition", "property_signature"):
                            f_name_node = member.child_by_field_name("name")
                            if f_name_node:
                                fields.append(self._get_node_text(f_name_node, source_bytes))

                classes.append(ClassMetadata(
                    name=class_name,
                    file_path=file_path,
                    language=lang,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    inherits=inherits,
                    dependencies=dependencies,
                    fields=fields,
                    methods=methods,
                    raw_code=self._get_node_text(node, source_bytes)
                ))

            # 2. React UI Functional Components (e.g. function App(), function Home())
            elif node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                func_name = self._get_node_text(name_node, source_bytes)
                # Convention: Capitalized functions in React/JS/TS are UI Components
                if func_name and func_name[0].isupper():
                    methods = []
                    params = []
                    param_list = node.child_by_field_name("parameters")
                    if param_list:
                        for p in param_list.children:
                            if p.type in ("identifier", "required_parameter", "formal_parameters", "object_pattern"):
                                p_str = self._get_node_text(p, source_bytes).strip("{} ")
                                for item in p_str.split(","):
                                    item_clean = item.split(":")[0].strip()
                                    if item_clean:
                                        params.append(ParameterMetadata(name=item_clean, type_hint="Props"))

                    methods.append(MethodMetadata(
                        name="render",
                        parameters=params,
                        return_type="JSX.Element",
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1
                    ))

                    classes.append(ClassMetadata(
                        name=func_name,
                        file_path=file_path,
                        language=lang,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        inherits=["React.FC"],
                        dependencies=[p.name for p in params],
                        fields=[],
                        methods=methods,
                        raw_code=self._get_node_text(node, source_bytes)
                    ))

            # 3. Arrow function React components (e.g. const Home = () => { ... })
            elif node.type in ("lexical_declaration", "variable_declaration"):
                for decl in node.children:
                    if decl.type == "variable_declarator":
                        name_child = decl.child_by_field_name("name")
                        val_child = decl.child_by_field_name("value")
                        if name_child and val_child and val_child.type in ("arrow_function", "function_expression"):
                            comp_name = self._get_node_text(name_child, source_bytes)
                            if comp_name and comp_name[0].isupper():
                                classes.append(ClassMetadata(
                                    name=comp_name,
                                    file_path=file_path,
                                    language=lang,
                                    start_line=decl.start_point[0] + 1,
                                    end_line=decl.end_point[0] + 1,
                                    inherits=["React.FC"],
                                    dependencies=[],
                                    fields=[],
                                    methods=[MethodMetadata(
                                        name="render",
                                        parameters=[],
                                        return_type="JSX.Element",
                                        start_line=decl.start_point[0] + 1,
                                        end_line=decl.end_point[0] + 1
                                    )],
                                    raw_code=self._get_node_text(decl, source_bytes)
                                ))

            for child in node.children:
                visit(child)

        visit(root_node)
        return classes

    # =========================================================================
    # GO (GOLANG) STRUCT & METHOD EXTRACTION
    # =========================================================================
    def _extract_go_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        """Traverses Go AST to extract structs and their associated receiver methods."""
        classes = {}
        all_methods = []

        def visit(node: Node):
            # 1. Type declaration: type OrderService struct { ... }
            if node.type == "type_declaration":
                for spec in node.children:
                    if spec.type == "type_spec":
                        name_node = spec.child_by_field_name("name")
                        type_node = spec.child_by_field_name("type")
                        struct_name = self._get_node_text(name_node, source_bytes)
                        fields = []
                        if type_node and type_node.type == "struct_type":
                            field_list = type_node.child_by_field_name("fields")
                            if field_list:
                                for f in field_list.children:
                                    if f.type == "field_declaration":
                                        f_text = self._get_node_text(f, source_bytes)
                                        if f_text:
                                            fields.append(f_text)

                        classes[struct_name] = ClassMetadata(
                            name=struct_name,
                            file_path=file_path,
                            language="go",
                            start_line=spec.start_point[0] + 1,
                            end_line=spec.end_point[0] + 1,
                            inherits=[],
                            dependencies=[],
                            fields=fields,
                            methods=[],
                            raw_code=self._get_node_text(spec, source_bytes)
                        )

            # 2. Method declaration: func (s *OrderService) PlaceOrder(...) ...
            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                m_name = self._get_node_text(name_node, source_bytes)
                receiver_node = node.child_by_field_name("receiver")
                recv_text = self._get_node_text(receiver_node, source_bytes).replace("*", "").replace("(", "").replace(")", "").strip()
                recv_type = recv_text.split()[-1] if recv_text else ""
                
                params = []
                param_list = node.child_by_field_name("parameters")
                if param_list:
                    for p in param_list.children:
                        if p.type == "parameter_declaration":
                            p_text = self._get_node_text(p, source_bytes)
                            parts = p_text.split()
                            p_name = parts[0] if parts else "arg"
                            p_type = parts[1] if len(parts) > 1 else "any"
                            params.append(ParameterMetadata(name=p_name, type_hint=p_type))

                res_node = node.child_by_field_name("result")
                ret_type = self._get_node_text(res_node, source_bytes) if res_node else "void"

                m_meta = MethodMetadata(
                    name=m_name,
                    parameters=params,
                    return_type=ret_type,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1
                )
                all_methods.append((recv_type, m_meta))

            for child in node.children:
                visit(child)

        visit(root_node)

        # Attach methods to corresponding structs
        for recv_type, m_meta in all_methods:
            if recv_type in classes:
                classes[recv_type].methods.append(m_meta)

        return list(classes.values())

    # =========================================================================
    # RUST STRUCT & IMPL EXTRACTION
    # =========================================================================
    def _extract_rust_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        """Traverses Rust AST to extract struct items and associated impl blocks."""
        classes = {}
        all_methods = []

        def visit(node: Node):
            # 1. Struct declaration: pub struct OrderService { ... }
            if node.type == "struct_item":
                name_node = node.child_by_field_name("name")
                struct_name = self._get_node_text(name_node, source_bytes)
                fields = []
                body = node.child_by_field_name("body")
                if body:
                    for f in body.children:
                        if f.type == "field_declaration":
                            fields.append(self._get_node_text(f, source_bytes))

                classes[struct_name] = ClassMetadata(
                    name=struct_name,
                    file_path=file_path,
                    language="rust",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    inherits=[],
                    dependencies=[],
                    fields=fields,
                    methods=[],
                    raw_code=self._get_node_text(node, source_bytes)
                )

            # 2. Impl block: impl OrderService { ... }
            elif node.type == "impl_item":
                type_node = node.child_by_field_name("type")
                struct_name = self._get_node_text(type_node, source_bytes)
                body = node.child_by_field_name("body")
                if body:
                    for item in body.children:
                        if item.type == "function_item":
                            fn_name_node = item.child_by_field_name("name")
                            fn_name = self._get_node_text(fn_name_node, source_bytes)
                            ret_node = item.child_by_field_name("return_type")
                            ret_type = self._get_node_text(ret_node, source_bytes).replace("->", "").strip() if ret_node else "()"
                            params = []
                            param_list = item.child_by_field_name("parameters")
                            if param_list:
                                for p in param_list.children:
                                    if p.type == "parameter":
                                        p_text = self._get_node_text(p, source_bytes)
                                        parts = p_text.split(":")
                                        p_name = parts[0].strip()
                                        p_type = parts[1].strip() if len(parts) > 1 else "Self"
                                        if p_name not in ("self", "&self", "&mut self"):
                                            params.append(ParameterMetadata(name=p_name, type_hint=p_type))

                            m_meta = MethodMetadata(
                                name=fn_name,
                                parameters=params,
                                return_type=ret_type,
                                start_line=item.start_point[0] + 1,
                                end_line=item.end_point[0] + 1
                            )
                            all_methods.append((struct_name, m_meta))

            for child in node.children:
                visit(child)

        visit(root_node)

        # Attach methods to corresponding structs
        for struct_name, m_meta in all_methods:
            if struct_name in classes:
                classes[struct_name].methods.append(m_meta)

        return list(classes.values())
