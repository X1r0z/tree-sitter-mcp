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

    def to_dict(self, include_file: bool = True) -> dict:
        result = {
            "name": self.name,
            "start_line": self.location.start_line,
            "end_line": self.location.end_line,
            "methods": self.methods,
        }
        if include_file:
            result["file"] = self.location.file
        return result


@dataclass
class CallInfo:
    caller: str | None = None
    callee: str
    location: Location
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
                functions.append(
                    FunctionInfo(
                        name=name,
                        location=self._node_location(func_node),
                        body=self._node_text(func_node),
                        node=func_node,
                    )
                )

        return functions

    def get_function_by_name(self, name: str) -> FunctionInfo | None:
        """Get a specific function by name."""
        for func in self.get_functions():
            if func.name == name:
                return func
        return None

    def get_function_variables(self, function_name: str) -> list[VariableInfo]:
        """Get all variables declared within a specific function."""
        all_vars = self.get_variables()
        return [v for v in all_vars if v.scope == function_name]

    def get_function_strings(self, function_name: str) -> list[StringLiteral]:
        """Get all string literals within a specific function."""
        func = self.get_function_by_name(function_name)
        if not func or not func.node:
            return []

        all_strings = self.get_strings()
        return [
            s
            for s in all_strings
            if (func.location.start_line <= s.location.start_line <= func.location.end_line)
        ]

    def get_function_body(self, function_name: str) -> str | None:
        """Get the source code body of a specific function."""
        func = self.get_function_by_name(function_name)
        if func:
            return func.body
        return None

    def get_function_callees(self, function_name: str) -> list[dict]:
        """Get all functions/methods called by a specific function."""
        calls = [c for c in self.get_calls() if c.caller == function_name]
        callees: list[dict] = []
        for call in calls:
            callee = call.callee
            if call.object_name:
                callee = f"{call.object_name}.{callee}"
            entry = {"callee": callee, "line": call.location.start_line}
            if not any(e["callee"] == callee for e in callees):
                callees.append(entry)
        return callees

    def get_function_callers(self, function_name: str) -> list[dict]:
        """Get all functions that call a specific function."""
        all_calls = self.get_calls()
        callers: list[dict] = []
        for call in all_calls:
            caller = call.caller or "<module>"
            if call.callee == function_name:
                entry = {"caller": caller, "line": call.location.start_line}
                if not any(e["caller"] == caller for e in callers):
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
                classes.append(
                    ClassInfo(
                        name=name,
                        location=self._node_location(class_node),
                        methods=methods,
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
