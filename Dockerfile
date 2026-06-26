# 软考成绩监控器 Dockerfile
# 镜像名称: ruankao-monitor
# 容器名称: ruankao-monitor

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests beautifulsoup4 lxml python-dotenv

COPY simple_monitor.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "simple_monitor.py"]
