# Tree-sitter MCP Server

基于 [tree-sitter](https://tree-sitter.github.io/tree-sitter/) 的 MCP 服务器，用于代码分析和安全审计。

## 特性

- **多语言支持**: Python, JavaScript/TypeScript, Java, Go
- **灵活的路径查询**: 支持单文件、glob 模式、整个目录
- **跨文件分析**: 在项目级别搜索 callers、callees、函数定义等

## 路径参数

大部分工具的 `path` 参数支持三种形式：

| 类型 | 示例 | 说明 |
|------|------|------|
| 单文件 | `/path/to/file.py` | 分析单个文件 |
| Glob 模式 | `**/*.py`, `src/**/*.js` | 匹配多个文件 |
| 目录 | `/path/to/project` | 递归搜索目录下所有支持的文件 |

系统会自动识别路径类型，无需额外参数。

## 支持的语言

- Python (.py)
- JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
- Java (.java)
- Go (.go)

## 安装

```bash
uv pip install -e .
```

## 运行

```bash
uv run tree-sitter-mcp
```

## MCP 配置

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

## 可用工具

### 文件级别

| 工具 | 描述 |
|------|------|
| `get_functions` | 提取所有函数定义 |
| `get_classes` | 提取所有类定义 |
| `get_function_calls` | 提取所有函数调用 |
| `get_imports` | 提取所有导入语句 |
| `get_variables` | 提取所有变量声明 |
| `get_call_graph` | 获取调用图 |
| `find_references` | 查找标识符引用 |
| `get_function_definition` | 获取指定函数的完整定义（含 body） |
| `get_function_calls_in_function` | 获取函数内的所有调用 |
| `get_function_variables` | 获取函数内的变量 |
| `get_function_strings` | 获取函数内的字符串 |
| `get_function_callees` | 获取函数调用的其他函数 |
| `get_function_callers` | 获取调用此函数的函数 |

## 输出示例

### 函数列表

```json
{
  "functions": [
    {"name": "main", "start_line": 10, "end_line": 15},
    {"name": "hello", "start_line": 5, "end_line": 8}
  ]
}
```

### 函数定义

```json
{
  "function": {
    "name": "main",
    "start_line": 10,
    "end_line": 12,
    "body": "def main():\n    hello()\n    print('done')"
  }
}
```

### 函数调用

```json
{
  "calls": [
    {"callee": "hello", "line": 11, "caller_function": "main"},
    {"callee": "print", "line": 12, "caller_function": "main", "object": "os", "is_method_call": true}
  ]
}
```
