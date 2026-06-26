# 软考成绩监控系统

基于Docker的软考成绩监控系统，定期监控软考官网工作动态区域，发现成绩相关新闻时自动发送邮件通知。

## 功能特点

- 🔍 自动监控软考官网工作动态区域
- 📧 每次检查都发送邮件报告（不会静默）
- 📅 仅监控当前年份的成绩新闻（避免显示往年旧记录）
- 🐳 完全Docker化部署，开箱即用
- ⏰ 可配置监控间隔（默认30分钟）
- 🚫 周末和节假日自动跳过监控
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

CHECK_INTERVAL=1800
```

**重要提示**：
- `EMAIL_PASSWORD` 不是邮箱登录密码，而是网易邮箱的授权码
- 获取授权码方法：登录网易邮箱 -> 设置 -> POP3/SMTP/IMAP -> 开启服务 -> 发送短信验证 -> 获取授权码

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

系统启动后会自动发送一封测试邮件和监控报告到配置的接收邮箱。

## 系统架构

```
┌─────────────────┐    30分钟间隔    ┌─────────────────┐
│  软考官网监控   │  ──────────────>  │  工作动态检查   │
│  Agent          │                  │  年份过滤       │
└─────────────────┘                  └─────────────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│  邮件通知服务   │  <─────────────  │  关键词匹配     │
│  网易163邮箱    │     发送报告     │  成绩新闻识别   │
└─────────────────┘                  └─────────────────┘
```

## 邮件标题规则

| 状态 | 邮件标题 |
|------|----------|
| 出成绩了 | `[软考监控] 出成绩了！发现 X 条成绩新闻` |
| 尚未发布 | `[软考监控] 尚未发布 - 本次检查未发现成绩新闻` |

## 监控关键词

系统默认监控以下关键词：
- 成绩
- 分数
- 考试结果
- 查询成绩
- 成绩发布
- 成绩查询
- 合格标准

如需修改关键词，请编辑 [config.py](config.py) 文件中的 `SCORE_KEYWORDS` 列表。

## 文件说明

| 文件 | 说明 |
|------|------|
| [simple_monitor.py](simple_monitor.py) | 监控主程序（核心逻辑） |
| [config.py](config.py) | 配置管理（关键词、URL等） |
| [requirements.txt](requirements.txt) | Python依赖列表 |
| [Dockerfile](Dockerfile) | Docker镜像构建文件 |
| [run.sh](run.sh) | 一键部署脚本 |
| [.env](.env) | 邮箱配置文件 |
| [.env.example](.env.example) | 配置模板 |

## 核心代码结构

### simple_monitor.py

```python
# 监控器类
class RuankaoMonitor:
    get_work_dynamic_news()     # 获取工作动态新闻列表
    check_score_news()          # 检查成绩相关新闻（仅当前年份）
    _extract_date()             # 从新闻中提取日期

# 邮件通知器类
class EmailNotifier:
    send_notification()         # 发送监控报告邮件
    send_test_email()           # 发送测试邮件

# 主函数
def main():
    # 启动监控循环
    # 每30分钟检查一次
    # 周末自动跳过
```

### config.py

```python
class Config:
    RUANKAO_URL          # 软考官网地址
    WORK_DYNAMIC_URL     # 工作动态页面地址
    SCORE_KEYWORDS       # 成绩相关关键词列表
    CHECK_INTERVAL       # 监控间隔（秒）
```

## 日志和状态

- 容器日志：`docker logs -f ruankao-monitor`
- 本地日志：`monitor.log`

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

## 许可证

MIT License
