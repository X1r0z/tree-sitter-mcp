# AGENTS.md

## Commands
- Install: `uv pip install -e .` or `uv pip install -e ".[dev]"` (with dev deps)
- Run server: `uv run tree-sitter-mcp`
- Lint: `uv run ruff check src/`
- Format: `uv run ruff format src/`

## Architecture
- `src/tree_sitter_mcp/server.py` - FastMCP server with tool definitions (@mcp.tool decorators)
- `src/tree_sitter_mcp/analyzer.py` - CodeAnalyzer class: AST parsing, function/class/field extraction, call graphs, inheritance analysis
- `src/tree_sitter_mcp/languages.py` - Language support: parsers, queries, extension mapping
- `src/tree_sitter_mcp/project.py` - ProjectAnalyzer class: multi-file/directory/glob analysis
- Supported languages: Python, JavaScript/TypeScript, Java, Go
- Path types: file (single), glob pattern (**/*.py), directory (recursive search)

## Code Style
- Python 3.10+, use `from __future__ import annotations`
- Use dataclasses for data structures (Location, FunctionInfo, ClassInfo, etc.)
- Ruff for linting (line-length=100, rules: E, F, W, I, UP, B, C4, SIM)
- Tool functions return `dict` with results or `{"error": str(e)}` on exception
- Use type hints (`str | None` syntax, not `Optional[str]`)
