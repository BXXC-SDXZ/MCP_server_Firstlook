# 修改分类逻辑，仅仅保留强本地类型
# 1：只保留remote和local两个大类。
# remote大类中分为两个小类：一类是已经部署在远程，已经可以直接调用；另一类是还没有部署在云端，但是可以部署在云端的
# 2：只保留“强本地类型”的作为本地类型，就是只能在本地部署的server，如果一个server既可以部署在本地又可以部署在云端之后由本地调用，则认为他属于云端。
# 可以理解为不部署在本地就不能用的server
import os
import re
import json
import pandas as pd
from pathlib import Path
import argparse

# 强本地依赖特征定义
STRONG_LOCAL_PATTERNS = [
    # 硬件操作特征
    r"gpio\.[a-z_]+",                   # GPIO操作
    r"usb\.[a-z_]+",                    # USB设备操作
    r"serial\.[a-z_]+",                 # 串口通信
    r"bluetooth\.[a-z_]+",              # 蓝牙操作
    r"hardware_id\s*=",                 # 硬件ID绑定
    
    # 本地网络绑定
    r"localhost:\d+",                   # 本地主机地址
    r"127\.0\.0\.1",                    # 本地环回地址
    r"0\.0\.0\.0",                      # 全零地址
    r"bind\('127.0.0.1'\)",             # 绑定本地地址
    r"listen\('localhost'\)",           # 监听本地主机
    
    # 文件系统强依赖
    r"open\(['\"]/dev/",                # 设备文件访问
    r"file:///dev/",                    # 设备文件协议
    r"mount\(",                         # 文件系统挂载
    r"shm_open\(",                      # 共享内存访问
    
    # 操作系统级依赖
    r"ioctl\(",                         # 设备IO控制
    r"mmap\(",                          # 内存映射
    r"fork\(",                          # 进程分叉
    r"ptrace\(",                        # 进程跟踪
    
    # 特定本地服务
    r"dbus\.[a-z_]+",                   # DBus通信
    r"systemd\.[a-z_]+",                # Systemd集成
    r"x11\.[a-z_]+",                    # X11图形接口
]

# 远程特征定义
REMOTE_CAPABLE_PATTERNS = [
    r"SSE",  # Server-Sent Events 协议
    r"api_key",  # API密钥配置
    r"api-key",  # API密钥字符串
    r"requests?\.(get|post|put|delete)", # HTTP请求库
    # r"https?://[\w\.\-/]+",             # URL链接
    r"cloud_provider\s*=",              # 云服务商配置
    r"boto3",                           # AWS SDK
    r"google\.cloud",                   # Google Cloud SDK
    r"azure",                           # Azure SDK
]

# 跳过分析的目录
SKIP_DIRS = ['docs', 'examples', 'test', 'tests', 'node_modules', 'vendor', '__pycache__']

def has_strong_local_dependency(content):
    """检测是否包含强本地依赖特征"""
    for pattern in STRONG_LOCAL_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def has_remote_capability(content):
    """检测是否包含远程部署能力"""
    for pattern in REMOTE_CAPABLE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def is_skippable_path(path):
    """检查是否在跳过目录中"""
    for skip_dir in SKIP_DIRS:
        if f"/{skip_dir}/" in path.replace("\\", "/") or path.endswith(f"/{skip_dir}"):
            return True
    return False

def has_strong_remote_signature(content):
    """
    检测是否包含 API endpoint 或 API_KEY 的特征
    - 示例1: https://api.openai.com
    - 示例2: API_KEY = "sk-..."
    """
    # https://mcp.api-inference.modelscope.net # ModelScope API endpoint
    # https?:\/\/[^\s]*modelscope\.net[^\s]*
    # https://dashscope.aliyuncs.com # 阿里云DashScope API endpoint
    # heeps?://[^\s]*aliyun\.com[^\s]* # 阿里云API endpoint
    # https://<env-id>.service.tcloudbase.com/ # 腾讯云TCloudBase API endpoint
    # https?://[^\s]*cloud.tencent.com[^\s]* # 腾讯云API endpoint
    api_patterns = [
        r"https?://api\.[\w\-]+\.\w+",  # API endpoint 如 api.openai.com

        r"SSE",

        # Vercel
        r"https://[^\s]*vercel.com[^\s]*", # Vercel API
        r"vercel",

        # 需转义字符 java等
        r"https?:\/\/[^\s]*modelscope\.net[^\s]*", # ModelScope
        r"https?:\/\/[^\s]*aliyun\.com[^\s]*",  # 阿里云
        r"https?:\/\/[^\s]*cloudbase\.net[^\s]*",  # 腾讯云CloudBase
        r"https?:\/\/[^\s]*cloud\.tencent\.com[^\s]*",  # 腾讯云
        r"https?:\/\/[^\s]*huaweicloud.com[^\s]*",  # 华为云
        r"https?:\/\/[^\s]*cloudflare[^\s]*\.com[^\s]*",  # Cloudflare
        r"https?:\/\/[^\s]*cloud\.google\.com[^\s]*",  # Google APIs

        # 无需转义字符 py等
        r"https?://[^\s]*modelscope\.net[^\s]*", # ModelScope
        r"https?://[^\s]*aliyun\.com[^\s]*",  # 阿里云
        r"https?://[^\s]*cloudbase\.net[^\s]*",  # 腾讯云CloudBase
        r"https?://[^\s]*cloud\.tencent\.com[^\s]*",  # 腾讯云
        r"https?://[^\s]*huaweicloud\.com[^\s]*",  # 华为云
        r"https?://[^\s]*cloudflare[^\s]*\.com[^\s]*",  # Cloudflare
        r"https?:\/\/[^\s]*cloud\.google\.com[^\s]*",  # Google APIs
    ]
    for pattern in api_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def analyze_repository(repo_path):
    print(f"repo_path: {repo_path}")
    """分析单个仓库的部署类型"""
    repo_name = os.path.basename(repo_path)
    print(f"Analyzing: {repo_name}")
    
    strong_local_found = False
    remote_capable_found = False
    
    # 遍历仓库文件
    for root, dirs, files in os.walk(repo_path):

        # print(f"root: {root}")
        # print(f"dirs: {dirs}")
        # print(f"files: {files}")
        # print()

        # 跳过指定目录
        dirs[:] = [d for d in dirs if not is_skippable_path(os.path.join(root, d))]
        
        for file in files:
            # 跳过非文本文件和目录
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bin', '.zip', '.gz', '.pdf')):
                continue
                
            file_path = os.path.join(root, file)
            if is_skippable_path(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # print(f"open file:{file_path}")
                    content = f.read()
                    
                    # 跳过LICENSE文件和大文件
                    if "license" in file.lower() or len(content) > 1000000:
                        continue
                    
                    # 检查特征
                    if not strong_local_found and has_strong_local_dependency(content):
                        strong_local_found = True
                        print(f"get strong local dependency in {file_path}")
                    if not remote_capable_found and has_remote_capability(content):
                        remote_capable_found = True
                        print(f"get remote capable in {file_path}")
                        
                    # 如果已发现强本地特征，提前终止扫描
                    if strong_local_found:
                        break
            
            except Exception as e:
                print(f"  Error reading {file_path}: {str(e)}")
    
    # 分类决策
    if strong_local_found:
        return "local"
    else:
        # 远程类型进一步细分
        if remote_capable_found:
            # 检查是否已提供可直接调用的API端点
            api_endpoint_found = False
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file in ["README.md", "readme.md", "Readme.md", "QUICKSTART.md", "GETTING_STARTED.md"]:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # https?://api\.[\w\-]+\.\w+
                                # API_KEY
                                # if re.search(r"https?://api\.[\w\-]+\.\w+", content):
                                #     api_endpoint_found = True
                                #     break
                                if has_strong_remote_signature(content):
                                    api_endpoint_found = True
                                    print(f"get API endpoint in {file_path}")
                                    break
                        except:
                            continue
                if api_endpoint_found:
                    break
            
            return "remote-deployed" if api_endpoint_found else "remote-deployable"
        else:
            return "unknown"

def generate_report(repos_dir, output_file="mcp_deployment_report.xlsx"):
    """生成分类报告"""
    results = []
    repo_paths = [d for d in os.listdir(repos_dir) 
                 if os.path.isdir(os.path.join(repos_dir, d))]
    
    for repo in repo_paths:
        repo_full_path = os.path.join(repos_dir, repo)
        category = analyze_repository(repo_full_path)
        results.append({
            "repository": repo,
            "category": category,
            "path": repo_full_path
        })
    
    # 创建DataFrame
    df = pd.DataFrame(results)
    
    # 统计摘要
    summary = df['category'].value_counts().reset_index()
    summary.columns = ['deployment_type', 'count']
    
    # 保存结果
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, sheet_name='Repository Classification', index=False)
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Report generated: {output_file}")
    print("\nClassification Summary:")
    print(summary)
    
    # 保存JSON格式用于后续分析
    json_path = output_file.replace('.xlsx', '.json')
    with open(json_path, 'w') as f:
        json.dump({
            "summary": summary.to_dict(orient='records'),
            "repositories": results
        }, f, indent=2)
    
    return output_file

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='MCP Server Deployment Classifier')
    # parser.add_argument('--src', type=str, default=r'C:\Data\PostGraduate-L\组内工作\研一下\20250401-MCP\code\final-auto\data-analysis\deployment-distribution\test-src',
    #                     help='Path to MCP repositories directory')
    # parser.add_argument('--output', type=str, default='mcp_deployment_report.xlsx',
    #                     help='Output report filename')
    
    # args = parser.parse_args()
    
    # # 验证路径存在
    # if not os.path.exists(args.src):
    #     print(f"Error: Source directory not found: {args.src}")
    #     exit(1)
    
    # print(f"Starting analysis of MCP repositories in: {args.src}")
    # report_path = generate_report(args.src, args.output)
    # print(f"Analysis complete. Report saved to: {report_path}")

    src_dirs = [
    r'C:\Data\PostGraduate-L\组内工作\研一下\20250401-MCP\code\final-auto\data-analysis\deployment-distribution\test-src',
    r'C:\Data\PostGraduate-L\组内工作\研一下\20250401-MCP\code\final-auto\data-analysis\deployment-distribution\test-src\test-0729',
    # r'D:\backup\mcp-repos\repo-3'
]

    # 2. 逐个处理
    for src_dir in src_dirs:
        if not os.path.isdir(src_dir):
            print(f"Warning: Skipping non-existent directory {src_dir}")
            continue

        # 3. 报告直接放在各自目录下，文件名固定为 mcp_report.xlsx
        dir_name = os.path.basename(os.path.normpath(src_dir))
        out_file = os.path.join(src_dir, f"mcp_{dir_name}_report.xlsx")
        # dir_name = os.path.basename(os.path.normpath(src_dir))
        # out_file = f"mcp_{dir_name}_report.xlsx"

        print(f"Starting analysis of MCP repositories in: {src_dir}")
        report_path = generate_report(src_dir, out_file)
        print(f"Analysis complete. Report saved to: {report_path}")