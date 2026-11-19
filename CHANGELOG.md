# CHANGELOG

## v1.0.0（2026-11-19）

首个可提交审核版本。

- 克隆 GitHub `jnMetaCode/agency-agents-zh` 的 `design/design-ux-architect.md`（MIT）作为角色骨架，保留第三方许可声明。
- 按用户选择实现**双域合并**：A 数据／内容标签体系设计、B 商品／包装标签合规审查；先分流，判据不混用。
- 纳入用户在 WorkBuddy 历史任务中的三类标签经验：标签法规与强制标注、产品标签用词强弱校准、标签口径文本陈旧（漂移）。
- 新增 `check_label_consistency.py`（口径归一化 + 四类漂移检测）与 `self_check.py`（12 条断言）。
- 新增承袭／增量对照表，明确不宣称首次发现规律。
- 通过 `validate_expert.py` 校验并 `register_expert.py` 注册；同步发布到 GitHub。
