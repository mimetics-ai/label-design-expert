# 标尺 · 标签体系设计与合规审查师（label-design-expert）

一个 WorkBuddy Agent 型专家：**设计数据／内容标签体系、审查商品／包装标签合规、检测跨文件标签口径漂移**，每条结论都带依据、落在三态里，判不了的明确交回人。

- 类型：Agent（单专家）
- 分类：`01-ProductDesign`（主要输出物是标签体系规格与信息架构文档，服务产品／内容／运营团队；合规审查为第二能力）
- 版本：v1.0.0
- 在线仓库：https://github.com/mimetics-ai/label-design-expert
- 本地工作区：`D:\标签设计专家`

## 能力边界

| 域 | 处理 | 不处理 |
|---|---|---|
| A 数据／内容标签体系 | 维度切分、命名与取值规范、层级、单一事实源、口径漂移定位 | 不写业务系统代码、不自动改线上标签库 |
| B 商品／包装标签 | 强制标注项、禁用词、商标标注、用词强弱校准、依据可追溯 | 不出具法律意见、不判侵权、不预测处罚、不替代印厂工艺确认 |

两域**先分流再判定**，判据不混用。

## 附带技能

`skills/label-taxonomy-governor`

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 三条纪律、触发条件、处理步骤、脚本边界 |
| `references/domain-a-taxonomy-rules.md` | A 域规则：正交维度、命名、枚举、四类漂移 |
| `references/domain-b-label-compliance.md` | B 域规则：强制标注表、禁用词、适用性判定、用词强弱 |
| `references/verdict-taxonomy.md` | 三态判据、四类漂移优先级、禁止出现的判定 |
| `references/experience-provenance.md` | **承袭 / 增量对照表**（不宣称首创） |
| `templates/label-spec-template.md` | 标签规格书模板 |
| `templates/label-audit-report-template.md` | 审查报告模板 |
| `config/rules.json` | 可配置规则：命名正则、保留词、分域禁用词、别名映射 |
| `scripts/check_label_consistency.py` | 口径一致性校验（Markdown + JSON 双输出） |
| `scripts/self_check.py` | 12 条冒烟断言 |

### 脚本用法

```bash
python scripts/check_label_consistency.py \
  --input declarations.json \
  --config config/rules.json \
  --output-md report.md \
  --output-json report.json

python scripts/self_check.py
```

`declarations.json` 结构：

```json
{
  "labels": [
    {"id": "integrity-level", "name": "完整性等级", "values": ["Low", "Medium", "High"],
     "source": "gate-manifest.json"}
  ],
  "declarations": [
    {"file": "gate-manifest.json", "key": "env.expectedIntegrity", "value": "Medium"},
    {"file": "label-guard.mjs", "key": "EXPECTED_INTEGRITY", "value": "Medium"},
    {"file": "M2-plan.md", "key": "expectedIntegrity", "value": "Low"}
  ]
}
```

脚本会把 `env.expectedIntegrity` / `EXPECTED_INTEGRITY` 归一到同一口径键，报出 `M2-plan.md` 的取值漂移。**脚本只查结构与一致性，不判定合法合规**；判定由模型按规则包完成，拍板由用户完成。

## 承袭与增量

| 承袭 | 增量 |
|---|---|
| `jnMetaCode/agency-agents-zh` 的 `design/design-ux-architect.md`（MIT） | 双域分流、三态判据、口径漂移脚本 |
| 本机 `pre-publish-evidence-gate`（先分流、四类缺口、三态、执行声明） | 迁到标签域，改为四类漂移 + 优先级 |
| 本机 `brand-delivery-compliance-expert`（逐项标注、依据可追溯、不适用≠缺失） | 与标签体系设计合并，两域共用一套输出格式 |
| 海巍驱蚊咨询报告 §4.3.1、海巍树脂谱系表 F30 行、brand-delivery 标签口径定案 | 转成可复用规则表、把「待拍板」做成独立输出项 |

完整对照见 `skills/label-taxonomy-governor/references/experience-provenance.md`；第三方许可全文见 `THIRD-PARTY-NOTICES.md`。**本专家不宣称首次发现任何标签设计规律。**

## 使用示例

- 帮我给这批内容设计一套标签体系，先说维度怎么切、命名怎么定。
- 这份产品标签文案帮我逐项查强制标注和禁用词，每条标明依据。
- 同一个标签在规格表、代码和文档里口径对不上，帮我定位漂移点。

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

`avatars/expert.png`，由图像生成工具按角色特征生成。可手动替换：PNG/JPG、512×512、≤500KB。

## 许可

MIT。第三方来源与版权声明见 `THIRD-PARTY-NOTICES.md`。
