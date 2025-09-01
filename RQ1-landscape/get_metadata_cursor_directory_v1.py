from lxml import html
import pandas as pd

# 1. 读取本地 HTML 文件
with open("all_cursor.html", "r", encoding="utf-8") as f:
    content = f.read()

# 2. 解析 HTML
tree = html.fromstring(content)

# 卡片
# /html/body/div[2]/div[2]/div/div[1]
# 链接
# /html/body/div[2]/div[2]/div/div[1]/div/a
# 名称
# /html/body/div[2]/div[2]/div/div[1]/div/a/div/div/h3
# 描述
# /html/body/div[2]/div[2]/div/div[1]/div/a/div/div/p/text()

# 提取所有的卡片
cards = tree.xpath("/html/body/div[2]/div[2]/div/div")

if not cards:
    print("没有找到任何服务器卡片")
    exit()

print(f"找到 {len(cards)} 个服务器卡片")

# 准备存储数据  
all_data = []

# 逐个处理卡片
for index, card in enumerate(cards):
    try:
        print(f"正在处理卡片 {index + 1}/{len(cards)}...")

        # 在卡片内查找相对元素
        name_elem = card.xpath(".//a/div/div/h3/text()")
        link_elem = card.xpath(".//a/@href")
        desc_elem = card.xpath(".//a/div/div/p/text()")

        # 确保所有元素都存在
        if name_elem and link_elem and desc_elem:
            name = name_elem[0].strip()
            link = "https://cursor.directory/" + link_elem[0].strip()
            description = desc_elem[0].strip()
            all_data.append({
                "Server Name": name,
                "Link": link,
                "Description": description
            })
        else:
            # 如果元素不存在则保存为空
            if not name_elem:
                name_elem = None
            if not link_elem:
                link_elem = None
            if not desc_elem:
                desc_elem = None
            all_data.append({
                "Server Name": name_elem[0].strip(),
                "Link": "https://cursor.directory/" + link_elem[0].strip(),
                "Description": desc_elem[0].strip()
            })
            print(f"⚠️ 卡片 {index + 1} 数据不完整: name={bool(name_elem)}, link={bool(link_elem)}, desc={bool(desc_elem)}")

    except Exception as e:
        print(f"⚠️ 处理卡片 {index + 1} 时出错: {str(e)}")

# 保存到CSV文件
if all_data:
    df = pd.DataFrame(all_data)
    df = df[["Server Name", "Link", "Description"]]  # 确保列顺序
    df.to_csv("cursordirectory_2507_v1.csv", index=False, encoding='utf-8-sig')
    print(f"\n✅ 提取完成：共 {len(df)} 个服务器，已保存到 cursordirectory_2507_v1.csv")
else:
    print("\n❌ 未提取到任何服务器数据")
