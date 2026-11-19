# CHANGELOG

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
