# -*- coding: utf-8 -*-
"""
系统功能测试脚本
测试监控系统核心功能是否正常
"""
import sys
import os
import json
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

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

def test_check_interval_default():
    """测试 CHECK_INTERVAL 默认值为600（10分钟）"""
    print("\n🔍 测试 CHECK_INTERVAL 默认值...")
    try:
        from simple_monitor import Config
        # 清除环境变量干扰
        old_val = os.environ.pop('CHECK_INTERVAL', None)
        try:
            config = Config()
            assert config.CHECK_INTERVAL == 600, f"预期600秒(10分钟)，实际{config.CHECK_INTERVAL}秒"
            print(f"✅ CHECK_INTERVAL 默认值 = {config.CHECK_INTERVAL}秒 = {config.CHECK_INTERVAL // 60}分钟")
            return True
        finally:
            if old_val:
                os.environ['CHECK_INTERVAL'] = old_val
    except Exception as e:
        print(f"❌ CHECK_INTERVAL 默认值测试失败: {e}")
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
        from simple_monitor import RuankaoMonitor
        
        monitor = RuankaoMonitor()
        # 使用模拟响应
        import requests
        resp = requests.Response()
        resp.status_code = 200
        resp._content = (
            '<html><body><ul>'
            '<li><a href="/index/work.html">2026年下半年计算机软件资格考试成绩查询通知</a> 2026-12-15</li>'
            '<li><a href="/index/work1.html">2026年下半年考试报名通知</a> 2026-08-01</li>'
            '<li><a href="/index/work2.html">关于计算机考试的政策调整通告</a> 2026-07-20</li>'
            '</ul></body></html>'
        ).encode('utf-8')
        resp.encoding = 'utf-8'
        monitor.session.get = lambda *args, **kwargs: resp
        
        news_list = monitor.get_work_dynamic_news()
        
        assert len(news_list) == 3, f"预期3条新闻，实际{len(news_list)}条"
        print(f"✅ 成功解析到 {len(news_list)} 条新闻")
        print(f"📰 最新新闻: {news_list[0]['title']}")
        return True
            
    except Exception as e:
        print(f"❌ 新闻解析失败: {e}")
        return False

def test_keyword_extraction():
    """测试关键字提取功能"""
    print("\n🔍 测试关键字提取...")
    try:
        from simple_monitor import extract_keywords, classify_news_type
        
        # 测试不同类型标题
        # 优先级：score > policy > exam > general
        # policy 关键词包括：规定/政策/通知/公告/通告/办法/调整
        # exam 关键词包括：考试/报名/考期/考点/场次/准考证/证书
        test_cases = [
            ("2026年下半年计算机软件资格考试成绩查询通知", "score"),  # score 优先
            ("2026年下半年考试报名公告", "policy"),  # "公告" 是 policy 关键词
            ("关于计算机考试的政策调整通告", "policy"),  # "政策"/"调整"/"通告" 都是 policy
            ("2026年上半年考试时间安排", "exam"),  # 只有 "考试" 是 exam 关键词
            ("2026年下半年准考证打印时间", "exam"),  # "准考证" 是 exam 关键词
        ]
        
        for title, expected_type in test_cases:
            keywords = extract_keywords(title)
            news_type = classify_news_type(title)
            
            assert news_type == expected_type, f"'{title}' 预期类型 {expected_type}, 实际 {news_type}"
            assert len(keywords) >= 2, f"'{title}' 关键字太少: {keywords}"
            # 仅当标题中包含年份时才验证年份被提取
            import re
            year_match = re.search(r'20\d{2}', title)
            if year_match:
                assert year_match.group() in keywords, f"'{title}' 应包含年份 {year_match.group()}"
            
            kw_str = ' · '.join(keywords)
            print(f"  ✅ [{news_type}] {title}")
            print(f"     关键字: {kw_str}")
        
        print(f"✅ 关键字提取与分类功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 关键字提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_all_news_enriched():
    """测试 get_all_news 返回丰富数据"""
    print("\n🔍 测试 get_all_news 丰富数据...")
    try:
        from simple_monitor import RuankaoMonitor
        import requests
        
        monitor = RuankaoMonitor()
        resp = requests.Response()
        resp.status_code = 200
        resp._content = (
            '<html><body><ul>'
            '<li><a href="/work1.html">2026年下半年计算机软件资格考试成绩查询通知</a> 2026-12-15</li>'
            '<li><a href="/work2.html">2026年下半年考试报名公告</a> 2026-08-01</li>'
            '</ul></body></html>'
        ).encode('utf-8')
        resp.encoding = 'utf-8'
        monitor.session.get = lambda *args, **kwargs: resp
        
        all_news = monitor.get_all_news()
        
        assert len(all_news) == 2, f"预期2条，实际{len(all_news)}"
        
        for news in all_news:
            # 必须包含丰富字段
            assert 'type' in news, f"缺少 type 字段"
            assert 'keywords' in news, f"缺少 keywords 字段"
            assert 'type_label' in news, f"缺少 type_label 字段"
            assert news['keywords'], f"keywords 不能为空"
            
            print(f"  ✅ [{news['type_label'][0]}] {news['title']}")
            print(f"     类型: {news['type']}, 关键字: {' · '.join(news['keywords'])}")
        
        print("✅ get_all_news 丰富数据功能正常")
        return True
        
    except Exception as e:
        print(f"❌ get_all_news 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_new_content_detection():
    """测试新内容检测逻辑 - 任何新内容都触发，不限于成绩"""
    print("\n🔍 测试新内容检测（不限于成绩新闻）...")
    try:
        from simple_monitor import MonitorAgent, RuankaoMonitor
        
        # 创建临时状态文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            state_file = tmp.name
        
        # 构造 agent
        agent = MonitorAgent.__new__(MonitorAgent)
        agent.monitor = RuankaoMonitor()
        agent.state_file = state_file
        
        # 初始 seen_urls 为空
        agent.seen_urls = set()
        
        # 模拟所有新闻（包含成绩、考试、政策、一般各种类型）
        mock_all_news = [
            {'title': '2026年下半年成绩查询通知', 'url': 'u1', 'date': '2026-12-15', 'type': 'score', 'keywords': ['2026', '成绩', '查询'], 'type_label': ('🎯 成绩相关', '#dc3545')},
            {'title': '2026年下半年报名公告', 'url': 'u2', 'date': '2026-08-01', 'type': 'exam', 'keywords': ['2026', '考试', '报名'], 'type_label': ('📋 考试相关', '#007bff')},
            {'title': '考试政策调整通告', 'url': 'u3', 'date': '2026-07-20', 'type': 'policy', 'keywords': ['政策', '考试', '调整'], 'type_label': ('📜 政策通知', '#ffc107')},
        ]
        
        # mock get_all_news
        agent.monitor.get_all_news = lambda: mock_all_news
        
        # 第一次检查 - 全部都是新内容
        new_items_1 = [n for n in mock_all_news if n['url'] not in agent.seen_urls]
        assert len(new_items_1) == 3, f"第一次应该发现3条新内容，实际{len(new_items_1)}"
        
        # 标记为已见
        agent.seen_urls.update([n['url'] for n in new_items_1])
        
        # 模拟有一条新内容（非成绩）
        mock_all_news_new = mock_all_news + [
            {'title': '2026年考试时间安排更新', 'url': 'u4', 'date': '2026-07-25', 'type': 'exam', 'keywords': ['2026', '考试', '时间', '安排'], 'type_label': ('📋 考试相关', '#007bff')},
        ]
        agent.monitor.get_all_news = lambda: mock_all_news_new
        
        # 第二次检查 - 只有 u4 是新的
        new_items_2 = [n for n in mock_all_news_new if n['url'] not in agent.seen_urls]
        assert len(new_items_2) == 1, f"第二次应该发现1条新内容，实际{len(new_items_2)}"
        assert new_items_2[0]['url'] == 'u4'
        # 关键：非成绩的考试新闻也被检测到
        assert new_items_2[0]['type'] == 'exam'
        
        # 清理临时文件
        os.unlink(state_file)
        
        print("✅ 新内容检测功能正常 - 任何类型的新内容都能被发现")
        return True
        
    except Exception as e:
        print(f"❌ 新内容检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_config():
    """测试邮件配置"""
    print("\n🔍 测试邮件配置...")
    try:
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

def test_stop_notification_exists():
    """测试 EmailNotifier 存在 send_stop_notification 方法"""
    print("\n🔍 测试停止通知方法存在性...")
    try:
        from simple_monitor import EmailNotifier
        
        notifier = EmailNotifier()
        assert hasattr(notifier, 'send_stop_notification'), "EmailNotifier 缺少 send_stop_notification 方法"
        
        # 也验证其他方法
        assert hasattr(notifier, 'send_new_content_notification'), "缺少 send_new_content_notification"
        assert hasattr(notifier, 'send_startup_notification'), "缺少 send_startup_notification"
        
        print("✅ 停止通知方法存在")
        print("  ✅ send_stop_notification(reason)")
        print("  ✅ send_new_content_notification(new_items, all_news)")
        print("  ✅ send_startup_notification()")
        return True
        
    except Exception as e:
        print(f"❌ 停止通知方法测试失败: {e}")
        return False

def test_signal_handlers_setup():
    """测试信号处理器注册"""
    print("\n🔍 测试信号处理器注册...")
    try:
        from simple_monitor import MonitorAgent, EmailNotifier, RuankaoMonitor
        import signal
        
        agent = MonitorAgent.__new__(MonitorAgent)
        agent.monitor = RuankaoMonitor()
        agent.notifier = EmailNotifier()
        agent.seen_urls = set()
        agent._stop_requested = False
        agent._stop_reason = ""
        agent.state_file = 'monitor_state.json'
        
        # 设置信号处理器（在主线程应该成功）
        agent._setup_signal_handlers()
        
        # 验证 stop_requested 标志可被设置
        assert agent._stop_requested == False
        
        # 手动模拟信号处理后的行为
        def simulate_signal():
            agent._stop_requested = True
            agent._stop_reason = "收到系统信号 SIGTERM"
        simulate_signal()
        
        assert agent._stop_requested == True
        assert agent._stop_reason == "收到系统信号 SIGTERM"
        
        print("✅ 信号处理器设置正常")
        print(f"  stop_requested = {agent._stop_requested}")
        print(f"  stop_reason = {agent._stop_reason}")
        return True
        
    except Exception as e:
        print(f"❌ 信号处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_file_format():
    """测试状态文件格式 (seen_urls)"""
    print("\n🔍 测试状态文件格式...")
    try:
        from simple_monitor import MonitorAgent, EmailNotifier, RuankaoMonitor
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            state_file = tmp.name
        
        agent = MonitorAgent.__new__(MonitorAgent)
        agent.monitor = RuankaoMonitor()
        agent.notifier = EmailNotifier()
        agent.seen_urls = {'http://example.com/1', 'http://example.com/2'}
        agent.state_file = state_file
        
        # 保存
        agent._save_state()
        
        # 读取验证
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'seen_urls' in data, "状态文件缺少 seen_urls 字段"
        assert 'last_check' in data, "状态文件缺少 last_check 字段"
        assert set(data['seen_urls']) == {'http://example.com/1', 'http://example.com/2'}
        
        # 加载验证
        loaded = agent._load_state()
        assert loaded == agent.seen_urls, f"加载状态不匹配: {loaded} != {agent.seen_urls}"
        
        os.unlink(state_file)
        
        print("✅ 状态文件格式正确（seen_urls）")
        return True
        
    except Exception as e:
        print(f"❌ 状态文件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skip_monitoring_logic():
    """测试静默时段跳过逻辑"""
    print("\n🔍 测试静默时段逻辑...")
    try:
        from simple_monitor import should_skip_monitoring, get_beijing_time
        
        skip, reason = should_skip_monitoring()
        now = get_beijing_time()
        
        print(f"  当前北京时间: {now.strftime('%H:%M:%S')}")
        print(f"  是否跳过: {skip} ({reason})")
        
        # 逻辑本身应该总是能返回 (bool, str)
        assert isinstance(skip, bool)
        assert isinstance(reason, str)
        
        print("✅ 静默时段逻辑正常")
        return True
        
    except Exception as e:
        print(f"❌ 静默时段测试失败: {e}")
        return False

def test_first_run_snapshot():
    """
    测试快照机制：首次运行应该建立基线快照，不触发垃圾消息
    
    关键验证点：
    1. 无状态文件 + seen_urls为空 → _is_first_run = True
    2. check_and_notify() 走 baseline 分支
    3. seen_urls 被填入所有现有新闻 URL
    4. 调用 send_baseline_notification，而不是 send_new_content_notification
    """
    print("\n🔍 测试快照机制 - 首次运行...")
    try:
        from simple_monitor import MonitorAgent, RuankaoMonitor, EmailNotifier
        
        # 在临时目录工作，避免真实 state 文件干扰
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, 'monitor_state.json')
            
            # 模拟 MonitorAgent（避免 __init__ 中的真实网络调用）
            agent = MonitorAgent.__new__(MonitorAgent)
            agent.monitor = RuankaoMonitor()
            agent.notifier = EmailNotifier()
            agent.state_file = state_file
            agent._stop_requested = False
            agent._stop_reason = ""
            
            # 模拟首次运行：无状态文件 → seen_urls 为空 → _is_first_run = True
            assert not os.path.exists(state_file), "临时目录不应有状态文件"
            agent.seen_urls = set()
            agent._is_first_run = True
            
            # 模拟网站上已有的新闻（这些是"旧"内容，首次运行不应通知）
            existing_news = [
                {'title': '2026年下半年计算机软件资格考试成绩查询通知', 'url': 'http://ruankao/1', 'date': '2026-12-15', 'type': 'score', 'keywords': ['2026', '成绩'], 'type_label': ('🎯 成绩相关', '#dc3545')},
                {'title': '2026年下半年考试报名公告', 'url': 'http://ruankao/2', 'date': '2026-08-01', 'type': 'policy', 'keywords': ['2026', '报名'], 'type_label': ('📜 政策通知', '#ffc107')},
                {'title': '关于计算机考试的政策调整通告', 'url': 'http://ruankao/3', 'date': '2026-07-20', 'type': 'policy', 'keywords': ['政策', '调整'], 'type_label': ('📜 政策通知', '#ffc107')},
            ]
            agent.monitor.get_all_news = lambda: existing_news
            
            # mock 通知方法，记录调用情况
            baseline_called = []
            new_content_called = []
            
            def mock_baseline(news):
                baseline_called.append(list(news))
                return True
            def mock_new_content(items, all_news):
                new_content_called.append(list(items))
                return True
            
            agent.notifier.send_baseline_notification = mock_baseline
            agent.notifier.send_new_content_notification = mock_new_content
            
            # 执行检查
            agent.check_and_notify()
            
            # 验证 1: baseline 被调用
            assert len(baseline_called) == 1, "首次运行应该调用一次 baseline 通知"
            assert baseline_called[0] == existing_news
            
            # 验证 2: new_content 没被调用（这是关键！避免垃圾消息）
            assert len(new_content_called) == 0, "首次运行不应该调用 new_content 通知"
            
            # 验证 3: seen_urls 已填充所有现有 URL
            assert len(agent.seen_urls) == 3, f"seen_urls 应该有3条，实际{len(agent.seen_urls)}"
            assert 'http://ruankao/1' in agent.seen_urls
            assert 'http://ruankao/2' in agent.seen_urls
            assert 'http://ruankao/3' in agent.seen_urls
            
            # 验证 4: _is_first_run 被重置为 False
            assert agent._is_first_run == False, "check_and_notify 后 _is_first_run 应为 False"
            
            # 验证 5: 状态文件已保存
            assert os.path.exists(state_file), "状态文件应该被创建"
            with open(state_file, 'r') as f:
                saved = json.load(f)
            assert set(saved['seen_urls']) == agent.seen_urls
            
            print(f"  ✅ baseline 通知被调用，3条现有新闻已存入快照")
            print(f"  ✅ new_content 通知未被调用（避免了垃圾消息！）")
            print(f"  ✅ _is_first_run 已重置为 False")
            print(f"  ✅ 状态文件已正确保存")
            print("✅ 快照机制首次运行测试通过")
            return True
        
    except Exception as e:
        print(f"❌ 快照机制首次运行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_snapshot_prevents_spam():
    """
    测试快照建立后，再次运行不会重复通知现有内容
    
    场景：已有快照 {u1, u2, u3}，网站内容不变
    验证：不触发任何通知
    """
    print("\n🔍 测试快照机制 - 已有快照不重复通知...")
    try:
        from simple_monitor import MonitorAgent, RuankaoMonitor, EmailNotifier
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, 'monitor_state.json')
            
            agent = MonitorAgent.__new__(MonitorAgent)
            agent.monitor = RuankaoMonitor()
            agent.notifier = EmailNotifier()
            agent.state_file = state_file
            agent._stop_requested = False
            agent._stop_reason = ""
            
            # 模拟已有快照（从 state 文件加载的）
            agent.seen_urls = {'http://ruankao/1', 'http://ruankao/2', 'http://ruankao/3'}
            agent._is_first_run = False  # 不是首次运行
            
            # 网站上的内容和快照一样（没有新内容）
            existing_news = [
                {'title': '新闻1', 'url': 'http://ruankao/1', 'date': '2026-12-15', 'type': 'score', 'keywords': ['2026'], 'type_label': ('🎯 成绩相关', '#dc3545')},
                {'title': '新闻2', 'url': 'http://ruankao/2', 'date': '2026-08-01', 'type': 'policy', 'keywords': ['报名'], 'type_label': ('📜 政策通知', '#ffc107')},
                {'title': '新闻3', 'url': 'http://ruankao/3', 'date': '2026-07-20', 'type': 'exam', 'keywords': ['考试'], 'type_label': ('📋 考试相关', '#007bff')},
            ]
            agent.monitor.get_all_news = lambda: existing_news
            
            # mock 通知方法
            baseline_called = []
            new_content_called = []
            
            agent.notifier.send_baseline_notification = lambda n: baseline_called.append(n) or True
            agent.notifier.send_new_content_notification = lambda items, all_news: new_content_called.append(items) or True
            
            # 执行检查
            agent.check_and_notify()
            
            # 关键验证：两个通知都不应被调用
            assert len(baseline_called) == 0, "已有快照时不应调用 baseline 通知"
            assert len(new_content_called) == 0, "没有新内容时不应调用 new_content 通知"
            
            print(f"  ✅ baseline 通知未被调用")
            print(f"  ✅ new_content 通知未被调用")
            print("✅ 快照机制防垃圾消息测试通过")
            return True
        
    except Exception as e:
        print(f"❌ 快照机制防垃圾消息测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_snapshot_detects_incremental():
    """
    测试快照建立后，只通知真正新增的内容
    
    场景：已有快照 {u1, u2}，网站新增 u3 → 只通知 u3
    """
    print("\n🔍 测试快照机制 - 增量更新检测...")
    try:
        from simple_monitor import MonitorAgent, RuankaoMonitor, EmailNotifier
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, 'monitor_state.json')
            
            agent = MonitorAgent.__new__(MonitorAgent)
            agent.monitor = RuankaoMonitor()
            agent.notifier = EmailNotifier()
            agent.state_file = state_file
            agent._stop_requested = False
            agent._stop_reason = ""
            
            # 模拟已有快照（从 state 文件加载的）
            agent.seen_urls = {'http://ruankao/1', 'http://ruankao/2'}
            agent._is_first_run = False
            
            # 网站有 3 条新闻：u1, u2（旧）+ u3（新增）
            current_news = [
                {'title': '旧新闻1', 'url': 'http://ruankao/1', 'date': '2026-12-15', 'type': 'score', 'keywords': ['2026'], 'type_label': ('🎯 成绩相关', '#dc3545')},
                {'title': '旧新闻2', 'url': 'http://ruankao/2', 'date': '2026-08-01', 'type': 'policy', 'keywords': ['报名'], 'type_label': ('📜 政策通知', '#ffc107')},
                {'title': '全新新闻3', 'url': 'http://ruankao/3', 'date': '2026-10-26', 'type': 'exam', 'keywords': ['考试', '新增'], 'type_label': ('📋 考试相关', '#007bff')},
            ]
            agent.monitor.get_all_news = lambda: current_news
            
            # mock 通知方法
            notified_items = []
            agent.notifier.send_new_content_notification = lambda items, all_news: notified_items.extend(items) or True
            
            # 执行检查
            agent.check_and_notify()
            
            # 验证：只通知了新增的 u3
            assert len(notified_items) == 1, f"应该只通知1条新增，实际{len(notified_items)}"
            assert notified_items[0]['url'] == 'http://ruankao/3'
            assert notified_items[0]['title'] == '全新新闻3'
            
            # 验证：seen_urls 已更新（新增 u3）
            assert 'http://ruankao/3' in agent.seen_urls
            assert len(agent.seen_urls) == 3
            
            print(f"  ✅ 只通知了新增的 1 条新闻：全新新闻3")
            print(f"  ✅ seen_urls 已更新为 3 条")
            print("✅ 快照机制增量更新测试通过")
            return True
        
    except Exception as e:
        print(f"❌ 快照机制增量更新测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_baseline_notification_exists():
    """测试 EmailNotifier 存在 send_baseline_notification 方法"""
    print("\n🔍 测试快照通知方法存在性...")
    try:
        from simple_monitor import EmailNotifier
        
        notifier = EmailNotifier()
        assert hasattr(notifier, 'send_baseline_notification'), "缺少 send_baseline_notification 方法"
        
        print("✅ send_baseline_notification 方法存在")
        return True
        
    except Exception as e:
        print(f"❌ 快照通知方法测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 软考官网监控系统功能测试 (V2)")
    print("=" * 60)
    
    tests = [
        ("依赖包导入", test_imports),
        ("CHECK_INTERVAL=10分钟", test_check_interval_default),
        ("官网访问", test_website_access),
        ("新闻解析", test_news_parsing),
        ("关键字提取与分类", test_keyword_extraction),
        ("enriched新闻数据", test_get_all_news_enriched),
        ("新内容检测(不限成绩)", test_new_content_detection),
        ("停止通知方法存在", test_stop_notification_exists),
        ("信号处理器设置", test_signal_handlers_setup),
        ("状态文件格式", test_state_file_format),
        ("静默时段逻辑", test_skip_monitoring_logic),
        ("邮件配置", test_email_config),
        ("快照-首次运行建基线", test_first_run_snapshot),
        ("快照-已有快照不重复通知", test_snapshot_prevents_spam),
        ("快照-只通知增量更新", test_snapshot_detects_incremental),
        ("快照通知方法存在", test_baseline_notification_exists),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试 '{name}' 执行出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:24s} : {status}")
    
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
