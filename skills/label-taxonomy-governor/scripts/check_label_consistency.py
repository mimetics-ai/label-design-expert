#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签口径一致性校验器。

只查结构与一致性：命名正则、枚举完整性、跨文件口径取值冲突、分域禁用词命中。
不判定语义是否等价、不判定整句是否构成违规宣称、不查法规现行效力。
判定由模型按 references/ 规则包完成，拍板由用户完成。

v1.2.0（2026-11-19 桌面标签实测回灌）：
  - normalize_key 保留 Unicode 字母/数字，中文口径键不再被剥成空串；
  - 新增「仅书写格式不同」识别：全角/空格/乘号差异不属四类漂移，
    标「需人工复核」，不临场发明第五类。

v1.2.2（2026-11-20 线上 7 条实测回灌）：
  - 域隔离：A 域口径治理不再采信输入里的 scope、也不输出 B 域「属性认定」/
    「分域禁用词」判定。线上第 1 条实测曾出现模型臆造「工业化学品」并生成
    「禁用词通过」的假合规结论，违反「先分流、判据不混用」「占位≠已具备」。
  - domain 字段：默认 A；仅显式 domain="B" 且给了 scope 时才跑分域禁用词。
    A 域输入若携带 scope，原样回显在 meta.scope_in_input，但不采信、不据此判定。

用法：
  python check_label_consistency.py --input declarations.json \
      --config config/rules.json --output-md report.md --output-json report.json
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "1.2.2"
PASS, FAIL, REVIEW = "通过", "不通过", "需人工复核"
DEFAULT_DRIFTS = ["值漂移", "名漂移", "范围漂移", "版本陈旧"]


def normalize_key(raw, aliases):
    """把 env.expectedIntegrity 与 EXPECTED_INTEGRITY 归一到同一口径键。

    v1.2：旧版 `[^a-z0-9]+` 会把纯中文 key 剥成空串，导致所有中文口径声明
    被错误归进同一组（2026-11-19 桌面 13 款标签实测发现）。现保留 Unicode
    字母与数字；NFKC 顺带处理全角字符。
    """
    key = str(raw).replace("\\", "/").split("/")[-1].split(".")[-1]
    key = unicodedata.normalize("NFKC", key).lower()
    key = re.sub(r"[^\w]+", "", key, flags=re.UNICODE).replace("_", "")
    return aliases.get(key, key)


def normalize_value(value):
    """只做书写格式归一，绝不合并语义不同的取值。

    NFKC（全角→半角）＋ 去空白 ＋ 乘号/星号→x。用于识别
    「210x194mm」与「210×194 mm」这类书写差异；归一后仍不同才是值漂移。
    """
    if not isinstance(value, str):
        return value
    s = unicodedata.normalize("NFKC", value).strip().lower()
    s = re.sub(r"[\s\u00a0]+", "", s)
    return s.replace("×", "x").replace("✕", "x").replace("*", "x")


def analyze(data, config):
    labels = data.get("labels") or []
    decls = data.get("declarations") or []
    # v1.2.2 域隔离：默认 A 域。只有显式 domain=="B" 才做 B 域属性认定/禁用词。
    # A 域输入里携带的 scope 一律不采信，仅原样回显供人工核对。
    domain = str(data.get("domain") or "A").strip().upper()
    is_b = domain == "B"
    scope_in_input = data.get("scope") or ""
    # A 域不采信 scope：仅 B 域把它当作有效属性认定参与禁用词判定。
    scope = (scope_in_input if is_b else "")

    naming = config.get("naming") or {}
    pattern = re.compile(naming.get("pattern", r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"))
    max_len = int(naming.get("max_length", 40))
    reserved = set(naming.get("reserved_words") or [])
    aliases = {normalize_key(k, {}): v for k, v in (config.get("key_aliases") or {}).items()}
    word_map = config.get("banned_label_words_scope") or {}
    drift_types = config.get("drift_types") or DEFAULT_DRIFTS
    priority = config.get("drift_priority") or drift_types

    active_words = list(word_map.get(scope) or [])
    active_words += [w for w in (word_map.get("通用") or []) if w not in active_words]

    naming_violations, enum_issues, conflicts, banned_hits, verdicts = [], [], [], [], []
    format_only = []

    # 1) 标签命名与取值枚举
    for lab in labels:
        lid = str(lab.get("id", ""))
        reasons = []
        if not lid or not pattern.match(lid):
            reasons.append("ID 不符合命名正则")
        if len(lid) > max_len:
            reasons.append("ID 超过最大长度 %d" % max_len)
        for part in lid.split("-"):
            if part.lower() in reserved:
                reasons.append("命中保留词 '%s'" % part)
        if reasons:
            naming_violations.append({"id": lid, "reasons": reasons})
            verdicts.append({"item": "标签 ID %s" % lid, "verdict": FAIL,
                             "basis": "依据：config/rules.json → naming",
                             "detail": "；".join(reasons)})

        vals = lab.get("values")
        vreasons = []
        if not isinstance(vals, list) or not vals:
            vreasons.append("取值枚举为空")
        else:
            seen = set()
            types = set()
            for v in vals:
                sk = json.dumps(v, ensure_ascii=False, sort_keys=True)
                if sk in seen:
                    vreasons.append("枚举值重复：%s" % sk)
                seen.add(sk)
                types.add(type(v).__name__)
            if len(types) > 1:
                vreasons.append("枚举值类型混杂：%s" % "/".join(sorted(types)))
        if vreasons:
            enum_issues.append({"id": lid, "reasons": vreasons})
            verdicts.append({"item": "标签取值 %s" % lid, "verdict": FAIL,
                             "basis": "依据：domain-a-taxonomy-rules.md 第三节",
                             "detail": "；".join(vreasons)})

    # 2) 跨文件口径取值
    groups = {}
    for d in decls:
        k = normalize_key(d.get("key", ""), aliases)
        groups.setdefault(k, []).append(d)
    for key, items in groups.items():
        by_value = {}
        for it in items:
            sk = json.dumps(it.get("value"), ensure_ascii=False, sort_keys=True)
            by_value.setdefault(sk, []).append(it)
        if len(by_value) <= 1:
            continue
        # v1.2：先排除「仅书写格式不同」。归一后仍不同才按值漂移判不通过。
        normalized = {normalize_value(json.loads(v)) for v in by_value}
        if len(normalized) == 1:
            format_only.append({"normalized_key": key,
                                "values": [json.loads(v) for v in by_value]})
            verdicts.append({
                "item": "口径键 %s" % key, "verdict": REVIEW,
                "basis": "依据：verdict-taxonomy.md 第八节（冲突不属四类）",
                "detail": "多个取值仅书写格式不同（全角／空格／乘号），不属四类漂移；"
                          "须人工统一写法并指定单一事实源，不临场发明第五类",
            })
            continue
        conflicts.append({
            "normalized_key": key,
            "drift_type": drift_types[0],
            "priority": priority.index(drift_types[0]) if drift_types[0] in priority else 99,
            "values": [{"value": json.loads(v), "files": [i.get("file", "") for i in its]}
                       for v, its in by_value.items()],
        })
        verdicts.append({
            "item": "口径键 %s" % key, "verdict": FAIL,
            "basis": "依据：domain-a-taxonomy-rules.md 第四节（值漂移）",
            "detail": "同一口径键出现 %d 个不同取值，须回到单一事实源定值" % len(by_value),
            "drift_type": drift_types[0],
        })

    # 3) 分域禁用词（v1.2.2：仅 B 域执行；A 域不做属性认定、不出合规结论）
    if not is_b:
        verdicts.append({
            "item": "域隔离", "verdict": REVIEW,
            "basis": "依据：SKILL.md 工作流程第 1 条（先分流）",
            "detail": "本任务为 A 域口径治理，不采信属性认定、不执行 B 域分域禁用词判定"
                      + ("；输入携带 scope=「%s」已忽略，须另行分流后认定" % scope_in_input
                         if scope_in_input else ""),
        })
    elif not scope:
        verdicts.append({"item": "属性认定", "verdict": REVIEW,
                         "basis": "依据：domain-b-label-compliance.md 第一节",
                         "detail": "B 域未提供 scope，未做分域禁用词检查；须先做产品属性认定"})
    else:
        for d in decls:
            text = " ".join(str(d.get(f, "")) for f in ("key", "value", "text") if d.get(f) is not None)
            for w in active_words:
                if w and w in text:
                    banned_hits.append({"file": d.get("file", ""), "word": w,
                                       "scope": scope, "context": text[:120]})
        if banned_hits:
            verdicts.append({"item": "分域禁用词（%s）" % scope, "verdict": FAIL,
                             "basis": "依据：config/rules.json → banned_label_words_scope.%s" % scope,
                             "detail": "命中 %d 处，须逐句核适用范围" % len(banned_hits)})
        else:
            verdicts.append({"item": "分域禁用词（%s）" % scope, "verdict": PASS,
                             "basis": "依据：config/rules.json → banned_label_words_scope.%s" % scope,
                             "detail": "所选词表未命中；不构成整句合规结论"})

    if not labels and not decls:
        verdicts.append({"item": "输入", "verdict": REVIEW,
                         "basis": "依据：SKILL.md 输入表",
                         "detail": "labels 与 declarations 均为空，无可核查内容"})

    checked_items = len(labels) + len(decls) + len(groups) + 1
    report = {
        "meta": {
            "version": VERSION,
            "script_ran": True,
            "domain": domain,
            "scope": scope or "未指定",
            "scope_in_input": scope_in_input,
            "scope_ignored": bool(scope_in_input and not is_b),
            "total_labels": len(labels),
            "total_declarations": len(decls),
            "normalized_keys": len(groups),
            "checked_items": checked_items,
            "rules_note": "规则来自 config/rules.json；脚本只查结构与一致性，不判定合法合规。",
        },
        "summary": {
            "conflicts": len(conflicts),
            "format_only": len(format_only),
            "naming_violations": len(naming_violations),
            "enum_issues": len(enum_issues),
            "banned_hits": len(banned_hits),
            "pass": sum(1 for v in verdicts if v["verdict"] == PASS),
            "fail": sum(1 for v in verdicts if v["verdict"] == FAIL),
            "review": sum(1 for v in verdicts if v["verdict"] == REVIEW),
        },
        "conflicts": conflicts,
        "format_only": format_only,
        "naming_violations": naming_violations,
        "enum_issues": enum_issues,
        "banned_hits": banned_hits,
        "verdicts": verdicts,
    }
    return report


def render_markdown(report):
    m = report["meta"]
    s = report["summary"]
    lines = [
        "【执行声明】脚本：已运行（%d 项）｜未运行（人工逐条）" % m["checked_items"],
        "",
        "# 标签口径一致性报告（脚本部分）",
        "",
        "- 版本：%s ｜ 任务域：%s" % (m["version"], m["domain"]),
        "- 属性认定：%s%s" % (
            m["scope"],
            "（输入携带 scope=「%s」已忽略，A 域不采信）" % m["scope_in_input"]
            if m.get("scope_ignored") else ""),
        "- 标签 %d 个 ｜ 口径声明 %d 条 ｜ 归一后口径键 %d 组 ｜ 仅格式差异 %d 组"
        % (m["total_labels"], m["total_declarations"], m["normalized_keys"], s["format_only"]),
        "- 结论：通过 %d ｜ 不通过 %d ｜ 需人工复核 %d" % (s["pass"], s["fail"], s["review"]),
        "",
        "> %s" % m["rules_note"],
        "",
        "## 逐项结论",
        "",
        "| 核查项 | 判定 | 依据 | 说明 |",
        "|---|---|---|---|",
    ]
    for v in report["verdicts"]:
        lines.append("| %s | `%s` | %s | %s |" %
                     (v["item"], v["verdict"], v["basis"], v["detail"].replace("|", "\\|")))
    if report["conflicts"]:
        lines += ["", "## 口径冲突明细", "", "| 口径键 | 漂移类型 | 取值 | 涉及文件 |", "|---|---|---|---|"]
        for c in report["conflicts"]:
            for v in c["values"]:
                lines.append("| %s | %s | %s | %s |" %
                             (c["normalized_key"], c["drift_type"],
                              str(v["value"]).replace("|", "\\|"), ", ".join(v["files"])))
    if report["format_only"]:
        lines += ["", "## 仅书写格式差异（不属四类漂移，需人工统一写法）", "",
                  "| 口径键 | 取值 |", "|---|---|"]
        for c in report["format_only"]:
            lines.append("| %s | %s |" %
                         (c["normalized_key"], " ／ ".join(str(v).replace("|", "\\|")
                                                          for v in c["values"])))
    if report["banned_hits"]:
        lines += ["", "## 分域禁用词命中", "", "| 文件 | 词 | 适用域 | 上下文 |", "|---|---|---|---|"]
        for h in report["banned_hits"]:
            lines.append("| %s | %s | %s | %s |" %
                         (h["file"], h["word"], h["scope"], h["context"].replace("|", "\\|")))
    lines += [
        "",
        "## 脚本边界（须如实转述）",
        "",
        "- 能做：命名正则、枚举重复性／类型一致性、同口径键取值冲突、书写格式差异识别、分域禁用词命中。",
        "- 不能做：语义是否等价、整句是否构成违规宣称、法规现行效力、哪个口径是权威、待办句是不是口径值。",
        "- 中文口径键与英文口径键按各自字符归一；不同语言的同义键须写进 `key_aliases`，脚本不猜。",
        "- 定性由模型按 `references/` 规则包完成；删改与放行由用户拍板。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="标签口径一致性校验（只查结构，不判定合规）")
    ap.add_argument("--input", required=True, help="declarations.json")
    ap.add_argument("--config", required=True, help="config/rules.json")
    ap.add_argument("--output-md", default="", help="Markdown 报告路径")
    ap.add_argument("--output-json", default="", help="JSON 报告路径")
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write("❌ 输入或配置读取失败，脚本不静默回退：%s\n" % exc)
        return 2

    if not isinstance(data, dict) or not isinstance(config, dict):
        sys.stderr.write("❌ 输入与配置都必须是 JSON 对象\n")
        return 2

    report = analyze(data, config)
    md = render_markdown(report)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
