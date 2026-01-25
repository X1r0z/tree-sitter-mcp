"""Project-level code analysis with directory and glob support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer import (
    CallInfo,
    ClassInfo,
    CodeAnalyzer,
    FieldInfo,
    FunctionInfo,
    ImportInfo,
    VariableInfo,
)
from .languages import FILE_EXTENSION_MAP


@dataclass
class PathType:
    FILE = "file"
    GLOB = "glob"
    DIRECTORY = "directory"


def detect_path_type(path: str) -> str:
    """Detect if path is a file, glob pattern, or directory."""
    if any(c in path for c in ["*", "?", "[", "]"]):
        return PathType.GLOB
    p = Path(path)
    if p.is_dir():
        return PathType.DIRECTORY
    return PathType.FILE


def get_supported_extensions() -> set[str]:
    """Get all supported file extensions."""
    return set(FILE_EXTENSION_MAP.keys())


def find_files(path: str) -> list[str]:
    """Find all supported source files based on path type.

    Args:
        path: File path, glob pattern, or directory path

    Returns:
        List of absolute file paths
    """
    path_type = detect_path_type(path)
    extensions = get_supported_extensions()

    if path_type == PathType.FILE:
        p = Path(path)
        if p.exists() and p.is_file() and p.suffix in extensions:
            return [str(p.resolve())]
        return []

    if path_type == PathType.GLOB:
        if path.startswith("/"):
            results = list(Path("/").glob(path.lstrip("/")))
        else:
            results = list(Path(".").glob(path))

        files = []
        for p in results:
            if p.is_file() and p.suffix in extensions:
                files.append(str(p.resolve()))
        return sorted(files)

    if path_type == PathType.DIRECTORY:
        directory = Path(path)
        files = []
        for ext in extensions:
            files.extend(str(p.resolve()) for p in directory.rglob(f"*{ext}") if p.is_file())
        return sorted(set(files))

    return []


class ProjectAnalyzer:
    """Analyzes multiple source files in a project."""

    def __init__(self, path: str):
        """Initialize with a file path, glob pattern, or directory.

        Args:
            path: File path, glob pattern (e.g., "**/*.py"), or directory path
        """
        self.path = path
        self.path_type = detect_path_type(path)
        self.files = find_files(path)
        self._analyzers: dict[str, CodeAnalyzer] = {}

    def _get_analyzer(self, file_path: str) -> CodeAnalyzer | None:
        """Get or create an analyzer for a file."""
        if file_path not in self._analyzers:
            try:
                self._analyzers[file_path] = CodeAnalyzer(file_path)
            except Exception:
                return None
        return self._analyzers[file_path]

    def get_functions(self) -> list[FunctionInfo]:
        """Get all functions from all files."""
        functions = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                functions.extend(analyzer.get_functions())
        return functions

    def get_classes(self) -> list[ClassInfo]:
        """Get all classes from all files."""
        classes = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                classes.extend(analyzer.get_classes())
        return classes

    def get_fields(self, class_name: str | None = None) -> list[FieldInfo]:
        """Get all fields from all files, optionally filtered by class name."""
        fields = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                fields.extend(analyzer.get_fields(class_name))
        return fields

    def get_calls(self) -> list[CallInfo]:
        """Get all function calls from all files."""
        calls = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                calls.extend(analyzer.get_calls())
        return calls

    def get_imports(self) -> list[ImportInfo]:
        """Get all imports from all files."""
        imports = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                imports.extend(analyzer.get_imports())
        return imports

    def get_variables(self) -> list[VariableInfo]:
        """Get all variables from all files."""
        variables = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                variables.extend(analyzer.get_variables())
        return variables

    def get_function_by_name(self, name: str, class_name: str | None = None) -> FunctionInfo | None:
        """Find a function by name across all files, optionally filtering by class_name."""
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                func = analyzer.get_function_by_name(name, class_name)
                if func:
                    return func
        return None

    def get_all_functions_by_name(
        self, name: str, class_name: str | None = None
    ) -> list[FunctionInfo]:
        """Find all functions with a given name across all files, optionally filtering by class_name."""
        functions = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                funcs = analyzer.get_all_functions_by_name(name, class_name)
                functions.extend(funcs)
        return functions

    def get_callers(self, function_name: str, class_name: str | None = None) -> list[dict]:
        """Find all callers of a function across all files."""
        callers = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                file_callers = analyzer.get_function_callers(function_name, class_name)
                for caller_info in file_callers:
                    callers.append(
                        {
                            "caller": caller_info["caller"],
                            "line": caller_info["line"],
                            "file": file_path,
                            "target_class": caller_info.get("target_class"),
                        }
                    )
        return sorted(callers, key=lambda x: (x["file"], x["line"]))

    def get_callees(self, function_name: str, class_name: str | None = None) -> list[dict]:
        """Find all functions called by a function across all files."""
        results = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                funcs = analyzer.get_all_functions_by_name(function_name, class_name)
                if funcs:
                    callees = analyzer.get_function_callees(function_name, class_name)
                    for c in callees:
                        results.append(
                            {
                                "callee": c["callee"],
                                "line": c["line"],
                                "file": file_path,
                                "class_name": c.get("class_name"),
                            }
                        )
        return sorted(results, key=lambda x: (x["file"], x["line"]))

    def get_function_variables(
        self, function_name: str, class_name: str | None = None
    ) -> list[dict]:
        """Get all variables in a function across all files."""
        results = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                variables = analyzer.get_function_variables(function_name, class_name)
                for v in variables:
                    results.append(
                        {
                            "name": v.name,
                            "line": v.location.start_line,
                            "file": file_path,
                        }
                    )
        return sorted(results, key=lambda x: (x["file"], x["line"]))

    def get_function_strings(self, function_name: str, class_name: str | None = None) -> list[dict]:
        """Get all strings in a function across all files."""
        results = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                strings = analyzer.get_function_strings(function_name, class_name)
                for s in strings:
                    results.append(
                        {
                            "value": s.value,
                            "line": s.location.start_line,
                            "file": file_path,
                        }
                    )
        return sorted(results, key=lambda x: (x["file"], x["line"]))

    def find_symbols(self, name: str) -> list[dict]:
        """Find all references to an identifier across all files."""
        refs = []
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                file_refs = analyzer.find_symbols(name)
                refs.extend(file_refs)
        return refs

    def get_class_by_name(self, class_name: str) -> ClassInfo | None:
        """Find a class by name across all files."""
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                cls = analyzer.get_class_by_name(class_name)
                if cls:
                    return cls
        return None

    def get_super_classes(self, class_name: str) -> list[ClassInfo]:
        """Get all parent classes of a specific class across all files.

        First finds the target class, then searches for its parent classes.
        """
        target_class = None
        for file_path in self.files:
            analyzer = self._get_analyzer(file_path)
            if analyzer:
                cls = analyzer.get_class_by_name(class_name)
                if cls:
                    target_class = cls
                    break

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
        """Get all child classes that inherit from a specific class across all files."""
        all_classes = self.get_classes()
        result = []
        for cls in all_classes:
            if class_name in cls.super_classes:
                result.append(cls)
        return result
