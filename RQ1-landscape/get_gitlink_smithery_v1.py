import pandas as pd
import random
from playwright.sync_api import sync_playwright

def extract_github_links(links):
    """直接提取GitHub链接"""
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        for i, link in enumerate(links):
            print(f"\n处理链接 {i+1}/{len(links)}: {link}")
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
                
                results.append({
                    "smithery_url": link,
                    "github_url": github_link
                })
                
                page.close()
                
            except Exception as e:
                print(f"出错: {str(e)}")
                results.append({
                    "smithery_url": link,
                    "github_url": None
                })
        
        context.close()
        browser.close()
    
    return results


if __name__ == "__main__":

    input_path = r"*******************************"
    output_path = r"*******************************"

    # 读取数据
    df = pd.read_excel(input_path)
    links = df["Link"].tolist()
    
    # 提取GitHub链接
    results = extract_github_links(links)
    
    # 保存结果
    results_df = pd.DataFrame(results)
    df["Github Link"] = results_df["github_url"]
    df["Market"] = "smithery"
    df.to_excel(output_path, index=False)
    
    print(f"完成! 结果已保存到 {output_path}")