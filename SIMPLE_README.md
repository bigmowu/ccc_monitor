# 软考成绩监控系统 - 简化版

超简洁的Docker化软考成绩监控系统，单文件部署，专门监控**2026年下半年**成绩/分数新闻。

## 🚀 快速开始

### 1. 创建配置文件

```bash
cp .env.example .env
```

或手动创建 `.env`（网易163邮箱）：

```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_RECEIVER=receiver_email@163.com
```

**重要**：
- `EMAIL_PASSWORD` 是网易邮箱的授权码，不是登录密码
- 获取授权码：网易邮箱设置 -> POP3/SMTP/IMAP -> 开启服务 -> 获取授权码

### 2. 构建Docker镜像

```bash
docker build -t ruankao-monitor .
```

### 3. 运行容器

```bash
docker run -d \
  --name ruankao-monitor \
  --env-file .env \
  -v $(pwd)/monitor_state.json:/app/monitor_state.json \
  ruankao-monitor
```

### 4. 查看日志

```bash
docker logs -f ruankao-monitor
```

## 📋 系统特点

- ✅ **超简洁**：单文件部署，无需复杂配置
- ✅ **Docker化**：一键启动，环境隔离
- ✅ **定向监控**：专门检测2026年下半年成绩/分数新闻
- ✅ **邮件通知**：发现新成绩新闻时发送网易163邮箱通知
- ✅ **去重机制**：避免重复通知同一新闻
- ✅ **夜间静默**：20:00 - 06:00 自动跳过监控
- ✅ **详细日志**：完整的运行日志记录

## 🔍 监控原理

系统定期访问 `https://www.ruankao.org.cn/index/work.html` 工作动态页面，仅匹配**标题同时包含以下要素**的新闻：

1. 目标年份（默认 `2026`，可用 `TARGET_YEAR` 修改）
2. 目标考期（默认 `下半年`，可用 `TARGET_SEMESTER` 修改）
3. 成绩关键词：成绩 / 分数 / 考试结果 / 查询成绩 / 成绩发布 / 成绩查询 / 合格标准

匹配到新新闻时，立即发送邮件通知。

## 📧 邮件内容

收到通知邮件时会包含：
- 🎯 新闻标题
- 📅 发布日期
- 🔗 详情链接
- 📊 相关新闻数量

## 🛠️ 常用命令

```bash
# 启动服务
docker start ruankao-monitor

# 停止服务
docker stop ruankao-monitor

# 重启服务
docker restart ruankao-monitor

# 查看状态
docker ps | grep ruankao-monitor

# 删除容器
docker rm -f ruankao-monitor

# 查看实时日志
docker logs -f --tail 100 ruankao-monitor

# 进入容器调试
docker exec -it ruankao-monitor sh
```

## 📁 文件说明

- `simple_monitor.py` - 核心监控程序（单文件包含所有功能）
- `Dockerfile` - Docker镜像构建文件
- `.env` - 环境变量配置文件
- `.env.example` - 配置模板
- `monitor_state.json` - 监控状态文件（自动生成，建议挂载持久化）
- `CHANGELOG.md` - 变更记录

## ⚙️ 配置说明

### 环境变量

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

## 📊 监控逻辑

```
每5分钟（可配置）：
├── 访问软考官网工作动态页面
├── 解析HTML获取新闻列表
├── 匹配「2026年下半年」+ 成绩关键词
├── 过滤已处理的新闻（去重）
├── 发现新新闻？
│   ├── 是 → 发送邮件通知
│   └── 否 → 静默，继续等待
└── 保存状态，等待下次检查
```

## 💡 使用建议

1. **首次运行**：系统会发送启动通知邮件，确认邮件配置正确
2. **定期检查**：建议每周检查一次容器运行状态
3. **日志管理**：日志文件会持续增长，建议定期清理
4. **备份配置**：备份 `.env` 文件和 `monitor_state.json`

## 📝 技术栈

- Python 3.11
- Docker
- Requests (HTTP请求)
- BeautifulSoup4 (HTML解析)

## 🎯 适用场景

- 等待2026年下半年软考成绩发布的考生
- 培训机构需要及时获取考试信息
- 企业人事部门关注员工考试结果

---

**注意**：请确保遵守软考官网的使用条款，合理设置监控频率，避免对官网造成过大压力。
