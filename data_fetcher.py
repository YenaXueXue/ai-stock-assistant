import baostock as bs
import pandas as pd
import logging
import datetime
from news_fetcher import get_stock_news

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_stock_info(symbol: str):
    """
    使用 Baostock 获取股票数据
    参数: symbol - 6位数字股票代码，如 '000001'
    返回: dict 包含行情、基本面、新闻、估值结构化数据
    """
    result = {
        'spot': None,
        'info': None,
        'news': [],
        'valuation': {  # 结构化估值数据，用于前端表格展示
            'pe': None,
            'pb': None,
            'roe': None,
            'turnover': None,
            'market_cap': None,
            'close': None,
            'change_pct': None,
            'high': None,
            'low': None,
            'volume': None,
            'amount': None
        }
    }

    # 转换代码格式：Baostock 需要 'sh.600000' 或 'sz.000001'
    if symbol.startswith('6'):
        bs_code = f"sh.{symbol}"
    elif symbol.startswith('0') or symbol.startswith('3'):
        bs_code = f"sz.{symbol}"
    else:
        bs_code = f"sz.{symbol}"

    # ========== 1. 获取行情和基本面数据（Baostock） ==========
    try:
        logging.info(f"正在从 Baostock 获取 {bs_code} 实时行情...")

        lg = bs.login()
        if lg.error_code != '0':
            logging.error(f"Baostock 登录失败: {lg.error_msg}")
            return result

        today = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount,peTTM,pbMRQ,psTTM,pcfNcfTTM,turn",
            start_date=start_date,
            end_date=today,
            frequency="d",
            adjustflag="2"
        )

        if rs.error_code != '0':
            logging.error(f"查询失败: {rs.error_msg}")
            bs.logout()
            return result

        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())

        if not data_list:
            logging.warning(f"未获取到 {bs_code} 的数据")
            bs.logout()
            return result

        df = pd.DataFrame(data_list, columns=rs.fields)
        for col in df.columns:
            if col != 'date':
                df[col] = pd.to_numeric(df[col], errors='coerce')

        latest = df.iloc[-1]

        # ===== 填充行情数据 =====
        result['spot'] = {
            '名称': symbol,
            '最新价': latest.get('close'),
            '涨跌幅': None,
            '成交量': latest.get('volume'),
            '成交额': latest.get('amount'),
            '最高': latest.get('high'),
            '最低': latest.get('low'),
            '今开': latest.get('open'),
            '昨收': None,
            '换手率': latest.get('turn'),
            '市盈率-动态': latest.get('peTTM'),
            '市净率': latest.get('pbMRQ'),
            '总市值': None
        }

        # 计算涨跌幅
        if len(df) >= 2:
            prev_close = df.iloc[-2]['close']
            if prev_close and prev_close != 0:
                change = (latest['close'] - prev_close) / prev_close * 100
                result['spot']['涨跌幅'] = round(change, 2)
                result['spot']['昨收'] = prev_close

        # ===== 填充 valuation 结构化数据 =====
        result['valuation']['close'] = latest.get('close')
        result['valuation']['high'] = latest.get('high')
        result['valuation']['low'] = latest.get('low')
        result['valuation']['volume'] = latest.get('volume')
        result['valuation']['amount'] = latest.get('amount')
        result['valuation']['pe'] = latest.get('peTTM')
        result['valuation']['pb'] = latest.get('pbMRQ')
        result['valuation']['turnover'] = latest.get('turn')
        result['valuation']['change_pct'] = result['spot']['涨跌幅']

        # 估算 ROE（PB / PE，简化估算）
        pe = result['valuation']['pe']
        pb = result['valuation']['pb']
        if pe and pb and pe != 0:
            result['valuation']['roe'] = round(pb / pe * 100, 2)

        logging.info(f"✅ 成功获取 {bs_code} 行情数据")

        result['info'] = {
            '股票代码': symbol,
            '最新价': result['spot'].get('最新价'),
            '涨跌幅': result['spot'].get('涨跌幅'),
            '市盈率': result['spot'].get('市盈率-动态'),
            '市净率': result['spot'].get('市净率'),
            '换手率': result['spot'].get('换手率')
        }

        bs.logout()

    except Exception as e:
        logging.error(f"❌ 获取行情数据失败: {e}")
        if bs.login_status():
            bs.logout()
        result['spot'] = None

    # ========== 2. 获取新闻 ==========
    try:
        logging.info(f"正在获取 {symbol} 相关新闻...")
        news_list = get_stock_news(symbol, max_items=5)
        result['news'] = news_list
        logging.info(f"✅ 获取到 {len(news_list)} 条新闻")
    except Exception as e:
        logging.warning(f"获取新闻失败: {e}")
        result['news'] = []

    return result


def format_stock_data_for_ai(stock_data: dict):
    """
    将获取到的股票数据格式化为纯文本，供 AI 分析
    """
    lines = []

    # -------- 1. 行情数据 --------
    spot = stock_data.get('spot')
    if spot:
        lines.append("=== 实时行情 ===")
        field_mapping = {
            '名称': '股票名称',
            '最新价': '最新价',
            '涨跌幅': '涨跌幅 (%)',
            '成交量': '成交量 (股)',
            '成交额': '成交额 (元)',
            '最高': '最高价',
            '最低': '最低价',
            '今开': '开盘价',
            '昨收': '昨收价',
            '换手率': '换手率 (%)',
            '市盈率-动态': '市盈率 (动态)',
            '市净率': '市净率'
        }
        for key, label in field_mapping.items():
            value = spot.get(key)
            if value is not None and value != '':
                lines.append(f"{label}: {value}")
        lines.append("")
    else:
        lines.append("⚠️ 未能获取到实时行情数据\n")

    # -------- 2. 基本面信息 --------
    info = stock_data.get('info')
    if info:
        lines.append("=== 基本指标 ===")
        for key, value in info.items():
            if value is not None and value != '':
                lines.append(f"{key}: {value}")
        lines.append("")

    # -------- 3. 新闻 --------
    news = stock_data.get('news', [])
    if news:
        lines.append("=== 近期相关新闻 ===")
        for i, item in enumerate(news, 1):
            title = item.get('标题', '')
            time_str = item.get('时间', '')
            source = item.get('来源', '')
            summary = item.get('摘要', '')[:80]
            lines.append(f"{i}. 【{source}】{title}")
            lines.append(f"   时间：{time_str}")
            lines.append(f"   摘要：{summary}...")
            lines.append("")
    else:
        lines.append("=== 近期新闻 ===\n暂无相关新闻")

    return "\n".join(lines)