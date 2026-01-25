"""Core code analysis functionality using tree-sitter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter

from .languages import detect_language, get_language, get_language_info, get_parser


@dataclass
class Location:
    file: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass
class FunctionInfo:
    name: str
    location: Location
    parameters: str = ""
    body: str = ""
    is_method: bool = False
    class_name: str | None = None
    node: tree_sitter.Node | None = None

    def to_dict(self, include_body: bool = True, include_file: bool = True) -> dict:
        result = {
            "name": self.name,
            "start_line": self.location.start_line,
            "end_line": self.location.end_line,
        }
        if include_file:
            result["file"] = self.location.file
        if self.is_method:
            result["is_method"] = True
        if self.class_name:
            result["class_name"] = self.class_name
        if include_body and self.body:
            result["body"] = self.body
        return result


@dataclass
class ClassInfo:
    name: str
    location: Location
    methods: list[str] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)
    super_classes: list[str] = field(default_factory=list)

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "name": self.name,
            "start_line": self.location.start_line,
            "end_line": self.location.end_line,
            "methods": self.methods,
            "fields": self.fields,
        }
        if include_file:
            result["file"] = self.location.file
        return result


@dataclass
class CallInfo:
    callee: str
    location: Location
    caller: str | None = None
    object_name: str | None = None
    is_method_call: bool = False

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "caller": self.caller,
            "callee": self.callee,
            "line": self.location.start_line,
        }
        if include_file:
            result["file"] = self.location.file
        if self.object_name:
            result["object"] = self.object_name
        if self.is_method_call:
            result["is_method_call"] = True
        return result


@dataclass
class VariableInfo:
    name: str
    location: Location
    scope: str | None = None

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "name": self.name,
            "line": self.location.start_line,
            "scope": self.scope,
        }
        if include_file:
            result["file"] = self.location.file
        return result


@dataclass
class ImportInfo:
    module: str
    location: Location

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "module": self.module,
            "line": self.location.start_line,
        }
        if include_file:
            result["file"] = self.location.file
        return result


@dataclass
class StringLiteral:
    value: str
    location: Location

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "value": self.value,
            "line": self.location.start_line,
        }
        if include_file:
            result["file"] = self.location.file
        return result


@dataclass
class FieldInfo:
    name: str
    location: Location
    field_type: str | None = None
    class_name: str | None = None

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "name": self.name,
            "line": self.location.start_line,
        }
        if include_file:
            result["file"] = self.location.file
        if self.field_type:
            result["type"] = self.field_type
        if self.class_name:
            result["class_name"] = self.class_name
        return result


class CodeAnalyzer:
    """Analyzes source code using tree-sitter."""

    def __init__(self, file_path: str | None = None, language: str | None = None):
        self.file_path = file_path
        self._language = language
        self._source: bytes | None = None
        self._tree: tree_sitter.Tree | None = None
        self._parser: tree_sitter.Parser | None = None

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self._source = path.read_bytes()
        if not self._language:
            self._language = detect_language(file_path)

        if not self._language:
            raise ValueError(f"Could not detect language for: {file_path}")

        self._parser = get_parser(self._language)
        if not self._parser:
            raise ValueError(f"Unsupported language: {self._language}")

        self._tree = self._parser.parse(self._source)

    def _node_location(self, node: tree_sitter.Node) -> Location:
        return Location(
            file=self.file_path or "<string>",
            start_line=node.start_point.row + 1,
            end_line=node.end_point.row + 1,
        )

    def _node_text(self, node: tree_sitter.Node) -> str:
        if self._source is None:
            return ""
        return self._source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    def _run_query(self, query_str: str) -> dict[str, list[tree_sitter.Node]]:
        if not self._tree or not self._language:
            return {}

        lang = get_language(self._language)
        if not lang:
            return {}

        try:
            query = tree_sitter.Query(lang, query_str)
            cursor = tree_sitter.QueryCursor(query)
            return cursor.captures(self._tree.root_node)
        except Exception:
            return {}

    def _find_enclosing_function(self, node: tree_sitter.Node) -> str | None:
        current = node.parent
        func_types = {
            "function_definition",
            "async_function_definition",
            "function_declaration",
            "method_definition",
            "arrow_function",
            "method_declaration",
            "constructor_declaration",
        }
        while current:
            if current.type in func_types:
                for child in current.children:
                    if child.type in ("identifier", "property_identifier", "field_identifier"):
                        return self._node_text(child)
                    if hasattr(child, "field_name") and child.type == "name":
                        return self._node_text(child)
            current = current.parent
        return None

    def _find_enclosing_class(self, node: tree_sitter.Node) -> str | None:
        """Find the name of the class that encloses this node."""
        if node.type == "method_declaration":
            for child in node.children:
                if child.type == "parameter_list":
                    for param in child.children:
                        if param.type == "parameter_declaration":
                            for p in param.children:
                                if p.type == "pointer_type":
                                    for pt in p.children:
                                        if pt.type == "type_identifier":
                                            return self._node_text(pt)
                                if p.type == "type_identifier":
                                    return self._node_text(p)
                    break

        class_types = {
            "class_definition",
            "class_declaration",
            "class_body",
            "interface_declaration",
        }
        current = node.parent
        while current:
            if current.type in class_types:
                for child in current.children:
                    if child.type in ("identifier", "type_identifier", "name"):
                        return self._node_text(child)
            current = current.parent
        return None

    def get_functions(self) -> list[FunctionInfo]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.function_query)
        func_nodes = captures.get("function", [])
        name_nodes = captures.get("name", [])

        functions = []
        for func_node in func_nodes:
            name = ""
            for name_node in name_nodes:
                if (
                    func_node.start_byte <= name_node.start_byte
                    and name_node.end_byte <= func_node.end_byte
                ):
                    name = self._node_text(name_node)
                    break
            if name:
                class_name = self._find_enclosing_class(func_node)
                functions.append(
                    FunctionInfo(
                        name=name,
                        location=self._node_location(func_node),
                        body=self._node_text(func_node),
                        node=func_node,
                        is_method=class_name is not None,
                        class_name=class_name,
                    )
                )

        return functions

    def get_function_by_name(self, name: str, class_name: str | None = None) -> FunctionInfo | None:
        """Get a specific function by name, optionally filtering by class_name."""
        for func in self.get_functions():
            if func.name == name and (class_name is None or func.class_name == class_name):
                return func
        return None

    def get_all_functions_by_name(
        self, name: str, class_name: str | None = None
    ) -> list[FunctionInfo]:
        """Get all functions with a given name, optionally filtering by class_name."""
        results = []
        for func in self.get_functions():
            if func.name == name and (class_name is None or func.class_name == class_name):
                results.append(func)
        return results

    def get_function_variables(
        self, function_name: str, class_name: str | None = None
    ) -> list[VariableInfo]:
        """Get all variables declared within a specific function."""
        funcs = self.get_all_functions_by_name(function_name, class_name)
        all_vars = self.get_variables()
        results = []
        for func in funcs:
            results.extend(
                v
                for v in all_vars
                if func.location.start_line <= v.location.start_line <= func.location.end_line
            )
        return results

    def get_function_strings(
        self, function_name: str, class_name: str | None = None
    ) -> list[StringLiteral]:
        """Get all string literals within a specific function."""
        funcs = self.get_all_functions_by_name(function_name, class_name)
        all_strings = self.get_strings()
        results = []
        for func in funcs:
            if func.node:
                results.extend(
                    s
                    for s in all_strings
                    if func.location.start_line <= s.location.start_line <= func.location.end_line
                )
        return results

    def get_function_body(self, function_name: str) -> str | None:
        """Get the source code body of a specific function."""
        func = self.get_function_by_name(function_name)
        if func:
            return func.body
        return None

    def get_function_callees(self, function_name: str, class_name: str | None = None) -> list[dict]:
        """Get all functions/methods called by a specific function."""
        funcs = self.get_all_functions_by_name(function_name, class_name)
        all_calls = self.get_calls()
        callees: list[dict] = []
        for func in funcs:
            for call in all_calls:
                if func.location.start_line <= call.location.start_line <= func.location.end_line:
                    callee = call.callee
                    if call.object_name:
                        callee = f"{call.object_name}.{callee}"
                    entry = {
                        "callee": callee,
                        "line": call.location.start_line,
                        "class_name": func.class_name,
                    }
                    if not any(
                        e["callee"] == callee and e["class_name"] == func.class_name
                        for e in callees
                    ):
                        callees.append(entry)
        return callees

    def get_function_callers(self, function_name: str, class_name: str | None = None) -> list[dict]:
        """Get all functions that call a specific function."""
        funcs = self.get_all_functions_by_name(function_name, class_name)
        all_calls = self.get_calls()
        callers: list[dict] = []
        for func in funcs:
            for call in all_calls:
                caller = call.caller or "<module>"
                if call.callee == function_name:
                    entry = {
                        "caller": caller,
                        "line": call.location.start_line,
                        "target_class": func.class_name,
                    }
                    if not any(
                        e["caller"] == caller and e["target_class"] == func.class_name
                        for e in callers
                    ):
                        callers.append(entry)
        return callers

    def get_classes(self) -> list[ClassInfo]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.class_query)
        class_nodes = captures.get("class", [])
        name_nodes = captures.get("name", [])

        classes = []
        for class_node in class_nodes:
            name = ""
            for name_node in name_nodes:
                if (
                    class_node.start_byte <= name_node.start_byte
                    and name_node.end_byte <= class_node.end_byte
                ):
                    name = self._node_text(name_node)
                    break
            if name:
                methods = self._extract_methods_from_class(class_node)
                fields = self._extract_fields_from_class(class_node)
                super_classes = self._extract_super_classes_from_class(class_node)
                classes.append(
                    ClassInfo(
                        name=name,
                        location=self._node_location(class_node),
                        methods=methods,
                        fields=fields,
                        super_classes=super_classes,
                    )
                )

        return classes

    def _extract_methods_from_class(self, class_node: tree_sitter.Node) -> list[str]:
        """Extract method names from a class node."""
        methods = []
        method_types = {
            "function_definition",
            "method_definition",
            "method_declaration",
            "constructor_declaration",
        }

        def walk(node: tree_sitter.Node):
            if node.type in method_types:
                for child in node.children:
                    if child.type in ("identifier", "property_identifier", "field_identifier"):
                        methods.append(self._node_text(child))
                        break
                    if child.type == "name":
                        methods.append(self._node_text(child))
                        break
                return
            for child in node.children:
                walk(child)

        walk(class_node)
        return methods

    def _extract_fields_from_class(self, class_node: tree_sitter.Node) -> list[str]:
        """Extract field names from a class node."""
        fields = []
        field_types = {
            "field_definition",
            "field_declaration",
        }
        method_types = {
            "function_definition",
            "method_definition",
            "method_declaration",
            "constructor_declaration",
        }

        def walk(node: tree_sitter.Node):
            if node.type in method_types:
                return
            if node.type in field_types:
                for child in node.children:
                    if child.type in ("identifier", "property_identifier", "field_identifier"):
                        fields.append(self._node_text(child))
                        break
                    if child.type == "variable_declarator":
                        for sub in child.children:
                            if sub.type == "identifier":
                                fields.append(self._node_text(sub))
                                break
                        break
                return
            if self._language == "python" and node.type == "expression_statement":
                for child in node.children:
                    if child.type == "assignment":
                        for sub in child.children:
                            if sub.type == "identifier":
                                text = self._node_text(sub)
                                if not text.startswith("self."):
                                    fields.append(text)
                                break
                        break
                return
            for child in node.children:
                walk(child)

        walk(class_node)
        return fields

    def _extract_super_classes_from_class(self, class_node: tree_sitter.Node) -> list[str]:
        """Extract parent class names from a class node."""
        super_classes = []

        if self._language == "python":
            for child in class_node.children:
                if child.type == "argument_list":
                    for arg in child.children:
                        if arg.type == "identifier" or arg.type == "attribute":
                            super_classes.append(self._node_text(arg))

        elif self._language == "javascript":
            for child in class_node.children:
                if child.type == "class_heritage":
                    for sub in child.children:
                        if sub.type == "identifier" or sub.type == "member_expression":
                            super_classes.append(self._node_text(sub))

        elif self._language == "java":
            for child in class_node.children:
                if child.type == "superclass":
                    for sub in child.children:
                        if sub.type == "type_identifier":
                            super_classes.append(self._node_text(sub))
                        elif sub.type == "generic_type":
                            for g in sub.children:
                                if g.type == "type_identifier":
                                    super_classes.append(self._node_text(g))
                                    break
                elif child.type == "super_interfaces":
                    for sub in child.children:
                        if sub.type == "type_list":
                            for t in sub.children:
                                if t.type == "type_identifier":
                                    super_classes.append(self._node_text(t))
                                elif t.type == "generic_type":
                                    for g in t.children:
                                        if g.type == "type_identifier":
                                            super_classes.append(self._node_text(g))
                                            break

        elif self._language == "go":
            for child in class_node.children:
                if child.type == "type_spec":
                    for sub in child.children:
                        if sub.type == "struct_type":
                            for field in sub.children:
                                if field.type == "field_declaration_list":
                                    for fd in field.children:
                                        if fd.type == "field_declaration":
                                            has_name = any(
                                                c.type == "field_identifier" for c in fd.children
                                            )
                                            if not has_name:
                                                for c in fd.children:
                                                    if c.type == "type_identifier":
                                                        super_classes.append(self._node_text(c))
                                                    elif c.type == "pointer_type":
                                                        for pt in c.children:
                                                            if pt.type == "type_identifier":
                                                                super_classes.append(
                                                                    self._node_text(pt)
                                                                )

        return super_classes

    def get_fields(self, class_name: str | None = None) -> list[FieldInfo]:
        """Get all fields, optionally filtered by class name."""
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        classes = self.get_classes()
        fields: list[FieldInfo] = []

        for cls in classes:
            if class_name and cls.name != class_name:
                continue
            field_infos = self._get_fields_from_class_node(cls.name)
            fields.extend(field_infos)

        return fields

    def _get_fields_from_class_node(self, class_name: str) -> list[FieldInfo]:
        """Get detailed field info for a specific class."""
        if not self._language or not self._tree:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.class_query)
        class_nodes = captures.get("class", [])
        name_nodes = captures.get("name", [])

        target_class_node = None
        for class_node in class_nodes:
            for name_node in name_nodes:
                if (
                    class_node.start_byte <= name_node.start_byte
                    and name_node.end_byte <= class_node.end_byte
                    and self._node_text(name_node) == class_name
                ):
                    target_class_node = class_node
                    break
            if target_class_node:
                break

        if not target_class_node:
            return []

        return self._extract_field_infos(target_class_node, class_name)

    def _extract_field_infos(
        self, class_node: tree_sitter.Node, class_name: str
    ) -> list[FieldInfo]:
        """Extract detailed field information from a class node."""
        fields: list[FieldInfo] = []
        field_types = {"field_definition", "field_declaration"}
        method_types = {
            "function_definition",
            "method_definition",
            "method_declaration",
            "constructor_declaration",
        }

        def walk(node: tree_sitter.Node):
            if node.type in method_types:
                return
            if node.type in field_types:
                name = ""
                field_type = None
                for child in node.children:
                    if child.type in ("identifier", "property_identifier", "field_identifier"):
                        name = self._node_text(child)
                    elif child.type == "variable_declarator":
                        for sub in child.children:
                            if sub.type == "identifier":
                                name = self._node_text(sub)
                                break
                    elif child.type in (
                        "type_annotation",
                        "type",
                        "type_identifier",
                        "integral_type",
                        "floating_point_type",
                        "boolean_type",
                        "generic_type",
                        "array_type",
                        "scoped_type_identifier",
                    ):
                        field_type = self._node_text(child)
                if name:
                    fields.append(
                        FieldInfo(
                            name=name,
                            location=self._node_location(node),
                            field_type=field_type,
                            class_name=class_name,
                        )
                    )
                return
            if self._language == "python" and node.type == "expression_statement":
                for child in node.children:
                    if child.type == "assignment":
                        name = ""
                        field_type = None
                        for sub in child.children:
                            if sub.type == "identifier":
                                text = self._node_text(sub)
                                if not text.startswith("self."):
                                    name = text
                            elif sub.type == "type":
                                field_type = self._node_text(sub)
                        if name:
                            fields.append(
                                FieldInfo(
                                    name=name,
                                    location=self._node_location(child),
                                    field_type=field_type,
                                    class_name=class_name,
                                )
                            )
                        break
                return
            for child in node.children:
                walk(child)

        walk(class_node)
        return fields

    def get_calls(self) -> list[CallInfo]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.call_query)
        call_nodes = captures.get("call", [])
        callee_nodes = captures.get("callee", [])
        method_nodes = captures.get("method", [])
        object_nodes = captures.get("object", [])

        # Build index by start_byte for O(1) lookup instead of O(n) scan
        callee_by_start = {n.start_byte: n for n in callee_nodes}
        method_by_start = {n.start_byte: n for n in method_nodes}
        object_by_start = {n.start_byte: n for n in object_nodes}

        calls = []
        for call_node in call_nodes:
            caller = self._find_enclosing_function(call_node)
            callee = ""
            is_method = False
            obj_name = None

            # Find matching captures within call_node's byte range
            call_start, call_end = call_node.start_byte, call_node.end_byte

            for start_byte, node in callee_by_start.items():
                if call_start <= start_byte and node.end_byte <= call_end:
                    callee = self._node_text(node)
                    break

            for start_byte, node in method_by_start.items():
                if call_start <= start_byte and node.end_byte <= call_end:
                    callee = self._node_text(node)
                    is_method = True
                    break

            for start_byte, node in object_by_start.items():
                if call_start <= start_byte and node.end_byte <= call_end:
                    obj_name = self._node_text(node)
                    break

            if callee:
                calls.append(
                    CallInfo(
                        callee=callee,
                        location=self._node_location(call_node),
                        caller=caller,
                        is_method_call=is_method,
                        object_name=obj_name,
                    )
                )

        return calls

    def get_imports(self) -> list[ImportInfo]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.import_query)
        module_nodes = captures.get("module", [])
        import_nodes = captures.get("import", [])

        imports = []
        for node in module_nodes:
            text = self._node_text(node).strip("\"'")
            imports.append(ImportInfo(module=text, location=self._node_location(node)))

        if not module_nodes:
            for node in import_nodes:
                text = self._node_text(node)
                imports.append(ImportInfo(module=text, location=self._node_location(node)))

        return imports

    def get_variables(self) -> list[VariableInfo]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.variable_query)
        name_nodes = captures.get("name", [])

        variables = []
        for node in name_nodes:
            scope = self._find_enclosing_function(node)
            variables.append(
                VariableInfo(
                    name=self._node_text(node),
                    location=self._node_location(node),
                    scope=scope,
                )
            )

        return variables

    def get_strings(self) -> list[StringLiteral]:
        if not self._language:
            return []

        lang_info = get_language_info(self._language)
        if not lang_info:
            return []

        captures = self._run_query(lang_info.string_query)
        string_nodes = captures.get("string", [])

        strings = []
        for node in string_nodes:
            text = self._node_text(node)
            strings.append(StringLiteral(value=text, location=self._node_location(node)))

        return strings

    def find_symbols(self, name: str) -> list[dict]:
        if not self._tree or not self._source:
            return []

        refs = []

        def walk(node: tree_sitter.Node):
            if node.is_named and self._node_text(node) == name:
                refs.append(
                    {
                        "type": node.type,
                        "location": self._node_location(node).to_dict(),
                        "context": self._node_text(node.parent) if node.parent else "",
                    }
                )
            for child in node.children:
                walk(child)

        walk(self._tree.root_node)
        return refs

    def get_reverse_call_graph(self) -> dict[str, list[dict]]:
        calls = self.get_calls()
        graph: dict[str, list[dict]] = {}

        for call in calls:
            caller = call.caller or "<module>"
            callee = call.callee
            if callee not in graph:
                graph[callee] = []
            entry = {"caller": caller, "line": call.location.start_line}
            if not any(e["caller"] == caller for e in graph[callee]):
                graph[callee].append(entry)

        return graph

    def get_class_by_name(self, class_name: str) -> ClassInfo | None:
        """Get a specific class by name."""
        for cls in self.get_classes():
            if cls.name == class_name:
                return cls
        return None

    def get_super_classes(self, class_name: str) -> list[ClassInfo]:
        """Get all parent classes of a specific class.

        Returns ClassInfo for each parent class that can be found in this file.
        """
        target_class = self.get_class_by_name(class_name)
        if not target_class:
            return []

        all_classes = self.get_classes()
        class_map = {c.name: c for c in all_classes}

        result = []
        for parent_name in target_class.super_classes:
            if parent_name in class_map:
                result.append(class_map[parent_name])
        return result

    def get_sub_classes(self, class_name: str) -> list[ClassInfo]:
        """Get all child classes that inherit from a specific class.

        Returns ClassInfo for each child class found in this file.
        """
        all_classes = self.get_classes()
        result = []
        for cls in all_classes:
            if class_name in cls.super_classes:
                result.append(cls)
        return result
