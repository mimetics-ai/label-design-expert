# 标尺 · 标签体系设计与合规审查师（label-design-expert）

一个 WorkBuddy Agent 型专家：**从零设计标签体系、设计商品标签版式并出可渲染样张、审查标签文案合规、检测跨文件口径漂移**。每条结论带依据、落在三态里，判不了的明确交回人。

- 类型：Agent（单专家）
- 分类：`01-ProductDesign`（主要输出物是标签体系规格、标注指南与视觉规格/样张；**标签设计与合规审查并列为两条主线，不是主次关系**）
- 版本：**v1.1.0**（设计能力升级）
- 在线仓库：https://github.com/mimetics-ai/label-design-expert
- 本地工作区：`D:\标签设计专家`

## 能力边界

| 域 | 能力面 | 处理 | 不处理 |
|---|---|---|---|
| A 数据／内容标签体系 | 体系设计生成 | D-Q-D-V 决策反推、维度/取值/关系/生命周期、标注指南、覆盖度验收 | 不写业务系统代码、不自动改线上标签库 |
| A 数据／内容标签体系 | 口径治理 | 跨文件取值漂移定位、命名与枚举校验 | 不判断标签是否贴合业务 |
| B 商品／包装标签 | 文案合规 | 强制标注、分域禁用词、商标标注、用词强弱 | 不出具法律意见、不判侵权、不预测处罚 |
| B 商品／包装标签 | 版式设计 | 五层信息层级、字号/对比度/边距/商标面积/静区/印刷参数、SVG 样张、设计令牌 | 不替代印厂工艺确认、样张不是印稿 |

**双域架构不变；B 域内文案合规与版式设计分开判。版式通过 ≠ 文案合规。**

## 附带技能（2 个）

### `skills/label-taxonomy-governor` — 体系设计、治理与文案合规

| 文件 | 用途 |
|---|---|
| `references/taxonomy-design-method.md` | **v1.1**：D-Q-D-V、粒度基数、五类关系、标注指南、生命周期、覆盖度、评审四问 |
| `references/domain-a-taxonomy-rules.md` | 正交维度、命名、枚举、层级、四类漂移 |
| `references/domain-b-label-compliance.md` | 属性认定、强制标注表、分域禁用词、商标、用词强弱 |
| `references/verdict-taxonomy.md` | 三态判据、漂移优先级、适用性判定 |
| `references/experience-provenance.md` | **承袭 / 增量对照**（不宣称首创） |
| `templates/` | 规格书、标注指南、审查报告模板 |
| `examples/taxonomy-design-example.json` | 可运行示例（含刻意反例 c11） |
| `config/rules.json` | 命名正则、保留词、分域禁用词、别名、覆盖度阈值 |
| `scripts/check_taxonomy_coverage.py` | **v1.1**：覆盖度与关系冲突校验 |
| `scripts/check_label_consistency.py` | 口径归一化与四类漂移检测 |
| `scripts/self_check.py` | 22 条冒烟断言 |

### `skills/label-visual-designer` — 版式与视觉设计（v1.1 新增）

| 文件 | 用途 |
|---|---|
| `references/visual-spec-rules.md` | 五层信息层级、栅格、字号/视距、WCAG 2.1 对比度、商标/码/印刷规则、评审五问 |
| `config/visual-rules.json` | 可配置阈值 |
| `templates/visual-spec-template.md` | 视觉规格表模板 |
| `examples/label-proof-input.json` | 可运行示例（占位文案） |
| `scripts/check_visual_spec.py` | 25 项可计算校验，Markdown + JSON 报告 |
| `scripts/render_label_proof.py` | SVG 样张 + HTML 预览 + `tokens.css` / `tokens.json` |
| `scripts/self_check.py` | 14 条冒烟断言 |

## 脚本用法

```bash
# A 域 · 覆盖度验收（v1.1）
python scripts/check_taxonomy_coverage.py \
  --input examples/taxonomy-design-example.json --config config/rules.json \
  --output-md coverage.md --output-json coverage.json

# A 域 · 口径一致性
python scripts/check_label_consistency.py \
  --input declarations.json --config config/rules.json \
  --output-md report.md --output-json report.json

# B 域 · 版式校验
python scripts/check_visual_spec.py \
  --input examples/label-proof-input.json --config config/visual-rules.json \
  --output-md visual-report.md --output-json visual-report.json

# B 域 · 渲染样张与设计令牌
python scripts/render_label_proof.py \
  --input examples/label-proof-input.json --output label-proof.svg \
  --tokens-css tokens.css --tokens-json tokens.json \
  --output-html label-proof.html --annotate

# 自检（两个技能各一份）
python scripts/self_check.py
```

`declarations.json` 结构（口径声明）：

```json
{
  "scope": "化妆品",
  "labels": [
    {"id": "integrity-level", "name": "完整性等级", "values": ["Low", "Medium", "High"]}
  ],
  "declarations": [
    {"file": "gate-manifest.json", "key": "env.expectedIntegrity", "value": "Medium"},
    {"file": "label-guard.mjs", "key": "EXPECTED_INTEGRITY", "value": "Medium"},
    {"file": "M2-plan.md", "key": "expectedIntegrity", "value": "Low"}
  ]
}
```

脚本会把 `env.expectedIntegrity` / `EXPECTED_INTEGRITY` 归一到同一口径键，报出 `M2-plan.md` 的取值漂移。**脚本只查结构与数值，不判定合法合规、不生成设计方案**；设计由 D-Q-D-V 链与视觉规格表完成，定性由模型完成，拍板由用户完成。

## 实测结果（v1.1.0）

| 项目 | 结果 |
|---|---|
| `label-taxonomy-governor/scripts/self_check.py` | **22/22 通过** |
| `label-visual-designer/scripts/self_check.py` | **14/14 通过** |
| 覆盖度示例 | 覆盖率 100%、检出互斥冲突 1 条 + 依赖冲突 1 条 |
| 版式示例 | 25 项校验：通过 23 / 不通过 0 / 需人工复核 2（文案合规未核、印厂规范待确认） |
| 样张产物 | `label-proof.svg` / `label-proof.html` / `tokens.css` / `tokens.json` |

工作区示例产物：`D:\标签设计专家\output\`。

## 承袭与增量

| 承袭 | 增量 |
|---|---|
| `jnMetaCode/agency-agents-zh` 的 `design/design-ux-architect.md`（MIT） | 双域分流、三态判据、口径漂移脚本、D-Q-D-V 设计链 |
| 本机 `pre-publish-evidence-gate`（先分流、四类缺口、三态、执行声明） | 迁到标签域，改为四类漂移 + 覆盖度六指标 |
| 本机 `brand-delivery-compliance-expert`（逐项标注、依据可追溯、不适用≠缺失、印前预检参数） | 与标签体系设计合并；印前参数前移到设计阶段做可计算校验 |
| 海巍驱蚊咨询报告 §4.3.1、海巍树脂谱系表 F30 行、brand-delivery 标签口径定案 | 转成可复用规则表、把「待拍板」做成独立输出项 |
| WCAG 2.1 对比度公式、通用排版实践（公开标准／通用实践） | 标签专属五层信息层级、SVG 样张与设计令牌输出 |

完整对照见 `skills/label-taxonomy-governor/references/experience-provenance.md`；第三方许可全文见 `THIRD-PARTY-NOTICES.md`。**本专家不宣称首次发现任何标签设计规律。**

## 使用示例

- 帮我给这批内容设计一套标签体系，先说维度怎么切、命名怎么定。
- 帮我设计一张产品标签版面并出样张，版式和文案合规分开给结论。
- 逐项核查这张标签的强制标注、禁用词和商标标注，每条给依据和三态结论。
- 同一个标签在规格表、代码和文档里口径对不上，帮我定位漂移点。（口径漂移也可直接提问，由 `check_label_consistency.py` 承载）

## 安装与注册

专家包必须放在专家目录才能被 WorkBuddy 检测：

```
%WORKBUDDY_CONFIG_DIR%\plugins\marketplaces\my-experts\plugins\label-design-expert\
```

```bash
python3 scripts/validate_expert.py <expert-dir>
python3 scripts/register_expert.py <expert-dir>
python3 scripts/package_expert.py <expert-dir>
```

注册后可在「专家中心 → 我的专家」看到「标尺」。

## 头像

`avatars/expert.png`（512×512，≤500KB），可手动替换。

## 边界

- **已注册到 WorkBuddy 专家平台「专家中心 → 我的专家」**（`marketplace.json` 中 `label-design-expert` / v1.1.0），即可见可用；官方专家市场的公开上架与审核是另一条分发通道，需单独提交，两者不冲突。
- 报告须写「不构成法律意见」与「请复核法规现行有效版本」；样张是设计稿不是印稿，印厂参数须确认。
- 三态只能是 `通过` / `不通过` / `需人工复核`；没跑脚本不许写跑过。

## 许可

MIT。第三方来源与版权声明见 `THIRD-PARTY-NOTICES.md`。
