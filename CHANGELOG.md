# CHANGELOG

## v1.2.0（2026-11-19）· 实测回灌：化学品规则与既有标签改版

主题：把「测试本专家」两轮真实任务暴露的能力缺口固化进包。双域架构、设计与合规并列定位、三态判据、不宣称首创的红线均不变；**展示字段沿用已发布措辞，未改动**。

来源（用户自有实测材料，只读参考）：`D:\WorkBuddy\2026-11-19-19-19-43\label_audit\` 的审查报告与设计建议书（9 个脚本任务 / 205 项核查）、`D:\标签设计专家\H100Z背标改版_20261119\` 的改版交付说明、设计规格、42 项版式校验报告与零改动复核。

### A 域 · 脚本缺陷与判据修复
- `check_label_consistency.py`：`normalize_key()` 保留 Unicode，中文口径键不再被 `[^a-z0-9]+` 剥成空串；`check_taxonomy_coverage.py` 版本同步到 1.2.0。
- 新增 `normalize_value()`（NFKC / 空白 / 乘号归一）与 `format_only` 报告段：`210×194 mm` vs `210x194mm` 判 `需人工复核`、不临场发明第五类漂移；真实值漂移仍判 `不通过`。报告新增 `normalized_keys`。
- `verdict-taxonomy.md` 补第八节「冲突不属四类时的处理」；`domain-a-taxonomy-rules.md` 补第八节「书写格式与交付命名」（含文件名描述整图导致裁切误判的实测案例）。
- 新增 `examples/consistency-example.json`（中文键 / 格式差异 / 真实值漂移三合一）；修正 SKILL.md 与 README 中原本指向不存在文件的示例路径。
- `config/rules.json` 版本与说明更新：工业化学品域无专用禁用词表，脚本只启用通用词表，化学品强制标注走规则包并标 `依据：待核实`。
- 自检 22 → **28 条**，新增中文键、格式差异、真实漂移、报告明细六组断言。

### B 域 · 工业化学品／危险品标签规则包（文案）
- 新增 `references/domain-b-chemical-label.md`：GHS 象形图、警示词、危险性说明、四段式防范说明、供应商标识、应急咨询电话、SDS 一致性、尺寸分档、GB 190 菱形运输标志、LQ/EQ、标准修订窗口，共 **11 项要素逐项三态**。
- **证据等级红线**：条款号来自项目材料自述引用、法规原文未取到，一律 `[I]` / `依据：待核实`；不得升格为法规结论，不得据此判断是否违法。每份报告写「不构成法律意见」与「请复核法规现行有效版本」。
- SKILL.md 新增第五条纪律「项目自述 ≠ 法规原文」，脚本边界表明确「化学品强制标注脚本不能做」。

### B 域 · 既有标签逆向工程与真实改版（版式）
- 新增 `references/visual-reverse-engineering.md`：px→mm 反算、四份输入策略、实测布局回灌闭环、三类实测踩坑、零改动纪律；`visual-spec-rules.md` 补第十节。
- 新增 `templates/redesign-spec-template.md`、`scripts/snapshot_unchanged.py`（哈希基线／复核）。
- `check_visual_spec.py` 新增三项可计算校验：**文案声明—版面元素一致性**（`copy_references`，写「扫码获取」却无二维码 → `不通过`）、**中文断行禁则**（基于实测 `wrapped_lines`，行首收束标点／行尾开启标点）、**占位声明**（`placeholder: true` → `需人工复核`）。商标规则依据补「来源域适用性须复核」。
- `render_label_proof.py` 新增 `wrap_cjk()` 与多行 `<text>`，支持实测断行回灌（H100Z 实测行数 8→7）。
- `config/visual-rules.json` 新增 `typography` 段。自检 14 → **22 条**。

### 文档、红线与定位
- `plugin.json`：`version` → `1.2.0`，顶层 `description` 与 `keywords` 补化学品／逆向工程／改版能力；`displayName` / `profession` / `displayDescription` / `tags` / `quickPrompts` / `categoryId` / `defaultInitPrompt` / `plugin` / `agentName` **全部保持不变**。
- Agent 定义：能力范围改为 2 技能 / 2 域 / 3 能力面 / 7 个可执行脚本；核心能力扩到 9 条；工作流程补既有稿改版闭环与零改动复核；新增红线「项目自述 ≠ 法规原文」「规则来源域适用性」「书写格式差异 ≠ 漂移」「占位 ≠ 已具备」「冲突不属四类」。
- `experience-provenance.md` 补第七节 v1.2 承袭／增量对照；明确**不宣称首次发现任何标签设计规律**。

### 验证与发布状态
- 自检：A 域 **28/28**、B 域 **22/22** 通过。
- 主脚本均实际运行：覆盖度 22 项（覆盖率 100%，冲突 2 条）、口径一致性 13 项（`conflicts=1` / `format_only=1`）、版式 25 项（23 通过 / 0 不通过 / 2 复核）、样张 4 份产物、零改动复核 34 文件 0/0/0。
- `validate_expert.py` 通过；`register_expert.py` 已更新本地注册；`package_expert.py` 产出 **33 文件**的 v1.2.0 压缩包（排除 `__pycache__` 与本地会话标记）。
- 产物目录：`D:\标签设计专家\output\v120\`。GitHub 同步与平台「更新版本」以实际提交为准。

---

## v1.1.0（2026-11-19）· 设计能力升级

主题：从「能判断对错」升级为「能产出设计稿」。双域架构、三态判据与不宣称首创的红线均不变。

### A 域 · 标签体系设计生成
- 新增 `references/taxonomy-design-method.md`：D-Q-D-V 决策反推链、粒度与基数、五类关系矩阵、标注指南六项、生命周期、覆盖度指标、设计评审四问。
- 新增 `templates/annotation-guide-template.md` 与 `examples/taxonomy-design-example.json`（含刻意反例 c11）。
- 新增 `scripts/check_taxonomy_coverage.py`：覆盖率、维度使用率、未登记取值、长尾值、单标签对象、互斥/依赖冲突，Markdown + JSON 双输出。
- `config/rules.json` 增加 `coverage` 阈值段；`domain-a-taxonomy-rules.md` 与规格书模板补设计生成入口。
- 自检从 16 条扩到 **22 条**（新增 6 条覆盖度断言）。

### B 域 · 标签视觉设计（新增技能 `label-visual-designer`）
- 新增五层信息层级、栅格、字号/视距、WCAG 2.1 对比度、商标面积与四角、二维码静区、印刷 TAC/线宽/K 值规则。
- 新增 `scripts/check_visual_spec.py`：25 项可计算校验，三态结论 + Markdown/JSON 报告。
- 新增 `scripts/render_label_proof.py`：渲染 SVG 样张（可开标注层）、HTML 预览页、`tokens.css` / `tokens.json` 设计令牌。
- 新增视觉规格模板与可运行示例（占位文案，明确「设计稿非印稿」）。
- 新增 `scripts/self_check.py`：**14 条断言全通过**。

### 文档与红线
- 主 Agent 能力范围扩为 2 技能 / 2 域 / 3 能力面 / 5 个脚本；新增「先设计后校验」纪律。
- 新增红线：版式通过 ≠ 文案合规、样张是设计稿不是印稿、指标不达标 ≠ 业务无效、脚本不能生成设计。
- `experience-provenance.md` 补 v1.1.0 承袭/增量对照；第三方 MIT 声明不变。
- 展示字段调整：tags 保持 3 个（替换措辞以覆盖新增的版式设计能力），quickPrompts 保持 3 个（第 2 条改为版式设计）。
- 展示定位校准（同版本内，按业主拍板「标签设计和合规」）：`displayDescription` 显式写入合规核查，顶层 `description` 改为 design and compliance，`quickPrompts` 第 3 条从口径漂移改为逐项合规审查入口；Agent 与 README 明确**设计与合规并列、不是主次关系**。口径漂移能力不变，仍由 `label-taxonomy-governor` 与 `check_label_consistency.py` 承载。

### 发布与验证状态
- 本地：`validate_expert.py` 通过；`register_expert.py` 已更新注册；`package_expert.py` 产出 28 文件 / 570,889 B 的 v1.1.0 压缩包。
- 自检：A 域 22/22、B 域 14/14；覆盖度、口径一致性、版式校验与样张渲染均已实际运行并产出报告。
- GitHub：v1.1.0 同步以 `mimetics-ai/label-design-expert` 的提交记录为准。

---

## v1.0.0（2026-11-19）

首个可提交审核版本。

- 克隆 GitHub `jnMetaCode/agency-agents-zh` 的 `design/design-ux-architect.md`（MIT）作为角色骨架，保留第三方许可声明。
- 按用户选择实现**双域合并**：A 数据／内容标签体系设计、B 商品／包装标签合规审查；先分流，判据不混用。
- 纳入用户在 WorkBuddy 历史任务中的三类标签经验：标签法规与强制标注、产品标签用词强弱校准、标签口径文本陈旧（漂移）。
- 新增 `check_label_consistency.py`（口径归一化 + 四类漂移检测）与 `self_check.py`（12 条断言）。
- 新增承袭／增量对照表，明确不宣称首次发现规律。
- 通过 `validate_expert.py` 校验并 `register_expert.py` 注册；同步发布到 GitHub。
