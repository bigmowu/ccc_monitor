# 软考成绩监控系统 - 快速部署指南

## 🚀 30秒快速开始

### 1. 创建配置文件
```bash
cat > .env << 'EOF'
# 网易163个人邮箱配置
SMTP_HOST=smtp.163.com
SMTP_PORT=465
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_RECEIVER=receiver_email@163.com

# 监控间隔时间（秒），默认30分钟
CHECK_INTERVAL=1800
EOF
```

### 2. 构建Docker镜像
```bash
docker build -t ruankao-monitor -f Dockerfile.simple .
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
- ✅ **智能监控**：每30分钟检查一次软考官网工作动态
- ✅ **周末跳过**：自动识别周末，周六日不监控
- ✅ **每次报告**：无论是否发现成绩，都发送监控报告
- ✅ **完整信息**：包含工作动态总数、最新新闻等信息
- ✅ **超简洁**：单文件部署，开箱即用

## 📧 邮件模板示例

### 未发现成绩新闻时：
```
🔔 软考监控报告

✅ 本次检查未发现成绩相关新闻

📊 监控概况
📰 工作动态总数: 6 条
🎯 成绩相关新闻: 0 条
⏰ 检查时间: 2026-06-26 14:30:00

📰 最新工作动态 (前5条)
1. 计算机技术与软件专业技术资格考试新版《网络规划设计师考试大纲》 正式颁布
   📅 2026-05-09

2. 2026年上半年计算机软件资格考试计算机化考试系统模拟练习的通告
   📅 2026-05-07
...
```

### 发现成绩新闻时：
```
🔔 软考监控报告

🎉 发现 1 条成绩相关新闻！

📋 成绩相关新闻
1. 2026年上半年计算机技术与软件专业技术资格考试成绩发布通告
   📅 发布日期: 2026-06-26
   🔗 详情链接: 点击查看

📊 监控概况
📰 工作动态总数: 7 条
🎯 成绩相关新闻: 1 条
...
```

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

- **监控频率**：每30分钟检查一次
- **监控时间**：仅工作日（周一至周五）
- **周末处理**：自动跳过周六、周日的监控
- **节假日**：可扩展添加节假日判断

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

系统默认监控以下关键词：
- 成绩
- 分数
- 考试结果
- 查询成绩
- 成绩发布
- 成绩查询
- 合格标准

如需修改，编辑 `simple_monitor.py` 文件中的 `SCORE_KEYWORDS` 列表。

## 📁 文件说明

- `simple_monitor.py` - 核心监控程序（单文件）
- `Dockerfile.simple` - Docker镜像构建文件
- `.env` - 环境变量配置文件
- `monitor_state.json` - 监控状态文件（自动生成）

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

1. **首次运行**：系统会发送测试邮件，确认邮件配置正确
2. **定期检查**：建议每周检查一次容器运行状态
3. **周末验证**：周末可以查看日志，确认自动跳过功能正常
4. **邮箱管理**：建议设置邮件规则，自动分类监控报告

## 🎯 系统架构

```
软考官网工作动态页面
         ↓
    每30分钟检查
         ↓
    解析HTML内容
         ↓
    匹配成绩关键词
         ↓
    生成监控报告
         ↓
    发送网易163邮箱
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
2. **监控频率**：30分钟间隔已足够，不建议更频繁
3. **网络稳定**：确保服务器网络连接稳定
4. **邮箱容量**：定期清理监控报告邮件，避免邮箱爆满

## 🚨 预期效果

- **工作日**：每30分钟收到一封监控报告邮件
- **周末**：不会收到监控报告（自动跳过）
- **发现成绩**：邮件标题会显示"🚨 软考成绩通知"
- **正常情况**：邮件标题显示"📊 软考监控报告"

---

**系统已优化为30分钟监控间隔 + 周末自动跳过 + 网易163邮箱支持！**