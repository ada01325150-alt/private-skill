#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List


SENSATIONAL_TOKENS = ["震惊", "速看", "必看", "一夜", "躺赚", "零成本"]
ATTRIBUTION_TOKENS = [
    "白皮书",
    "报告",
    "国家广播电视总局",
    "中国网络视听",
    "QuestMobile",
    "Sensor Tower",
    "DataEye",
    "艾媒",
]
CLAIM_TOKENS = ["增长", "留存", "付费", "转化", "出海", "海外", "爆款", "用户", "投放", "算法", "完播"]
DEFAULT_FOCUS_ACCOUNTS = [
    "广大大短剧笔记",
    "广大大",
    "剧查查",
    "DataEye",
    "新腕",
    "新腕儿",
    "漫剧有数",
    "红果",
    "红果短剧",
]


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"[。！？!?\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def resolve_root() -> Path:
    return Path(__file__).resolve().parent.parent


def normalize_text(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_content(input_path: Path, row: Dict) -> str:
    rel = str(row.get("content_path") or "").strip()
    if not rel:
        return ""
    file_path = input_path.parent / rel
    if not file_path.exists():
        return ""
    return normalize_text(file_path.read_text(encoding="utf-8", errors="ignore"))


def score_source(title: str, text: str, account_name: str, focus_hit: bool) -> int:
    score = 40
    if len(text) >= 2500:
        score += 10
    if len(re.findall(r"\d+(?:\.\d+)?%", text)) >= 2:
        score += 10
    if len(re.findall(r"\d{4}", text)) >= 2:
        score += 8
    if any(tok in title or tok in text for tok in ATTRIBUTION_TOKENS):
        score += 16
    if account_name:
        score += 4
    if focus_hit:
        score += 12
    if any(tok in title for tok in SENSATIONAL_TOKENS):
        score -= 12
    return max(0, min(100, score))


def parse_focus_accounts(raw: str) -> List[str]:
    parts = [part.strip() for part in str(raw or "").split(",")]
    return [part for part in parts if part]


def load_focus_accounts_file(path: str) -> List[str]:
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: List[str] = []
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        rows.append(text)
    return rows


def match_focus_accounts(account_name: str, title: str, text: str, focus_accounts: List[str]) -> List[str]:
    merged = " ".join([account_name or "", title or "", text or ""])
    hits: List[str] = []
    seen = set()
    for name in focus_accounts:
        if name and name in merged and name not in seen:
            seen.add(name)
            hits.append(name)
    return hits


def extract_claim(text: str) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    for s in sentences:
        if any(tok in s for tok in CLAIM_TOKENS):
            return s[:120]
    return sentences[0][:120]


def counter_claim(claim: str) -> str:
    if not claim:
        return "样本不足，需补证据后再做结论"
    if "增长" in claim:
        return "增长可能由短期投放驱动，不代表留存和付费可持续"
    if "爆款" in claim:
        return "爆款结论可能是幸存者偏差，需对失败样本做反向复盘"
    if "算法" in claim:
        return "平台算法变动会重置有效策略，需保留内容原创和合规护城河"
    if "付费" in claim:
        return "付费提升可能以口碑损耗为代价，需联合复购和退订率评估"
    return "该结论可能只在特定题材/地区有效，需要明确边界条件"


def boundary_conditions(text: str) -> List[str]:
    out: List[str] = []
    if any(k in text for k in ["美国", "北美"]):
        out.append("仅在北美高ARPU市场验证")
    if any(k in text for k in ["拉美", "东南亚"]):
        out.append("在增长市场需二次本地化")
    if any(k in text for k in ["TikTok", "YouTube", "平台规则", "合规"]):
        out.append("受平台规则和AI标注政策约束")
    if any(k in text for k in ["投放", "买量", "ROI"]):
        out.append("强依赖投放成本与素材迭代速度")
    if not out:
        out.append("边界条件未明确，默认仅作假设")
    return out


def action_from_text(text: str) -> str:
    if any(k in text for k in ["留存", "完播", "前三集", "钩子"]):
        return "将前3集做双版本AB：强反转版 vs 情绪铺垫版，按完播和连看率决策"
    if any(k in text for k in ["付费", "转化", "解锁"]):
        return "把关键真相揭示前置到付费节点前一集，优化首付转化"
    if any(k in text for k in ["本地化", "海外", "出海"]):
        return "同剧情至少输出美区/拉美区两套语义与价值观版本"
    if any(k in text for k in ["AI", "数字人", "版权", "授权"]):
        return "上线前强制执行授权台账和AI标注检查"
    return "将结论先转为1个可测实验，再决定是否纳入模板"


def overseas_fit_score(title: str, text: str, action: str) -> int:
    merged = " ".join([title or "", text or "", action or ""])
    score = 35
    if any(k in merged for k in ["海外", "出海", "北美", "拉美", "东南亚", "美国"]):
        score += 20
    if any(k in merged for k in ["留存", "完播", "连看", "转化", "付费", "复播"]):
        score += 18
    if any(k in merged for k in ["钩子", "反转", "冲突", "卡点", "前三集"]):
        score += 15
    if any(k in merged for k in ["本地化", "文化", "语义", "翻译"]):
        score += 10
    if any(k in merged for k in ["AI", "授权", "合规", "违规", "下架"]):
        score += 8
    return max(0, min(100, score))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis-antithesis-synthesis matrix from WeChat article harvest.")
    parser.add_argument("--input", required=True, help="articles.jsonl path")
    parser.add_argument("--out-dir", required=True, help="output directory")
    parser.add_argument("--wechat-only", action="store_true", help="only include mp.weixin.qq.com links")
    parser.add_argument("--min-source-score", type=int, default=55, help="minimum source score for final matrix")
    parser.add_argument(
        "--focus-accounts",
        default="",
        help="comma-separated focus accounts, e.g. '剧查查,新腕儿,漫剧有数'",
    )
    parser.add_argument(
        "--focus-accounts-file",
        default="",
        help="one account keyword per line; comment line starts with #",
    )
    parser.add_argument(
        "--focus-only",
        action="store_true",
        help="keep only rows matched to focus accounts",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    root = resolve_root()
    focus_accounts_file = args.focus_accounts_file
    if not focus_accounts_file:
        default_file = root / "data/wechat-research/focus_accounts_shortdrama.txt"
        focus_accounts_file = str(default_file)
    focus_accounts = []
    focus_accounts.extend(DEFAULT_FOCUS_ACCOUNTS)
    focus_accounts.extend(parse_focus_accounts(args.focus_accounts))
    focus_accounts.extend(load_focus_accounts_file(focus_accounts_file))
    # Keep order and dedupe.
    seen_focus = set()
    focus_accounts = [item for item in focus_accounts if not (item in seen_focus or seen_focus.add(item))]

    rows: List[Dict] = []
    for line in input_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("blocked"):
            continue
        url = str(row.get("final_url") or row.get("source_url") or "")
        if args.wechat_only and "mp.weixin.qq.com" not in url:
            continue

        text = read_content(input_path, row)
        title = str(row.get("title") or "")
        account_name = str(row.get("account_name") or "").strip()
        if not text:
            continue

        focus_hits = match_focus_accounts(account_name, title, text, focus_accounts)
        if args.focus_only and (not focus_hits):
            continue

        source_score = score_source(title, text, account_name=account_name, focus_hit=bool(focus_hits))
        if source_score < max(args.min_source_score, 0):
            continue

        thesis = extract_claim(text)
        anti = counter_claim(thesis)
        boundaries = boundary_conditions(text)
        action = action_from_text(text)
        fit_score = overseas_fit_score(title, text, action)

        rows.append(
            {
                "keyword": row.get("keyword", ""),
                "title": title,
                "account_name": account_name,
                "url": url,
                "source_score": source_score,
                "overseas_fit_score": fit_score,
                "focus_hits": focus_hits,
                "thesis": thesis,
                "antithesis": anti,
                "boundary_conditions": boundaries,
                "synthesis_action": action,
            }
        )

    rows.sort(
        key=lambda item: (
            len(item.get("focus_hits") or []),
            int(item.get("overseas_fit_score") or 0),
            int(item.get("source_score") or 0),
        ),
        reverse=True,
    )

    matrix_jsonl = out_dir / "dialectic-matrix.jsonl"
    with matrix_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    matrix_md = out_dir / "dialectic-matrix.md"
    lines = [
        "# 微信文章思辨矩阵（命题-反命题-综合）",
        "",
        f"- 输入: `{input_path}`",
        f"- 有效条目: `{len(rows)}`",
        f"- 聚焦账号关键词: `{', '.join(focus_accounts)}`",
        "",
        "| # | keyword | account_name | focus_hits | source_score | fit_score | thesis | antithesis | synthesis_action |",
        "|---|---|---|---|---:|---:|---|---|---|",
    ]
    for i, row in enumerate(rows, start=1):
        lines.append(
            "| {i} | {k} | {n} | {h} | {s} | {f} | {t} | {a} | {x} |".format(
                i=i,
                k=str(row.get("keyword", "")).replace("|", "/"),
                n=str(row.get("account_name", "") or "N/A").replace("|", "/"),
                h=", ".join(row.get("focus_hits") or []).replace("|", "/") or "N/A",
                s=row.get("source_score", 0),
                f=row.get("overseas_fit_score", 0),
                t=str(row.get("thesis", "")).replace("|", "/"),
                a=str(row.get("antithesis", "")).replace("|", "/"),
                x=str(row.get("synthesis_action", "")).replace("|", "/"),
            )
        )

    matrix_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    action_counter = Counter(row.get("synthesis_action", "") for row in rows if row.get("synthesis_action"))
    high_win_md = out_dir / "high-win-system.md"
    h = [
        "# 高胜率策略草案（基于微信文章思辨）",
        "",
        "## 海外爆款优先信号（Top 5）",
        "",
    ]
    top_fit = sorted(rows, key=lambda item: int(item.get("overseas_fit_score") or 0), reverse=True)[:5]
    if top_fit:
        for item in top_fit:
            h.append(
                "- {title}（account={account}, fit={fit}, action={action}）".format(
                    title=str(item.get("title") or "")[:48],
                    account=item.get("account_name") or "N/A",
                    fit=item.get("overseas_fit_score", 0),
                    action=item.get("synthesis_action") or "",
                )
            )
    else:
        h.append("- 暂无足够样本。")

    h.extend(
        [
            "",
        "## 高优先动作",
        "",
        ]
    )
    if action_counter:
        for action, cnt in action_counter.most_common(8):
            h.append(f"- {action}（命中 {cnt} 篇）")
    else:
        h.append("- 暂无足够样本，请扩大关键词或降低最小来源分。")

    h.extend(
        [
            "",
            "## 建议落地",
            "",
            "- 将高优先动作写入 Agent gate（VPS/DCS 前置校验）。",
            "- 每条动作必须绑定1个可测指标（完播/连看/首付/导流）。",
            "- 每周复盘时保留失败样本，更新反命题库。",
        ]
    )
    high_win_md.write_text("\n".join(h) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
