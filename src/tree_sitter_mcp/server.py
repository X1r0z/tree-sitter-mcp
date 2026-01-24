"""Tree-sitter MCP Server for code analysis."""

from __future__ import annotations

from fastmcp import FastMCP

from .analyzer import CodeAnalyzer
from .project import PathType, ProjectAnalyzer, detect_path_type

mcp = FastMCP(
    name="tree-sitter-mcp",
    instructions="""
    Tree-sitter MCP Server for code analysis.
    Provides function/class extraction, call graph analysis, and code structure analysis.
    Supported languages: Python, JavaScript, Java, Go

    Path parameter supports:
    - Single file: /path/to/file.py
    - Glob pattern: **/*.py, src/**/*.js
    - Directory: /path/to/project (searches all supported files recursively)
    """,
)


def _is_single_file(path: str) -> bool:
    """Check if path refers to a single file."""
    return detect_path_type(path) == PathType.FILE


@mcp.tool
def get_functions(path: str) -> dict:
    """Extract all function/method definitions.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            functions = analyzer.get_functions()
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "count": len(functions),
                "functions": [f.to_dict(include_body=False, include_file=False) for f in functions],
            }
        else:
            project = ProjectAnalyzer(path)
            functions = project.get_functions()
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(functions),
                "functions": [f.to_dict(include_body=False, include_file=True) for f in functions],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_classes(path: str) -> dict:
    """Extract all class/struct/interface definitions.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            classes = analyzer.get_classes()
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "count": len(classes),
                "classes": [c.to_dict(include_file=False) for c in classes],
            }
        else:
            project = ProjectAnalyzer(path)
            classes = project.get_classes()
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(classes),
                "classes": [c.to_dict(include_file=True) for c in classes],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_function_calls(path: str) -> dict:
    """Extract all function/method calls.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            calls = analyzer.get_calls()
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "count": len(calls),
                "calls": [c.to_dict(include_file=False) for c in calls],
            }
        else:
            project = ProjectAnalyzer(path)
            calls = project.get_calls()
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(calls),
                "calls": [c.to_dict(include_file=True) for c in calls],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_imports(path: str) -> dict:
    """Extract all import statements.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            imports = analyzer.get_imports()
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "count": len(imports),
                "imports": [i.to_dict(include_file=False) for i in imports],
            }
        else:
            project = ProjectAnalyzer(path)
            imports = project.get_imports()
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(imports),
                "imports": [i.to_dict(include_file=True) for i in imports],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_variables(path: str) -> dict:
    """Extract all variable declarations.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            variables = analyzer.get_variables()
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "count": len(variables),
                "variables": [v.to_dict(include_file=False) for v in variables],
            }
        else:
            project = ProjectAnalyzer(path)
            variables = project.get_variables()
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(variables),
                "variables": [v.to_dict(include_file=True) for v in variables],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_call_graph(path: str) -> dict:
    """Get call graph: which functions call which other functions.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            return {
                "path": path,
                "path_type": "file",
                "language": analyzer._language,
                "call_graph": analyzer.get_call_graph(),
            }
        else:
            project = ProjectAnalyzer(path)
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "call_graph": project.get_call_graph(),
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_callers(path: str, function_name: str) -> dict:
    """Find all functions that call a specific function.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        function_name: Name of the function to find callers for
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            reverse_graph = analyzer.get_reverse_call_graph()
            callers = sorted(reverse_graph.get(function_name, []), key=lambda x: x["line"])
            return {
                "path": path,
                "path_type": "file",
                "function": function_name,
                "callers": callers,
            }
        else:
            project = ProjectAnalyzer(path)
            callers = project.get_callers(function_name)
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "function": function_name,
                "callers": callers,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_callees(path: str, function_name: str) -> dict:
    """Find all functions called by a specific function.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        function_name: Name of the function to find callees for
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            graph = analyzer.get_call_graph()
            callees = sorted(graph.get(function_name, []), key=lambda x: x["line"])
            return {
                "path": path,
                "path_type": "file",
                "function": function_name,
                "callees": callees,
            }
        else:
            project = ProjectAnalyzer(path)
            callees = project.get_callees(function_name)
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "function": function_name,
                "callees": callees,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def find_references(path: str, name: str) -> dict:
    """Find all references to a specific identifier.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        name: Identifier name to search for
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            refs = analyzer.find_references(name)
            return {
                "path": path,
                "path_type": "file",
                "name": name,
                "count": len(refs),
                "references": refs,
            }
        else:
            project = ProjectAnalyzer(path)
            refs = project.find_references(name)
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "name": name,
                "count": len(refs),
                "references": refs,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_function_definition(path: str, function_name: str) -> dict:
    """Get the complete definition (source code) of a specific function.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        function_name: Name of the function to retrieve
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            func = analyzer.get_function_by_name(function_name)
            if not func:
                return {"error": f"Function '{function_name}' not found"}
            return {
                "path": path,
                "path_type": "file",
                "function": func.to_dict(),
            }
        else:
            project = ProjectAnalyzer(path)
            functions = project.get_all_functions_by_name(function_name)
            if not functions:
                return {"error": f"Function '{function_name}' not found"}
            return {
                "path": path,
                "path_type": project.path_type,
                "files_searched": len(project.files),
                "count": len(functions),
                "functions": [f.to_dict() for f in functions],
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_function_variables(path: str, function_name: str) -> dict:
    """Get all variables declared within a specific function.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        function_name: Name of the function to analyze
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            variables = analyzer.get_function_variables(function_name)
            variables = sorted(variables, key=lambda v: v.location.start_line)
            return {
                "path": path,
                "path_type": "file",
                "function": function_name,
                "count": len(variables),
                "variables": [v.to_dict() for v in variables],
            }
        else:
            project = ProjectAnalyzer(path)
            for file_path in project.files:
                analyzer = project._get_analyzer(file_path)
                if analyzer:
                    func = analyzer.get_function_by_name(function_name)
                    if func:
                        variables = analyzer.get_function_variables(function_name)
                        variables = sorted(variables, key=lambda v: v.location.start_line)
                        return {
                            "path": path,
                            "path_type": project.path_type,
                            "file": file_path,
                            "function": function_name,
                            "count": len(variables),
                            "variables": [v.to_dict() for v in variables],
                        }
            return {"error": f"Function '{function_name}' not found"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_function_strings(path: str, function_name: str) -> dict:
    """Get all string literals within a specific function.

    Args:
        path: File path, glob pattern (e.g., **/*.py), or directory path
        function_name: Name of the function to analyze
    """
    try:
        if _is_single_file(path):
            analyzer = CodeAnalyzer(path)
            strings = analyzer.get_function_strings(function_name)
            strings = sorted(strings, key=lambda s: s.location.start_line)
            return {
                "path": path,
                "path_type": "file",
                "function": function_name,
                "count": len(strings),
                "strings": [s.to_dict() for s in strings],
            }
        else:
            project = ProjectAnalyzer(path)
            for file_path in project.files:
                analyzer = project._get_analyzer(file_path)
                if analyzer:
                    func = analyzer.get_function_by_name(function_name)
                    if func:
                        strings = analyzer.get_function_strings(function_name)
                        strings = sorted(strings, key=lambda s: s.location.start_line)
                        return {
                            "path": path,
                            "path_type": project.path_type,
                            "file": file_path,
                            "function": function_name,
                            "count": len(strings),
                            "strings": [s.to_dict() for s in strings],
                        }
            return {"error": f"Function '{function_name}' not found"}
    except Exception as e:
        return {"error": str(e)}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
