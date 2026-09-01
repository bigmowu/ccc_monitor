# 软考成绩监控系统 - 快速部署指南

专门监控**2026年下半年**软考成绩/分数新闻，发现新新闻时通过网易163邮箱自动通知。

## 🚀 快速开始

### 1. 创建配置文件
```bash
cp .env.example .env
```

或手动创建 `.env`：
```env
# 网易163个人邮箱配置
SMTP_HOST=smtp.163.com
SMTP_PORT=465
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_RECEIVER=receiver_email@163.com

# 监控间隔时间（秒），代码默认5分钟
CHECK_INTERVAL=300

# 监控目标考期，仅匹配标题含"2026年下半年"的成绩/分数新闻
TARGET_YEAR=2026
TARGET_SEMESTER=下半年
```

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

- ✅ **网易163邮箱**：使用个人邮箱，无需企业账户
- ✅ **定向监控**：专门检测2026年下半年成绩/分数新闻
- ✅ **智能去重**：同一新闻只通知一次，避免重复打扰
- ✅ **夜间静默**：20:00 - 06:00 自动跳过监控
- ✅ **按需通知**：仅发现新成绩新闻时发送邮件，平时静默
- ✅ **超简洁**：单文件部署，开箱即用

## 📧 邮件通知

- **启动时**：发送一封「系统已启动」通知邮件
- **发现新成绩新闻时**：发送「出成绩了！发现 X 条成绩新闻」邮件，包含新闻标题、发布日期、详情链接
- **未发现新新闻时**：保持静默，不发送邮件

## 🔧 网易邮箱配置说明

### 获取授权码步骤：
1. 登录网易163邮箱
2. 点击顶部"设置" → "POP3/SMTP/IMAP"
3. 开启"POP3/SMTP服务"
4. 按照提示发送短信验证
5. 获得"授权码"（这就是 EMAIL_PASSWORD）

### 配置示例：
```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
EMAIL_SENDER=myemail@163.com
EMAIL_PASSWORD=ABCDEFGHIJKLNMOP  # 这里填授权码，不是登录密码
EMAIL_RECEIVER=myemail@163.com   # 可以发给自己的邮箱
```

## ⏰ 监控时间安排

- **监控频率**：默认每5分钟检查一次（`CHECK_INTERVAL` 可调）
- **夜间静默**：20:00 - 06:00 自动跳过监控
- **监控范围**：仅匹配标题含「2026年下半年」且命中成绩关键词的新闻

## 🛠️ 常用命令

```bash
# 启动服务
docker start ruankao-monitor

# 停止服务
docker stop ruankao-monitor

# 重启服务
docker restart ruankao-monitor

# 查看最近100行日志
docker logs --tail 100 ruankao-monitor

# 实时查看日志
docker logs -f ruankao-monitor

# 删除容器
docker rm -f ruankao-monitor

# 进入容器调试
docker exec -it ruankao-monitor sh
```

## 📊 监控关键词

系统默认监控以下关键词（命中任意一个即可）：
- 成绩
- 分数
- 考试结果
- 查询成绩
- 成绩发布
- 成绩查询
- 合格标准

匹配规则：新闻标题必须同时包含目标年份（`TARGET_YEAR`）与目标考期（`TARGET_SEMESTER`），并命中任一关键词。如需修改关键词，编辑 `simple_monitor.py` 中的 `SCORE_KEYWORDS` 列表。

## 📁 文件说明

- `simple_monitor.py` - 核心监控程序（单文件）
- `Dockerfile` - Docker镜像构建文件
- `.env` - 环境变量配置文件（不入库）
- `.env.example` - 配置模板
- `monitor_state.json` - 监控状态文件（自动生成，建议挂载持久化）
- `CHANGELOG.md` - 变更记录

## 🐛 故障排查

### 邮件发送失败
1. 检查 `.env` 文件配置是否正确
2. 确认使用的是授权码而非登录密码
3. 检查容器日志：`docker logs ruankao-monitor`

### 无法访问软考官网
1. 检查网络连接
2. 查看容器日志确认具体错误
3. 可能需要配置代理

### 容器无法启动
1. 检查Docker服务：`docker ps`
2. 确认 `.env` 文件存在且格式正确
3. 查看详细错误：`docker logs ruankao-monitor`

## 💡 使用建议

1. **首次运行**：系统会发送启动通知邮件，确认邮件配置正确
2. **定期检查**：建议每周检查一次容器运行状态
3. **日志管理**：日志文件会持续增长，建议定期清理
4. **邮箱管理**：可设置邮件规则，自动分类成绩通知

## 🎯 系统架构

```
软考官网工作动态页面
         ↓
   每5分钟检查（可配置）
         ↓
   解析HTML内容
         ↓
   匹配「2026年下半年」+ 成绩关键词
         ↓
   过滤已处理新闻（去重）
         ↓
   发现新新闻 → 发送网易163邮箱
         ↓
   用户收到邮件通知
```

## 📝 技术栈

- Python 3.11
- Docker
- 网易163 SMTP服务
- Requests (HTTP请求)
- BeautifulSoup4 (HTML解析)

## ⚠️ 注意事项

1. **授权码安全**：不要泄露 `.env` 文件中的授权码
2. **监控频率**：默认5分钟间隔已足够，不建议过于频繁
3. **网络稳定**：确保服务器网络连接稳定
4. **状态持久化**：重启容器时建议挂载 `monitor_state.json`，避免重复通知

## 🚨 预期效果

- **启动时**：收到一封「系统已启动」通知邮件
- **发现成绩**：收到「出成绩了！发现 X 条成绩新闻」通知邮件
- **平时**：静默运行，不发送打扰邮件
- **夜间**：20:00 - 06:00 跳过监控

---

**系统已优化为：专门监控2026年下半年成绩/分数 + 按需通知 + 夜间静默！**
