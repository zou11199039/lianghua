# 量化交易系统（基于 QMT）

这是一个基于 QMT / qmtmini 的本地量化交易系统原型，主要功能：

- 使用 QMT 客户端（需在本机运行）下载行情数据并存入本地数据库/Parquet
- 提供回测、策略框架、中文界面和钉钉通知集成

快速开始：

1. 确保已安装并登录 QMT / 迅投极速交易终端（你已经有桌面快捷方式，如“中航证券QMT实盘-交易端”）。
2. 安装依赖（建议使用虚拟环境）：
   pip install -r requirements.txt
3. 运行示例下载脚本（若未运行终端，会尝试用快捷方式启动）:
   python scripts/download_history.py --codes 600000.SH --start 2020-01-01

定时任务（Scheduler）：
- 项目包含示例调度器 `scripts/scheduler.py`（基于 APScheduler），用于定时触发数据增量下载并写入本地存储。
- 测试示例（每 60 秒运行一次）：
  python scripts/scheduler.py --interval 60 --codes 600000.SH --period 1d

配置说明：
- 数据存储位于 `db/` 目录，默认使用 SQLite + Parquet 存储（轻量开发）。
- 实盘下单依赖 qmtmini 接口及权限，当前仓库实现了数据下载与本地存储的初始模块。

安全提示：
- 请不要在公共仓库中泄露你的 API Key 或钉钉 Webhook。将敏感配置放在本地 `config.json` 或使用环境变量管理。
