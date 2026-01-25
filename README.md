# tree-sitter-mcp

A MCP server for code analysis using [tree-sitter](https://tree-sitter.github.io/tree-sitter/). Provides AST-based code structure extraction, call graph analysis, and symbol reference tracking.

## Features

- **Function/Class/Field Extraction** - Extract all function/method and class/struct/interface/field definitions
- **Inheritance Analysis** - Extract class inheritance relationships, including parent classes and child classes
- **Call Graph Analysis** - Build call graphs showing caller-callee relationships
- **Import Analysis** - Extract import statements and dependencies
- **Variable Tracking** - Identify variable declarations with scope information
- **Symbol Reference Tracking** - Find all references to a specific symbol
- **Multi-Path Support** - Analyze single files, glob patterns, or entire directories

## Supported Languages

| Language | Extensions |
|----------|------------|
| Python | `.py`, `.pyw`, `.pyi` |
| JavaScript/TypeScript | `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.tsx` |
| Java | `.java` |
| Go | `.go` |

## Installation

```bash
# Using uv (recommended)
uv tool install git+https://github.com/X1r0z/tree-sitter-mcp

# Using pip
pip install git+https://github.com/X1r0z/tree-sitter-mcp
```

## Usage

Run the server using `tree-sitter-mcp` directly:

```json
{
  "mcpServers": {
    "tree-sitter": {
      "command": "tree-sitter-mcp"
    }
  }
}
```

Or run the server using `uv` from the source directory:

```json
{
  "mcpServers": {
    "tree-sitter": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/tree-sitter-mcp",
        "tree-sitter-mcp"
      ]
    }
  }
}
```

## Tools

### Code Structure

| Tool | Description |
|------|-------------|
| `get_functions` | Extract all function/method definitions |
| `get_classes` | Extract all class/struct/interface definitions |
| `get_fields` | Extract all field definitions |
| `get_imports` | Extract all import statements |
| `get_variables` | Extract all variable declarations |

### Inheritance Analysis

| Tool | Description |
|------|-------------|
| `get_super_classes` | Get all parent classes of a specific class |
| `get_sub_classes` | Get all child classes that inherit from a specific class |

### Call Graph Analysis

| Tool | Description |
|------|-------------|
| `get_callers` | Find functions that call a specific function |
| `get_callees` | Find functions called by a specific function |

### Function-Level Analysis

| Tool | Description |
|------|-------------|
| `get_function_definition` | Get the complete source code of a function |
| `get_function_variables` | Get all variables declared in a function |
| `get_function_strings` | Get all string literals in a function |

### Symbol Reference Tracking

| Tool | Description |
|------|-------------|
| `find_symbols` | Find all references to a specific symbol |

## Path Types

All tools accept a `path` parameter that supports:

- **Single file**: `/path/to/file.py`
- **Glob pattern**: `**/*.py`, `src/**/*.js`
- **Directory**: `/path/to/project` (searches all supported files recursively)

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

## License

MIT
