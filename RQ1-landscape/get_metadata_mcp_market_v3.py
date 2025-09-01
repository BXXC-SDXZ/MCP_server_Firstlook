# 实现增量保存
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import re
import traceback

# ==== Selenium 启动配置 ====
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36')

driver = uc.Chrome(options=chrome_options)

# ==== 目标网站和输出路径 ====
base_url = "https://mcpmarket.com/en/server"
output_dir = "pages_0715/mcpmarket"
os.makedirs(output_dir, exist_ok=True)

# ==== 用于存储所有新增数据 ====
all_data = []
seen_links = set()

try:
    print(f'正在访问目标网站: {base_url}')
    driver.get(base_url)
    time.sleep(5)

    total_results = 0
    loaded_results = 0
    scroll_count = 0
    max_scrolls = 400  # 安全限制，防止无限循环

    while scroll_count < max_scrolls:
        scroll_count += 1

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"\n滚动 #{scroll_count} 到底部，等待加载新内容...")
        time.sleep(2.5)

        # 保存当前 HTML
        html_content = driver.page_source
        html_filename = f'{output_dir}/mcp_market_page_{scroll_count}.html'
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"已保存 HTML 文件: {html_filename}")

        # 解析 HTML，提取卡片
        soup = BeautifulSoup(html_content, 'html.parser')
        server_cards = soup.find_all('a', attrs={'id': lambda x: x and x.startswith('tool-card-')})
        print(f"当前页面卡片总数: {len(server_cards)}")

        new_scroll_data = []

        for card in server_cards:
            name_tag = card.find('h3', class_='font-medium text-lg text-gray-900 dark:text-gray-100 line-clamp-1 group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors')
            name = name_tag.text.strip() if name_tag else "未命名"

            desc_tag = card.find('p', class_='text-gray-600 dark:text-gray-400 line-clamp-2 mb-4 leading-relaxed font-light')
            description = desc_tag.text.strip() if desc_tag else "无描述"

            href = card.get('href')
            full_url = f"https://mcpmarket.com{href}" if href else "链接缺失"

            # 只添加未见过的新链接
            if full_url not in seen_links:
                seen_links.add(full_url)
                new_scroll_data.append({
                    'Server Name': name,
                    'Description': description,
                    'Link': full_url
                })

        # 保存增量数据
        if new_scroll_data:
            print(f"本轮新增服务器数: {len(new_scroll_data)}")
            print(f"new_scroll_data: {new_scroll_data}")
            df = pd.DataFrame(new_scroll_data)
            excel_filename = f'{output_dir}/mcp_market_scroll_{scroll_count}.xlsx'
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f"新增服务器数: {len(new_scroll_data)}，已保存为: {excel_filename}")
            all_data.extend(new_scroll_data)
        else:
            print("本轮无新增服务器卡片，跳过保存")

        # 检查是否全部加载完成
        try:
            status_element = driver.find_element(By.CSS_SELECTOR, 'div.text-sm.text-gray-600.dark\\:text-gray-400.text-center')
            status_text = status_element.text
            print(f"状态文本: {status_text}")

            match = re.search(r'Showing (\d+) of (\d+) results', status_text)
            if match:
                loaded_results = int(match.group(1))
                total_results = int(match.group(2))
                print(f"已加载服务器数: {loaded_results}/{total_results}")

                if loaded_results >= total_results:
                    print("所有服务器数据已加载完成，停止滚动")
                    break
        except:
            print("⚠️ 未能获取页面状态信息")

    # ==== 保存最终总表 ====
    if all_data:
        final_df = pd.DataFrame(all_data)
        total_excel = f'{output_dir}/mcpmarket_servers_total.xlsx'
        final_df.to_excel(total_excel, index=False, engine='openpyxl')
        print(f"\n所有新增数据已合并保存为总表: {total_excel}")
        print(f"总共提取服务器数: {len(all_data)}")
    else:
        print("最终无新增服务器数据")

except Exception as e:
    print(f"\n脚本运行时发生错误: {e}")
    traceback.print_exc()

finally:
    driver.quit()
    print("所有操作已完成，浏览器已关闭")
