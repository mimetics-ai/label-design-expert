#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签视觉设计技能 · 冒烟断言。运行：python self_check.py

覆盖：对比度、字号、安全边距、商标、二维码、印刷参数、SVG 渲染、设计令牌、
v1.2 新增的文案—版面一致性、中文断行禁则、占位声明与三态封闭。
"""
import copy
import json
import sys
from pathlib import Path

from check_visual_spec import analyze, contrast_ratio, PASS, FAIL, REVIEW
from render_label_proof import render_svg, build_tokens, wrap_cjk

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

# ---- v1.2.0 · 2026-11-19 桌面标签实测回灌断言 ----
w1 = wrap_cjk("预防措施远离热源。禁止吸烟", 8)
check("15 中文断行不产生孤行句号（句号并入上一行）",
      "预防措施远离热源。" in w1
      and not any(ln.lstrip().startswith("。") for ln in w1))
w2 = wrap_cjk("适用范围（工业用）说明", 5)
check("16 行尾开括号不留孤悬",
      not any(ln.rstrip().endswith("（") for ln in w2))

d_noqr = copy.deepcopy(BASE)
d_noqr["copy_references"] = ["qrcode"]
d_noqr["regions"] = [x for x in d_noqr["regions"] if x["type"] != "qrcode"]
check("17 文案写「扫码获取」但版面无二维码被拦",
      has_fail(analyze(d_noqr, CONFIG), "文案—版面一致性"))

d_withqr = copy.deepcopy(BASE)
d_withqr["copy_references"] = ["qrcode"]
check("18 文案声明与版面二维码一致时通过",
      any(v["verdict"] == PASS and "文案—版面一致性" in v["item"]
          for v in analyze(d_withqr, CONFIG)["verdicts"]))

d_badwrap = copy.deepcopy(BASE)
d_badwrap["regions"][0]["wrapped_lines"] = ["预防措施文本", "。禁止吸烟"]
check("19 行首标点被中文禁则拦下",
      has_fail(analyze(d_badwrap, CONFIG), "中文断行禁则"))

d_goodwrap = copy.deepcopy(BASE)
d_goodwrap["regions"][0]["wrapped_lines"] = ["预防措施文本。", "禁止吸烟"]
check("20 合法断行通过中文禁则",
      any(v["verdict"] == PASS and "中文断行禁则" in v["item"]
          for v in analyze(d_goodwrap, CONFIG)["verdicts"]))

d_ph = copy.deepcopy(BASE)
for x in d_ph["regions"]:
    if x["type"] == "qrcode":
        x["placeholder"] = True
check("21 占位区块标需人工复核且不计为已具备",
      any(v["verdict"] == REVIEW and "占位区块声明" in v["item"]
          for v in analyze(d_ph, CONFIG)["verdicts"]))

check("22 新增结论仍封闭三态",
      {v["verdict"] for v in analyze(d_noqr, CONFIG)["verdicts"]} <= {PASS, FAIL, REVIEW})

# ---- v1.2.1 · 印刷数值项三态判据统一（50 用例 × 50 轮验收用例 #34 实测发现） ----
check("23 K 值越界判不通过、未提供判需人工复核",
      has_fail(variant(lambda d: d["print"].update(black_text_k=80)), "K 值")
      and any(v["verdict"] == REVIEW and "K 值" in v["item"]
              for v in variant(lambda d: d["print"].pop("black_text_k", None))["verdicts"]))

passed = sum(1 for _, ok, _ in results if ok)
print("标尺 · 标签视觉设计器自检 v1.2.1")
print("-" * 50)
for name, ok, extra in results:
    print("%s %s%s" % ("✅" if ok else "❌", name, ("｜" + extra) if extra else ""))
print("-" * 50)
print("结果：%d/%d 通过" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
