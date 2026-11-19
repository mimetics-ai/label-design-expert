#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签体系覆盖度与结构健康度校验（v1.1.0 新增）。

只算结构与一致性：覆盖率、维度使用率、未登记取值、长尾值、单标签对象、关系冲突。
不判断标签是否贴合业务、不判断取值语义是否等价。指标不达标 ≠ 业务无效。

用法：
  python check_taxonomy_coverage.py --input taxonomy-design-example.json \
      --config config/rules.json --output-md coverage.md --output-json coverage.json
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "1.2.0"
PASS, FAIL, REVIEW = "通过", "不通过", "需人工复核"
DEFAULTS = {
    "min_coverage": 0.95,
    "min_dimension_usage": 0.20,
    "max_long_tail_ratio": 0.30,
    "max_single_tag_rate": 0.20,
    "min_value_hits": 2,
}


def analyze(data, config):
    cfg = dict(DEFAULTS)
    cfg.update((config.get("coverage") or {}))
    labels = data.get("labels") or []
    samples = data.get("samples") or []
    relations = data.get("relations") or []

    declared = {}
    for lab in labels:
        declared[lab.get("id", "")] = {
            "values": set(str(v) for v in (lab.get("values") or [])),
            "status": lab.get("status", "active"),
        }

    used_dims = Counter()
    value_hits = Counter()
    orphan_values, unknown_dims, relation_conflicts = [], [], []
    labeled, single_tagged = 0, 0

    for s in samples:
        labmap = s.get("labels") or {}
        sid = s.get("id", "")
        if labmap:
            labeled += 1
        if len(labmap) == 1:
            single_tagged += 1
        for dim, raw in labmap.items():
            vals = raw if isinstance(raw, list) else [raw]
            used_dims[dim] += 1
            for val in vals:
                value_hits["%s:%s" % (dim, str(val))] += 1
                if dim not in declared:
                    unknown_dims.append({"sample": sid, "dimension": dim})
                elif str(val) not in declared[dim]["values"]:
                    orphan_values.append({"sample": sid, "dimension": dim, "value": str(val)})

    total = len(samples)
    coverage_rate = labeled / total if total else 0.0
    single_tag_rate = single_tagged / total if total else 0.0
    dimension_coverage = {d: (used_dims.get(d, 0) / total if total else 0.0) for d in declared}

    all_values = ["%s:%s" % (d, v) for d, info in declared.items() for v in info["values"]]
    observed = [k for k in all_values if value_hits.get(k, 0) > 0]
    long_tail = [k for k in all_values if 0 < value_hits.get(k, 0) <= cfg["min_value_hits"]]
    long_tail_ratio = len(long_tail) / len(observed) if observed else 0.0

    for r in relations:
        rtype = r.get("type")
        a, b = r.get("a", ""), r.get("b", "")
        if rtype not in ("exclusive", "requires"):
            continue
        for s in samples:
            keys = set()
            for k, v in (s.get("labels") or {}).items():
                for vv in (v if isinstance(v, list) else [v]):
                    keys.add("%s:%s" % (k, vv))
            if rtype == "exclusive" and a in keys and b in keys:
                relation_conflicts.append({"sample": s.get("id", ""), "type": "exclusive",
                                           "detail": "%s 与 %s 同时命中" % (a, b)})
            if rtype == "requires" and a in keys and b not in keys:
                relation_conflicts.append({"sample": s.get("id", ""), "type": "requires",
                                           "detail": "%s 已命中但依赖 %s 缺失" % (a, b)})

    verdicts = []

    def add(item, verdict, detail, basis):
        verdicts.append({"item": item, "verdict": verdict, "detail": detail, "basis": basis})

    add("覆盖率 coverage_rate", PASS if coverage_rate >= cfg["min_coverage"] else FAIL,
        "%.1f%%（阈值 ≥ %.0f%%）" % (coverage_rate * 100, cfg["min_coverage"] * 100),
        "依据：taxonomy-design-method.md 第六节")
    add("未登记维度 / 取值", FAIL if (unknown_dims or orphan_values) else PASS,
        "未知维度 %d 处，未登记取值 %d 处" % (len(unknown_dims), len(orphan_values)),
        "依据：taxonomy-design-method.md 第三节")
    add("关系矩阵冲突", FAIL if relation_conflicts else PASS,
        "互斥/依赖冲突 %d 条" % len(relation_conflicts),
        "依据：taxonomy-design-method.md 第三节")
    add("长尾值占比", REVIEW if long_tail_ratio > cfg["max_long_tail_ratio"] else PASS,
        "%.1f%%（阈值 ≤ %.0f%%）；长尾值：%s" %
        (long_tail_ratio * 100, cfg["max_long_tail_ratio"] * 100,
         ", ".join(long_tail[:6]) or "无"),
        "依据：config/rules.json → coverage")
    add("单标签对象占比", REVIEW if single_tag_rate > cfg["max_single_tag_rate"] else PASS,
        "%.1f%%（阈值 ≤ %.0f%%）" % (single_tag_rate * 100, cfg["max_single_tag_rate"] * 100),
        "依据：taxonomy-design-method.md 第二节")
    weak_dims = {d: round(v, 3) for d, v in dimension_coverage.items()
                 if v < cfg["min_dimension_usage"]}
    add("维度使用率", REVIEW if weak_dims else PASS,
        "低使用维度：%s" % (json.dumps(weak_dims, ensure_ascii=False) if weak_dims else "无"),
        "依据：config/rules.json → coverage")

    if not samples:
        add("输入", REVIEW, "samples 为空，指标不可计算", "依据：SKILL.md 输入表")

    report = {
        "meta": {"version": VERSION, "script_ran": True,
                 "total_samples": total, "total_dimensions": len(declared),
                 "checked_items": len(samples) + len(labels) + len(relations) + 6,
                 "rules_note": "指标只说明结构健康度，不说明业务有效性；判定由模型完成，拍板由用户完成。"},
        "metrics": {
            "coverage_rate": round(coverage_rate, 4),
            "single_tag_rate": round(single_tag_rate, 4),
            "long_tail_ratio": round(long_tail_ratio, 4),
            "dimension_coverage": {d: round(v, 4) for d, v in dimension_coverage.items()},
            "value_hits": dict(value_hits),
            "long_tail_values": long_tail,
        },
        "orphan_values": orphan_values,
        "unknown_dimensions": unknown_dims,
        "relation_conflicts": relation_conflicts,
        "verdicts": verdicts,
        "summary": {
            "pass": sum(1 for v in verdicts if v["verdict"] == PASS),
            "fail": sum(1 for v in verdicts if v["verdict"] == FAIL),
            "review": sum(1 for v in verdicts if v["verdict"] == REVIEW),
        },
    }
    return report


def render_markdown(report):
    m, t, s = report["meta"], report["metrics"], report["summary"]
    lines = [
        "【执行声明】脚本：已运行（%d 项）｜未运行（人工逐条）" % m["checked_items"],
        "",
        "# 标签体系覆盖度报告（脚本部分）",
        "",
        "- 版本：%s ｜ 样本 %d 个 ｜ 维度 %d 个" % (m["version"], m["total_samples"], m["total_dimensions"]),
        "- 覆盖率 %.1f%% ｜ 单标签对象 %.1f%% ｜ 长尾值占比 %.1f%%" %
        (t["coverage_rate"] * 100, t["single_tag_rate"] * 100, t["long_tail_ratio"] * 100),
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
    lines += ["", "## 维度使用率", "", "| 维度 | 使用率 |", "|---|---|"]
    for d, v in t["dimension_coverage"].items():
        lines.append("| %s | %.1f%% |" % (d, v * 100))
    if report["relation_conflicts"]:
        lines += ["", "## 关系冲突", "", "| 样本 | 类型 | 说明 |", "|---|---|---|"]
        for c in report["relation_conflicts"]:
            lines.append("| %s | %s | %s |" % (c["sample"], c["type"], c["detail"]))
    lines += [
        "",
        "## 脚本边界",
        "",
        "- 能做：覆盖率、维度使用率、未登记值、长尾值、单标签对象、互斥/依赖冲突。",
        "- 不能做：业务有效性、语义等价、标注一致性统计量。",
        "- 指标不达标 ≠ 业务无效；维度合并与值域拆分由用户拍板。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="标签体系覆盖度与结构健康度校验")
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
