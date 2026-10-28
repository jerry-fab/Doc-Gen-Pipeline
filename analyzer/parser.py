import os
from typing import Optional, List
from tree_sitter import Language, Parser, Node
import tree_sitter_python as tspython
import tree_sitter_c_sharp as tscsharp
import tree_sitter_java as tsjava

from analyzer.models import ClassMetadata, MethodMetadata, ParameterMetadata, FileAnalysisResult

class UniversalASTParser:
    def __init__(self):
        self.parsers = {}
        # Initialize Python
        try:
            self.py_lang = Language(tspython.language())
            self.py_parser = Parser(self.py_lang)
            self.parsers["python"] = self.py_parser
        except Exception as e:
            print(f"[Warning] Failed to initialize Python parser: {e}")

        # Initialize C#
        try:
            self.cs_lang = Language(tscsharp.language())
            self.cs_parser = Parser(self.cs_lang)
            self.parsers["csharp"] = self.cs_parser
        except Exception as e:
            print(f"[Warning] Failed to initialize C# parser: {e}")

        # Initialize Java
        try:
            self.java_lang = Language(tsjava.language())
            self.java_parser = Parser(self.java_lang)
            self.parsers["java"] = self.java_parser
        except Exception as e:
            print(f"[Warning] Failed to initialize Java parser: {e}")

    def detect_language(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".cs": "csharp",
            ".java": "java",
        }
        return mapping.get(ext)

    def parse_file(self, file_path: str) -> Optional[FileAnalysisResult]:
        lang = self.detect_language(file_path)
        if not lang or lang not in self.parsers:
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()
        except Exception as e:
            print(f"[Error] Failed to read {file_path}: {e}")
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

        return FileAnalysisResult(
            file_path=file_path,
            language=lang,
            classes=classes
        )

    def _get_node_text(self, node: Optional[Node], source_bytes: bytes) -> str:
        if not node:
            return ""
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()

    # ------------------ PYTHON PARSER ------------------
    def _extract_python_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        classes = []

        def visit(node: Node):
            if node.type == "class_definition":
                class_name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(class_name_node, source_bytes) if class_name_node else "AnonymousClass"

                # Superclasses / Inheritance
                inherits = []
                superclasses_node = node.child_by_field_name("superclasses")
                if superclasses_node:
                    for child in superclasses_node.children:
                        if child.type in ("identifier", "attribute"):
                            inherits.append(self._get_node_text(child, source_bytes))

                # Body & Methods
                methods = []
                dependencies = []
                docstring = None
                body_node = node.child_by_field_name("body")
                if body_node:
                    for stmt in body_node.children:
                        if stmt.type == "expression_statement" and docstring is None:
                            first_child = stmt.children[0] if stmt.children else None
                            if first_child and first_child.type == "string":
                                docstring = self._get_node_text(first_child, source_bytes).strip("\"'\n ")
                        elif stmt.type == "function_definition":
                            method = self._extract_python_method(stmt, source_bytes)
                            methods.append(method)
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

            for child in node.children:
                visit(child)

        visit(root_node)
        return classes

    def _extract_python_method(self, node: Node, source_bytes: bytes) -> MethodMetadata:
        name_node = node.child_by_field_name("name")
        method_name = self._get_node_text(name_node, source_bytes) if name_node else "unknown_func"

        return_type_node = node.child_by_field_name("return_type")
        return_type = self._get_node_text(return_type_node, source_bytes) if return_type_node else "Any"

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

    # ------------------ C# PARSER ------------------
    def _extract_csharp_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        classes = []

        def visit(node: Node):
            if node.type in ("class_declaration", "interface_declaration", "record_declaration"):
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"

                inherits = []
                for child in node.children:
                    if child.type == "base_list":
                        for base_child in child.children:
                            if base_child.type not in (":", ","):
                                inherits.append(self._get_node_text(base_child, source_bytes))

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

    # ------------------ JAVA PARSER ------------------
    def _extract_java_classes(self, root_node: Node, source_bytes: bytes, file_path: str) -> List[ClassMetadata]:
        classes = []

        def visit(node: Node):
            if node.type in ("class_declaration", "interface_declaration", "record_declaration"):
                name_node = node.child_by_field_name("name")
                class_name = self._get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"

                inherits = []
                for child in node.children:
                    if child.type in ("superclass", "super_interfaces", "extends_interfaces"):
                        for sub in child.children:
                            if sub.type not in ("extends", "implements", ","):
                                inherits.append(self._get_node_text(sub, source_bytes))

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
