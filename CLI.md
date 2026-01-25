# Tree-sitter Analyzer CLI

Command-line interface for analyzing code using tree-sitter AST parsing.

## Installation

```bash
# Using uv (recommended)
uv tool install git+https://github.com/X1r0z/tree-sitter-mcp

# Using pip
pip install git+https://github.com/X1r0z/tree-sitter-mcp
```

After installation, the `tree-sitter-analyzer` command will be available.

## Usage

```bash
tree-sitter-analyzer <command> <path> [options]
```

### Path Types

All commands accept a `path` argument that supports:

- **Single file**: `/path/to/file.py`
- **Glob pattern**: `**/*.py`, `src/**/*.js`
- **Directory**: `/path/to/project` (searches all supported files recursively)

### Supported Languages

| Language | Extensions |
|----------|------------|
| Python | `.py`, `.pyw`, `.pyi` |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| Java | `.java` |
| Go | `.go` |

### Output Formats

By default, output is in human-readable format. Use `--json` flag for JSON output.

```bash
# Human-readable output
tree-sitter-analyzer functions ./src/

# JSON output
tree-sitter-analyzer functions ./src/ --json
```

## Commands

### Code Structure Commands

#### `functions` - Extract Function Definitions

Extract all function/method definitions from source code.

```bash
tree-sitter-analyzer functions <path> [-q QUERY] [--body] [--json]
```

| Option | Description |
|--------|-------------|
| `-q, --query` | Filter by function name (fuzzy match) |
| `--body` | Include function body in output |
| `--json` | Output in JSON format |

**Examples:**

```bash
# List all functions in a file
tree-sitter-analyzer functions ./src/main.py

# Filter functions containing "get"
tree-sitter-analyzer functions ./src/ -q get

# Include function bodies
tree-sitter-analyzer functions ./src/main.py --body

# Output as JSON
tree-sitter-analyzer functions ./src/ --json
```

#### `classes` - Extract Class Definitions

Extract all class/struct/interface definitions.

```bash
tree-sitter-analyzer classes <path> [-q QUERY] [--json]
```

| Option | Description |
|--------|-------------|
| `-q, --query` | Filter by class name (fuzzy match) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# List all classes in a directory
tree-sitter-analyzer classes ./src/

# Filter classes containing "Handler"
tree-sitter-analyzer classes ./src/ -q Handler
```

#### `fields` - Get Class Fields

Get all fields of a specific class.

```bash
tree-sitter-analyzer fields <path> -c CLASS_NAME [--json]
```

| Option | Description |
|--------|-------------|
| `-c, --class-name` | Class name to get fields for (required) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Get fields of a class
tree-sitter-analyzer fields ./src/models.py -c User

# Search across a project
tree-sitter-analyzer fields ./src/ -c DatabaseConfig
```

#### `imports` - Extract Import Statements

Extract all import statements from source code.

```bash
tree-sitter-analyzer imports <path> [-q QUERY] [--json]
```

| Option | Description |
|--------|-------------|
| `-q, --query` | Filter by module name (fuzzy match) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# List all imports
tree-sitter-analyzer imports ./src/main.py

# Find imports containing "json"
tree-sitter-analyzer imports ./src/ -q json
```

#### `variables` - Extract Variable Declarations

Extract all variable declarations with scope information.

```bash
tree-sitter-analyzer variables <path> [-q QUERY] [--json]
```

| Option | Description |
|--------|-------------|
| `-q, --query` | Filter by variable name (fuzzy match) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# List all variables
tree-sitter-analyzer variables ./src/config.py

# Find variables containing "config"
tree-sitter-analyzer variables ./src/ -q config
```

### Inheritance Analysis Commands

#### `super-classes` - Get Parent Classes

Get all parent classes (superclasses) of a specific class.

```bash
tree-sitter-analyzer super-classes <path> -c CLASS_NAME [--json]
```

| Option | Description |
|--------|-------------|
| `-c, --class-name` | Class name to find parents for (required) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Find parent classes
tree-sitter-analyzer super-classes ./src/models.py -c AdminUser
```

#### `sub-classes` - Get Child Classes

Get all child classes (subclasses) that inherit from a specific class.

```bash
tree-sitter-analyzer sub-classes <path> -c CLASS_NAME [--json]
```

| Option | Description |
|--------|-------------|
| `-c, --class-name` | Class name to find children for (required) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Find child classes across a project
tree-sitter-analyzer sub-classes ./src/ -c BaseModel
```

### Call Graph Analysis Commands

#### `callers` - Find Function Callers

Find all functions that call a specific function.

```bash
tree-sitter-analyzer callers <path> -f FUNCTION [-c CLASS_NAME] [--json]
```

| Option | Description |
|--------|-------------|
| `-f, --function` | Function name to find callers for (required) |
| `-c, --class-name` | Class name to filter methods |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Find all callers of a function
tree-sitter-analyzer callers ./src/ -f process_data

# Find callers of a method within a class
tree-sitter-analyzer callers ./src/ -f save -c DatabaseHandler
```

#### `callees` - Find Called Functions

Find all functions called by a specific function.

```bash
tree-sitter-analyzer callees <path> -f FUNCTION [-c CLASS_NAME] [--json]
```

| Option | Description |
|--------|-------------|
| `-f, --function` | Function name to find callees for (required) |
| `-c, --class-name` | Class name to filter methods |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Find all functions called by main
tree-sitter-analyzer callees ./src/main.py -f main

# Find callees of a method
tree-sitter-analyzer callees ./src/ -f initialize -c Application
```

### Function-Level Analysis Commands

#### `definition` - Get Function Source Code

Get the complete source code of a specific function.

```bash
tree-sitter-analyzer definition <path> -f FUNCTION [-c CLASS_NAME] [--json]
```

| Option | Description |
|--------|-------------|
| `-f, --function` | Function name to retrieve (required) |
| `-c, --class-name` | Class name to filter methods |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Get function definition
tree-sitter-analyzer definition ./src/utils.py -f parse_config

# Get method definition from a class
tree-sitter-analyzer definition ./src/ -f connect -c Database
```

#### `function-variables` - Get Variables in Function

Get all variables declared within a specific function.

```bash
tree-sitter-analyzer function-variables <path> -f FUNCTION [-c CLASS_NAME] [--json]
```

| Option | Description |
|--------|-------------|
| `-f, --function` | Function name to analyze (required) |
| `-c, --class-name` | Class name to filter methods |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Get variables in a function
tree-sitter-analyzer function-variables ./src/main.py -f process_request
```

#### `function-strings` - Get Strings in Function

Get all string literals within a specific function.

```bash
tree-sitter-analyzer function-strings <path> -f FUNCTION [-c CLASS_NAME] [--json]
```

| Option | Description |
|--------|-------------|
| `-f, --function` | Function name to analyze (required) |
| `-c, --class-name` | Class name to filter methods |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Get string literals in a function
tree-sitter-analyzer function-strings ./src/api.py -f handle_request
```

### Symbol Reference Commands

#### `symbols` - Find Symbol References

Find all references to a specific identifier.

```bash
tree-sitter-analyzer symbols <path> -n NAME [--json]
```

| Option | Description |
|--------|-------------|
| `-n, --name` | Identifier name to search for (required) |
| `--json` | Output in JSON format |

**Examples:**

```bash
# Find all references to a symbol
tree-sitter-analyzer symbols ./src/ -n CONFIG_PATH

# Find references in a single file
tree-sitter-analyzer symbols ./src/main.py -n logger
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (check stderr for details) |

## JSON Output Format

All commands return JSON with a consistent structure:

```json
{
  "path": "/absolute/path/to/target",
  "path_type": "file|directory|glob",
  "count": 10,
  "files_searched": 5,
  ...
}
```

On error:

```json
{
  "error": "Error message"
}
```
