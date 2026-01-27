# parse_questions.py
from docx import Document
import re
import json
import os

# ===== 硬编码文件路径 =====
INPUT_DOCX = "./test1.docx"
OUTPUT_JSON = "./questions.json"


def count_choices_from_text(text: str) -> int:
    labels = re.findall(r'([A-Z])、', text)
    if not labels:
        return 0
    max_label = max(labels)
    return ord(max_label) - ord('A') + 1


def is_option_fragment(text: str) -> bool:
    return bool(re.match(r'^\s*[B-Z]、', text.strip()))


def extract_and_fix_paragraphs(docx_path):
    doc = Document(docx_path)
    raw_paragraphs = [p.text for p in doc.paragraphs]

    fixed = []
    i = 0
    while i < len(raw_paragraphs):
        current = raw_paragraphs[i]
        current_stripped = current.strip()

        if (current_stripped and
                'A、' in current_stripped and
                not re.match(r'^\s*[A-Z]、', current_stripped) and
                i + 1 < len(raw_paragraphs) and
                is_option_fragment(raw_paragraphs[i + 1])
        ):
            merged = current.rstrip() + " " + raw_paragraphs[i + 1].lstrip()
            fixed.append(merged)
            i += 2
        else:
            fixed.append(current)
            i += 1

    return [line.strip() for line in fixed if line.strip()]


def parse_raw_questions(docx_path):
    """仅解析题干和选项数，不处理 is_negative"""
    lines = extract_and_fix_paragraphs(docx_path)
    questions = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if re.match(r'^\s*[A-Z]、', line):
            i += 1
            continue

        stem_and_options = line
        num_choices = 0

        if re.search(r'[A-Z]、', stem_and_options):
            num_choices = count_choices_from_text(stem_and_options)
            stem = re.split(r'\s*[A-Z]、', stem_and_options, maxsplit=1)[0].strip()
        else:
            stem = stem_and_options
            if i + 1 < len(lines) and re.search(r'[A-Z]、', lines[i + 1]):
                num_choices = count_choices_from_text(lines[i + 1])
                i += 1

        clean_stem = re.sub(r'^\d+[\.、]\s*', '', stem).strip()
        if num_choices == 0:
            num_choices = 4

        if clean_stem:
            questions.append({
                "text": clean_stem,
                "num_choices": num_choices,
                "is_negative": False  # 默认 false
            })

        i += 1

    return questions


def parse_reverse_ranges(input_str: str, total: int):
    """
    解析用户输入的题号范围，如 "3,5,7-10,15"
    返回 set of indices (0-based)
    """
    if not input_str.strip():
        return set()

    indices = set()
    parts = re.split(r'[,，\s]+', input_str.strip())

    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= end <= total:
                    indices.update(range(start - 1, end))  # 转为 0-based
                else:
                    print(f"⚠️ 警告: 范围 {part} 超出题目总数 ({total})，已忽略")
            except ValueError:
                print(f"⚠️ 警告: 无效范围 '{part}'，已忽略")
        else:
            try:
                num = int(part)
                if 1 <= num <= total:
                    indices.add(num - 1)  # 转为 0-based
                else:
                    print(f"⚠️ 警告: 题号 {num} 超出范围 (1-{total})，已忽略")
            except ValueError:
                print(f"⚠️ 警告: 无效题号 '{part}'，已忽略")

    return indices


def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"questions": data}, f, ensure_ascii=False, indent=2)


def main():
    print("📝 心理测评题目解析器")
    print("请选择模式：")
    print("1. 生成 JSON 后手动修改 is_negative（推荐新手）")
    print("2. 运行时指定反向计分题号（自动设置 is_negative=true）")

    mode = input("请输入 1 或 2: ").strip()

    print(f"\n正在解析: {INPUT_DOCX}")
    questions = parse_raw_questions(INPUT_DOCX)
    total = len(questions)
    print(f"✅ 共提取 {total} 道题目\n")

    if mode == "2":
        print("📌 请输入反向计分题号（支持单个或范围，用逗号/空格分隔）")
        print("   示例: 3, 7, 12-15, 20")
        user_input = input("题号: ").strip()

        reverse_indices = parse_reverse_ranges(user_input, total)
        for idx in reverse_indices:
            questions[idx]["is_negative"] = True

        print(f"✅ 已将 {len(reverse_indices)} 道题目标记为反向计分")
    elif mode != "1":
        print("❌ 无效输入，默认使用模式 1（全部 is_negative=false）")

    save_json(questions, OUTPUT_JSON)
    print(f"\n📄 JSON 已保存至: {OUTPUT_JSON}")
    print("💡 提示: 可用 VS Code / Excel 打开 JSON 手动调整 is_negative")


if __name__ == "__main__":
    main()