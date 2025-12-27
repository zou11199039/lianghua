<!-- 请在提交 PR 时按模板填写，便于审查与回退 -->

# PR 标题（简短清晰）
例如：`ci: add pytest workflow`、`fix: handle None from xtdata`、`feat: add MeanReversionStrategy`。

## 变更类型
- [ ] feat: 新功能
- [ ] fix: bug 修复
- [ ] docs: 文档更新
- [ ] test: 测试用例变更/补充
- [ ] chore: 构建/工具/依赖变更

## 变更描述
请用 1-3 句概述本次变更的目的与要点。

## 关联 Issue / 任务
- 关联任务/Issue 编号（如果有）：

## 变更影响范围
列出受影响的模块/文件（例如：`src/strategies/mean_reversion.py`, ` .github/workflows/ci.yml`）

## 验证步骤（测试计划）
请列出本地或 CI 中验证变更的方法：
1. 在本地创建并激活虚拟环境
2. 安装依赖：`pip install -r requirements.txt`
3. 运行测试：`pytest -q` 并确认全部通过
4. （如有）手动运行脚本或示例以验证行为

## 回滚计划
若变更导致问题，如何快速回退：
- 直接 revert 本次 PR
- 恢复到上一次通过 CI 的提交

## Reviewer 指南（审查要点）
- 注意检查测试覆盖面是否充分
- 检查是否引入不可选的外部依赖（如需可选依赖请使用懒加载或在 README 中声明）
- 检查配置/密钥是否未被提交（使用 `config.example.json` 并提醒用户在 CI 中使用 Secrets）

## 截图 / 运行日志（如适用）
请附上界面截图或测试日志片段（若涉及 UI 或行为差异）

---

谢谢你的贡献！✅ 请在 PR 描述中贴出本模板内容并逐项填写，便于快速通过审查与合并。