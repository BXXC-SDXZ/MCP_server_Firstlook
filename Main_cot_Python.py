import os
import time
import csv
from openai import OpenAI
from tqdm import tqdm
import json

# ✅ 初始化 DashScope 客户端（OpenAI 接口兼容模式）
client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ✅ 加载工具函数信息
with open("") as f:
    tools = json.load(f)

def build_messages(code: str, description: str):
    return [
        {
            "role": "system",
            "content": """You are an assistant responsible for determining whether a Python function’s natural language description accurately expresses the function’s main functionality and purpose. Your primary goal is to verify the functional consistency between the description and the actual behavior implemented in the code.

# Input Structure
You will be given:
1. Function Code: A Python function implementation.
2. Description: A natural language explanation of what the function is supposed to do.

# Evaluation Procedure
Follow these six steps to perform your evaluation:

[Step 1] Understand the Function:
Summarize the function’s main functionality and purpose based on its code implementation.

[Step 2] Parse the Description:
Interpret the intended behavior and expectations stated in the description.

[Step 3] Compare Consistency:
Determine whether the described functionality is consistent with what the code actually does. Focus on truthfulness and functional consistency rather than implementation details.

[Step 4] Consistency Judgment:
Decide whether the description truthfully and sufficiently reflects the function’s behavior. A brief description is acceptable as long as it accurately captures the core function.

[Step 5] Misalignment Categorization (if inconsistent):
If the description is inconsistent, assign one of the following categories:
  - Missing Description - The description is completely absent.
  - Incomplete Description - The description omits important functionality.
  - Overstated Description - The description claims functionality not implemented in the code.
  - Misleading Description - The description conveys behavior that contradicts what the function actually does.
  - Useless Description - The description contains no meaningful content. It may consist of vague placeholders (e.g., “do something”), nonsense strings, random characters, or meaningless punctuation that offer no information about the function’s purpose or behavior.
[Step 6] Final Output:
Use the following format for your conclusion:
Consistent or Inconsistent  
Reason: ...  
Category: ...  
Category Explanation: ...
Evaluation Procedure: from step1 to step 5

# Regulations
1. Prioritize functional consistency: Focus on whether the description accurately and consistently represents the behavior of the function.
2. Simplicity is acceptable: Descriptions do not need to be comprehensive if they truthfully capture the main purpose.
3. Ignore implementation detail matching: Do not penalize descriptions for not mentioning internal logic, algorithms, or structure.
4. Choose only one misalignment category when applicable.
"""
        },
        {
            "role": "user",
            "content": (
                f"Function and Description to be evaluated:\n\n"
                f"Code:\n```python\n{code}\n```\n\n"
                f"Description: \"{description}\""
            )
        }
    ]




# ✅ 自动重试 API 调用（如断网时等待恢复）
def robust_completion(client, model, messages):
    while True:
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2
            )
        except Exception as e:
            print(f"⚠️ API 调用失败：{e}，将在 3 分钟后重试...")
            time.sleep(180)

# ✅ 解析判断结果与分析步骤（使用 Consistent/Inconsistent）
def parse_judgment_with_category(reply: str):
    reply = reply.strip().replace("**", "")
    lines = reply.splitlines()

    answer = ""
    reason = ""
    category = ""
    category_reason = ""

    step1 = []
    step2 = []
    step3 = []
    step4 = []

    current_step = None
    for line in lines:
        line = line.strip()
        if line.lower().startswith("consistent"):
            answer = "Consistent"
        elif line.lower().startswith("inconsistent"):
            answer = "Inconsistent"
        elif line.startswith("Reason:"):
            reason = line[7:].strip()
        elif line.startswith("Category:"):
            category = line[9:].strip()
        elif line.startswith("Category Explanation:"):
            category_reason = line[22:].strip()
        elif "STEP 1" in line.upper():
            current_step = "step1"
        elif "STEP 2" in line.upper():
            current_step = "step2"
        elif "STEP 3" in line.upper():
            current_step = "step3"
        elif "STEP 4" in line.upper():
            current_step = "step4"
        else:
            if current_step == "step1":
                step1.append(line)
            elif current_step == "step2":
                step2.append(line)
            elif current_step == "step3":
                step3.append(line)
            elif current_step == "step4":
                step4.append(line)

    if not category:
        category = "NONE" if answer == "Consistent" else "Unspecified"
    if not category_reason:
        category_reason = "None" if category == "NONE" else "Unstated"

    analysis_steps = (
        "[Step 1] " + " ".join(step1).strip() + "\n" +
        "[Step 2] " + " ".join(step2).strip() + "\n" +
        "[Step 3] " + " ".join(step3).strip() + "\n" +
        "[Step 4] " + " ".join(step4).strip()
    )

    return answer, reason, category, category_reason, analysis_steps

# ✅ 主检测逻辑（添加重试）
def check_tools_with_qwen(tools, model="qwen-plus", delay=1.2):
    results = []
    for tool in tqdm(tools, desc="检测中"):
        messages = build_messages(tool["code"], tool["description"])
        completion = robust_completion(client, model, messages)
        reply = completion.choices[0].message.content.strip()
        answer, reason, category, category_reason, analysis_steps = parse_judgment_with_category(reply)
        print(f"[{tool['name']}] → {answer}: {reason} ({category})")
        results.append({
            "name": tool["name"],
            "location": tool.get("location", ""),
            "code": tool["code"],
            "description": tool["description"],
            "answer": answer,
            "reason": reason,
            "category": category,
            "category_reason": category_reason,
            "analysis_steps": analysis_steps
        })
        time.sleep(delay)
    return results

# ✅ 主程序入口
if __name__ == "__main__":
    results = check_tools_with_qwen(tools)

    csv_file = ""
    with open(csv_file, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "location", "code", "description",
            "answer", "reason", "category", "category_reason", "analysis_steps"
        ])
        writer.writeheader()
        for item in results:
            try:
                writer.writerow(item)
            except Exception as e:
                print(f"❌ 写入错误：{e}")
                print(f"跳过的 item 内容：\n{json.dumps(item, indent=2, ensure_ascii=False)}")


    print(f"\n✅ 检测完成，结果已保存为 {csv_file}")
