import os
import ssl
import warnings
import urllib3

os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
warnings.filterwarnings('ignore')
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 保存原始请求方法
original_get = requests.get
original_session_request = requests.Session.request

def debug_get(url, *args, **kwargs):
    kwargs['verify'] = False
    print(f"\n🔍 请求 URL: {url}")
    resp = original_get(url, *args, **kwargs)
    print(f"📊 状态码: {resp.status_code}")
    print(f"📄 Content-Type: {resp.headers.get('Content-Type')}")
    print(f"📝 响应内容 (前500字符):\n{resp.text[:500]}")
    return resp

def debug_session_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    print(f"\n🔍 Session请求: {method} {url}")
    resp = original_session_request(self, method, url, *args, **kwargs)
    print(f"📊 状态码: {resp.status_code}")
    print(f"📄 Content-Type: {resp.headers.get('Content-Type')}")
    print(f"📝 响应内容 (前500字符):\n{resp.text[:500]}")
    return resp

# 应用调试补丁
requests.get = debug_get
requests.Session.request = debug_session_request

import akshare as ak

print("开始测试 AKShare 数据获取...")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"✅ 成功获取数据，共 {len(df)} 条记录")
    result = df[df['代码'] == '000001']
    if not result.empty:
        print("✅ 找到平安银行数据：")
        print(result[['名称', '最新价', '涨跌幅', '总市值']].to_string())
    else:
        print("⚠️ 未找到 000001")
except Exception as e:
    print(f"❌ 获取数据失败: {e}")
    import traceback
    traceback.print_exc()