import os
import ast
import csv
import json
from tqdm import tqdm

# === 目录配置 ===
BASE_DIR = ""
OUTPUT_FILE = ""
SUMMARY_FILE = ""
TOOLS_JSON_FILE = ""

# === 判断是否为 @mcp.tool 装饰器 ===
def is_mcp_tool_decorator(decorator):
    if isinstance(decorator, ast.Call) and hasattr(decorator.func, "attr"):
        return decorator.func.attr == "tool"
    elif isinstance(decorator, ast.Attribute):
        return decorator.attr == "tool"
    return False

# === 判断是否使用 FastMCP（导入或实例化） ===
def uses_fastmcp(ast_node, source_text):
    # 1. 通过 import/from/try 导入 FastMCP
    for stmt in ast_node.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom, ast.Try)):
            sub_statements = stmt.body if isinstance(stmt, ast.Try) else [stmt]
            for s in sub_statements:
                if isinstance(s, ast.Import):
                    for alias in s.names:
                        if "fastmcp" in alias.name.lower() or alias.name == "FastMCP":
                            return True
                elif isinstance(s, ast.ImportFrom):
                    if s.module and "mcp.server" in s.module:
                        for alias in s.names:
                            if alias.name == "FastMCP":
                                return True
    # 2. 匹配实例化语句：FastMCP(
    if "FastMCP(" in source_text or "FastMCP (" in source_text:
        return True
    return False

# === 初始化结构 ===
tool_data = []
tool_json_format = []
server_summary = []

# === 获取 server 子目录 ===
server_dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]

# === 扫描每个 server 目录 ===
for server_id, server_name in enumerate(tqdm(server_dirs, desc="扫描服务器目录"), start=1):
    server_path = os.path.join(BASE_DIR, server_name)
    py_files = []
    for root, _, files in os.walk(server_path):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    is_python = "是" if py_files else "否"
    tool_count = 0
    contains_fastmcp = 0

    for py_file in tqdm(py_files, desc=f"处理 {server_name}", leave=False):
        abs_path = os.path.abspath(py_file)

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            print(f"⚠️ 读取失败: {py_file}，原因: {e}")
            continue

        try:
            node = ast.parse(source, filename=py_file)
        except Exception as e:
            print(f"⚠️ AST 解析失败: {py_file}，原因: {e}")
            continue

        # 检查是否使用 FastMCP（导入或实例化）
        if contains_fastmcp == 0 and uses_fastmcp(node, source):
            contains_fastmcp = 1

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(is_mcp_tool_decorator(d) for d in item.decorator_list):
                    tool_count += 1

                    # 提取 description 参数或 docstring
                    explicit_description = None
                    for d in item.decorator_list:
                        if isinstance(d, ast.Call) and hasattr(d.func, "attr") and d.func.attr == "tool":
                            for kw in d.keywords:
                                if kw.arg == "description" and isinstance(kw.value, ast.Str):
                                    explicit_description = kw.value.s

                    docstring = ast.get_docstring(item)
                    if explicit_description:
                        desc_status = "有（显式）"
                        desc_content = explicit_description
                    elif docstring:
                        desc_status = "有（docstring）"
                        desc_content = docstring.strip()
                    else:
                        desc_status = "无"
                        desc_content = "<空>"

                    try:
                        func_code = ast.get_source_segment(source, item).strip()
                    except Exception:
                        func_code = "<unavailable>"

                    tool_data.append({
                        "server_id": server_id,
                        "server_name": server_name,
                        "file_path": abs_path,
                        "function_name": item.name,
                        "description_status": desc_status,
                        "description_content": desc_content,
                        "code": func_code
                    })

                    tool_json_format.append({
                        "name": item.name,
                        "location": abs_path,
                        "code": func_code,
                        "description": desc_content if desc_content != "<空>" else ""
                    })

    server_summary.append({
        "server_id": server_id,
        "server_name": server_name,
        "is_python": is_python,
        "tool_count": tool_count,
        "contains_fastmcp": contains_fastmcp
    })

# === 写入输出文件 ===
if tool_data:
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tool_data[0].keys())
        writer.writeheader()
        for row in tool_data:
            try:
                writer.writerow(row)
            except Exception as e:
                print(f"⚠️ 写入失败（函数: {row.get('function_name')}）: {e}")

if server_summary:
    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=server_summary[0].keys())
        writer.writeheader()
        writer.writerows(server_summary)

with open(TOOLS_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(tool_json_format, f, indent=2, ensure_ascii=False)

print("\n✅ 扫描完成，输出已生成：")
print(f"→ 工具详细 CSV:      {OUTPUT_FILE}")
print(f"→ JSON 工具结构:     {TOOLS_JSON_FILE}")
print(f"→ Server 汇总表:     {SUMMARY_FILE}")
