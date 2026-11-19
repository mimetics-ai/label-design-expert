#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签版式校验器。

只算几何与数值：WCAG 对比度、字号/视距下限、安全边距、商标面积与四角、
二维码边长与静区、印刷 TAC/线宽/K 值/dpi、五层信息层级。
不判断文案是否合规、商标图样是否与注册证一致、配色是否符合品牌。

v1.2.0（2026-11-19 桌面标签实测回灌）新增三项可计算校验：
  - 文案声明—版面元素一致性（写「扫码获取」却无二维码 → 不通过）；
  - 中文断行禁则（行首标点 / 行尾开括号，基于实测回灌的 wrapped_lines）；
  - 占位区块声明（占位 ≠ 已具备，标需人工复核）。

用法：
  python check_visual_spec.py --input label-proof-input.json \
      --config config/visual-rules.json \
      --output-md visual-report.md --output-json visual-report.json
"""
import argparse
import json
import sys
from pathlib import Path

VERSION = "1.2.2"
PASS, FAIL, REVIEW = "通过", "不通过", "需人工复核"

# 中文排版禁则：行首不得出现收束标点，行尾不得出现开启标点/引号。
FORBIDDEN_LINE_HEAD = "。，、；：！？）】》」』”’%‰℃"
FORBIDDEN_LINE_TAIL = "（【《「『“‘"


def hex_to_rgb(value):
    s = str(value).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError("invalid hex color: %s" % value)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def srgb_linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(color):
    r, g, b = hex_to_rgb(color)
    return 0.2126 * srgb_linear(r) + 0.7152 * srgb_linear(g) + 0.0722 * srgb_linear(b)


def contrast_ratio(fg, bg):
    la, lb = luminance(fg), luminance(bg)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def analyze(data, config):
    label = data.get("label") or {}
    regions = data.get("regions") or []
    pr = data.get("print") or {}
    W = float(label.get("width_mm", 0))
    H = float(label.get("height_mm", 0))
    bleed = float(label.get("bleed_mm", (config.get("page") or {}).get("bleed_mm", 3)))
    safe = float(label.get("safe_mm", (config.get("page") or {}).get("safe_mm", 5)))
    typ = config.get("type") or {}
    tm = config.get("trademark") or {}
    codes = config.get("codes") or {}
    print_rules = config.get("print") or {}
    view_distance = float(label.get("view_distance_mm", typ.get("view_distance_mm", 400)))
    view_min = view_distance * float(typ.get("view_distance_factor", 0.003))
    large_mm = float(typ.get("large_text_font_mm", 4.0))
    contrast_min = typ.get("contrast_ratio") or {}
    min_font = typ.get("min_font_mm") or {}
    typo = config.get("typography") or {}
    forbidden_head = set(str(typo.get("forbidden_line_head", FORBIDDEN_LINE_HEAD)))
    forbidden_tail = set(str(typo.get("forbidden_line_tail", FORBIDDEN_LINE_TAIL)))

    verdicts = []

    def add(item, verdict, detail, basis, metric=None):
        row = {"item": item, "verdict": verdict, "detail": detail, "basis": basis}
        if metric is not None:
            row["metric"] = metric
        verdicts.append(row)

    if W <= 0 or H <= 0:
        add("成品尺寸", REVIEW, "未提供有效的 W×H，几何校验不可计算", "依据：SKILL.md 输入表")
        W, H = W or 1.0, H or 1.0

    # 1) 对比度 / 字号 / 安全边距（逐区块）
    for r in regions:
        rid, rtype = r.get("id", ""), r.get("type", "body")
        if rtype == "qrcode":
            continue
        fg, bg = r.get("fg", "#000000"), r.get("bg", "#FFFFFF")
        try:
            cr = contrast_ratio(fg, bg)
            font = float(r.get("font_mm", 0))
            need = float(contrast_min.get("large_text", 3.0)) if font >= large_mm \
                else float(contrast_min.get("body", 4.5))
            add("对比度 %s" % rid, PASS if cr >= need else FAIL,
                "%.2f:1（要求 ≥ %.1f:1，字号 %gmm）" % (cr, need, font),
                "依据：visual-spec-rules.md 第三节（WCAG 2.1）", round(cr, 3))
        except ValueError as exc:
            add("对比度 %s" % rid, REVIEW, "颜色值无法解析：%s" % exc,
                "依据：visual-spec-rules.md 第三节")

        font = float(r.get("font_mm", 0))
        type_min = float(min_font.get(rtype, min_font.get("body", 1.8)))
        required = max(type_min, view_min)
        add("字号 %s" % rid, PASS if font >= required else FAIL,
            "%gmm（要求 ≥ %gmm = max(类型 %g, 视距 %g)）" % (font, required, type_min, view_min),
            "依据：visual-spec-rules.md 第三节", font)

    for r in regions:
        rid = r.get("id", "")
        try:
            x, y = float(r.get("x", 0)), float(r.get("y", 0))
            w, h = float(r.get("w", 0)), float(r.get("h", 0))
        except (TypeError, ValueError):
            add("安全边距 %s" % rid, REVIEW, "坐标不是数值，无法判定", "依据：visual-spec-rules.md 第二节")
            continue
        inside = x >= safe and y >= safe and x + w <= W - safe and y + h <= H - safe
        add("安全边距 %s" % rid, PASS if inside else FAIL,
            "x=%g y=%g w=%g h=%g ｜ 安全区 x≥%g, y≥%g, 右≤%g, 下≤%g" %
            (x, y, w, h, safe, safe, W - safe, H - safe),
            "依据：visual-spec-rules.md 第二节", inside)

    # 2) 商标：面积、四角、字号
    trademarks = [r for r in regions if r.get("type") == "trademark"]
    names = [r for r in regions if r.get("type") == "product-name"]
    if not trademarks:
        add("商标区块", REVIEW, "未声明商标区块；若本标签无需商标，请确认适用性问题",
            "依据：visual-spec-rules.md 第四节")
    for r in trademarks:
        w, h = float(r.get("w", 0)), float(r.get("h", 0))
        ratio = (w * h) / (W * H)
        max_ratio = float(tm.get("max_area_ratio", 0.1111))
        add("商标面积 %s" % r.get("id", ""), PASS if ratio <= max_ratio else FAIL,
            "%.2f%%（上限 %.2f%%）" % (ratio * 100, max_ratio * 100),
            "依据：海巍驱蚊咨询报告 §4.3.1（规则来源域适用性须复核）", round(ratio, 5))
        x, y = float(r.get("x", 0)), float(r.get("y", 0))
        z = float(tm.get("corner_zone_mm", 20))
        top = y <= z
        bottom = y + h >= H - z
        left = x <= z
        right = x + w >= W - z
        corner = (top or bottom) and (left or right)
        if tm.get("corners_only", True):
            add("商标四角 %s" % r.get("id", ""), PASS if corner else FAIL,
                "x=%g y=%g w=%g h=%g ｜ 角区 %gmm" % (x, y, w, h, z),
                "依据：海巍驱蚊咨询报告 §4.3.1（规则来源域适用性须复核）", corner)
        if names:
            max_name_font = max(float(n.get("font_mm", 0)) for n in names)
            tf = float(r.get("font_mm", 0))
            add("商标字号 %s" % r.get("id", ""), PASS if tf <= max_name_font else FAIL,
                "%gmm（产品名 %gmm）" % (tf, max_name_font),
                "依据：海巍驱蚊咨询报告 §4.3.1（规则来源域适用性须复核）")

    # 3) 二维码：边长、静区
    qrs = [r for r in regions if r.get("type") == "qrcode"]
    if not qrs:
        add("追溯二维码", REVIEW, "未声明二维码区块；若本标签无需追溯码，请确认适用性问题",
            "依据：visual-spec-rules.md 第四节")
    for r in qrs:
        side = min(float(r.get("w", 0)), float(r.get("h", 0)))
        need = float(codes.get("qr_min_side_mm", 15))
        add("二维码边长 %s" % r.get("id", ""), PASS if side >= need else FAIL,
            "%gmm（要求 ≥ %gmm）" % (side, need),
            "依据：visual-spec-rules.md 第四节", side)
        modules = float(codes.get("qr_modules_per_side", 21))
        quiet_need = float(codes.get("qr_quiet_zone_modules", 4)) * (side / modules)
        quiet = float(r.get("quiet_zone_mm", 0))
        add("二维码静区 %s" % r.get("id", ""), PASS if quiet >= quiet_need else FAIL,
            "%gmm（要求 ≥ %.2fmm = %g 模块 × %gmm）" %
            (quiet, quiet_need, codes.get("qr_quiet_zone_modules", 4), side / modules),
            "依据：visual-spec-rules.md 第四节", round(quiet, 3))

    # 4) 印刷
    tac = pr.get("tac_percent")
    max_tac = float(print_rules.get("max_tac_percent", 300))
    add("总墨量 TAC", (PASS if float(tac) <= max_tac else FAIL) if tac is not None else REVIEW,
        "%s%%（上限 %g%%）" % (tac, max_tac) if tac is not None else "未提供，需印厂确认",
        "依据：印前预检规则")
    line = pr.get("min_line_mm")
    min_line = float(print_rules.get("min_line_mm", 0.2))
    add("最小线宽", (PASS if float(line) >= min_line else FAIL) if line is not None else REVIEW,
        "%smm（下限 %gmm）" % (line, min_line) if line is not None else "未提供，需印厂确认",
        "依据：印前预检规则")
    k = pr.get("black_text_k")
    need_k = print_rules.get("black_text_k", 100)
    # v1.2.1：数值明确越界判「不通过」，与 TAC/线宽/dpi 一致；未提供才判「需人工复核」。
    # 「需印厂确认」由独立的「印厂规范」复核项承载，不在数值判据里重复。
    add("黑色文字 K 值", (PASS if k == need_k else FAIL) if k is not None else REVIEW,
        "%s（要求 %s%% K）" % (k, need_k) if k is not None else "未提供，需印厂确认",
        "依据：印前预检规则")
    dpi = pr.get("resolution_dpi")
    add("图像分辨率", (PASS if float(dpi) >= float(print_rules.get("min_resolution_dpi", 300)) else FAIL)
        if dpi is not None else REVIEW,
        "%sdpi（下限 %sdpi）" % (dpi, print_rules.get("min_resolution_dpi", 300)),
        "依据：印前预检规则")

    # 5) 信息层级：L1 不小于 L4
    mand = [r for r in regions if r.get("type") == "mandatory"]
    claims = [r for r in regions if r.get("type") == "claim"]
    if not mand:
        add("信息层级 L1", FAIL, "缺少 mandatory 强制标注区块",
            "依据：visual-spec-rules.md 第一节")
    elif claims:
        mmin = min(float(r.get("font_mm", 0)) for r in mand)
        cmax = max(float(r.get("font_mm", 0)) for r in claims)
        add("信息层级 L1 ≥ L4", PASS if mmin >= cmax else FAIL,
            "强制项最小 %gmm ｜ 功效项最大 %gmm" % (mmin, cmax),
            "依据：visual-spec-rules.md 第一节")

    # 6) 文案声明—版面元素一致性（v1.2）
    # 实测来源：背标印「扫码获取 SDS」但版面无二维码 → 标签自述与版面不一致。
    copy_refs = data.get("copy_references") or []
    region_ids = [str(r.get("id", "")) for r in regions]
    need_map = {
        "qrcode": bool(qrs),
        "qr": bool(qrs),
        "emergency-phone": any("emergency" in i or "phone" in i for i in region_ids),
    }
    for ref in copy_refs:
        ref = str(ref).lower()
        if ref in need_map:
            ok = need_map[ref]
            add("文案—版面一致性 %s" % ref, PASS if ok else FAIL,
                "文案声明引用 %s；版面%s对应区块" % (ref, "存在" if ok else "缺少"),
                "依据：visual-spec-rules.md 第十节（文案—版面逻辑一致性）")
        else:
            add("文案—版面一致性 %s" % ref, REVIEW,
                "未内置该引用类型的判据，须人工核对版面是否具备对应元素",
                "依据：visual-spec-rules.md 第十节")

    # 7) 中文断行禁则（v1.2，基于实测回灌的 wrapped_lines）
    for r in regions:
        lines = r.get("wrapped_lines") or []
        if not isinstance(lines, list) or not lines:
            continue
        bad = [ln for ln in lines
               if str(ln).strip() and (str(ln).lstrip()[0] in forbidden_head
                                      or str(ln).rstrip()[-1] in forbidden_tail)]
        add("中文断行禁则 %s" % r.get("id", ""), FAIL if bad else PASS,
            "%d 行，行首/行尾标点违规 %d 处%s" %
            (len(lines), len(bad), ("｜" + str(bad[0])[:30]) if bad else ""),
            "依据：visual-spec-rules.md 第十节（中文禁则）")

    # 8) 占位 ≠ 已具备（v1.2）
    placeholders = [r for r in regions if r.get("placeholder") is True]
    if placeholders:
        add("占位区块声明", REVIEW,
            "%d 个区块为占位（%s）；不得计为已具备功能，须列「待业主拍板」" %
            (len(placeholders), ", ".join(str(r.get("id", "")) for r in placeholders)),
            "依据：visual-spec-rules.md 第十节（占位 ≠ 已具备）")

    # 9) 边界：合规与印厂规范交叉引用
    if not data.get("compliance_checked"):
        add("文案合规交叉引用", REVIEW,
            "本次仅做版式，文案合规未核；版式通过 ≠ 文案合规",
            "依据：SKILL.md 纪律 1")
    if not data.get("print_spec_source"):
        add("印厂规范", REVIEW,
            "未提供印厂规范，采用 config 默认值，需印厂确认",
            "依据：visual-spec-rules.md 第二节")

    report = {
        "meta": {
            "version": VERSION, "script_ran": True,
            "size_mm": [W, H], "bleed_mm": bleed, "safe_mm": safe,
            "view_distance_mm": view_distance, "regions": len(regions),
            "checked_items": len(verdicts),
            "rules_note": "脚本只算几何与数值，不判断文案合规、商标图样一致性与品牌表现。样张是设计稿不是印稿。",
        },
        "summary": {
            "pass": sum(1 for v in verdicts if v["verdict"] == PASS),
            "fail": sum(1 for v in verdicts if v["verdict"] == FAIL),
            "review": sum(1 for v in verdicts if v["verdict"] == REVIEW),
        },
        "verdicts": verdicts,
    }
    return report


def render_markdown(report):
    m, s = report["meta"], report["summary"]
    lines = [
        "【执行声明】脚本：已运行（%d 项）｜未运行（人工逐条）" % m["checked_items"],
        "",
        "# 标签版式校验报告（脚本部分）",
        "",
        "- 版本：%s ｜ 成品 %g×%gmm ｜ 出血 %gmm ｜ 安全边距 %gmm ｜ 视距 %gmm" %
        (m["version"], m["size_mm"][0], m["size_mm"][1], m["bleed_mm"], m["safe_mm"],
         m["view_distance_mm"]),
        "- 区块 %d 个 ｜ 结论：通过 %d ｜ 不通过 %d ｜ 需人工复核 %d" %
        (m["regions"], s["pass"], s["fail"], s["review"]),
        "",
        "> %s" % m["rules_note"],
        "",
        "| 核查项 | 判定 | 依据 | 说明 |",
        "|---|---|---|---|",
    ]
    for v in report["verdicts"]:
        lines.append("| %s | `%s` | %s | %s |" %
                     (v["item"], v["verdict"], v["basis"], v["detail"].replace("|", "\\|")))
    lines += [
        "",
        "## 脚本边界（须如实转述）",
        "",
        "- 能做：WCAG 对比度、字号/视距下限、安全边距、商标面积与四角、二维码边长与静区、"
        "TAC/线宽/K 值、信息层级、文案声明—版面元素一致性、中文断行禁则。",
        "- 不能做：文案合规、商标图样一致性、配色品牌适配、扫码实测、实际印刷效果、"
        "字体真实字形测量（wrapped_lines 须由设计脚本实测回灌）。",
        "- 版式通过 ≠ 文案合规；占位 ≠ 已具备；法规现行有效性与印厂工艺须人工复核。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="标签版式校验（只算几何与数值，不判合规）")
    ap.add_argument("--input", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--output-md", default="")
    ap.add_argument("--output-json", default="")
    args = ap.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write("❌ 输入或配置读取失败，脚本不静默回退：%s\n" % exc)
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
