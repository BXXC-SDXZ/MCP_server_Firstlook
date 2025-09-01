# 仿照mcp.so的get_metadata_mcp_so_v1.py
# 这里拿不到git链接
# 之后会有一个新文件通过mcp-so的页面来获取git链接
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# # ==== category 列表 ====
# categories = [
#     "official-servers",
#     "research-and-data",
#     "cloud-platforms",
#     "browser-automation",
#     "databases",
#     "ai-chatbot",
#     "file-systems",
#     "os-automation",
#     "finance",
#     "communication",
#     "developer-tools",
#     "knowledge-and-memory",
#     "entertainment-and-media",
#     "calendar-management",
#     "database",
#     "location-services",
#     "customer-data-platforms",
#     "security",
#     "monitoring",
#     "virtualization",
#     "cloud-storage",
# ]

# ==== 提前准备好的url =====
# https://smithery.ai/search?q=is%3Adeployed&page=1
urls = [
    # "https://smithery.ai/search?q=is%3Afeatured",
    # "https://smithery.ai/search?q=is%3Adeployed",
    # "https://smithery.ai/search?q=web+search",
    # "https://smithery.ai/search?q=browser%20automation",
    # "https://smithery.ai/search?q=memory%20systems%20and%20memory%20extensions%20for%20agents",
    # "https://smithery.ai/search?q=Find%20integrations%20that%20extend%20language%20model%20capabilities%20with%20third-party%20APIs%2C%20support%20multimodal%20queries%2C%20enable%20product%20search%2C%20custom%20prompt%20engineering%2C%20response%20validation%2C%20and%20facilitate%20connections%20to%20external%20AI%20agents%20or%20models%20for%20enhanced%20workflow%20efficiency.",
    # "https://smithery.ai/search?q=Integrations%20that%20enable%20interaction%2C%20extraction%2C%20and%20manipulation%20of%20Figma%20design%20data%20through%20AI%20tools%20or%20coding%20environments.%20Search%20for%20solutions%20that%20facilitate%20connecting%20design%20assets%20to%20development%20workflows%2C%20programmatically%20accessing%20or%20editing%20design%20elements%2C%20and%20bridging%20the%20gap%20between%20designs%20and%20code%20for%20enhanced%20collaboration%20and%20efficiency."
    "https://smithery.ai/search?q=Find%20systems%20that%20offer%20real-time%20weather%20data%2C%20forecasts%2C%20and%20meteorological%20information%20for%20integration%20into%20applications%2C%20supporting%20features%20like%20current%20conditions%2C%20future%20predictions%2C%20and%20environmental%20context%20enhancement."
]
categories = [
    # "featured",
    # "popular",
    # "Web Search",
    # "Browser Automation",
    # "Memory Management",
    # "AI Integration Tools",
    # "AI Design Integration",
    "Weather Data APIs",
]
category_urls_dict = dict(zip(categories, urls))
# ==== Selenium 启动配置 ====
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36')

driver = uc.Chrome(options=chrome_options)

# ==== 遍历所有 category 和每一页 ====
# for category in categories:
# ==== 遍历所有 category 和每一页 ====
for category, url in category_urls_dict.items():
    # 创建对应目录
    os.makedirs(f"pages_0715/{category}", exist_ok=True)

    # 用于存储每个 category 下的所有数据
    all_data = []

    page = 1
    while True:  # 无限循环，直到检测到页面为空
        if page == 1:
            # url = f'https://mcp.so/servers?category={category}'
            link = f'{url}'
        else:
            # url = f'https://mcp.so/servers?category={category}&page={page}'
            link = f'{url}&page={page}'
        try:
            print(f'正在访问 [{category}] 第 {page} 页: {link}')
            driver.get(link)

            time.sleep(3)

            html_content = driver.page_source
            filename = f'pages_0715/{category}/page_{page}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f'保存完成: {filename}')

            # 执行解析和数据提取过程
            data = []

            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找所有服务器卡片
            server_cards = soup.find_all('a', class_='group bg-card rounded-lg border border-border p-4 hover:border-primary/50 hover:shadow-md hover:shadow-primary/5 transition-all duration-200 h-full flex flex-col relative z-10 overflow-hidden')
            
            # 如果当前页面没有找到任何服务器卡片，说明该 category 已结束，跳出循环
            if not server_cards:
                print(f"[{category}] 第 {page} 页没有找到任何数据，退出该类别的爬取！")
                break

            print(f"第 {page} 页数据有效，继续抓取")

            for card in server_cards:
                # 打印当前卡片的 HTML 内容（可选）
                # print(card.prettify())
                # 提取名称
                name = card.find('h3', class_='text-base font-semibold text-foreground group-hover:text-primary transition-colors truncate').text.strip()
                # print(f"名称: {name}")
                # 提取简介
                description_tag = card.find('p', class_='text-muted-foreground text-sm leading-relaxed line-clamp-2')
                description = description_tag.text.strip() if description_tag else ""
                # print(f"简介: {description}")

                # 提取网页链接
                href = card.get('href')   # 因为card就是那个<a>标签
                link_smithery = f"https://smithery.ai{href}" if href else ""
                # print(f"链接: {link_smithery}")

                data.append({
                    'Category': category,
                    'Server Name': name,
                    'Description': description,
                    'Link': link_smithery
                    # 'GitHub链接': github_link
                })

             # 将当前页数据追加到该 category 的所有数据中
            all_data.extend(data)
            # 创建 DataFrame 并保存到 Excel
            df = pd.DataFrame(data)
            excel_filename = f'pages_0715/{category}/smithery_servers_page_{page}.xlsx'
            df.to_excel(excel_filename, index=False, engine='openpyxl')

            print(f"数据已成功保存到 {excel_filename}")
            page += 1  # 继续抓取下一页
        except Exception as e:
            print(f'访问失败: [{category}] 第 {page} 页, 错误: {e}')
    
    # 当该 category 所有页面的数据都抓取完后，保存到 Excel
    if all_data:
        df = pd.DataFrame(all_data)
        excel_filename = f'pages_0715/{category}/smithery_servers_{category}.xlsx'
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"数据已成功保存到 {excel_filename}")

# ==== 完成，退出浏览器 ====
driver.quit()
print("所有页面已保存完成！")



