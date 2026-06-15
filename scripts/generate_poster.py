#!/usr/bin/env python3
"""
AI资讯日报海报生成器 v5.5
- 实时天气：wttr.in API（自动翻译中文）
- 实时新闻：多源抓取 + 严格质量过滤 + 按分类精准fallback
- 限行：兰州规则自动计算
- 日期：系统时间
- 5条资讯：1 AI + 1 房产 + 1 甘肃/兰州 + 1 国际 + 1 金融
"""
import os, hashlib, base64, requests, random, json, re, time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ====== 字体 ======
def find_font(size=20, bold=False):
    if bold:
        paths = [
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
        ]
    else:
        paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()

# ====== 实时数据获取 ======

def fetch_weather(city="Lanzhou"):
    """从 wttr.in 获取实时天气，翻译为中文"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        r = requests.get(url, timeout=10, headers={"User-Agent": "curl/7.0"})
        data = r.json()
        cur = data["current_condition"][0]
        today = data["weather"][0]
        weather_desc = cur["weatherDesc"][0]["value"]
        # 翻译为中文
        weather_cn = WEATHER_MAP.get(weather_desc, weather_desc)
        temp_high = today["maxtempC"]
        temp_low = today["mintempC"]
        return {
            "weather": weather_cn,
            "weather_raw": weather_desc,
            "temp_high": temp_high,
            "temp_low": temp_low,
        }
    except Exception as e:
        print(f"天气获取失败({e})，使用默认值")
        return {"weather": "晴", "weather_raw": "Sunny", "temp_high": "30", "temp_low": "18"}

def clean_html(text):
    """清洗HTML标签和特殊字符"""
    text = re.sub(r'<[^>]+>', '', text)          # 去标签
    text = re.sub(r'&[a-z]+;', ' ', text)        # 去实体
    text = re.sub(r'\s+', ' ', text)              # 合并空白
    return text.strip()

def smart_trim(text, max_len):
    """智能截断，尽量在标点处断开"""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # 尝试在标点处断开
    for i in range(max_len, max_len//2, -1):
        if text[i-1] in '，。；！？、,.;!? ':
            return text[:i-1]
    return text[:max_len]

def extract_summary(raw_text, max_len=80):
    """
    从原始文本中提取摘要：尽量截取后半段（具体描述部分），而非标题/来源前缀
    """
    text = raw_text.strip()
    # 去掉常见的日期前缀
    text = re.sub(r'^\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\s*', '', text)
    text = re.sub(r'^\d{1,2}月\d{1,2}日\s*', '', text)
    # 去掉来源前缀（如"新华社："、"每日甘肃："等）
    text = re.sub(r'^[^\s]{2,8}[讯电报道]?\s*[：:：]\s*', '', text)
    # 如果太长，截断
    if len(text) > max_len:
        text = smart_trim(text, max_len)
    return text

# 天气英文→中文映射
WEATHER_MAP = {
    "Sunny": "晴", "Clear": "晴", "Partly cloudy": "多云", "Partly Cloudy": "多云",
    "Cloudy": "阴", "Overcast": "阴", "Mist": "雾", "Fog": "雾", "Haze": "霾",
    "Light rain": "小雨", "Moderate rain": "中雨", "Heavy rain": "大雨",
    "Light snow": "小雪", "Moderate snow": "中雪", "Heavy snow": "大雪",
    "Dust storm": "扬沙", "Sandstorm": "沙尘暴", "Dust": "浮尘",
    "Thunderstorm": "雷阵雨", "Rain": "雨", "Snow": "雪",
}

def fetch_news():
    """
    按分类获取当日最新资讯：
    - 1条 AI 行业新闻
    - 1条 房产行业新闻
    - 1条 甘肃/兰州本地资讯
    - 1条 国际新闻
    - 1条 金融财经新闻
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    ai_news = []
    estate_news = []
    gansu_news = []
    international_news = []
    finance_news = []
    
    # ====== AI 行业新闻 ======
    print("  🔍 抓取AI行业新闻...")
    # 源: txtmix AI早报
    try:
        url = f"https://txtmix.com/posts/news/ai-morning-news-{today_str}/"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            clean = clean_html(line)
            if len(clean) > 15 and not clean.startswith(('{', '(', 'var ', 'function')):
                # 冒号在前15字内才拆分（如"OpenAI：发布新模型"），否则保留整行
                colon_pos = -1
                if '：' in clean[:20]:
                    colon_pos = clean[:20].index('：')
                elif ':' in clean[:20]:
                    colon_pos = clean[:20].index(':')
                if colon_pos > 0 and colon_pos < 15:
                    parts = re.split(r'[：:]', clean, maxsplit=1)
                    title = smart_trim(parts[0], 35)
                    summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                else:
                    title = smart_trim(clean, 35)
                    summary = clean
                ai_news.append({"title": title, "summary": summary, "source": "AI内参"})
        print(f"    txtmix获取 {len(ai_news)} 条")
    except Exception as e:
        print(f"    txtmix失败: {e}")
    
    # 源: neican.ai
    try:
        url = f"https://www.neican.ai/morningnews/{today_str}-ai-{today_str}-/"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            clean = clean_html(line)
            if len(clean) > 15 and not clean.startswith(('{', '(', 'var ', 'function', '今天是20')):
                # 冒号在前15字内才拆分（来源格式），否则保留整行
                colon_pos = -1
                if '：' in clean[:20]:
                    colon_pos = clean[:20].index('：')
                elif ':' in clean[:20]:
                    colon_pos = clean[:20].index(':')
                if colon_pos > 0 and colon_pos < 15:
                    parts = re.split(r'[：:]', clean, maxsplit=1)
                    title = smart_trim(parts[0], 35)
                    summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                else:
                    title = smart_trim(clean, 35)
                    summary = clean
                ai_news.append({"title": title, "summary": summary, "source": "AI内参"})
        print(f"    neican获取 {len(lines)} 行")
    except Exception as e:
        print(f"    neican失败: {e}")
    
    # ====== 房产行业新闻 ======
    print("  🏠 抓取房产行业新闻...")
    time.sleep(2)  # 避免请求过快被封
    for kw in ["房地产+最新", "楼市+政策+2026"]:
        if len(estate_news) >= 5:
            break
        try:
            url = f"https://www.sogou.com/web?query={kw}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            r = requests.get(url, timeout=15, headers=headers)
            text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 15]
            for line in lines:
                clean = clean_html(line)
                if len(clean) > 12 and len(re.findall(r'[\u4e00-\u9fff]', clean)) >= 5:
                    if any(kw in clean for kw in ['房产', '房地产', '楼市', '买房', '住房', '物业', '楼盘', '房价', '房企']):
                        # 冒号在前15字内才拆分（来源格式），否则保留整行
                        colon_pos = -1
                        if '：' in clean[:20]:
                            colon_pos = clean[:20].index('：')
                        elif ':' in clean[:20]:
                            colon_pos = clean[:20].index(':')
                        if colon_pos > 0 and colon_pos < 15:
                            parts = re.split(r'[：:]', clean, maxsplit=1)
                            title = smart_trim(parts[0], 35)
                            summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                        else:
                            title = smart_trim(clean, 35)
                            summary = clean
                        estate_news.append({"title": title, "summary": summary, "source": "房产资讯"})
        except Exception as e:
            print(f"    搜狗房产失败: {e}")
    print(f"    搜狗获取 {len(estate_news)} 条")
    
    # ====== 甘肃/兰州本地资讯 ======
    print("  🏙 抓取甘肃/兰州本地资讯...")
    time.sleep(3)  # 避免请求过快被封
    for kw in ["兰州+新闻", "甘肃+最新"]:
        if len(gansu_news) >= 5:
            break
        try:
            url = f"https://www.sogou.com/web?query={kw}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            r = requests.get(url, timeout=15, headers=headers)
            text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 15]
            for line in lines:
                clean = clean_html(line)
                if len(clean) > 12 and len(re.findall(r'[\u4e00-\u9fff]', clean)) >= 5:
                    if any(kw in clean for kw in ['兰州', '甘肃', '西北', '天水', '西宁', '城关', '七里河', '安宁', '皋兰', '陇']):
                        # 冒号在前15字内才拆分（来源格式），否则保留整行
                        colon_pos = -1
                        if '：' in clean[:20]:
                            colon_pos = clean[:20].index('：')
                        elif ':' in clean[:20]:
                            colon_pos = clean[:20].index(':')
                        if colon_pos > 0 and colon_pos < 15:
                            parts = re.split(r'[：:]', clean, maxsplit=1)
                            title = smart_trim(parts[0], 35)
                            summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                        else:
                            title = smart_trim(clean, 35)
                            summary = clean
                        gansu_news.append({"title": title, "summary": summary, "source": "本地资讯"})
        except Exception as e:
            print(f"    搜狗甘肃失败: {e}")
    print(f"    搜狗获取 {len(gansu_news)} 条")
    
    # ====== 国际新闻 ======
    print("  🌍 抓取国际新闻...")
    time.sleep(2)
    for kw in ["国际新闻+最新", "全球+热点"]:
        if len(international_news) >= 5:
            break
        try:
            url = f"https://www.sogou.com/web?query={kw}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            r = requests.get(url, timeout=15, headers=headers)
            text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 15]
            for line in lines:
                clean = clean_html(line)
                if len(clean) > 12 and len(re.findall(r'[\u4e00-\u9fff]', clean)) >= 5:
                    if any(kw in clean for kw in ['国际', '全球', '美国', '欧洲', '日本', '韩国', '中东', '欧盟', '联合国', '世界', '普京', '拜登', '特朗普', '外交', '冲突', '贸易战', '关税']):
                        # 冒号在前15字内才拆分（来源格式），否则保留整行
                        colon_pos = -1
                        if '：' in clean[:20]:
                            colon_pos = clean[:20].index('：')
                        elif ':' in clean[:20]:
                            colon_pos = clean[:20].index(':')
                        if colon_pos > 0 and colon_pos < 15:
                            parts = re.split(r'[：:]', clean, maxsplit=1)
                            title = smart_trim(parts[0], 35)
                            summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                        else:
                            title = smart_trim(clean, 35)
                            summary = clean
                        international_news.append({"title": title, "summary": summary, "source": "国际新闻"})
        except Exception as e:
            print(f"    搜狗国际失败: {e}")
    print(f"    搜狗获取 {len(international_news)} 条")
    
    # ====== 金融财经新闻 ======
    print("  💰 抓取金融财经新闻...")
    time.sleep(3)
    for kw in ["财经+最新+新闻", "A股+行情", "央行+政策", "人民币+汇率", "黄金+价格"]:
        if len(finance_news) >= 8:
            break
        try:
            url = f"https://www.sogou.com/web?query={kw}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            r = requests.get(url, timeout=15, headers=headers)
            text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 15]
            for line in lines:
                clean = clean_html(line)
                if len(clean) > 12 and len(re.findall(r'[\u4e00-\u9fff]', clean)) >= 5:
                    # 放宽匹配：金融/财经/股市/经济/央行/汇率/金价/基金/理财/银行/券商等
                    finance_kw = ['股市', 'A股', '上证', '深证', '创业板', '央行', '利率', '降息', '加息', '人民币', '美元', '黄金', '基金', '投资', '理财', '银行', '保险', '券商', 'IPO', '上市', '涨停', '跌停', '期货', '债券', '数字货币', '比特币', '金融', '财经', '经济', '沪指', '恒生', '美股', '纳斯达克', '标普', '汇率', '金价', '银价', '大宗商品', 'CPI', 'PPI', 'GDP', 'M2', 'LPR', 'MLF']
                    if any(kw in clean for kw in finance_kw):
                        # 冒号在前15字内才拆分（来源格式），否则保留整行
                        colon_pos = -1
                        if '：' in clean[:20]:
                            colon_pos = clean[:20].index('：')
                        elif ':' in clean[:20]:
                            colon_pos = clean[:20].index(':')
                        if colon_pos > 0 and colon_pos < 15:
                            parts = re.split(r'[：:]', clean, maxsplit=1)
                            title = smart_trim(parts[0], 35)
                            summary = smart_trim(parts[1], 80) if len(parts) > 1 else clean
                        else:
                            title = smart_trim(clean, 35)
                            summary = clean
                        finance_news.append({"title": title, "summary": summary, "source": "金融财经"})
                time.sleep(0.1)  # 微延迟避免过快
        except Exception as e:
            print(f"    搜狗财经失败: {e}")
    print(f"    搜狗获取 {len(finance_news)} 条")
    
    # ====== 质量过滤函数 ======
    junk_patterns = [
        r'^\d{4}-\d{2}-\d{2}',           # 日期开头
        r'^AI,', r'^[A-Z][a-z]+ \d',     # 英文+数字
        r'^\d+月\d+日',                   # 月日开头
        r'^\d{4}年\d{1,2}月\d{1,2}日',   # 完整日期开头（汇总新闻特征）
        r'^\d{4}年\d{1,2}月',            # 年月开头
    ]
    skip_phrases = [
        'AI新闻早报', 'AI早报', 'AI 新闻早报', 'AI 早报', 'Text Matrix', '今天是20',
        # 汇总/过期内容特征
        '新闻早报', '早报｜', '早报 |', '日报｜', '日报 |',
    ]
    # 页面描述类文本特征（非新闻标题）
    desc_phrases = [
        '是由', '主办', '新闻办公室', '热点法律', 'Copyright', '版权所有', '关于我们', '联系我们', '新闻发布会',
        # 导航/汇总描述文本
        '近期', '更多', '新闻追踪', '热点新闻', '新闻动态', '新闻列表', '新闻中心', '新闻资讯',
        '为您推荐', '相关新闻', '推荐阅读', '精彩推荐', '热门文章',
        '第1期', '第2期', '第3期', '第4期', '第5期', '第6期', '第7期', '第8期', '第9期', '第10期',
        '手机版', '客户端', 'APP下载', '扫描二维码', '关注微信',
        '首页', '上一页', '下一页', '尾页', '页次',
    ]
    # 标题格式异常检测：纯数字序号、编号开头等
    bad_title_starts = ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '①', '②', '③', '④', '⑤']
    
    def filter_quality(news_list):
        seen = set()
        result = []
        for n in news_list:
            t = n["title"]
            # 纯英文/数字/符号
            if re.match(r'^[A-Za-z0-9\s,.\-:!?()（）【】\[\]]+$', t):
                continue
            is_junk = False
            for pat in junk_patterns:
                if re.match(pat, t):
                    is_junk = True
                    break
            if is_junk:
                continue
            if any(phrase in t for phrase in skip_phrases):
                continue
            # 过滤页面描述文本
            if any(phrase in t for phrase in desc_phrases):
                continue
            # 标题以数字序号开头（如"1. xxx"）——可能是列表项而非新闻
            if any(t.startswith(s) for s in bad_title_starts):
                continue
            # 标题太长（超过50字的一般是描述段落而非标题）
            if len(t) > 50:
                continue
            # 必须包含至少6个中文字（更严格）
            if len(re.findall(r'[\u4e00-\u9fff]', t)) < 6:
                continue
            # 过滤含emoji的汇总标题（如"📚 兰州教育新闻2026年5月20日"）
            if re.search(r'[📚📢📰📊📈📉🗞🔔]', t) and re.search(r'\d{4}年\d{1,2}月\d{1,2}日', t):
                continue
            key = t[:8]
            if key not in seen:
                seen.add(key)
                result.append(n)
        return result
    
    ai_news = filter_quality(ai_news)
    estate_news = filter_quality(estate_news)
    gansu_news = filter_quality(gansu_news)
    international_news = filter_quality(international_news)
    finance_news = filter_quality(finance_news)
    
    print(f"  AI: {len(ai_news)}条 | 房产: {len(estate_news)}条 | 甘肃: {len(gansu_news)}条 | 国际: {len(international_news)}条 | 金融: {len(finance_news)}条")
    
    # ====== 组装5条新闻：1 AI + 1 房产 + 1 甘肃 + 1 国际 + 1 金融 ======
    # 使用有序字典记录每个分类的新闻
    categories = [
        ("AI", ai_news),
        ("房产", estate_news),
        ("甘肃", gansu_news),
        ("国际", international_news),
        ("金融", finance_news),
    ]
    
    final_news = []
    global_seen = set()
    
    def add_from(pool, count):
        added = 0
        for n in pool:
            if added >= count:
                break
            key = n["title"][:8]
            if key not in global_seen:
                global_seen.add(key)
                final_news.append(n)
                added += 1
        return added
    
    # 先尝试每个分类各取1条
    for cat_name, pool in categories:
        add_from(pool, 1)
    
    # 如果某个分类抓取为空，用fallback按分类索引补全
    if len(final_news) < 5:
        fallback = get_fallback_news()
        # fallback顺序固定：[0]AI [1]房产 [2]甘肃 [3]国际 [4]金融
        fb_map = {
            "AI": fallback[0],
            "房产": fallback[1],
            "甘肃": fallback[2],
            "国际": fallback[3],
            "金融": fallback[4],
        }
        # 确定哪个分类缺失
        filled_cats = set()
        for i, (cat_name, pool) in enumerate(categories):
            if any(n.get("source", "") in ["AI内参", ""] for n in final_news if i == 0):
                pass  # AI内参也算AI
        # 简单方案：看当前有几条，缺的从fallback补对应位置
        need = 5 - len(final_news)
        # 如果前几个分类的抓取有结果但后面的没有，直接补fallback中缺失位置
        for i, (cat_name, pool) in enumerate(categories):
            if len(final_news) >= 5:
                break
            # 检查这个分类是否已经有（通过source粗略判断）
            got_it = False
            if cat_name == "AI":
                got_it = any(n.get("source", "") in ["AI内参"] for n in final_news)
            elif cat_name == "房产":
                got_it = any(n.get("source", "") in ["房产资讯"] for n in final_news)
            elif cat_name == "甘肃":
                got_it = any(n.get("source", "") in ["本地资讯"] for n in final_news)
            elif cat_name == "国际":
                got_it = any(n.get("source", "") in ["国际新闻"] for n in final_news)
            elif cat_name == "金融":
                got_it = any(n.get("source", "") in ["金融财经"] for n in final_news)
            if not got_it:
                fb_item = fb_map.get(cat_name)
                if fb_item:
                    key = fb_item["title"][:8]
                    if key not in global_seen:
                        global_seen.add(key)
                        final_news.append(fb_item)
    
    # 最终兜底：如果还不够5条，顺序补fallback
    if len(final_news) < 5:
        print(f"  仅 {len(final_news)} 条，补充默认资讯")
        fallback = get_fallback_news()
        for fb in fallback:
            if len(final_news) >= 5:
                break
            key = fb["title"][:8]
            if key not in global_seen:
                global_seen.add(key)
                final_news.append(fb)
    
    # 返回前5条，加上编号，精炼摘要
    result = []
    for i, n in enumerate(final_news[:5]):
        title = n["title"]
        raw_summary = n.get("summary", title)
        # 如果摘要和标题完全一样 → 没有额外摘要，用标题本身即可
        if raw_summary.strip() == title.strip():
            summary = title
        else:
            # 精炼摘要：去掉标题重复前缀
            summary = extract_summary(raw_summary, 80)
            # 如果摘要开头和标题前15字重复，去掉重复部分
            if len(title) >= 10 and summary[:10] == title[:10]:
                summary = summary[len(title):].strip()
                if not summary or len(summary) < 8:
                    summary = raw_summary[len(title):].strip()
        # 最终兜底
        if not summary or len(summary) < 8:
            summary = title
        result.append({
            "num": i + 1,
            "title": title,
            "summary": summary,
            "source": n.get("source", "综合资讯"),
        })
    return result

def get_fallback_news():
    """
    当日热点备选新闻（确保每天不同，按分类组织）
    结构: 1 AI + 1 房产 + 1 甘肃 + 1 国际 + 1 金融
    """
    today = datetime.now()
    pools = [
        # 池1
        [
            {"title": "智源大会2026：全球AI领袖齐聚北京", "summary": "第8届智源大会聚焦Agent、具身智能、AI安全等前沿议题，200余位专家参与", "source": "腾讯新闻"},
            {"title": "贝壳找房AI估值系统覆盖全国300城", "summary": "深度学习模型实现房屋自动估值，准确率达95%，推动行业数字化升级", "source": "TechWeb"},
            {"title": "兰州新区出台人才引进新政", "summary": "兰州新区发布系列人才政策，提供住房补贴、创业扶持等优惠措施", "source": "甘肃日报"},
            {"title": "G7峰会闭幕：聚焦AI治理与气候合作", "summary": "七国集团领导人就人工智能国际监管框架达成初步共识，推动全球AI治理", "source": "新华社"},
            {"title": "央行宣布定向降准0.25个百分点", "summary": "释放长期流动性约5000亿元，支持实体经济发展，A股三大指数集体高开", "source": "第一财经"},
        ],
        # 池2
        [
            {"title": "GPT-5推理成本降低50%：开发者福音", "summary": "OpenAI最新模型在保持性能同时大幅降低API调用费用，开发者社区反响热烈", "source": "机器之心"},
            {"title": "兰州首套房利率降至3.25%创新低", "summary": "兰州市出台楼市新政，降低购房门槛，刺激刚需入市，市场反应积极", "source": "兰州晚报"},
            {"title": "天水文旅持续升温：麦积山游客创新高", "summary": "天水市文旅产业持续火爆，麦积山石窟景区单日接待游客突破历史纪录", "source": "甘肃文旅"},
            {"title": "中东局势新进展：多方推动停火谈判", "summary": "联合国安理会紧急磋商，多国呼吁立即停火，国际油价应声回落3%", "source": "央视新闻"},
            {"title": "A股成交额突破1.5万亿创年内新高", "summary": "科技股领涨，北向资金单日净流入超200亿，市场做多情绪高涨", "source": "证券时报"},
        ],
        # 池3
        [
            {"title": "阿里千问3.0发布：多模态能力重大升级", "summary": "通义千问3.0在图文理解、代码生成等任务上全面对标国际一流模型", "source": "36氪"},
            {"title": "2026年房地产行业数字化转型加速", "summary": "多家头部房企加速AI+IoT布局，智慧社区、智能家居成为新增长点", "source": "经济观察报"},
            {"title": "兰张高铁兰武段通车运营一周年", "summary": "兰州至张掖高铁开通一年，累计发送旅客超800万人次，带动沿线经济发展", "source": "每日甘肃"},
            {"title": "欧盟通过数字欧元法案进入立法快车道", "summary": "欧洲议会高票通过，数字欧元有望2028年正式推出，全球CBDC竞赛升温", "source": "财联社"},
            {"title": "国际金价突破2800美元创历史新高", "summary": "全球央行持续增持黄金储备，避险情绪推动金价连涨，年内涨幅已超30%", "source": "上海证券报"},
        ],
    ]
    idx = (today.day + today.month) % len(pools)
    return pools[idx]

def get_traffic():
    """兰州限行规则"""
    wd = datetime.now().weekday()
    if wd >= 5:
        return "今日不限行"
    return {0: "限1和6", 1: "限2和7", 2: "限3和8", 3: "限4和9", 4: "限5和0"}[wd]

# ====== 获取实时数据 ======
print("🌤 获取实时天气...")
weather_data = fetch_weather()
print(f"   天气: {weather_data['weather']}, 温度: {weather_data['temp_low']}~{weather_data['temp_high']}°C")

print("📰 获取最新资讯...")
news_items = fetch_news()
for item in news_items:
    print(f"   {item['num']}. {item['title']}")

now = datetime.now()
weekday_cn = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][now.weekday()]

weather_info = {
    "city": "兰州",
    "date_str": now.strftime("%Y/%m/%d"),
    "weather": weather_data["weather"],
    "temp_low": weather_data["temp_low"],
    "temp_high": weather_data["temp_high"],
    "traffic": get_traffic(),
}

print(f"📅 日期: {weather_info['date_str']} {weekday_cn}")
print(f"🚗 限行: {weather_info['traffic']}")

quotes = [
    "每一天都是攀登，每一步都算数",
    "山顶的风，只属于坚持到底的人",
    "迎着晨光出发，不负每一份热爱",
    "向阳而生，追光而行",
    "你比想象中更强大",
    "今天的努力，是明天的底气",
]

# ====== 参数 ======
W = 800
MIN_H = 1600  # 最小高度
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(SCRIPT_DIR, "poster_today.png")
BG_PATH = os.path.join(SCRIPT_DIR, "bg_mountain.png")

# ====== 配色 ======
C_BG_DARK    = (8, 20, 48)
C_GOLD        = (255, 200, 0)
C_STROKE      = (4, 12, 35)
C_WHITE2      = (240, 245, 255)
C_GRAY        = (180, 190, 210)
C_BLUE_SRC    = (100, 180, 255)
C_CARD_BG     = (10, 22, 52, 180)
C_CARD_BORDER = (50, 70, 120, 120)
C_TRAFFIC_G   = (80, 220, 120)
C_TRAFFIC_R   = (255, 130, 80)

# ====== 预计算卡片高度（先算再建画布） ======
card_x, card_w = 40, 720
CONTENT_X = 100
CONTENT_W = card_w - CONTENT_X - 24
TITLE_LINE_H = 36
SUMMARY_LINE_H = 26
CARD_PAD_TOP = 22
CARD_PAD_BOTTOM = 18

def wrap_text(text, font, max_width):
    """按像素宽度自动换行，返回行列表"""
    lines = []
    current_line = ""
    for char in text:
        test = current_line + char
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    return lines

f_title2_pre = find_font(26, bold=True)
f_sum_pre = find_font(18)

# 计算每张卡片的高度
card_heights = []
for item in news_items:
    title_lines = wrap_text(item["title"], f_title2_pre, CONTENT_W)
    summary_lines = wrap_text(item["summary"], f_sum_pre, CONTENT_W)
    title_block_h = len(title_lines) * TITLE_LINE_H
    summary_block_h = len(summary_lines) * SUMMARY_LINE_H
    src_h = 24 if item.get("source") else 0
    src_gap = 8 if item.get("source") else 0
    content_h = title_block_h + 10 + summary_block_h + src_gap + src_h
    card_h = max(content_h + CARD_PAD_TOP + CARD_PAD_BOTTOM, 100)
    card_heights.append(card_h)

# 分隔线之后的总高度
sep_y_estimate = 480  # 估算分隔线Y位置
cards_total = sum(card_heights) + (len(card_heights) - 1) * 14  # 卡片+间距
footer_h = 60
H = max(MIN_H, sep_y_estimate + cards_total + footer_h)
print(f"📐 画布高度: {H}px (5张卡片共{cards_total}px)")

# ====== 画布 ======
bg = None
if os.path.exists(BG_PATH):
    try:
        bg = Image.open(BG_PATH).convert("RGB").resize((W,H), Image.LANCZOS)
        print(f"背景图加载成功: {BG_PATH}")
    except Exception as e:
        print(f"背景图加载失败: {e}")

if bg is None:
    img = Image.new("RGB", (W,H), C_BG_DARK)
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = int(8 + 12*y/H); g = int(20 + 35*y/H); b = int(48 + 60*y/H)
        d.line([(0,y),(W,y)], fill=(min(255,r),min(255,g),min(255,b)))
else:
    img = bg.copy()

# 深色蒙版
ov = Image.new("RGBA", (W,H), (0,0,0,0))
od = ImageDraw.Draw(ov)
for y in range(H):
    od.line([(0,y),(W,y)], fill=(5,12,35,130))
for y in range(280):
    a = int(220 - 120*y/280)
    od.line([(0,y),(W,y)], fill=(3,8,28, max(0,min(255,a))))
for y in range(H-120, H):
    a = int(130 + 80*(y-(H-120))/120)
    od.line([(0,y),(W,y)], fill=(3,8,28, max(0,min(255,a))))
img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
draw = ImageDraw.Draw(img)

# ====== 顶部装饰光点 ======
for _ in range(40):
    x = random.randint(30, W-30)
    y = random.randint(20, 250)
    r = random.randint(1, 4)
    draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 210, random.randint(40, 180)))

# ====== 大标题（居中偏上）======
f_title = find_font(82, bold=True)
title = "AI 资讯日报"
tb = draw.textbbox((0,0), title, font=f_title)
tw, th = tb[2]-tb[0], tb[3]-tb[1]
tx, ty = (W-tw)//2, 95

for dx in [-3,3]:
    for dy in [-3,3]:
        draw.text((tx+dx, ty+dy), title, fill=C_STROKE, font=f_title)
for dx,dy in [(-3,0),(3,0),(0,-3),(0,3)]:
    draw.text((tx+dx, ty+dy), title, fill=C_STROKE, font=f_title)
draw.text((tx+4, ty+4), title, fill=(0,0,0), font=f_title)
draw.text((tx, ty), title, fill=C_GOLD, font=f_title)

# ====== 大标题下方左侧：日期/天气/限行/励志语（竖向排列）======
info_x = 60
info_y = ty + th + 56

# 日期
f_date = find_font(22)
date_txt = f"{weather_info['date_str']}  {weekday_cn}"
draw.text((info_x, info_y), date_txt, fill=C_GRAY, font=f_date)

# 天气
info_y += 38
f_weather = find_font(20)
w = weather_info["weather"]
weather_icons = {"晴":"☀","多云":"⛅","阴":"☁","雨":"🌧","雪":"❄"}
icon_txt = weather_icons.get(w[:1], "🌤")
weather_txt = f"{icon_txt} {weather_info['city']} · {w} {weather_info['temp_low']}~{weather_info['temp_high']}°C"
draw.text((info_x, info_y), weather_txt, fill=C_GRAY, font=f_weather)

# 限行
info_y += 40
traffic = weather_info["traffic"]
tc = C_TRAFFIC_G if "不限" in traffic else C_TRAFFIC_R
f_tf_val = find_font(26, bold=True)
draw.text((info_x, info_y), traffic, fill=tc, font=f_tf_val)

# 励志语（居中）
info_y += 40
f_quote = find_font(20)
quote = random.choice(quotes)
quote_lines = []
line = ""
for char in quote:
    test = line + char
    tb2 = f_quote.getbbox(test)
    if tb2[2] - tb2[0] > 660:
        quote_lines.append(line)
        line = char
    else:
        line = test
quote_lines.append(line)

total_h = len(quote_lines[:2]) * 30 - 4
start_y = info_y + (40 - total_h) // 2
for i, ql in enumerate(quote_lines[:2]):
    qb2 = draw.textbbox((0,0), ql, font=f_quote)
    qw2 = qb2[2] - qb2[0]
    qx = (W - qw2) // 2
    draw.text((qx, start_y + i*30), ql, fill=C_GOLD, font=f_quote)

info_y += 40

# ====== 分隔线 ======
sep_y = info_y + 16
draw.line([(120, sep_y), (W-120, sep_y)], fill=C_GOLD + (120,), width=2)

# ====== 新闻卡片 ======
y_pos = sep_y + 28

f_num    = find_font(48, bold=True)
f_title2 = find_font(26, bold=True)
f_sum    = find_font(18)
f_src    = find_font(15)

for idx, item in enumerate(news_items):
    card_h = card_heights[idx]
    title_lines = wrap_text(item["title"], f_title2, CONTENT_W)
    summary_lines = wrap_text(item["summary"], f_sum, CONTENT_W)

    card = Image.new("RGBA", (card_w, card_h), (0,0,0,0))
    cd = ImageDraw.Draw(card)

    cd.rounded_rectangle([0, 0, card_w, card_h], radius=18, fill=C_CARD_BG)
    cd.rounded_rectangle([0, 0, card_w, card_h], radius=18, outline=C_CARD_BORDER, width=1)

    # 编号（垂直居中于卡片）
    num_str = f"{item['num']:02d}"
    nb = cd.textbbox((0,0), num_str, font=f_num)
    nw, nh = nb[2]-nb[0], nb[3]-nb[1]
    num_x = 28
    num_y = (card_h - nh) // 2 - 4
    cd.text((num_x, num_y), num_str, fill=C_GOLD, font=f_num)
    dot_y = num_y + nh + 6
    cd.ellipse([num_x+14, dot_y, num_x+22, dot_y+8], fill=C_GOLD + (180,))

    # 标题（多行，按像素宽度自动换行）
    ty = CARD_PAD_TOP
    for line in title_lines:
        cd.text((CONTENT_X, ty), line, fill=C_GOLD, font=f_title2)
        ty += TITLE_LINE_H

    # 摘要（多行，标题下方留10px间距）
    ty += 10
    for line in summary_lines:
        cd.text((CONTENT_X, ty), line, fill=C_WHITE2, font=f_sum)
        ty += SUMMARY_LINE_H

    # 来源
    src = item.get("source", "")
    if src:
        ty += 8
        cd.text((CONTENT_X, ty), f"📋 {src}", fill=C_BLUE_SRC, font=f_src)

    img.paste(card, (card_x, y_pos), card)
    y_pos += card_h + 14

# ====== 底部 ======
y_pos += 20
f_footer = find_font(15)
footer = "由太阳自动整理 · 工作日早8:00推送"
fb = draw.textbbox((0,0), footer, font=f_footer)
draw.text(((W - fb[2]+fb[0])//2, y_pos), footer, fill=(160,170,200), font=f_footer)

# ====== 保存 & 推送 ======
img = img.convert("RGB")
img.save(OUT_PATH, "PNG", optimize=True)
print(f"\n✅ 海报已生成: {OUT_PATH}, 大小: {os.path.getsize(OUT_PATH)/1024:.1f}KB")

webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1989ffa2-e11d-4e4d-81a6-bef37925a3bd"
with open(OUT_PATH, "rb") as f:
    img_data = f.read()
if len(img_data)/1024/1024 > 2:
    Image.open(OUT_PATH).convert("RGB").save(OUT_PATH, "JPEG", quality=80)
    with open(OUT_PATH, "rb") as f:
        img_data = f.read()
    print(f"已压缩, 新大小: {len(img_data)/1024:.1f}KB")

b64 = base64.b64encode(img_data).decode()
md5 = hashlib.md5(img_data).hexdigest()
r = requests.post(webhook_url, json={"msgtype":"image","image":{"base64":b64,"md5":md5}}).json()
print(f"推送: {r}")
print("✅ 推送成功！" if r.get("errcode")==0 else f"❌ 失败: {r}")
