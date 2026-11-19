#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签样张渲染器。

把视觉规格 JSON 渲染成 SVG 设计稿，并输出 CSS/JSON 设计令牌与可选 HTML 预览页。
样张是设计稿不是印稿：文案为占位符，不得直接下厂。

v1.2.0（2026-11-19 桌面标签实测回灌）新增 wrap_cjk()：
中文断行禁则——行首收束标点并入上一行、行尾开启标点移到下一行。
实测断行结果可经 wrapped_lines 回灌，由 check_visual_spec.py 复验。
等宽估算不替代字体测量，真实排版须以印厂/设计脚本实测为准。

用法：
  python render_label_proof.py --input label-proof-input.json \
      --output label-proof.svg --tokens-css tokens.css --tokens-json tokens.json \
      --output-html label-proof.html --annotate
"""
import argparse
import html
import json
import sys
from pathlib import Path

VERSION = "1.2.1"

FORBIDDEN_LINE_HEAD = "。，、；：！？）】》」』”’%‰℃"
FORBIDDEN_LINE_TAIL = "（【《「『“‘"


def wrap_cjk(text, max_chars):
    """按最大字符数断行，并应用中文禁则。

    实测来源：H100Z 背标真实改版时，逐字断行把句号「。」单独甩到一行；
    加入禁则后四段行数 8→7，底部安全余量同时改善。
    """
    s = str(text)
    if max_chars < 1:
        return [s] if s else []
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            if cur:
                lines.append(cur)
            cur = ""
            continue
        if len(cur) >= max_chars:
            if ch in FORBIDDEN_LINE_HEAD:
                cur += ch
                lines.append(cur)
                cur = ""
                continue
            if cur and cur[-1] in FORBIDDEN_LINE_TAIL:
                tail = cur[-1]
                cur = cur[:-1]
                lines.append(cur)
                cur = tail + ch
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def render_svg(data, annotate=False):
    label = data.get("label") or {}
    regions = data.get("regions") or []
    W = float(label.get("width_mm", 90))
    H = float(label.get("height_mm", 60))
    bleed = float(label.get("bleed_mm", 3))
    safe = float(label.get("safe_mm", 5))
    vb_w = W + 2 * bleed
    vb_h = H + 2 * bleed + 9

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
        'viewBox="%g %g %g %g" role="img" aria-label="标签设计样张">' %
        (vb_w, vb_h, -bleed, -bleed, vb_w, vb_h),
        '<rect x="%g" y="%g" width="%g" height="%g" fill="#F4F5F7"/>' %
        (-bleed, -bleed, vb_w, vb_h),
        '<rect x="0" y="0" width="%g" height="%g" fill="#FFFFFF"/>' % (W, H),
        '<rect x="%g" y="%g" width="%g" height="%g" fill="none" '
        'stroke="#E0533D" stroke-width="0.3" stroke-dasharray="1.5 1"/>' %
        (-bleed, -bleed, W + 2 * bleed, H + 2 * bleed),
        '<rect x="0.15" y="0.15" width="%g" height="%g" fill="none" '
        'stroke="#111111" stroke-width="0.3"/>' % (W - 0.3, H - 0.3),
        '<rect x="%g" y="%g" width="%g" height="%g" fill="none" '
        'stroke="#9AA3AF" stroke-width="0.25" stroke-dasharray="1 1"/>' %
        (safe, safe, W - 2 * safe, H - 2 * safe),
    ]

    for r in regions:
        rid = r.get("id", "")
        x, y = float(r.get("x", 0)), float(r.get("y", 0))
        w, h = float(r.get("w", 0)), float(r.get("h", 0))
        fg, bg = r.get("fg", "#111111"), r.get("bg", "#FFFFFF")
        out.append('<rect id="%s" x="%g" y="%g" width="%g" height="%g" fill="%s" '
                   'stroke="#D6DAE1" stroke-width="0.15"/>' %
                   (html.escape(rid, quote=True), x, y, w, h, bg))
        if r.get("type") == "qrcode":
            quiet = float(r.get("quiet_zone_mm", 0))
            if quiet:
                out.append('<rect x="%g" y="%g" width="%g" height="%g" fill="none" '
                           'stroke="#9AA3AF" stroke-width="0.2" stroke-dasharray="0.8 0.8"/>' %
                           (x - quiet, y - quiet, w + 2 * quiet, h + 2 * quiet))
            cell = w / 7.0
            for i in range(7):
                for j in range(7):
                    filled = (i * 3 + j * 5 + i * j) % 3 == 0
                    corner = (i < 2 and j < 2) or (i < 2 and j > 4) or (i > 4 and j < 2)
                    if filled or corner:
                        out.append('<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' %
                                   (x + j * cell, y + i * cell, cell, cell, fg))
        else:
            font = float(r.get("font_mm", 2.5))
            raw = str(r.get("text", ""))
            supplied = r.get("wrapped_lines")
            lines = supplied if isinstance(supplied, list) and supplied else \
                wrap_cjk(raw, max(1, int(w / max(font * 0.95, 0.1))))
            for li, ln in enumerate(lines):
                out.append('<text x="%g" y="%g" font-size="%g" fill="%s" '
                           'font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif">%s</text>' %
                           (x + 0.8, y + font + 0.6 + li * font * 1.25, font, fg,
                            html.escape(str(ln), quote=False)))
        if annotate:
            out.append('<rect x="%g" y="%g" width="%g" height="2.6" fill="#2563EB" '
                       'opacity="0.9"/>' % (x, y - 2.6, max(w * 0.55, 18)))
            out.append('<text x="%g" y="%g" font-size="1.5" fill="#FFFFFF" '
                       'font-family="sans-serif">%s  %gx%gmm</text>' %
                       (x + 0.6, y - 0.8, html.escape(rid, quote=False), w, h))

    out.append('<text x="0" y="%g" font-size="2.0" fill="#6B7280" '
               'font-family="sans-serif">设计稿 · 占位文案 · 非印稿 ｜ '
               '红虚线=出血 %gmm ｜ 灰虚线=安全边距 %gmm</text>' % (H + bleed + 3, bleed, safe))
    out.append('</svg>')
    return "\n".join(out)


def build_tokens(data):
    label = data.get("label") or {}
    regions = data.get("regions") or []
    colors, sizes = {}, {}
    for r in regions:
        if r.get("fg"):
            colors.setdefault(str(r["fg"]), "ink")
        if r.get("bg"):
            colors.setdefault(str(r["bg"]), "paper")
        if r.get("font_mm"):
            sizes["--type-%s" % r.get("id", "region")] = "%gmm" % float(r["font_mm"])
    tokens = {
        "--label-width": "%gmm" % float(label.get("width_mm", 90)),
        "--label-height": "%gmm" % float(label.get("height_mm", 60)),
        "--bleed": "%gmm" % float(label.get("bleed_mm", 3)),
        "--safe": "%gmm" % float(label.get("safe_mm", 5)),
        "--ink": "#1A1A1A",
        "--paper": "#FFFFFF",
    }
    tokens.update(sizes)
    return tokens


def render_html(svg, data, tokens):
    rows = []
    for r in data.get("regions") or []:
        rows.append("<tr><td>%s</td><td>%s</td><td>%s×%s mm</td><td>%s mm</td></tr>" %
                    (html.escape(str(r.get("id", ""))), html.escape(str(r.get("type", ""))),
                     r.get("w", ""), r.get("h", ""), r.get("font_mm", "—")))
    token_rows = "".join("<tr><td><code>%s</code></td><td>%s</td></tr>" %
                         (html.escape(k), html.escape(v)) for k, v in tokens.items())
    tpl = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>标签设计样张 · 设计稿</title>
<style>
body{margin:0;padding:32px;background:#F7F8FA;color:#1F2430;
     font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;}
h1{font-size:22px;margin:0 0 6px}h2{font-size:16px;margin:28px 0 10px}
.note{font-size:13px;color:#5B6472;margin:0 0 20px}
.card{background:#FFF;border:1px solid #E3E6EC;border-radius:10px;padding:24px;
      box-shadow:0 2px 10px rgba(20,30,50,.05)}
svg{max-width:100%;height:auto}
table{border-collapse:collapse;width:100%;font-size:13px;background:#FFF}
th,td{border:1px solid #E3E6EC;padding:7px 10px;text-align:left}
th{background:#EEF1F6}code{font-size:12px}
</style></head><body>
<h1>标签设计样张</h1>
<p class="note">__NOTE__</p>
<div class="card">__SVG__</div>
<h2>区块清单</h2><table><tr><th>ID</th><th>类型</th><th>尺寸</th><th>字号</th></tr>__ROWS__</table>
<h2>设计令牌</h2><table><tr><th>令牌</th><th>值</th></tr>__TOKEN_ROWS__</table>
</body></html>"""
    # 用占位符替换而非 % 格式化：CSS 里的 100% 会被误当格式符
    return (tpl.replace("__NOTE__", html.escape(str(data.get("note", "设计稿，非印稿")), quote=False))
               .replace("__SVG__", svg)
               .replace("__ROWS__", "".join(rows))
               .replace("__TOKEN_ROWS__", token_rows))


def main():
    ap = argparse.ArgumentParser(description="渲染标签 SVG 样张与设计令牌")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--tokens-css", default="")
    ap.add_argument("--tokens-json", default="")
    ap.add_argument("--output-html", default="")
    ap.add_argument("--annotate", action="store_true")
    args = ap.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write("❌ 输入读取失败：%s\n" % exc)
        return 2

    svg = render_svg(data, args.annotate)
    Path(args.output).write_text(svg, encoding="utf-8")
    tokens = build_tokens(data)
    if args.tokens_json:
        Path(args.tokens_json).write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.tokens_css:
        css = ":root {\n" + "\n".join("  %s: %s;" % (k, v) for k, v in tokens.items()) + "\n}\n"
        Path(args.tokens_css).write_text(css, encoding="utf-8")
    if args.output_html:
        Path(args.output_html).write_text(render_html(svg, data, tokens), encoding="utf-8")
    print("✅ 样张 v%s 已生成" % VERSION)
    print("  SVG: %s (%d B)" % (args.output, len(svg.encode("utf-8"))))
    print("  区块: %d 个 ｜ 设计令牌: %d 个 ｜ 标注层: %s" %
          (len(data.get("regions") or []), len(tokens), "开" if args.annotate else "关"))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
