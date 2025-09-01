# 从官方页面获取github链接
# 分批处理 追加到csv文件 ---- 比追加到xlsx文件效率更高

import pandas as pd
import random
from playwright.sync_api import sync_playwright
from tqdm import tqdm
import os
from openpyxl import load_workbook
from openpyxl import Workbook

def extract_github_links(links):
    """直接提取GitHub链接"""
    gitlink_results = []  # 用于存储GitHub链接结果
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        for i, link in enumerate(links):
            # print(f"\n处理链接 {i+1}/{len(links)}: {link}")
            # print(i + 1, end=' ')
            print(f"\n{i+1}")
            github_link = None
            
            try:
                page = context.new_page()
                page.goto(link, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                # 直接查找包含GitHub链接的<a>标签
                github_element = page.query_selector('a[href*="github.com"]')
                
                if github_element:
                    github_link = github_element.get_attribute("href")
                    # print(f"找到 GitHub 链接：{github_link}")
                else:
                    print("未找到GitHub链接")

                # 将结果添加到列表中
                if github_link:
                    gitlink_results.append(github_link)
                else:
                    gitlink_results.append(None)
                
                page.close()
                
            except Exception as e:
                print(f"出错: {str(e)}")
                gitlink_results.append(None)
        
        context.close()
        browser.close()
    
    return gitlink_results

if __name__ == "__main__":
    input_path = r"*******************************"
    output_path = r"*******************************"
   # 读取数据
    df = pd.read_excel(input_path)

    # 改为分批处理并且分批保存数据
    link_len = df.shape[0] # 行数
    batch_size = 500 # 3条数据处理一次

    # 删除已存在的输出文件（如果需要重新开始）
    if os.path.exists(output_path):
        os.remove(output_path)

    # 初始化CSV文件（仅写入列名，不写入数据）
    if not os.path.exists(output_path):
        # 方法1：直接构造带新列的表头（推荐）
        columns = df.columns.tolist() + ["Github Link", "Market"]
        pd.DataFrame(columns=columns).to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # 方法2：从原始数据中提取列名（保留列顺序）
        # header_df = df.iloc[0:0].copy()  # 取空DataFrame（仅列名）
        # header_df["Github Link"] = ""
        # header_df["Market"] = ""
        # header_df.to_csv(output_path, index=False)

    # results = []
    for i in tqdm(range(0, link_len, batch_size), desc="处理链接"):
        # batch_links = links[i:i + batch_size]
        # 获取批次数据
        batch_data = df.iloc[i:i + batch_size].copy()  # 使用.copy()确保是副本
        batch_git_results = extract_github_links(batch_data["Link"].tolist())

        # 整合数据
        if batch_git_results:
            batch_data.loc[:, "Github Link"] = batch_git_results
            batch_data.loc[:, "Market"] = "official"
            # saveDataAdd(batch_data, output_path)
            # 追加数据（跳过表头）
            batch_data.to_csv(output_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            print(f"数据已成功追加到文件 {output_path}")
            print(f"已处理批次 {i//batch_size + 1}/{(link_len + batch_size - 1) // batch_size}")
            print()
        else:
            print(f"未获取到数据，跳过保存")
    
    print(f"完成! 结果已保存到 {output_path}")