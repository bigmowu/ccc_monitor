# -*- coding: utf-8 -*-
"""
系统功能测试脚本
测试监控系统核心功能是否正常
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试依赖包导入"""
    print("🔍 测试依赖包导入...")
    try:
        import requests
        from bs4 import BeautifulSoup
        print("✅ 依赖包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 依赖包导入失败: {e}")
        return False

def test_website_access():
    """测试软考官网访问"""
    print("\n🔍 测试软考官网访问...")
    try:
        import requests
        response = requests.get("https://www.ruankao.org.cn", timeout=10)
        if response.status_code == 200:
            print("✅ 软考官网访问正常")
            return True
        else:
            print(f"❌ 软考官网访问异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 软考官网访问失败: {e}")
        return False

def test_news_parsing():
    """测试新闻解析功能"""
    print("\n🔍 测试新闻解析功能...")
    try:
        from monitor import RuankaoMonitor
        
        monitor = RuankaoMonitor()
        news_list = monitor.get_work_dynamic_news()
        
        if news_list:
            print(f"✅ 成功解析到 {len(news_list)} 条新闻")
            print(f"📰 最新新闻: {news_list[0]['title']}")
            return True
        else:
            print("⚠️ 未解析到新闻，可能是网页结构变化")
            return False
            
    except Exception as e:
        print(f"❌ 新闻解析失败: {e}")
        return False

def test_keyword_matching():
    """测试关键词匹配"""
    print("\n🔍 测试关键词匹配...")
    try:
        from monitor import RuankaoMonitor
        
        monitor = RuankaoMonitor()
        keywords = ["成绩", "分数", "考试结果"]
        
        score_news = monitor.check_score_related_news(keywords)
        
        print(f"✅ 关键词匹配功能正常，找到 {len(score_news)} 条相关新闻")
        if score_news:
            for news in score_news[:3]:  # 只显示前3条
                print(f"   - {news['title']}")
        return True
        
    except Exception as e:
        print(f"❌ 关键词匹配失败: {e}")
        return False

def test_email_config():
    """测试邮件配置"""
    print("\n🔍 测试邮件配置...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
            print("💡 请在 .env 文件中配置邮箱信息")
            return False
        else:
            print("✅ 邮件配置完整")
            sender = os.getenv('EMAIL_SENDER')
            receiver = os.getenv('EMAIL_RECEIVER')
            print(f"📧 发件人: {sender}")
            print(f"📧 收件人: {receiver}")
            return True
            
    except Exception as e:
        print(f"❌ 邮件配置检查失败: {e}")
        return False

def test_simple_version():
    """测试简化版"""
    print("\n🔍 测试简化版本...")
    try:
        # 检查简化版文件是否存在
        if os.path.exists('simple_monitor.py'):
            print("✅ 简化版文件存在")
            
            # 尝试导入
            import importlib.util
            spec = importlib.util.spec_from_file_location("simple_monitor", "simple_monitor.py")
            if spec and spec.loader:
                print("✅ 简化版文件格式正确")
                return True
            else:
                print("❌ 简化版文件格式错误")
                return False
        else:
            print("❌ 简化版文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 简化版测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 软考监控系统功能测试")
    print("=" * 60)
    
    tests = [
        ("依赖包导入", test_imports),
        ("官网访问", test_website_access),
        ("新闻解析", test_news_parsing),
        ("关键词匹配", test_keyword_matching),
        ("邮件配置", test_email_config),
        ("简化版本", test_simple_version)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试 '{name}' 执行出错: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:12s} : {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用。")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查配置和环境。")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)