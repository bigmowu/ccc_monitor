# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass
from typing import List
import re

@dataclass
class MonitoringConfig:
    """监控配置类"""
    # 软考官网配置
    RUANKAO_URL: str = "https://www.ruankao.org.cn"
    WORK_DYNAMIC_URL: str = "https://www.ruankao.org.cn/index/work.html"
    
    # 监控间隔时间（秒）
    CHECK_INTERVAL: int = 600  # 10分钟
    
    # 成绩相关关键词
    SCORE_KEYWORDS: List[str] = None
    
    # 邮件配置
    SMTP_HOST: str = "smtp.163.com"
    SMTP_PORT: int = 465
    
    def __post_init__(self):
        if self.SCORE_KEYWORDS is None:
            self.SCORE_KEYWORDS = [
                "成绩", "分数", "考试结果", "查询成绩", 
                "成绩发布", "成绩查询", "合格标准"
            ]

# 从环境变量获取配置
def get_config() -> MonitoringConfig:
    """从环境变量获取配置"""
    config = MonitoringConfig()
    
    # 邮件配置
    config.SMTP_HOST = os.getenv("SMTP_HOST", config.SMTP_HOST)
    config.SMTP_PORT = int(os.getenv("SMTP_PORT", config.SMTP_PORT))
    config.EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    config.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    config.EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
    
    # 监控配置
    config.CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", config.CHECK_INTERVAL))
    
    return config