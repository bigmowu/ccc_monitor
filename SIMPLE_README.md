# 软考成绩监控系统 - 简化版

超简洁的Docker化软考成绩监控系统，单文件部署，10分钟监控一次。

## 🚀 快速开始

### 1. 创建配置文件

```bash
cat > .env << 'EOF'
# 腾讯企业邮箱配置
SMTP_HOST=smtp.exmail.qq.com
SMTP_PORT=465
EMAIL_SENDER=your_email@company.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_RECEIVER=receiver_email@company.com
EOF
```

**重要**：
- `EMAIL_PASSWORD` 是腾讯企业邮箱的授权码，不是登录密码
- 获取授权码：邮箱设置 -> 账户 -> POP3/SMTP服务 -> 生成授权码

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

- ✅ **超简洁**：单文件部署，无需复杂配置
- ✅ **Docker化**：一键启动，环境隔离
- ✅ **智能监控**：监控软考官网工作动态区域
- ✅ **邮件通知**：发现成绩新闻立即发送腾讯企业邮箱
- ✅ **去重机制**：避免重复通知同一新闻
- ✅ **详细日志**：完整的运行日志记录

## 🔍 监控原理

系统定期访问 `https://www.ruankao.org.cn/index/work.html` 工作动态页面，检查是否包含以下关键词：

- 成绩
- 分数  
- 考试结果
- 查询成绩
- 成绩发布
- 成绩查询
- 合格标准

发现匹配新闻时，立即发送邮件通知。

## 📧 邮件示例

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
- `Dockerfile.simple` - 简化版Docker镜像构建文件
- `.env` - 环境变量配置文件
- `monitor_state.json` - 监控状态文件（自动生成）

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SMTP_HOST | SMTP服务器地址 | smtp.exmail.qq.com |
| SMTP_PORT | SMTP端口 | 465 |
| EMAIL_SENDER | 发件邮箱 | - |
| EMAIL_PASSWORD | 邮箱授权码 | - |
| EMAIL_RECEIVER | 收件邮箱 | - |

### 修改监控间隔

编辑 `simple_monitor.py` 文件中的 `CHECK_INTERVAL`：

```python
CHECK_INTERVAL = 600  # 改为其他秒数，如 300 = 5分钟
```

修改后需要重新构建镜像：
```bash
docker build -t ruankao-monitor -f Dockerfile.simple .
```

## 🔧 故障排查

### 邮件发送失败

1. 检查 `.env` 文件配置是否正确
2. 确认使用的是授权码而非登录密码
3. 检查容器日志：`docker logs ruankao-monitor`

### 无法访问软考官网

1. 检查网络连接
2. 查看容器日志确认具体错误
3. 可能需要配置代理（暂不支持）

### 容器无法启动

1. 检查Docker服务是否运行：`docker ps`
2. 确认 `.env` 文件存在且格式正确
3. 查看详细错误：`docker logs ruankao-monitor`

## 📊 监控逻辑

```
每10分钟：
├── 访问软考官网工作动态页面
├── 解析HTML获取新闻列表
├── 匹配成绩相关关键词
├── 过滤已处理的新闻
├── 发现新新闻？
│   ├── 是 → 发送邮件通知
│   └── 否 → 继续等待
└── 保存状态，等待下次检查
```

## 💡 使用建议

1. **首次运行**：系统会发送测试邮件，确认邮件配置正确
2. **定期检查**：建议每周检查一次容器运行状态
3. **日志管理**：日志文件会持续增长，建议定期清理
4. **备份配置**：备份 `.env` 文件和 `monitor_state.json`

## 📝 技术栈

- Python 3.11
- Docker
- Requests (HTTP请求)
- BeautifulSoup4 (HTML解析)

## 🎯 适用场景

- 软考考生等待成绩发布
- 培训机构需要及时获取考试信息
- 企业人事部门关注员工考试结果

---

**注意**：请确保遵守软考官网的使用条款，合理设置监控频率，避免对官网造成过大压力。