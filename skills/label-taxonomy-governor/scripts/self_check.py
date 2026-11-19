#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冒烟断言。运行：python self_check.py

断言覆盖：口径键归一化（含中文键）、值漂移检出、书写格式差异识别、
命名正则、保留词、长度、枚举重复／类型混杂、分域禁用词命中与不误报、
三态封闭、执行声明、报告渲染、覆盖度与设计能力指标。
"""
import json
import sys
from pathlib import Path

from check_label_consistency import (analyze, normalize_key, normalize_value,
                                     render_markdown, VERSION, PASS, FAIL, REVIEW)
from check_taxonomy_coverage import analyze as analyze_coverage
from check_taxonomy_coverage import render_markdown as render_coverage_markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE.parent / "config" / "rules.json").read_text(encoding="utf-8"))
ALIASES = {normalize_key(k, {}): v for k, v in CONFIG["key_aliases"].items()}

BASE = {
    "domain": "B",
    "scope": "化妆品",
    "labels": [
        {"id": "integrity-level", "name": "完整性等级", "values": ["Low", "Medium", "High"]},
    ],
    "declarations": [
        {"file": "gate-manifest.json", "key": "env.expectedIntegrity", "value": "Medium"},
        {"file": "label-guard.mjs", "key": "EXPECTED_INTEGRITY", "value": "Medium"},
        {"file": "M2-plan.md", "key": "expectedIntegrity", "value": "Low"},
    ],
}

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))


r = analyze(BASE, CONFIG)

# 1 口径键归一化
check("01 env.expectedIntegrity 与 EXPECTED_INTEGRITY 归一到同一键",
      normalize_key("env.expectedIntegrity", ALIASES) == normalize_key("EXPECTED_INTEGRITY", ALIASES))

# 2 值漂移被检出
check("02 两种取值检出 1 组冲突", len(r["conflicts"]) == 1)

# 3 漂移类型
check("03 冲突定性为值漂移",
      bool(r["conflicts"]) and r["conflicts"][0]["drift_type"] == "值漂移")

# 4 定位到漂移文件
check("04 冲突明细定位到 M2-plan.md",
      bool(r["conflicts"]) and any(
          "M2-plan.md" in f
          for v in r["conflicts"][0]["values"] for f in v["files"]))

# 5 全一致时无冲突
consistent = dict(BASE)
consistent["declarations"] = [dict(d, value="Medium") for d in BASE["declarations"]]
check("05 三处取值一致时 0 冲突", len(analyze(consistent, CONFIG)["conflicts"]) == 0)

# 6 合法 ID 不报命名违规
check("06 integrity-level 通过命名检查", len(r["naming_violations"]) == 0)

# 7 保留词被拦
bad_name = {"labels": [{"id": "other-tag", "values": ["a"]}], "declarations": []}
check("07 other-tag 命中保留词被拦", len(analyze(bad_name, CONFIG)["naming_violations"]) == 1)

# 8 超长 ID 被拦
long_name = {"labels": [{"id": "a" * 45, "values": ["a"]}], "declarations": []}
check("08 超长 ID 被拦", len(analyze(long_name, CONFIG)["naming_violations"]) == 1)

# 9 枚举重复被检出
dup = {"labels": [{"id": "stage", "values": ["a", "a"]}], "declarations": []}
check("09 枚举重复被检出", len(analyze(dup, CONFIG)["enum_issues"]) == 1)

# 10 类型混杂被检出
mixed = {"labels": [{"id": "stage", "values": ["Low", 2]}], "declarations": []}
check("10 枚举类型混杂被检出", len(analyze(mixed, CONFIG)["enum_issues"]) == 1)

# 11 分域禁用词命中
banned = {"domain": "B", "scope": "化妆品", "labels": [],
          "declarations": [{"file": "label.txt", "key": "copy", "text": "本品可防蚊，纯植物配方"}]}
rb = analyze(banned, CONFIG)
check("11 化妆品域命中「防蚊」「纯植物」", len(rb["banned_hits"]) >= 2)

# 12 非适用域的词不误报
no_false = {"domain": "B", "scope": "化妆品", "labels": [],
            "declarations": [{"file": "label.txt", "key": "copy", "text": "含铲除配方说明"}]}
check("12 农药域「铲除」不在化妆品词表，不误报",
      len(analyze(no_false, CONFIG)["banned_hits"]) == 0)

# 附加：三态封闭 + 执行声明（不占 12 条编号）
all_verdicts = {v["verdict"] for v in r["verdicts"]}
check("附A 结论只出现三态", all_verdicts <= {PASS, FAIL, REVIEW})
check("附B 执行声明首行存在", render_markdown(r).startswith("【执行声明】脚本：已运行"))
check("附C meta.script_ran = True", r["meta"]["script_ran"] is True)
check("附D B 域未指定 scope 时属性认定标需人工复核",
      any(v["verdict"] == REVIEW and v["item"] == "属性认定"
          for v in analyze({"domain": "B", "labels": [], "declarations": []}, CONFIG)["verdicts"]))

# v1.1.0 · 覆盖度与设计能力断言
EXAMPLE = json.loads((HERE.parent / "examples" / "taxonomy-design-example.json").read_text(encoding="utf-8"))
rc = analyze_coverage(EXAMPLE, CONFIG)
check("附E 覆盖率计算正确（11/11 全有标签）", rc["metrics"]["coverage_rate"] == 1.0)
check("附F 互斥与依赖两类冲突都被检出",
      {c["type"] for c in rc["relation_conflicts"]} >= {"exclusive", "requires"})
check("附G 互斥冲突定位到刻意反例 c11",
      any(c["sample"] == "c11" and c["type"] == "exclusive" for c in rc["relation_conflicts"]))
orphan = {"labels": [{"id": "d", "values": ["a"]}],
          "samples": [{"id": "s1", "labels": {"d": "b"}}]}
check("附H 未登记取值被检出", len(analyze_coverage(orphan, CONFIG)["orphan_values"]) == 1)
check("附I 覆盖度报告首行有执行声明",
      render_coverage_markdown(rc).startswith("【执行声明】脚本：已运行"))
check("附J 覆盖度结论只出现三态",
      {v["verdict"] for v in rc["verdicts"]} <= {PASS, FAIL, REVIEW})

# v1.2.0 · 2026-11-19 桌面标签实测回灌断言
check("附K 中文口径键不再被归一成空串",
      normalize_key("产品数量", ALIASES) == "产品数量"
      and normalize_key("产品数量", ALIASES) != normalize_key("供应商地址", ALIASES))
chinese = {"domain": "B", "scope": "化妆品", "labels": [],
           "declarations": [
               {"file": "a.md", "key": "产品数量", "value": "66"},
               {"file": "b.md", "key": "产品数量", "value": "66"},
               {"file": "c.md", "key": "供应商地址", "value": "广州"},
           ]}
rcn = analyze(chinese, CONFIG)
check("附L 中文 key 正确分组且不误报冲突",
      rcn["meta"]["normalized_keys"] == 2 and len(rcn["conflicts"]) == 0)
fmt = {"domain": "B", "scope": "化妆品", "labels": [],
       "declarations": [
           {"file": "a.py", "key": "resinBackLabelSize", "value": "210x194mm"},
           {"file": "b.md", "key": "resinBackLabelSize", "value": "210×194 mm"},
       ]}
rf = analyze(fmt, CONFIG)
check("附M 仅书写格式差异判需人工复核、不发明第五类",
      len(rf["format_only"]) == 1 and len(rf["conflicts"]) == 0
      and any(v["verdict"] == REVIEW and "书写格式" in v["detail"] for v in rf["verdicts"]))
real_drift = {"domain": "B", "scope": "化妆品", "labels": [],
              "declarations": [
                  {"file": "a.md", "key": "productCount", "value": "66"},
                  {"file": "b.md", "key": "productCount", "value": "65"},
              ]}
check("附N 真实值漂移仍判不通过",
      len(analyze(real_drift, CONFIG)["conflicts"]) == 1)
check("附O 格式归一函数只归一书写、不吞数值",
      normalize_value("210×194 mm") == normalize_value("210x194mm")
      and normalize_value("66") != normalize_value("65"))
check("附P 报告列出归一后键组数与格式差异明细",
      "归一后口径键 2 组" in render_markdown(rcn)
      and "仅书写格式差异" in render_markdown(rf))

# v1.2.2 · 2026-11-20 线上 7 条实测回灌：A/B 域隔离，禁止臆造属性认定
a_mix = {"scope": "工业化学品", "labels": [],
         "declarations": [{"file": "spec.md", "key": "size", "value": "210×194 mm"}]}
ra = analyze(a_mix, CONFIG)
md_a = render_markdown(ra)
check("附Q A 域忽略输入 scope、不输出禁用词判定",
      ra["meta"]["domain"] == "A" and ra["meta"]["scope_ignored"] is True
      and ra["meta"]["scope"] == "未指定"
      and not any("分域禁用词" in v["item"] for v in ra["verdicts"]))
check("附R A 域报告显式写出域隔离与 scope 已忽略",
      "任务域：A" in md_a and "已忽略" in md_a and "工业化学品" in md_a)
check("附S A 域仍给需人工复核的域隔离项、不发明第四态",
      any(v["item"] == "域隔离" and v["verdict"] == REVIEW for v in ra["verdicts"])
      and {v["verdict"] for v in ra["verdicts"]} <= {PASS, FAIL, REVIEW})
check("附T 显式 B 域仍正常跑禁用词（不因隔离失效）",
      any("分域禁用词" in v["item"] for v in rb["verdicts"]))

passed = sum(1 for _, ok, _ in results if ok)
print("标尺 · 标签治理器自检 v%s" % VERSION)
print("-" * 46)
for name, ok, extra in results:
    print("%s %s%s" % ("✅" if ok else "❌", name, ("｜" + extra) if extra else ""))
print("-" * 46)
print("结果：%d/%d 通过" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
