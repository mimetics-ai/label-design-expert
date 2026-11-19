#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签视觉设计技能 · 14 条冒烟断言。运行：python self_check.py"""
import copy
import json
import sys
from pathlib import Path

from check_visual_spec import analyze, contrast_ratio, PASS, FAIL, REVIEW
from render_label_proof import render_svg, build_tokens

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG = json.loads((ROOT / "config" / "visual-rules.json").read_text(encoding="utf-8"))
BASE = json.loads((ROOT / "examples" / "label-proof-input.json").read_text(encoding="utf-8"))

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))


def has_fail(report, keyword):
    return any(v["verdict"] == FAIL and keyword in v["item"] for v in report["verdicts"])


def variant(mutator):
    d = copy.deepcopy(BASE)
    mutator(d)
    return analyze(d, CONFIG)


r = analyze(BASE, CONFIG)

# 01 对比度公式
check("01 纯黑/纯白对比度 = 21:1", abs(contrast_ratio("#000000", "#FFFFFF") - 21.0) < 0.01)
# 02 中灰对比度
check("02 #777777/#FFFFFF ≈ 4.48:1", abs(contrast_ratio("#777777", "#FFFFFF") - 4.48) < 0.05)
# 03 示例无阻断项
check("03 示例版式无「不通过」", r["summary"]["fail"] == 0,
      "通过 %d / 复核 %d" % (r["summary"]["pass"], r["summary"]["review"]))
# 04 示例保留边界复核项
check("04 示例保留「需人工复核」边界项", r["summary"]["review"] >= 2)
# 05 低对比度
check("05 低对比度被拦",
      has_fail(variant(lambda d: d["regions"][0].update(fg="#EEEEEE")), "对比度"))
# 06 字号不足
check("06 强制项字号不足被拦",
      has_fail(variant(lambda d: [x.update(font_mm=1.0) for x in d["regions"]
                                  if x["type"] == "mandatory"]), "字号"))
# 07 安全边距
check("07 超出安全边距被拦",
      has_fail(variant(lambda d: d["regions"][0].update(x=1)), "安全边距"))
# 08 商标面积
check("08 商标面积超 1/9 被拦",
      has_fail(variant(lambda d: [x.update(w=40, h=20) for x in d["regions"]
                                  if x["type"] == "trademark"]), "商标面积"))
# 09 商标四角
check("09 商标不在四角被拦",
      has_fail(variant(lambda d: [x.update(x=40, y=25, w=13, h=9) for x in d["regions"]
                                  if x["type"] == "trademark"]), "商标四角"))
# 10 二维码边长
check("10 二维码边长不足被拦",
      has_fail(variant(lambda d: [x.update(w=10, h=15) for x in d["regions"]
                                  if x["type"] == "qrcode"]), "二维码边长"))
# 11 二维码静区
check("11 二维码静区不足被拦",
      has_fail(variant(lambda d: [x.update(quiet_zone_mm=1.0) for x in d["regions"]
                                  if x["type"] == "qrcode"]), "二维码静区"))
# 12 印刷总墨量
check("12 TAC 超标被拦",
      has_fail(variant(lambda d: d["print"].update(tac_percent=350)), "总墨量"))
# 13 SVG 渲染
svg = render_svg(BASE, annotate=True)
all_ids = [x["id"] for x in BASE["regions"]]
check("13 SVG 含 viewBox 与全部区块 ID",
      "viewBox" in svg and all(i in svg for i in all_ids))
# 14 令牌与三态
tokens = build_tokens(BASE)
check("14 设计令牌可序列化且结论封闭三态",
      "--label-width" in tokens and json.loads(json.dumps(tokens))["--bleed"] == "3mm"
      and {v["verdict"] for v in r["verdicts"]} <= {PASS, FAIL, REVIEW})

passed = sum(1 for _, ok, _ in results if ok)
print("标尺 · 标签视觉设计器自检 v1.1.0")
print("-" * 50)
for name, ok, extra in results:
    print("%s %s%s" % ("✅" if ok else "❌", name, ("｜" + extra) if extra else ""))
print("-" * 50)
print("结果：%d/%d 通过" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
