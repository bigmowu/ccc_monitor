# -*- coding: utf-8 -*-
"""
软考成绩监控系统 - 简化单文件版本
运行方式: docker run -d --env-file .env ruankao-monitor
"""
import time
import logging
import json
import os
import smtplib
import re
from datetime import datetime, date
from dataclasses import dataclass
from typing import List, Set

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
    
    # 监控间隔（秒）
    CHECK_INTERVAL = 1800  # 30分钟
    
    # 成绩关键词
    SCORE_KEYWORDS = ["成绩", "分数", "考试结果", "查询成绩", "成绩发布", "成绩查询", "合格标准"]
    
    # 邮件配置（从环境变量读取）
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

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
def should_skip_monitoring() -> tuple[bool, str]:
    """
    判断是否应该跳过监控（周末或节假日）
    
    Returns:
        tuple[bool, str]: (是否跳过, 原因)
    """
    today = date.today()
    weekday = today.weekday()  # 0-6, 0是周一，6是周日
    
    # 检查是否是周末
    if weekday >= 5:  # 5=周六, 6=周日
        return True, f"今天是周末（{'周六' if weekday == 5 else '周日'}），跳过监控"
    
    # TODO: 可以添加节假日判断逻辑
    # 比如添加一个节假日列表，或者调用节假日API
    
    return False, ""

# ==================== 监控器 ====================
class RuankaoMonitor:
    """软考官网监控器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_work_dynamic_news(self) -> List[dict]:
        """获取工作动态新闻"""
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
        return datetime.now().strftime('%Y-%m-%d')
    
    def check_score_news(self) -> List[dict]:
        """检查成绩相关新闻（仅显示2026年）"""
        all_news = self.get_work_dynamic_news()
        score_news = []
        target_year = datetime.now().strftime('%Y')
        
        for news in all_news:
            title_lower = news['title'].lower()
            news_year = news['date'][:4] if news['date'] else ''
            
            if news_year == target_year and any(kw.lower() in title_lower for kw in Config.SCORE_KEYWORDS):
                score_news.append(news)
                logger.info(f"发现{target_year}年成绩新闻: {news['title']}")
        
        return score_news

# ==================== 邮件通知器 ====================
class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self):
        self.config = Config()
    
    def send_notification(self, news_list: List[dict], all_news: List[dict] = None) -> bool:
        """发送监控报告邮件"""
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            
            if news_list:
                subject = f'[软考监控] 出成绩了！发现 {len(news_list)} 条成绩新闻'
            else:
                subject = '[软考监控] 尚未发布 - 本次检查未发现成绩新闻'
            
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_SENDER
            msg['To'] = self.config.EMAIL_RECEIVER
            msg['Subject'] = Header(subject, 'utf-8')
            
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h1>软考监控报告</h1>
            </div>
            """
            
            if news_list:
                html += f"""
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <strong>发现 {len(news_list)} 条成绩相关新闻！</strong>
                </div>
                <h2 style="color: #28a745;">成绩相关新闻</h2>
                """
                
                for i, news in enumerate(news_list, 1):
                    html += f"""
                    <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #28a745;">
                        <h3 style="margin: 0 0 10px 0;">{i}. {news['title']}</h3>
                        <p style="margin: 5px 0;">发布日期: {news['date']}</p>
                        <p style="margin: 5px 0;">详情链接: <a href="{news['url']}" target="_blank" style="color: #007bff;">点击查看</a></p>
                    </div>
                    """
            else:
                html += f"""
                <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <strong>本次检查未发现成绩相关新闻</strong>
                </div>
                """
            
            if all_news:
                html += f"""
                <h2 style="color: #6c757d; margin-top: 30px;">监控概况</h2>
                <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>工作动态总数:</strong> {len(all_news)} 条</p>
                    <p><strong>成绩相关新闻:</strong> {len(news_list)} 条</p>
                    <p><strong>检查时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <h3 style="color: #6c757d; margin-top: 20px;">最新工作动态 (前5条)</h3>
                """
                
                for i, news in enumerate(all_news[:5], 1):
                    html += f"""
                    <div style="background: #ffffff; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 2px solid #dee2e6;">
                        <p style="margin: 0;"><strong>{i}.</strong> {news['title']}</p>
                        <p style="margin: 5px 0; color: #6c757d; font-size: 12px;">{news['date']}</p>
                    </div>
                    """
            
            html += f"""
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                <p>监控网址: <a href="{Config.WORK_DYNAMIC_URL}" target="_blank" style="color: #007bff;">{Config.WORK_DYNAMIC_URL}</a></p>
                <p>监控频率: 每 {Config.CHECK_INTERVAL // 60} 分钟检查一次</p>
                <p>监控时间: 工作日（周末及节假日跳过）</p>
                <p>系统状态: 正常运行中</p>
            </div></body></html>
            """
            
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT, timeout=30) as server:
                server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                server.sendmail(self.config.EMAIL_SENDER, [self.config.EMAIL_RECEIVER], msg.as_string())
            
            logger.info("监控报告邮件发送成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """发送测试邮件"""
        try:
            from email.mime.text import MIMEText
            from email.header import Header
            
            msg = MIMEText('Ruankao Monitor Test Email - System is running\n\nConfig:\n- Interval: 30 minutes\n- Schedule: Workdays only\n- Notification: 163 Email', 'plain', 'utf-8')
            msg['From'] = self.config.EMAIL_SENDER
            msg['To'] = self.config.EMAIL_RECEIVER
            msg['Subject'] = Header('[Ruankao Monitor] Test Email', 'utf-8')
            
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT, timeout=30) as server:
                server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                server.sendmail(self.config.EMAIL_SENDER, [self.config.EMAIL_RECEIVER], msg.as_string())
            
            logger.info("测试邮件发送成功")
            return True
            
        except Exception as e:
            logger.error(f"测试邮件失败: {e}")
            return False

# ==================== 主程序 ====================
class MonitorAgent:
    """监控代理"""
    
    def __init__(self):
        self.monitor = RuankaoMonitor()
        self.notifier = EmailNotifier()
        self.state_file = 'monitor_state.json'
        self.processed_urls: Set[str] = self._load_state()
    
    def _load_state(self) -> Set[str]:
        """加载已处理状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f).get('processed_urls', []))
        except:
            pass
        return set()
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_urls': list(self.processed_urls),
                    'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def check_and_notify(self):
        """检查并发送通知（每次都发送监控报告）"""
        logger.info("=" * 60)
        logger.info(f"开始检查... {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # 获取所有新闻
            all_news = self.monitor.get_work_dynamic_news()
            
            # 获取成绩相关新闻
            score_news = self.monitor.check_score_news()
            
            # 发送监控报告邮件（无论是否有成绩新闻）
            logger.info(f"📊 准备发送监控报告: 总新闻 {len(all_news)} 条，成绩新闻 {len(score_news)} 条")
            
            if self.notifier.send_notification(score_news, all_news):
                logger.info("✅ 监控报告发送成功")
                
                # 如果有新的成绩新闻，更新状态
                new_score_news = [news for news in score_news if news['url'] not in self.processed_urls]
                if new_score_news:
                    logger.info(f"🎉 发现 {len(new_score_news)} 条新成绩新闻！")
                    for news in new_score_news:
                        self.processed_urls.add(news['url'])
                    self._save_state()
                
        except Exception as e:
            logger.error(f"检查出错: {e}")
    
    def run(self):
        """运行监控"""
        logger.info("🚀 软考成绩监控系统启动")
        logger.info(f"📧 {Config.EMAIL_SENDER} -> {Config.EMAIL_RECEIVER}")
        logger.info(f"⏰ 每 {Config.CHECK_INTERVAL // 60} 分钟检查一次")
        logger.info(f"🚫 周末和节假日自动跳过监控")
        
        # 发送测试邮件
        self.notifier.send_test_email()
        
        # 首次检查
        self.check_and_notify()
        
        # 定期监控
        logger.info("🔄 进入定期监控模式")
        
        while True:
            try:
                time.sleep(Config.CHECK_INTERVAL)
                
                # 检查是否应该跳过监控
                should_skip, reason = should_skip_monitoring()
                if should_skip:
                    logger.info(f"⏭️ 跳过本次监控: {reason}")
                    continue
                
                self.check_and_notify()
                
            except KeyboardInterrupt:
                logger.info("👋 系统停止")
                break
            except Exception as e:
                logger.error(f"监控出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试

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