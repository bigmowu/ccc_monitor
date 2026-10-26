# -*- coding: utf-8 -*-
"""
软考官网监控系统 - 简化单文件版本
运行方式: docker run -d --env-file .env ruankao-monitor
"""
import time
import logging
import json
import os
import signal
import sys
import smtplib
import re
from datetime import datetime, date, timedelta, timezone
from dataclasses import dataclass
from typing import List, Set, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("正在安装依赖包...")
    import subprocess
    subprocess.run(['pip', 'install', 'requests', 'beautifulsoup4', 'lxml'], check=True)
    import requests
    from bs4 import BeautifulSoup

# ==================== 配置管理 ====================
@dataclass
class Config:
    """系统配置"""
    # 软考官网
    RUANKAO_URL = "https://www.ruankao.org.cn"
    WORK_DYNAMIC_URL = "https://www.ruankao.org.cn/index/work.html"

    # 成绩关键词（用于在邮件中标记新闻类型）
    SCORE_KEYWORDS = ["成绩", "分数", "考试结果", "查询成绩", "成绩发布", "成绩查询", "合格标准"]

    # 监控目标考期（默认2026年下半年）
    TARGET_YEAR = os.getenv("TARGET_YEAR", "2026")
    TARGET_SEMESTER = os.getenv("TARGET_SEMESTER", "下半年")

    # 配置（从环境变量读取）
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))  # 默认10分钟

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 工具函数 ====================
def get_beijing_time() -> datetime:
    """获取当前北京时间（UTC+8）"""
    return datetime.now(timezone(timedelta(hours=8)))

def should_skip_monitoring() -> tuple[bool, str]:
    """
    判断是否应该跳过监控（20:00-06:00跳过）
    
    Returns:
        tuple[bool, str]: (是否跳过, 原因)
    """
    now = get_beijing_time()
    hour = now.hour
    
    # 20:00 - 06:00 之间跳过监控
    if hour >= 20 or hour < 6:
        return True, f"当前时间 {hour:02d}:{now.minute:02d}，处于静默时段（20:00-06:00），跳过监控"
    
    return False, ""

# ==================== 关键字摘要 ====================
# 中文停用词（用于关键字提取）
CHINESE_STOPWORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '但', '而', '或', '与', '及', '等', '对', '将', '为', '以',
    '于', '从', '被', '把', '让', '使', '如', '由', '之', '其', '此', '该', '此',
    '个', '中', '年', '月', '日', '时', '分', '第', '次', '项', '条', '件',
])

def extract_keywords(title: str, max_keywords: int = 5) -> List[str]:
    """
    从标题中提取关键字
    
    使用简单的基于关键词匹配的方法：
    1. 保留数字和年份
    2. 匹配预定义的领域关键词
    3. 去除停用词和标点符号
    
    Args:
        title: 新闻标题
        max_keywords: 最多返回多少个关键字
        
    Returns:
        关键字列表
    """
    keywords = []
    
    # 领域关键词库（按优先级排序）
    domain_keywords = [
        '成绩', '分数', '查询', '发布', '合格', '标准', '分数线',
        '考试', '报名', '通知', '公告', '通告', '规定', '政策',
        '计算机', '软件', '资格', '职业', '技术', '水平',
        '高级', '中级', '初级',
        '上半年', '下半年', '春季', '秋季',
        '考期', '场次', '考点', '准考证', '证书',
        '变更', '调整', '延期', '取消', '恢复', '新增',
        '2024', '2025', '2026', '2027',
    ]
    
    # 提取年份
    year_match = re.search(r'20\d{2}', title)
    if year_match:
        keywords.append(year_match.group())
    
    # 匹配领域关键词
    for kw in domain_keywords:
        if kw in title and kw not in keywords:
            keywords.append(kw)
        if len(keywords) >= max_keywords:
            break
    
    # 如果领域关键词不够，尝试提取其他有意义的词
    if len(keywords) < 2:
        # 从标题中提取名词性短语（简单中文分词）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', title)
        words = text.split()
        for word in words:
            if len(word) >= 2 and word not in CHINESE_STOPWORDS and word not in keywords:
                keywords.append(word)
            if len(keywords) >= max_keywords:
                break
    
    return keywords[:max_keywords]

def classify_news_type(title: str) -> str:
    """
    根据标题判断新闻类型
    
    优先级：score > policy > exam > general
    原因：政策类通告包含广泛，应该优先于泛泛的考试关键词
    
    Returns:
        'score' 成绩相关, 'policy' 政策通知, 'exam' 考试相关, 'general' 一般
    """
    title_lower = title.lower()
    
    # 成绩相关（最高优先级）
    if any(kw.lower() in title_lower for kw in Config.SCORE_KEYWORDS):
        return 'score'
    
    # 政策相关（第二优先级，因为政策通告覆盖范围广）
    policy_keywords = ['规定', '政策', '通知', '公告', '通告', '办法', '调整']
    if any(kw in title for kw in policy_keywords):
        return 'policy'
    
    # 考试相关
    exam_keywords = ['考试', '报名', '考期', '考点', '场次', '准考证', '证书']
    if any(kw in title for kw in exam_keywords):
        return 'exam'
    
    return 'general'

NEWS_TYPE_LABELS = {
    'score': ('🎯 成绩相关', '#dc3545'),
    'exam': ('📋 考试相关', '#007bff'),
    'policy': ('📜 政策通知', '#ffc107'),
    'general': ('📰 动态新闻', '#6c757d'),
}

# ==================== 监控器 ====================
class RuankaoMonitor:
    """软考官网监控器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_work_dynamic_news(self) -> List[dict]:
        """获取所有工作动态新闻"""
        try:
            response = self.session.get(Config.WORK_DYNAMIC_URL, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'lxml')
            news_list = []
            
            # 查找所有新闻项
            news_items = soup.find_all('li')
            for item in news_items:
                link = item.find('a', href=True)
                if link and link.get('href'):
                    title = link.get_text(strip=True)
                    if title and len(title) > 5:  # 过滤太短的标题
                        news_list.append({
                            'title': title,
                            'url': Config.RUANKAO_URL + link['href'] if link['href'].startswith('/') else link['href'],
                            'date': self._extract_date(item)
                        })
            
            logger.info(f"获取到 {len(news_list)} 条工作动态新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return []
    
    def _extract_date(self, item) -> str:
        """提取日期"""
        try:
            text = item.get_text(strip=True)
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', text)
            if date_match:
                return date_match.group()
        except:
            pass
        return get_beijing_time().strftime('%Y-%m-%d')
    
    def get_all_news(self) -> List[dict]:
        """获取所有工作动态新闻（带类型分类和关键字）"""
        raw_news = self.get_work_dynamic_news()
        enriched_news = []
        
        for news in raw_news:
            news_type = classify_news_type(news['title'])
            keywords = extract_keywords(news['title'])
            
            enriched_news.append({
                'title': news['title'],
                'url': news['url'],
                'date': news['date'],
                'type': news_type,
                'keywords': keywords,
                'type_label': NEWS_TYPE_LABELS.get(news_type, NEWS_TYPE_LABELS['general']),
            })
        
        return enriched_news

# ==================== 邮件通知器 ====================
class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self):
        self.config = Config()
    
    def _send_email(self, subject: str, html_body: str, timeout: int = 30) -> bool:
        """通用邮件发送方法
        
        Args:
            subject: 邮件主题
            html_body: HTML 正文
            timeout: SMTP 连接超时秒数（停止通知时应传短超时，如 5 秒）
        """
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_SENDER
            msg['To'] = self.config.EMAIL_RECEIVER
            msg['Subject'] = Header(subject, 'utf-8')
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT, timeout=timeout) as server:
                server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                server.sendmail(self.config.EMAIL_SENDER, [self.config.EMAIL_RECEIVER], msg.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_new_content_notification(self, new_items: List[dict], all_news: List[dict]) -> bool:
        """
        发送新内容发现通知邮件
        
        Args:
            new_items: 新发现的新闻列表（已包含 type, keywords 字段）
            all_news: 当前所有新闻列表（用于概况展示）
        """
        try:
            # 统计新内容类型
            score_count = sum(1 for n in new_items if n['type'] == 'score')
            policy_count = sum(1 for n in new_items if n['type'] == 'policy')
            exam_count = sum(1 for n in new_items if n['type'] == 'exam')
            general_count = sum(1 for n in new_items if n['type'] == 'general')
            
            # 构建有力的主题（按优先级选最激动的那个）
            if score_count > 0:
                subject = f'� 出成绩了！（{score_count} 条更新）'
            elif policy_count > 0:
                subject = f'📜 出政策了！（{policy_count} 条更新）'
            elif exam_count > 0:
                subject = f'📋 出考试相关了！（{exam_count} 条更新）'
            else:
                subject = f'� 出新闻了！（{len(new_items)} 条更新）'
            
            # 构建 HTML
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h1>🔔 软考监控 - 发现新内容</h1>
            </div>
            
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <strong>共发现 {len(new_items)} 条新内容</strong>
                <div style="margin-top: 8px; font-size: 14px; color: #555;">
                    {f'🎯 成绩相关 {score_count} 条' if score_count > 0 else ''}
                    {f'📋 考试相关 {exam_count} 条' if exam_count > 0 else ''}
                    {f'📜 其他动态 {other_count} 条' if other_count > 0 else ''}
                </div>
            </div>
            
            <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 8px;">📰 新增内容详情</h2>
            """
            
            # 逐条展示新内容
            for i, news in enumerate(new_items, 1):
                type_label, type_color = news.get('type_label', NEWS_TYPE_LABELS['general'])
                keywords_str = ' · '.join(news.get('keywords', [])) or '无关键字'
                
                html += f"""
                <div style="background: #f8f9fa; padding: 15px; margin: 12px 0; border-radius: 8px; border-left: 4px solid {type_color};">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="background: {type_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">
                            {type_label}
                        </span>
                        <span style="color: #6c757d; font-size: 12px;">📅 {news['date']}</span>
                    </div>
                    <h3 style="margin: 5px 0; font-size: 16px; color: #333;">
                        {i}. {news['title']}
                    </h3>
                    <div style="margin: 8px 0;">
                        <span style="color: #6c757d; font-size: 12px;">🔑 关键字:</span>
                        <span style="background: #e9ecef; padding: 2px 8px; border-radius: 4px; margin-left: 5px; font-size: 12px;">
                            {keywords_str}
                        </span>
                    </div>
                    <p style="margin: 8px 0;">
                        <a href="{news['url']}" target="_blank" style="color: #007bff; text-decoration: none; font-size: 13px;">
                            👉 查看详情
                        </a>
                    </p>
                </div>
                """
            
            # 监控概况
            html += f"""
            <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 8px; margin-top: 30px;">📊 监控概况</h2>
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <p style="margin: 5px 0;"><strong>工作动态总数:</strong> {len(all_news)} 条</p>
                <p style="margin: 5px 0;"><strong>本次新增:</strong> {len(new_items)} 条</p>
                <p style="margin: 5px 0;"><strong>检查时间:</strong> {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                <p>监控网址: <a href="{Config.WORK_DYNAMIC_URL}" target="_blank" style="color: #007bff;">{Config.WORK_DYNAMIC_URL}</a></p>
                <p>监控频率: 每 {Config.CHECK_INTERVAL // 60} 分钟检查一次</p>
                <p>静默时段: 20:00 - 06:00（自动跳过）</p>
                <p>系统状态: 正常运行中</p>
            </div>
            </body></html>
            """
            
            logger.info(f"新内容通知邮件发送成功（{len(new_items)} 条新内容）")
            return self._send_email(subject, html)
            
        except Exception as e:
            logger.error(f"新内容通知邮件发送失败: {e}")
            return False
    
    def send_startup_notification(self) -> bool:
        """发送启动通知邮件"""
        try:
            subject = '[软考监控] 🚀 系统已启动'
            
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h1>🚀 软考监控系统已启动</h1>
            </div>
            <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h2>系统配置</h2>
                <p><strong>发送邮箱:</strong> {self.config.EMAIL_SENDER}</p>
                <p><strong>接收邮箱:</strong> {self.config.EMAIL_RECEIVER}</p>
                <p><strong>检查频率:</strong> 每 {Config.CHECK_INTERVAL // 60} 分钟</p>
                <p><strong>静默时段:</strong> 20:00 - 06:00（自动跳过）</p>
                <p><strong>通知策略:</strong> 发现任何新内容时立即通知，每条新闻附带关键字摘要</p>
            </div>
            <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <strong>📋 监控说明</strong>
                <p style="margin: 10px 0;">系统将持续监控软考官网工作动态区域，发现任何新内容都会立即发送邮件通知。</p>
                <p style="margin: 10px 0;">每条通知包含新闻类型标记、关键字摘要和详情链接。</p>
            </div>
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                <p>启动时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>监控网址: <a href="{Config.WORK_DYNAMIC_URL}" target="_blank" style="color: #007bff;">{Config.WORK_DYNAMIC_URL}</a></p>
            </div></body></html>
            """
            
            logger.info("启动通知邮件发送成功")
            return self._send_email(subject, html)
            
        except Exception as e:
            logger.error(f"启动通知邮件失败: {e}")
            return False
    
    def send_stop_notification(self, reason: str = "正常停止") -> bool:
        """
        发送服务停止通知邮件
        
        Args:
            reason: 停止原因描述
        """
        try:
            subject = '[软考监控] ⚠️ 服务已停止'
            
            # 尝试从状态文件读取最后检查时间
            last_check_str = "未知"
            try:
                if os.path.exists('monitor_state.json'):
                    with open('monitor_state.json', 'r', encoding='utf-8') as f:
                        state = json.load(f)
                        last_check_str = state.get('last_check', '未知')
            except:
                pass
            
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h1>⚠️ 软考监控服务已停止</h1>
            </div>
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <strong>停止原因: {reason}</strong>
            </div>
            <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h2>运行状态</h2>
                <p><strong>停止时间:</strong> {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>最后检查:</strong> {last_check_str}</p>
                <p><strong>运行时长:</strong> 服务已停止，请查看日志了解详情</p>
            </div>
            <div style="background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <strong>💡 恢复建议</strong>
                <p style="margin: 10px 0;">如果使用 Docker 部署：</p>
                <code style="background: #e9ecef; padding: 5px 10px; border-radius: 4px;">docker restart ruankao-monitor</code>
            </div>
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                <p>监控网址: <a href="{Config.WORK_DYNAMIC_URL}" target="_blank" style="color: #007bff;">{Config.WORK_DYNAMIC_URL}</a></p>
            </div></body></html>
            """
            
            logger.info(f"停止通知邮件发送成功（原因: {reason}）")
            # 停止通知用短超时（5秒），因为可能正被 Docker 倒计时追杀
            return self._send_email(subject, html, timeout=5)
            
        except Exception as e:
            logger.error(f"停止通知邮件发送失败: {e}")
            return False
    
    def send_baseline_notification(self, all_news: List[dict]) -> bool:
        """
        首次运行快照建立通知
        
        告诉用户：这些现有的 N 条新闻已存为基线快照，
        只有后续真正新增的内容才会触发通知。
        """
        try:
            subject = f'[软考监控] 📸 初始快照已建立（{len(all_news)} 条现有新闻）'
            
            # 按类型统计
            type_counts = {}
            for n in all_news:
                t = n['type']
                type_counts[t] = type_counts.get(t, 0) + 1
            
            type_summary = '、'.join(
                f"{NEWS_TYPE_LABELS[t][0]} {c} 条" 
                for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
            )
            
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #17a2b8 0%, #007bff 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h1>📸 监控快照已建立</h1>
            </div>
            
            <div style="background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <strong>✅ 首次运行，已将当前 {len(all_news)} 条新闻存为基线快照</strong>
                <p style="margin: 10px 0; font-size: 14px; color: #555;">
                    这些是网站上已经存在的内容，<strong>不会触发通知</strong>。<br>
                    只有后续真正新增的新闻才会发送邮件提醒。
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <p><strong>快照时间:</strong> {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>快照总数:</strong> {len(all_news)} 条</p>
                <p><strong>类型分布:</strong> {type_summary}</p>
            </div>
            
            <h3 style="color: #333; border-bottom: 2px solid #17a2b8; padding-bottom: 8px; margin-top: 30px;">📋 快照内容（参考）</h3>
            """
            
            # 列出快照内容（最多20条，避免邮件过长）
            max_show = min(len(all_news), 20)
            for i, news in enumerate(all_news[:max_show], 1):
                type_label, type_color = news.get('type_label', NEWS_TYPE_LABELS['general'])
                html += f"""
                <div style="background: #ffffff; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 3px solid {type_color}; font-size: 13px;">
                    <span style="background: {type_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-right: 8px;">{type_label}</span>
                    {i}. {news['title']}
                </div>
                """
            
            if len(all_news) > max_show:
                html += f"""
                <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 10px;">
                    ...还有 {len(all_news) - max_show} 条新闻未展示，已全部存入快照
                </div>
                """
            
            html += f"""
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                <p>监控网址: <a href="{Config.WORK_DYNAMIC_URL}" target="_blank" style="color: #007bff;">{Config.WORK_DYNAMIC_URL}</a></p>
                <p>快照机制: 首次运行存基线 → 后续只通知真正新增内容</p>
            </div>
            </body></html>
            """
            
            logger.info(f"快照建立通知邮件发送成功（{len(all_news)} 条）")
            return self._send_email(subject, html)
            
        except Exception as e:
            logger.error(f"快照建立通知邮件发送失败: {e}")
            return False

# ==================== 主程序 ====================
class MonitorAgent:
    """监控代理"""
    
    def __init__(self):
        self.monitor = RuankaoMonitor()
        self.notifier = EmailNotifier()
        self.state_file = 'monitor_state.json'
        
        # 检查是否存在状态文件（用于判断首次运行）
        state_file_exists = os.path.exists(self.state_file)
        self.seen_urls: Set[str] = self._load_state()
        
        # 快照机制：只有在"无状态文件"且"加载后仍为空"时才判定为首次运行
        # 如果旧版本迁移过来有 processed_urls，不算首次运行
        self._is_first_run = (not state_file_exists) and len(self.seen_urls) == 0
        
        self._stop_requested = False
        self._stop_reason = ""
        
        # 注册信号处理器
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def handle_signal(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.info(f"📡 收到信号 {sig_name}，准备停止...")
            self._stop_requested = True
            self._stop_reason = f"收到系统信号 {sig_name}"
        
        # 仅在主线程注册
        try:
            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
        except (ValueError, AttributeError):
            # 在非主线程或某些环境中可能无法设置信号处理器
            logger.warning("⚠️ 无法注册信号处理器")
    
    def _load_state(self) -> Set[str]:
        """加载已处理状态（兼容旧版本 processed_urls key）"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 新格式 key
                    if 'seen_urls' in data:
                        return set(data.get('seen_urls', []))
                    # 旧格式 key（版本兼容迁移）
                    if 'processed_urls' in data:
                        logger.info("📦 检测到旧版本状态文件，自动迁移 processed_urls -> seen_urls")
                        return set(data.get('processed_urls', []))
        except Exception as e:
            logger.warning(f"加载状态文件失败（将以空状态启动）: {e}")
        return set()
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'seen_urls': list(self.seen_urls),
                    'last_check': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def check_and_notify(self):
        """检查并发送通知（首次运行建立快照，后续运行只通知真正新增的内容）"""
        logger.info("=" * 60)
        logger.info(f"开始检查... {get_beijing_time().strftime('%H:%M:%S')}")
        
        try:
            # 获取所有新闻（带类型和关键字）
            all_news = self.monitor.get_all_news()
            
            if not all_news:
                logger.warning("⚠️ 本次未获取到任何新闻，跳过")
                return
            
            # ========== 快照机制：首次运行建立基线快照 ==========
            if self._is_first_run:
                logger.info(f"📸 首次运行，建立快照：共 {len(all_news)} 条现有新闻")
                # 把当前所有 URL 作为基线快照存入，不逐条发新内容通知
                for news in all_news:
                    self.seen_urls.add(news['url'])
                self._save_state()
                
                # 发送一封"快照已建立"的摘要邮件，让用户知道初始状态
                if self.notifier.send_baseline_notification(all_news):
                    logger.info("✅ 快照建立通知邮件发送成功")
                else:
                    logger.warning("⚠️ 快照建立邮件发送失败（快照已保存，下次运行可通知到真正新增内容）")
                
                self._is_first_run = False
                return
            
            # ========== 正常增量对比：找出真正新增的 ==========
            new_items = [news for news in all_news if news['url'] not in self.seen_urls]
            
            if new_items:
                logger.info(f"📬 发现 {len(new_items)} 条新内容！")
                for item in new_items:
                    keywords_str = ' · '.join(item.get('keywords', []))
                    logger.info(f"  - [{item['type_label'][0]}] {item['title']} (关键字: {keywords_str})")
                
                # 发送新内容通知邮件
                if self.notifier.send_new_content_notification(new_items, all_news):
                    logger.info("✅ 新内容通知邮件发送成功")
                    
                    # 更新已见URL集合
                    for news in new_items:
                        self.seen_urls.add(news['url'])
                    self._save_state()
            else:
                logger.info(f"🔕 未发现新内容，静默中...")
                # 仍然更新最后检查时间
                self._save_state()
                
        except Exception as e:
            logger.error(f"检查出错: {e}")
    
    def run(self):
        """运行监控"""
        logger.info("🚀 软考官网监控系统启动")
        logger.info(f"📧 {Config.EMAIL_SENDER} -> {Config.EMAIL_RECEIVER}")
        logger.info(f"⏰ 每 {Config.CHECK_INTERVAL // 60} 分钟检查一次")
        logger.info(f" 静默时段: 20:00 - 06:00（自动跳过）")
        logger.info(f"� 快照机制: {'首次运行 → 建立基线快照' if self._is_first_run else f'已有快照 {len(self.seen_urls)} 条'}")
        logger.info(f"�� 只有真正新增的内容才触发邮件通知（避免垃圾消息）")
        
        stop_reason = "未知"
        
        try:
            # 发送启动通知邮件
            self.notifier.send_startup_notification()
            
            # 首次检查
            self.check_and_notify()
            
            # 定期监控
            logger.info("🔄 进入定期监控模式")
            
            while not self._stop_requested:
                # 分段 sleep，便于快速响应停止信号
                sleep_remaining = Config.CHECK_INTERVAL
                check_interval = 5  # 每5秒检查一次停止信号
                
                while sleep_remaining > 0 and not self._stop_requested:
                    sleep_time = min(check_interval, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
                
                if self._stop_requested:
                    stop_reason = self._stop_reason or "收到停止信号"
                    break
                
                # 检查是否应该跳过监控
                should_skip, reason = should_skip_monitoring()
                if should_skip:
                    logger.info(f"⏭️ 跳过本次监控: {reason}")
                    continue
                
                self.check_and_notify()
            
            stop_reason = self._stop_reason or "系统正常停止"
            
        except KeyboardInterrupt:
            stop_reason = "用户中断 (Ctrl+C)"
            logger.info(f"👋 {stop_reason}")
        except Exception as e:
            stop_reason = f"异常退出: {type(e).__name__}: {e}"
            logger.error(f"💥 监控主循环异常: {e}", exc_info=True)
        finally:
            logger.info(f"📤 发送停止通知邮件，原因: {stop_reason}")
            self.notifier.send_stop_notification(stop_reason)
            logger.info("👋 软考监控系统已完全退出")

def main():
    """主函数"""
    # 验证环境变量
    if not all([Config.EMAIL_SENDER, Config.EMAIL_PASSWORD, Config.EMAIL_RECEIVER]):
        logger.error("❌ 请在环境变量中配置 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")
        return
    
    agent = MonitorAgent()
    agent.run()

if __name__ == "__main__":
    main()
