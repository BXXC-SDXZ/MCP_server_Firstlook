'''
FilePath: get_tag_by_llm_en_v1.py
Author: lemon
Date: 2025-07-25 00:31:11
LastEditors: Please set LastEditors
LastEditTime: 2025-09-01 20:19:09
Copyright: 2025 xxxTech CO.,LTD. All Rights Reserved.
Descripttion: 
'''
import pandas as pd
import time
import json
from http import HTTPStatus
import dashscope
import os
import json
from typing import List, Dict

# 配置 DashScope API 密钥
dashscope.api_key = "*******************************"

import pandas as pd
from typing import List, Dict

# 加载分类体系，并返回结构化数据
def load_categories(category_file: str) -> List[Dict[str, object]]:
    """
    使用 pandas 读取 MCP 分类 Excel 文件，返回结构化数据：
    [
        {
            "title": "...",
            "title_description": "...",
            "sub_categories": [
                {
                    "sub_title": "...",
                    "sub_title_description": "..."
                },
                ...
            ]
        },
        ...
    ]
    """
    df = pd.read_excel(category_file, sheet_name=0)

    # 填充 title 和 title-description 的缺失值（向下填充）
    df['title'] = df['title'].ffill()
    df['title-description'] = df['title-description'].ffill()

    # 按 title 分组
    grouped = df.groupby('title')

    result = []

    for title, group in grouped:
        title_description = group['title-description'].iloc[0]
        sub_categories = []

        # 遍历子项
        for _, row in group.iterrows():
            sub_title = str(row['sub-title']).strip()
            sub_title_desc = str(row['sub-title-description']).strip()

            if sub_title and sub_title != 'nan':
                sub_categories.append({
                    "sub_title": sub_title,
                    "sub_title_description": sub_title_desc
                })

        result.append({
            "title": title,
            "title_description": title_description,
            "sub_categories": sub_categories
        })

    return result

# 构建英文版prompt
def generate_prompt_en(
        category_file: str,
        server_description: str
) -> str:
    """
    Build an English prompt for LLM-based MCP Server classification.
    """
    # 1. Load structured category system
    categories = load_categories(category_file)
    # print(categories)

    # 2. Build human-readable category standard
    lines = []
    for cat in categories:
        lines.append(f"Level-1 Category: {cat['title']} — {cat['title_description']}")
        for sub in cat['sub_categories']:
            lines.append(f"  └─ Level-2 Category: {sub['sub_title']} — {sub['sub_title_description']}")
        lines.append("")  # blank line for readability

    standard_text = "\n".join(lines).strip()

    # 3. Compose final prompt
    prompt = f"""You are an expert MCP Server classification assistant with knowledge in computer systems, AI, and software engineering. Your task is to accurately classify a given MCP Server description according to the following category standard and explain your reasoning.

    Category Standard (contains {len(categories)} level-1 categories, each with level-2 sub-categories and functional descriptions):
    {standard_text}

    Classification Rules:
    1. Assign up to one level-2 category in the format "level-1/level-2". If no level-2 exists, use the level-1 category only.
    2. Base your decision on the functional descriptions provided for each category.
    3. If classification is impossible, label it as "unclassified".
    4. Return a standard JSON object with:
    - level-1 category (key: "Level-1")
    - level-2 category (key: "Level-2", optional)
    - justification (key: "Reason"), explaining which keywords or functions led to this choice.

    Output Examples:
    - {{"Level-1": "developer-tools", "Level-2": "model-deployment", "Reason": "The server mentions RESTful APIs for deploying ML models, matching model-deployment."}}
    - {{"Level-1": "data-processing", "Reason": "Focuses on data cleaning and format conversion, aligning with data-processing."}}

    MCP Server Description:
    {server_description}
    """
    return prompt.strip()

# def classify_with_llm(description, categories, max_retries=3):
def classify_with_llm(category_file, description, max_retries=3):
    """调用大模型进行分类，并返回含理由的结果"""
    # prompt = generate_prompt_en(description, categories)
    prompt = generate_prompt_en(category_file, description)
    # print(f"prompt: " + prompt)

    for attempt in range(max_retries):
        try:
            response = dashscope.Generation.call(
                model="qwen-plus",
                messages=[{"role": "user", "content": prompt}],
                result_format='message',
                top_p=0.8,
                temperature=0.3,
                enable_search=False
            )

            if response.status_code == HTTPStatus.OK:
                result_str = response.output.choices[0]['message']['content']
                start_idx = result_str.find('{')
                end_idx = result_str.rfind('}') + 1
                json_str = result_str[start_idx:end_idx]
                result = json.loads(json_str)

                # 兼容字段
                return {
                    "Level-1": result.get("Level-1", "unclassified"),
                    "Level-2": result.get("Level-2", ""),
                    "Reason": result.get("Reason", "none")
                }
            else:
                print(f'请求失败: {response.code}, {response.message}')
                time.sleep(2)
        except Exception as e:
            print(f"分类出错: {str(e)}")
            time.sleep(3)

    return {"Level-1": "unclassified", "Level-2": "", "Reason": "Failing to call model or respond abnormal !"}


def main():

    # 文件路径配置
    input_file = r"*******************************"
    category_file = r"*******************************"
    output_file = r"*******************************"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 加载数据
    df = pd.read_csv(input_file)
    # categories = load_categories(category_file)
    # 打印分类体系以供调试
    # print(json.dumps(categories, indent=2, ensure_ascii=False))

    # 添加分类列
    df['Level-1'] = ""
    df['Level-2'] = ""
    df['Reason'] = ""

    total = len(df)
    for idx, row in df.iterrows():
        description = str(row.get('Description', '')).strip()
        # if not description or len(description) < 10:
        # 这里改成了5
        # 0820 改成3
        if not description or len(description) < 3: 
            result = {"Level-1": "unclassified", "Level-2": "", "Reason": "Description too short or missing."}
        else:
            print(f"正在处理 ({idx+1}/{total}): {row.get('Server Name', '')[:30]}...")
            # result = classify_with_llm(description, categories)
            result = classify_with_llm(category_file, description)

        df.at[idx, 'Level-1'] = result['Level-1']
        df.at[idx, 'Level-2'] = result['Level-2']
        df.at[idx, 'Reason'] = result['Reason']

        if (idx + 1) % 10 == 0:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n分类完成，结果保存至: {output_file}")

    

if __name__ == '__main__':
    main()
