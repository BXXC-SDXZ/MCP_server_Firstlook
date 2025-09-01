# 这里拿不到git链接
# 之后会有一个新文件通过mcp-so的页面来获取git链接
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# ==== 你提前准备好的 category 列表 ====
categories = [
    "official-servers",
    "research-and-data",
    "cloud-platforms",
    "browser-automation",
    "databases",
    "ai-chatbot",
    "file-systems",
    "os-automation",
    "finance",
    "communication",
    "developer-tools",
    "knowledge-and-memory",
    "entertainment-and-media",
    "calendar-management",
    "database",
    "location-services",
    "customer-data-platforms",
    "security",
    "monitoring",
    "virtualization",
    "cloud-storage",
]

# ==== Selenium 启动配置 ====
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36')

driver = uc.Chrome(options=chrome_options)

# ==== 遍历所有 category 和每一页 ====
for category in categories:
    # 创建对应目录
    os.makedirs(f"pages_0715/{category}", exist_ok=True)

    # 用于存储每个 category 下的所有数据
    all_data = []

    page = 1
    while True:  # 无限循环，直到检测到页面为空
        if page == 1:
            url = f'https://mcp.so/servers?category={category}'
        else:
            url = f'https://mcp.so/servers?category={category}&page={page}'
        try:
            print(f'正在访问 [{category}] 第 {page} 页: {url}')
            driver.get(url)

            time.sleep(3)

            # 检查页面是否包含“需要先检查您的连接的安全性”字样
            html_content = driver.page_source            
            while "需要先检查您的连接的安全性" in html_content:
                print("页面需要人机验证！")
                # 每 10 秒检查一次是否通过验证
                time.sleep(10)
                html_content = driver.page_source  # 获取新的 HTML 内容
                # 提示用户完成验证
                if "需要先检查您的连接的安全性" not in html_content:
                    print("人机验证已通过，继续抓取数据。")
                    break

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
            # server_cards = soup.find_all('div', class_='flex flex-col cursor-pointer bg-background rounded-xl border border-gray-300 dark:border-gray-700 p-4 shadow-lg hover:shadow-xl transition-shadow')
            server_cards = soup.find_all('div', class_='h-full flex flex-col cursor-pointer bg-background rounded-xl border border-gray-300 dark:border-gray-700 p-4 shadow-lg hover:shadow-xl transition-shadow')
            # 如果当前页面没有找到任何服务器卡片，说明该 category 已结束，跳出循环
            if not server_cards:
                print(f"[{category}] 第 {page} 页没有找到任何数据，退出该类别的爬取！")
                break

            print(f"第 {page} 页数据有效，继续抓取")

            for card in server_cards:
                # 打印当前卡片的 HTML 内容（可选）
                # print(card.prettify())
                # 提取名称
                # name = card.find('h3', class_='font-medium text-md line-clamp-1 -mt-1').text.strip()
                name = card.find('div', class_='font-medium text-sm line-clamp-1 -mt-1').text.strip()
                print(f"名称: {name}")
                # 提取简介
                # description_tag = card.find('p', class_='text-foreground mb-4 text-sm line-clamp-3 flex-1 shrink-0 overflow-y-auto')
                description_tag = card.find('p', class_='text-foreground mb-0 text-sm line-clamp-3 flex-1 shrink-0 overflow-y-auto')
                description = description_tag.text.strip() if description_tag else ""
                print(f"简介: {description}")
                
                # 提取GitHub链接
                # 250626 无法直接通过页面提取到github链接了
                # github_link = "N/A"
                # for a_tag in card.find_all('a', target='_blank'):
                #     if 'github.com' in a_tag['href']:
                #         github_link = a_tag['href']
                #         break

                # 换为提取网页链接
                # <a class="h-full flex flex-col" href="/server/edgeone-pages-mcp/TencentEdgeOne?tab=tools">
                a_tag = card.find('a', class_='h-full flex flex-col')
                href = a_tag['href'] if a_tag else ""
                link = f"https://mcp.so{href}" if href else ""
                print(f"链接: {link}")
                # data.append({
                #     '类别': category,
                #     '名称': name,
                #     '简介': description,
                #     'GitHub链接': github_link
                # })
                data.append({
                    'Category': category,
                    'Server Name': name,
                    'Description': description,
                    'Link': link
                    # 'GitHub链接': github_link
                })

             # 将当前页数据追加到该 category 的所有数据中
            all_data.extend(data)
            # 创建 DataFrame 并保存到 Excel
            df = pd.DataFrame(data)
            excel_filename = f'pages_0715/{category}/mcp_servers_page_{page}.xlsx'
            df.to_excel(excel_filename, index=False, engine='openpyxl')

            print(f"数据已成功保存到 {excel_filename}")
            page += 1  # 继续抓取下一页
        except Exception as e:
            print(f'访问失败: [{category}] 第 {page} 页, 错误: {e}')
    
    # 当该 category 所有页面的数据都抓取完后，保存到 Excel
    if all_data:
        df = pd.DataFrame(all_data)
        excel_filename = f'pages_0715/{category}/mcp_servers_{category}.xlsx'
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"数据已成功保存到 {excel_filename}")

# ==== 完成，退出浏览器 ====
driver.quit()
print("所有页面已保存完成！")



