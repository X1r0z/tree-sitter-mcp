# AGENTS.md

## Commands
- Install: `uv pip install -e .` or `uv pip install -e ".[dev]"` (with dev deps)
- Run MCP server: `uv run tree-sitter-mcp`
- Run CLI tool: `uv run tree-sitter-analyzer <command> <path> [options]`
- Lint: `uv run ruff check src/`
- Format: `uv run ruff format src/`

## Architecture
- **tree_sitter_mcp/** - FastMCP server exposing AST analysis as MCP tools
  - `server.py` - @mcp.tool decorated functions (get_functions, get_classes, etc.)
  - `analyzer.py` - CodeAnalyzer: single-file AST parsing, call graphs, inheritance
  - `project.py` - ProjectAnalyzer: multi-file/glob/directory analysis
  - `languages.py` - Language configs: parsers, queries, extension mapping
- **tree_sitter_analyzer/** - CLI wrapper around CodeAnalyzer/ProjectAnalyzer
- Supported: Python, JavaScript/TypeScript, Java, Go
- Path types: glob (**/*.py), directory (recursive)

## Code Style
- Python 3.10+, `from __future__ import annotations` at top of every file
- Dataclasses for data structures (Location, FunctionInfo, ClassInfo, FieldInfo, etc.)
- Type hints: `str | None` not `Optional[str]`
- Tool/CLI functions return `dict` with results or `{"error": str(e)}` on exception
- Ruff: line-length=100, rules E, F, W, I, UP, B, C4, SIM
