# 标尺 · 标签体系设计与合规审查师（label-design-expert）

一个 WorkBuddy Agent 型专家：**从零设计标签体系、设计商品标签版式并出可渲染样张、审查既有真实标签并出零改动改版稿、审查标签文案合规、检测跨文件口径漂移**。每条结论带依据、落在三态里，判不了的明确交回人。

- 类型：Agent（单专家）
- 分类：`01-ProductDesign`（**标签设计与合规审查并列为两条主线，不是主次关系**）
- 版本：**v1.2.0**（桌面标签实测回灌：工业化学品规则 + 既有标签逆向工程与真实改版）
- 在线仓库：https://github.com/mimetics-ai/label-design-expert
- 本地工作区：`D:\标签设计专家`

> 展示字段沿用 v1.1.0 已通过平台审核的定位措辞：`displayName` / `profession` / `displayDescription` / `tags` / `quickPrompts` / `categoryId` 均未改动，避免破坏「设计与合规并列」的已发布定位；v1.2 的能力增量写进 `description`、Agent、技能包与本文件。

## 能力边界

| 域 | 能力面 | 处理 | 不处理 |
|---|---|---|---|
| A 数据／内容标签体系 | 体系设计生成 | D-Q-D-V 决策反推、维度/取值/关系/生命周期、标注指南、覆盖度验收 | 不写业务系统代码、不自动改线上标签库 |
| A 数据／内容标签体系 | 口径治理 | 跨文件取值漂移定位、**中文口径键**、**仅书写格式差异**、命名与枚举校验 | 不判断标签是否贴合业务、不决定哪种写法权威 |
| B 商品／包装标签 | 文案合规 | 强制标注、分域禁用词、商标标注、用词强弱；**v1.2 工业化学品／危险品 11 项要素**（GHS、警示词、四段式、SDS） | 不出具法律意见、不判侵权、不预测处罚；化学品条款号一律 `依据：待核实` |
| B 商品／包装标签 | 版式设计 | 五层信息层级、字号/对比度/边距/商标面积/静区/印刷参数、SVG 样张、设计令牌；**v1.2 既有稿 px→mm 反算、实测布局回灌、真实改版、零改动基线** | 不替代印厂工艺确认、样张不是印稿、不从缩略图目测坐标 |

**双域架构不变；B 域内文案合规与版式设计分开判。版式通过 ≠ 文案合规。**

## v1.2.0 实测回灌了什么

来自 2026-11-19「测试本专家」的两轮真实任务：第一轮审查桌面 `公司产品标签`（9 个脚本任务 / 205 项核查），第二轮拿 H100Z 背标做真实改版（42 项版式核查，从 9 条 `不通过` 收敛到 39 通过 / 0 不通过 / 3 需人工复核；原文件 579 个零改动）。

| 实测暴露的缺口 | 固化到包里的东西 |
|---|---|
| `check_label_consistency.py` 把中文 key 归一成空串 | `normalize_key()` 保留 Unicode；新增 `consistency-example.json` 可运行示例 |
| 「`210×194 mm` vs `210x194mm`」被当成口径冲突 | 新增 `normalize_value()` 与 `format_only`，仅书写格式差异判 `需人工复核`，**不发明第五类漂移** |
| 工业化学品标签无专用核查表 | 新增 `domain-b-chemical-label.md`：11 项要素、四段式防范说明、尺寸分档、GB 190 菱形、LQ/EQ、标准修订窗口；条款号全部 `[I]` |
| 既有标签只能目测、改版无闭环 | 新增 `visual-reverse-engineering.md`、`redesign-spec-template.md`、`snapshot_unchanged.py` |
| 中文断行把句号甩到下一行 | `wrap_cjk()` + `wrapped_lines` 回灌校验（实测行数 8→7） |
| 文案写「扫码获取」但版面没有二维码 | `copy_references` 文案—版面一致性校验 |
| 预留位被当成已具备功能 | `placeholder: true` 必须标 `需人工复核`；占位 ≠ 已具备 |
| README 里的 `declarations.json` 其实不存在 | 补 `examples/consistency-example.json`，脚本用法改为包内真实路径 |

**红线同步收紧**：项目自述 ≠ 法规原文、规则来源域适用性未确认 → 需人工复核、实测坐标不目测不虚构、阈值边界向上取整后复验、冲突不属四类 ≠ 通过。

## 附带技能（2 个）

### `skills/label-taxonomy-governor` — 体系设计、治理与文案合规

| 文件 | 用途 |
|---|---|
| `references/taxonomy-design-method.md` | D-Q-D-V、粒度基数、五类关系、标注指南、生命周期、覆盖度、评审四问 |
| `references/domain-a-taxonomy-rules.md` | 正交维度、命名、枚举、四类漂移、**v1.2 第八节书写格式与交付命名** |
| `references/domain-b-label-compliance.md` | 属性认定、强制标注表、分域禁用词、商标、用词强弱 |
| `references/domain-b-chemical-label.md` | **v1.2 新增**：工业化学品／危险品 11 项要素、四段式、尺寸分档、运输标志、SDS 一致性 |
| `references/verdict-taxonomy.md` | 三态判据、漂移优先级、适用性判定、**v1.2 第八节冲突不属四类** |
| `references/experience-provenance.md` | **承袭 / 增量对照**（不宣称首创），v1.2 第七节 |
| `templates/` | 规格书、标注指南、审查报告模板 |
| `examples/taxonomy-design-example.json` | 覆盖度可运行示例（含刻意反例 c11） |
| `examples/consistency-example.json` | **v1.2 新增**：中文键 / 格式差异 / 真实值漂移三合一示例 |
| `config/rules.json` | 命名正则、保留词、分域禁用词、别名、覆盖度阈值 |
| `scripts/check_taxonomy_coverage.py` | 覆盖度与关系冲突校验 |
| `scripts/check_label_consistency.py` | 口径归一化、四类漂移、**中文键与 `format_only`** |
| `scripts/self_check.py` | **28 条**冒烟断言 |

### `skills/label-visual-designer` — 版式与视觉设计

| 文件 | 用途 |
|---|---|
| `references/visual-spec-rules.md` | 五层信息层级、栅格、字号/视距、WCAG 2.1、商标/码/印刷规则、评审五问、**v1.2 第十节实测规则** |
| `references/visual-reverse-engineering.md` | **v1.2 新增**：px→mm 反算、四份输入策略、实测布局回灌闭环、三类踩坑、零改动纪律 |
| `config/visual-rules.json` | 可配置阈值（含中文禁则字符） |
| `templates/visual-spec-template.md` | 视觉规格表模板 |
| `templates/redesign-spec-template.md` | **v1.2 新增**：真实内容改版规格表模板 |
| `examples/label-proof-input.json` | 可运行示例（占位文案） |
| `scripts/check_visual_spec.py` | 25 项可计算校验 + **v1.2 三项新判据**，Markdown + JSON 报告 |
| `scripts/render_label_proof.py` | SVG 样张 + HTML 预览 + `tokens.css` / `tokens.json`；**v1.2 `wrap_cjk()`** |
| `scripts/snapshot_unchanged.py` | **v1.2 新增**：零改动哈希基线／复核 |
| `scripts/self_check.py` | **22 条**冒烟断言 |

## 脚本用法

在 `skills/<技能名>/` 目录下执行（示例路径均为包内真实文件）：

```bash
# A 域 · 覆盖度验收
python scripts/check_taxonomy_coverage.py \
  --input examples/taxonomy-design-example.json --config config/rules.json \
  --output-md coverage.md --output-json coverage.json

# A 域 · 口径一致性（v1.2 示例：中文键 + 格式差异 + 真实漂移）
python scripts/check_label_consistency.py \
  --input examples/consistency-example.json --config config/rules.json \
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

# B 域 · 零改动基线 / 交付前复核（v1.2）
python scripts/snapshot_unchanged.py --root <原目录> --out baseline.txt
python scripts/snapshot_unchanged.py --root <原目录> --compare baseline.txt --out 零改动复核.txt

# 自检（两个技能各一份）
python scripts/self_check.py
```

口径输入结构（`labels` + `declarations`）：

```json
{
  "scope": "工业化学品",
  "labels": [{"id": "integrity-level", "name": "完整性等级", "values": ["Low", "Medium", "High"]}],
  "declarations": [
    {"file": "gate-manifest.json", "key": "env.expectedIntegrity", "value": "Medium"},
    {"file": "label-guard.mjs", "key": "EXPECTED_INTEGRITY", "value": "Medium"},
    {"file": "M2-plan.md", "key": "expectedIntegrity", "value": "Low"},
    {"file": "设计规格.md", "key": "成品尺寸", "value": "210×194 mm"},
    {"file": "layout.json", "key": "成品尺寸", "value": "210x194mm"}
  ]
}
```

前三行归一到同一口径键并报出值漂移；后两行是中文键且仅书写格式不同，判 `需人工复核`。**脚本只查结构与数值，不判定合法合规、不生成设计方案**；设计由 D-Q-D-V 链与视觉规格表完成，定性由模型完成，拍板由用户完成。跨语言同义键写进 `config/rules.json` 的 `key_aliases`，脚本不猜。

## 实测结果（v1.2.0，脚本已实际运行）

| 项目 | 结果 |
|---|---|
| `label-taxonomy-governor/scripts/self_check.py` | **28/28 通过** |
| `label-visual-designer/scripts/self_check.py` | **22/22 通过** |
| 覆盖度示例 | 22 项检查：覆盖率 100%、长尾 11.1%、单标签 9.1%；检出互斥冲突 1 条 + 依赖冲突 1 条（刻意反例 c11 / c05） |
| 口径一致性示例 | 13 项检查：7 条声明 → 3 组归一键；`conflicts=1`（值漂移）、`format_only=1`（`210×194 mm` / `210x194mm`）；通过 1 / 不通过 1 / 需人工复核 1 |
| 版式示例 | 25 项校验：通过 23 / 不通过 0 / 需人工复核 2（文案合规未核、印厂规范待确认） |
| 样张产物 | `label-proof.svg`（5,977 B）/ `label-proof.html` / `tokens.css` / `tokens.json`（10 个设计令牌，标注层开启） |
| 零改动复核 | 基线 34 文件 → 复核 34 文件；新增 0 / 删除 0 / 变化 0 |

产物目录：`D:\标签设计专家\output\v120\`（覆盖度、口径、版式报告 + 样张 + 令牌 + 零改动复核）。

## 承袭与增量

| 承袭 | 增量 |
|---|---|
| `jnMetaCode/agency-agents-zh` 的 `design/design-ux-architect.md`（MIT） | 双域分流、三态判据、口径漂移脚本、D-Q-D-V 设计链 |
| 本机 `pre-publish-evidence-gate`（先分流、四类缺口、三态、执行声明） | 迁到标签域，改为四类漂移 + 覆盖度六指标 |
| 本机 `brand-delivery-compliance-expert`（逐项标注、依据可追溯、不适用≠缺失、印前预检参数） | 与标签体系设计合并；印前参数前移到设计阶段做可计算校验 |
| 海巍驱蚊咨询报告 §4.3.1、海巍树脂谱系表 F30 行、brand-delivery 标签口径定案 | 转成可复用规则表、把「待拍板」做成独立输出项 |
| WCAG 2.1 对比度公式、通用排版实践（公开标准／通用实践） | 标签专属五层信息层级、SVG 样张与设计令牌输出 |
| 2026-11-19 桌面标签审查报告、H100Z 背标改版规格与 42 项校验（用户自有实测材料） | **v1.2**：中文键归一、格式差异三态、化学品 11 项表、既有稿反算与改版闭环、中文断行禁则、文案—版面一致性、占位声明、零改动哈希基线 |

完整对照见 `skills/label-taxonomy-governor/references/experience-provenance.md`；第三方许可全文见 `THIRD-PARTY-NOTICES.md`。**本专家不宣称首次发现任何标签设计规律。**

## 使用示例

- 帮我给这批内容设计一套标签体系，先说维度怎么切、命名怎么定。
- 帮我设计一张产品标签版面并出样张，版式和文案合规分开给结论。
- 逐项核查这张标签的强制标注、禁用词和商标标注，每条给依据和三态结论。
- 同一个标签在规格表、代码和文档里口径对不上，帮我定位漂移点。
- 这张工业化学品标签的 GHS 象形图、警示词和四段式防范说明齐不齐？逐项三态。
- 审查桌面这批标签并拿其中一张改版，**不能动任何原文件**，交付前做零改动复核。

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

注册后可在「专家中心 → 我的专家」看到「标尺」。v1.1.0 已在 WorkBuddy 开放平台审核通过并公开发布；v1.2.0 需通过平台「更新版本」上传新包。

## 头像

`avatars/expert.png`（512×512，≤500KB），可手动替换。

## 边界

- **已注册到 WorkBuddy 专家平台「专家中心 → 我的专家」**；官方专家市场的公开上架与审核是另一条分发通道，需单独提交，两者不冲突。
- 报告须写「不构成法律意见」与「请复核法规现行有效版本」；化学品条款号来自项目材料自述引用（`[I]`），**不得据此判断是否违法**。
- 样张是设计稿不是印稿，印厂参数须确认；占位 ≠ 已具备。
- 三态只能是 `通过` / `不通过` / `需人工复核`；没跑脚本不许写跑过。

## 许可

MIT。第三方来源与版权声明见 `THIRD-PARTY-NOTICES.md`。
