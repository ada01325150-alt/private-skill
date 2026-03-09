#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path


TAG_RULES = {
    "节奏设计": ["钩子", "高潮", "完播", "节拍", "悬念"],
    "结构方法": ["三幕", "六步", "大纲", "分场", "结构"],
    "人物一致性": ["人物小传", "人设", "角色", "口吻", "关系"],
    "分镜工程": ["分镜", "机位", "景别", "正反打", "镜头"],
    "工业化生产": ["工作流", "团队", "流程", "选本", "质检"],
}


def normalize_text(content: str) -> str:
    text = content
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_tags(text: str) -> list[str]:
    tags: list[str] = []
    for tag, words in TAG_RULES.items():
        if any(word in text for word in words):
            tags.append(tag)
    return tags


def first_summary(text: str, limit: int = 120) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate extraction process documents from harvested WeChat articles.")
    parser.add_argument("--input", required=True, help="articles.jsonl path")
    parser.add_argument("--out-dir", required=True, help="round output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    insights_jsonl = out_dir / "article-insights.jsonl"
    process_md = out_dir / "extraction-process.md"

    rows = []
    tag_counter = Counter()

    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        content_path = item.get("content_path")
        blocked = bool(item.get("blocked"))

        text = ""
        if (not blocked) and content_path:
            article_file = input_path.parent / str(content_path)
            if article_file.exists():
                text = normalize_text(article_file.read_text(encoding="utf-8"))

        tags = detect_tags(text)
        for tag in tags:
            tag_counter[tag] += 1

        record = {
            "doc_id": item.get("doc_id"),
            "keyword": item.get("keyword"),
            "title": item.get("title"),
            "account_name": item.get("account_name", ""),
            "final_url": item.get("final_url"),
            "blocked": blocked,
            "chars": item.get("chars", 0),
            "tags": tags,
            "summary": first_summary(text, 160) if text else "",
            "content_path": content_path,
        }
        rows.append(record)

    with insights_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    md_lines = []
    md_lines.append("# 文章提炼过程文档")
    md_lines.append("")
    md_lines.append(f"- 输入文件: `{input_path}`")
    md_lines.append(f"- 提炼记录数: `{len(rows)}`")
    md_lines.append("")
    md_lines.append("## 标签统计")
    md_lines.append("")
    if tag_counter:
        for tag, cnt in tag_counter.most_common():
            md_lines.append(f"- {tag}: {cnt}")
    else:
        md_lines.append("- 无可用标签（可能均为 blocked 或内容为空）。")

    md_lines.append("")
    md_lines.append("## 单篇提炼")
    md_lines.append("")
    for idx, row in enumerate(rows, start=1):
        md_lines.append(f"### {idx}. {row['title']}")
        md_lines.append("")
        md_lines.append(f"- keyword: `{row['keyword']}`")
        md_lines.append(f"- account_name: `{row.get('account_name') or 'N/A'}`")
        md_lines.append(f"- url: {row['final_url']}")
        md_lines.append(f"- tags: `{', '.join(row['tags']) if row['tags'] else '无'}`")
        md_lines.append(f"- chars: `{row['chars']}`")
        if row["summary"]:
            md_lines.append(f"- summary: {row['summary']}")
        md_lines.append("")

    md_lines.append("## Agent / Skill 进化建议（自动归纳）")
    md_lines.append("")
    md_lines.append("- `AG-03A`: 强化三幕式与六步节拍时间锚点产出。")
    md_lines.append("- `AG-03B`: 持续校验 100s 钩子链与 30% 高潮命中。")
    md_lines.append("- `AG-03C`: 增强人物小传锚点与漂移检测。")
    md_lines.append("- `AG-06B`: 强化分镜语法、机位连续与场景一致性校验。")
    md_lines.append("- `hook-chain-gate` / `shot-continuity-linter`: 作为关键 Skill 门禁。")

    process_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
