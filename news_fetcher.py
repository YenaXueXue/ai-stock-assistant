import requests
import json
import re
import logging
import warnings
import ssl
import urllib3

# 禁用 SSL 警告
warnings.filterwarnings('ignore')
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_news_from_eastmoney(symbol: str, max_items: int = 5):
    """
    从东方财富直接获取股票相关新闻（使用 requests + JSONP 解析）
    参数: symbol - 6位数字股票代码
    返回: list of dict [{"标题": "...", "时间": "...", "来源": "...", "摘要": "..."}]
    """
    news_list = []
    try:
        # 东方财富新闻搜索接口
        url = "https://search-api-web.eastmoney.com/search/jsonp"

        # 构造请求参数
        params = {
            "cb": "jQuery",  # JSONP 回调函数名（占位）
            "param": json.dumps({
                "uid": "",
                "keyword": symbol,
                "type": ["cmsArticle", "cmsArticleVip"],  # 资讯类型
                "client": "web",
                "clientType": "web",
                "clientVersion": "curr",
                "param": {
                    "cmsArticle": {
                        "searchScope": "default",
                        "sort": "default",
                        "pageIndex": 1,
                        "pageSize": max_items,
                        "preTag": "<em>",
                        "postTag": "</em>"
                    }
                }
            })
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://search.eastmoney.com/",
            "Accept": "*/*"
        }

        logging.info(f"正在从东方财富获取 {symbol} 相关新闻...")
        resp = requests.get(url, params=params, headers=headers, verify=False, timeout=10)

        if resp.status_code != 200:
            logging.warning(f"东方财富新闻请求失败，状态码: {resp.status_code}")
            return news_list

        # 解析 JSONP 响应
        # 格式: jQuery({...})
        text = resp.text

        # 提取 JSON 内容（去掉回调函数包装）
        json_match = re.search(r'^[^(]+\((.*)\);?$', text, re.DOTALL)
        if not json_match:
            logging.warning("无法解析 JSONP 响应")
            # 尝试直接解析为 JSON（备用）
            try:
                data = json.loads(text)
            except:
                return news_list
        else:
            try:
                data = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                logging.warning(f"JSON 解析失败: {e}")
                return news_list

        # 提取新闻列表
        articles = data.get('data', {}).get('cmsArticle', [])
        if not articles:
            # 尝试其他可能的数据路径
            articles = data.get('data', {}).get('list', [])

        if not articles:
            logging.warning("东方财富未返回新闻数据")
            return news_list

        for item in articles[:max_items]:
            title = item.get('title', '') or item.get('Title', '')
            if not title or len(title) < 3:
                continue

            # 过滤掉无关内容
            if any(k in title for k in ['广告', '推广', '免责']):
                continue

            pub_time = item.get('date', '') or item.get('pubDate', '') or item.get('PublishTime', '')
            source = item.get('source', '') or item.get('Source', '') or "东方财富"
            summary = item.get('summary', '') or item.get('Summary', '') or item.get('content', '') or title

            news_list.append({
                "标题": title[:60],
                "时间": pub_time,
                "来源": source,
                "摘要": summary[:100]
            })

        if news_list:
            logging.info(f"✅ 东方财富获取到 {len(news_list)} 条新闻")
        else:
            logging.warning("东方财富未提取到有效新闻")

    except Exception as e:
        logging.warning(f"东方财富新闻获取异常: {e}")

    return news_list


def get_news_from_akshare(symbol: str, max_items: int = 5):
    """
    使用 AKShare 获取新闻（备用方案，尝试多个接口）
    """
    try:
        import akshare as ak

        # 尝试不同的接口和参数
        interfaces = [
            {'func': ak.stock_news_em, 'params': {'symbol': symbol}},
            {'func': ak.stock_news_em, 'params': {'stock': symbol}},
            {'func': ak.stock_news_sina, 'params': {'symbol': symbol}},
        ]

        for interface in interfaces:
            try:
                df = interface['func'](**interface['params'])
                if df is not None and not df.empty:
                    news_list = []
                    title_col = '标题' if '标题' in df.columns else 'title'
                    time_col = '发布时间' if '发布时间' in df.columns else 'public_time'
                    content_col = '内容' if '内容' in df.columns else 'content'

                    for _, row in df.head(max_items).iterrows():
                        title = str(row.get(title_col, ''))[:60]
                        if title and len(title) > 3:
                            news_list.append({
                                "标题": title,
                                "时间": str(row.get(time_col, '')),
                                "来源": "AKShare",
                                "摘要": str(row.get(content_col, ''))[:100] or title[:100]
                            })
                    if news_list:
                        logging.info(f"✅ AKShare 获取到 {len(news_list)} 条新闻")
                        return news_list
            except Exception as e:
                logging.debug(f"AKShare 接口尝试失败: {e}")
                continue

    except ImportError:
        logging.warning("AKShare 未安装")
    except Exception as e:
        logging.warning(f"AKShare 新闻获取失败: {e}")

    return []


def get_mock_news(symbol: str, max_items: int = 5):
    """
    生成模拟新闻（保底方案）
    """
    mock_templates = [
        {"标题": f"{symbol} 股价震荡整理，机构维持推荐评级",
         "摘要": f"{symbol}近期股价震荡整理，多家机构维持推荐评级，目标价较当前仍有上行空间。"},
        {"标题": f"{symbol} 获北向资金增持，持仓比例有所提升",
         "摘要": f"数据显示，{symbol}近期获北向资金持续增持，持仓比例创近期新高。"},
        {"标题": f"{symbol} 发布业绩快报，营收和利润均实现增长",
         "摘要": f"{symbol}发布业绩快报，营收和利润均实现同比增长，符合市场预期。"},
        {"标题": f"{symbol} 行业政策利好出台，公司有望受益",
         "摘要": f"行业政策利好出台，{symbol}作为行业龙头有望持续受益。"},
        {"标题": f"{symbol} 与知名企业达成战略合作",
         "摘要": f"{symbol}宣布与知名企业达成战略合作，双方将在业务领域展开深度合作。"},
        {"标题": f"{symbol} 新产品即将上市，市场关注度提升",
         "摘要": f"{symbol}新产品即将上市，市场关注度显著提升，多家机构提前布局。"},
        {"标题": f"{symbol} 股东户数减少，筹码趋于集中",
         "摘要": f"{symbol}股东户数环比减少，筹码趋于集中，散户减少、机构增持迹象明显。"},
        {"标题": f"{symbol} 分红方案出炉，股息率具有吸引力",
         "摘要": f"{symbol}分红方案出炉，现金分红比例较高，股息率在行业中具有吸引力。"},
    ]

    import random
    random.seed(int(symbol[-4:]) if len(symbol) >= 4 else 42)
    selected = random.sample(mock_templates, min(max_items, len(mock_templates)))

    news_list = []
    for i, item in enumerate(selected):
        news_list.append({
            "标题": item["标题"],
            "时间": f"2026-06-{22 - i:02d} {10 + i * 2:02d}:30",
            "来源": "模拟数据",
            "摘要": item["摘要"]
        })
    return news_list


def get_stock_news(symbol: str, max_items: int = 5):
    """
    综合获取新闻（优先级：东方财富直抓 > AKShare > 模拟数据）
    """
    # 1. 东方财富直抓
    news = get_news_from_eastmoney(symbol, max_items)
    if news:
        return news

    # 2. AKShare 备用
    news = get_news_from_akshare(symbol, max_items)
    if news:
        return news

    # 3. 模拟新闻（保底）
    logging.warning(f"所有真实新闻源均失败，使用模拟数据 (股票: {symbol})")
    return get_mock_news(symbol, max_items)