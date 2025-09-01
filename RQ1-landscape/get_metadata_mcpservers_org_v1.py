import requests
from lxml import html
import time
import pandas as pd

base_url = "https://mcpservers.org/?page="
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
}

session = requests.Session()
session.headers.update(headers)

all_data = []

for i in range(1, 40):  # page 1 to 39
    url = f"{base_url}{i}"
    print(f"Processing page {i}: {url}")

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        tree = html.fromstring(response.content)

        # 获取所有服务器卡片容器
        # /html/body/div[2]/div[2]/div[3]/div[1]
        server_cards = tree.xpath("/html/body/div[2]/div[2]/div[3]/div")

        if not server_cards:
            print(f"No server cards found on page {i}")
            continue

        print(f"  Found {len(server_cards)} server cards on page {i}")

        # 逐个处理每个服务器卡片
        for card in server_cards:
            try:
                # 在卡片内相对查找元素
                # card /html/body/div[2]/div[2]/div[3]/div

                # 名称
                # /html/body/div[2]/div[2]/div[3]/div[1]/div[1]/div[1]/div/div
                name_elem = card.xpath(".//div[1]/div[1]/div/div/text()")

                # link
                # /html/body/div[2]/div[2]/div[3]/div[1]/div[2]/a
                link_elem = card.xpath(".//div[2]/a/@href")

                # description
                # /html/body/div[2]/div[2]/div[3]/div[1]/div[1]/div[2]/text()
                desc_elem = card.xpath(".//div[1]/div[2]/text()")
               

                # 确保所有元素都存在
                if name_elem and link_elem and desc_elem:
                    name = name_elem[0].strip()
                    link = "https://mcpservers.org" + link_elem[0] if link_elem[0].startswith("/") else link_elem[0]
                    description = desc_elem[0].strip()

                    all_data.append({
                        "Server Name": name,
                        "Link": link,
                        "Description": description
                    })
                    # print(f"  Processed: {name} - {link}")
                else:
                    if not name_elem:
                        name_elem = None
                    if not link_elem:
                        link_elem = None
                    if not desc_elem:
                        desc_elem = None
                    all_data.append({
                        "Server Name": name_elem[0].strip(),
                        "Link": "https://mcpservers.org" + link_elem[0],
                        "Description": desc_elem[0].strip()
                    })
                    print(f"Missing data in card on page {i}")
            except Exception as e:
                print(f"Error processing a server card on page {i}: {e}")
       
        time.sleep(0.3)  # 可选延迟
    except Exception as e:
        print(f"Error on page {i}: {e}")

# 创建DataFrame并保存为CSV
if all_data:
    df = pd.DataFrame(all_data)
    df.to_csv("mcpserversorg_2507_v1.csv", index=False, encoding="utf-8-sig")
    print(f"\nDone! {len(df)} servers saved to mcpserversorg_2507_v1.csv")
else:
    print("\nNo data collected. Please check the scraping process.")