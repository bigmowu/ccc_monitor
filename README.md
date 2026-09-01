# 软考成绩监控系统

基于Docker的软考成绩监控系统，专门监控**2026年下半年**软考官网工作动态区域，发现成绩/分数相关新闻时自动发送邮件通知。

## 功能特点

- 🎯 专门检测 **2026年下半年** 的成绩/分数新闻（标题需同时包含目标年份与考期）
- 📧 发现新成绩新闻时自动发送邮件通知（未发现时静默，不打扰）
- 🔍 标题关键词匹配 + URL 去重，避免重复通知同一条新闻
- 🐳 完全Docker化部署，开箱即用
- ⏰ 可配置监控间隔（代码默认5分钟，可通过环境变量调整）
- 🌙 夜间静默时段（20:00 - 06:00）自动跳过监控
- 📝 详细日志记录

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并配置邮箱信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_RECEIVER=receiver_email@163.com

CHECK_INTERVAL=300
TARGET_YEAR=2026
TARGET_SEMESTER=下半年
```

**重要提示**：
- `EMAIL_PASSWORD` 不是邮箱登录密码，而是网易邮箱的授权码
- 获取授权码方法：登录网易邮箱 -> 设置 -> POP3/SMTP/IMAP -> 开启服务 -> 发送短信验证 -> 获取授权码
- `TARGET_YEAR` / `TARGET_SEMESTER` 可省略，默认即为 `2026` 和 `下半年`

### 2. 使用Docker启动

```bash
# 构建镜像
docker build -t ruankao-monitor .

# 启动容器
docker run -d --name ruankao-monitor --env-file .env --restart=always ruankao-monitor

# 查看日志
docker logs -f ruankao-monitor

# 停止容器
docker stop ruankao-monitor

# 删除容器
docker rm ruankao-monitor
```

或者使用一键部署脚本：

```bash
./run.sh
```

### 3. 验证运行

系统启动后会自动发送一封启动通知邮件，之后仅在发现新的目标成绩新闻时发送通知邮件。

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SMTP_HOST | SMTP服务器地址 | smtp.163.com |
| SMTP_PORT | SMTP端口 | 465 |
| EMAIL_SENDER | 发件邮箱 | - |
| EMAIL_PASSWORD | 邮箱授权码 | - |
| EMAIL_RECEIVER | 收件邮箱 | - |
| CHECK_INTERVAL | 监控间隔（秒） | 300（5分钟） |
| TARGET_YEAR | 目标考试年份 | 2026 |
| TARGET_SEMESTER | 目标考期 | 下半年 |

## 监控范围

系统只匹配**标题同时包含以下要素**的新闻：

1. 目标年份（默认 `2026`）
2. 目标考期（默认 `下半年`）
3. 任一成绩关键词（见下方列表）

即标题形如「2026年下半年…成绩…」的新闻才会触发通知。2025年及更早、或2026年上半年的旧新闻会被自动忽略。

## 系统架构

```
┌─────────────────┐    CHECK_INTERVAL    ┌─────────────────┐
│  软考官网监控   │  ────────────────>  │  目标考期过滤   │
│  Agent          │                     │  2026下半年     │
└─────────────────┘                     └─────────────────┘
        │                                        │
        │                                        │
        ▼                                        ▼
┌─────────────────┐                  ┌─────────────────┐
│  邮件通知服务   │  <─────────────  │  关键词匹配     │
│  网易163邮箱    │     发送通知      │  + URL去重      │
└─────────────────┘                  └─────────────────┘
```

## 邮件标题规则

| 状态 | 邮件标题 |
|------|----------|
| 出成绩了 | `[软考监控] 出成绩了！发现 X 条成绩新闻` |
| 尚未发布 | `[软考监控] 尚未发布 - 本次检查未发现成绩新闻` |

> 注意：当前版本默认仅在**发现新成绩新闻**时发送邮件，未发现时静默，不会每次检查都发送。

## 监控关键词

系统默认监控以下关键词：
- 成绩
- 分数
- 考试结果
- 查询成绩
- 成绩发布
- 成绩查询
- 合格标准

如需修改关键词，请编辑 [simple_monitor.py](simple_monitor.py) 文件中的 `SCORE_KEYWORDS` 列表。

## 文件说明

| 文件 | 说明 |
|------|------|
| [simple_monitor.py](simple_monitor.py) | 监控主程序（核心逻辑，Docker 实际运行） |
| [config.py](config.py) | 备用配置模块（当前主程序内置配置，未直接使用） |
| [requirements.txt](requirements.txt) | Python依赖列表 |
| [Dockerfile](Dockerfile) | Docker镜像构建文件 |
| [run.sh](run.sh) | 一键部署脚本 |
| [.env](.env) | 邮箱配置文件（不入库） |
| [.env.example](.env.example) | 配置模板 |
| monitor_state.json | 已处理新闻状态（自动生成，建议挂载持久化） |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 |

## 核心代码结构

### simple_monitor.py

```python
class Config:
    TARGET_YEAR       # 目标年份（默认2026）
    TARGET_SEMESTER   # 目标考期（默认下半年）
    SCORE_KEYWORDS    # 成绩相关关键词列表
    CHECK_INTERVAL    # 监控间隔（秒）

class RuankaoMonitor:
    get_work_dynamic_news()     # 获取工作动态新闻列表
    check_score_news()          # 检测目标考期（2026下半年）成绩新闻
    _extract_date()             # 从新闻中提取日期

class EmailNotifier:
    send_notification()         # 发送成绩通知邮件
    send_startup_notification() # 发送启动通知邮件

class MonitorAgent:
    check_and_notify()          # 检查并通知（仅新成绩新闻时发邮件）
    run()                       # 监控主循环
```

## 日志和状态

- 容器日志：`docker logs -f ruankao-monitor`
- 本地日志：`monitor.log`
- 已处理新闻：`monitor_state.json`（建议通过 `-v $(pwd)/monitor_state.json:/app/monitor_state.json` 挂载持久化）

## 故障排查

### 邮件发送失败

1. 检查 `.env` 文件配置是否正确
2. 确认使用的是授权码而非登录密码
3. 检查网络连接和防火墙设置

### 无法访问软考官网

1. 检查网络连接
2. 查看Docker容器日志：`docker logs -f ruankao-monitor`

### Docker容器无法启动

1. 检查Docker服务是否运行
2. 查看详细错误信息：`docker logs ruankao-monitor`

## 技术栈

- Python 3.11
- Docker
- Requests - HTTP请求
- BeautifulSoup4 - HTML解析
- smtplib - 邮件发送
- python-dotenv - 环境变量管理

## 变更记录

详见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

MIT License
