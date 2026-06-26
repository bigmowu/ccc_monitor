#!/bin/bash
# 软考监控器 - 一键部署脚本

echo "=== 软考成绩监控器部署 ==="

if [ ! -f .env ]; then
    echo "❌ 错误: 未找到 .env 配置文件"
    echo "请先创建 .env 文件并配置邮箱信息"
    exit 1
fi

echo "📦 停止旧容器..."
docker stop ruankao-monitor 2>/dev/null || true
docker rm ruankao-monitor 2>/dev/null || true

echo "🔨 构建镜像..."
docker build -t ruankao-monitor .

echo "🚀 启动容器..."
docker run -d \
    --name ruankao-monitor \
    --env-file .env \
    --restart=always \
    ruankao-monitor

echo "✅ 部署完成！"
echo ""
echo "📋 常用命令:"
echo "  查看日志:   docker logs -f ruankao-monitor"
echo "  停止容器:   docker stop ruankao-monitor"
echo "  启动容器:   docker start ruankao-monitor"
echo "  删除容器:   docker rm ruankao-monitor"
echo "  重启容器:   docker restart ruankao-monitor"
