#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""零改动基线／复核工具（v1.2.0）。

审查既有标签时，用户常要求「不能动任何原文件」。本工具在动手前记录指定目录内
全部文件的 SHA256 + 字节数，结束后复核并输出差异报告。只读取，不写被扫描目录。

用法：
  python snapshot_unchanged.py --root <dir> [--root <dir> ...] --out baseline.txt
  python snapshot_unchanged.py --root <dir> [--root <dir> ...] \
      --compare baseline.txt --out report.txt

退出码：0 = 零改动（或基线已写出）；1 = 检出差异；2 = 参数／IO 错误。
"""
import argparse
import hashlib
import sys
from pathlib import Path


def scan(roots):
    snap = {}
    for root in roots:
        r = Path(root)
        if not r.exists():
            raise FileNotFoundError("目录不存在：%s" % r)
        for p in sorted(r.rglob("*")):
            if not p.is_file():
                continue
            if "__pycache__" in p.parts or p.suffix == ".pyc":
                continue
            key = str(p.resolve())
            snap[key] = (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size)
    return snap


def serialize(snap):
    return "\n".join("%s  %d  %s" % (h, s, k) for k, (h, s) in sorted(snap.items())) + "\n"


def parse(text):
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 2)
        if len(parts) != 3:
            raise ValueError("基线格式无法解析：%s" % line[:80])
        h, size, key = parts
        out[key] = (h, int(size))
    return out


def compare(base, now):
    added = sorted(set(now) - set(base))
    removed = sorted(set(base) - set(now))
    changed = sorted(k for k in set(base) & set(now) if base[k] != now[k])
    lines = [
        "# 零改动复核",
        "",
        "- 基线文件数：%d ｜ 复核文件数：%d" % (len(base), len(now)),
        "- 新增：%d ｜ 删除：%d ｜ 变化：%d" % (len(added), len(removed), len(changed)),
    ]
    for title, items in (("新增", added), ("删除", removed), ("变化", changed)):
        if items:
            lines += ["", "## %s" % title] + ["- %s" % i for i in items]
    lines += ["", "结论：%s" % ("零改动" if not (added or removed or changed) else "检出差异，不得宣称零改动"), ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="记录／复核文件哈希基线（只读）")
    ap.add_argument("--root", action="append", required=True, help="被扫描目录，可重复")
    ap.add_argument("--out", default="", help="基线或报告输出路径")
    ap.add_argument("--compare", default="", help="已有基线文件，进入复核模式")
    args = ap.parse_args()

    try:
        now = scan(args.root)
    except (OSError, ValueError) as exc:
        sys.stderr.write("❌ 扫描失败：%s\n" % exc)
        return 2

    if args.compare:
        try:
            base = parse(Path(args.compare).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            sys.stderr.write("❌ 基线读取失败：%s\n" % exc)
            return 2
        text = compare(base, now)
        clean = "零改动" in text and "新增：0 ｜ 删除：0 ｜ 变化：0" in text
    else:
        text = serialize(now)
        clean = True

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    sys.stdout.write(text if args.compare else "✅ 基线已记录：%d 个文件\n" % len(now))
    return 0 if clean else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
