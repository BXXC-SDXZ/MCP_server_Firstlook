import pandas as pd
import re

# === Step 1: 读取 CSV 文件 ===
df = pd.read_csv("")

# === Step 2: 精简规则匹配函数（仅四个强范式） ===
def get_matched_strong_patterns(row):
    if row['answer'] != 'Inconsistent' or row['category'] != 'Incomplete Description':
        return None

    reason = str(row['reason']).lower()
    matched = set()

    # R1: 包含 error / errors / exception / handling / 异常组合句式
    if (
        'error' in reason or
        'errors' in reason or
        'exception' in reason or
        'exception handling' in reason or
        re.search(r'(?=.*\b(error|errors|exception)\b)(?=.*\b(handle|handling)\b)', reason) or
        re.search(r"(does not|do not|don't)\s+include\s+(error|errors|warning|warnings)", reason)
    ):
        matched.add('R1_error_related')

    # R2: 包含 return / returns / output / format
    if (
        'return' in reason or
        'returns' in reason or
        'output' in reason or
        'format' in reason or
        'full output' in reason or
        ('result' in reason and 'format' in reason)
    ):
        matched.add('R2_format_related')

    # R3: 处理 invalid / empty 情况的句式
    if re.search(r'in case of .*invalid', reason) or re.search(r'handling of .*?(invalid|empty)', reason):
        matched.add('R3_invalid_handling')

    # R4: logging 相关
    if 'log' in reason or 'logging' in reason:
        matched.add('R4_logging')

    return ', '.join(sorted(matched)) if matched else None

# === Step 3: 执行匹配 ===
df['matched_pattern'] = df.apply(get_matched_strong_patterns, axis=1)
df['possible_false_positive'] = df['matched_pattern'].notnull()

# === Step 4: 输出结果文件 ===

# 清洗后的数据（误报移除）
df[~df['possible_false_positive']].drop(columns=['possible_false_positive']).to_csv("All_filtered_output.csv", index=False)

# 被筛除的误报（含命中范式）
df[df['possible_false_positive']].drop(columns=['possible_false_positive']).to_csv("All_filtered_out_false_positives.csv", index=False)
