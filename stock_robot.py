import pandas as pd
import requests
import random
import time
import os
from datetime import datetime, timedelta

# --- 首席策略 11.0：动态锚点与因子穿透配置 ---
CONFIG = {
    "PRICE": (12, 25),          # 价格基因
    "ZF": (3.0, 6.0),           # 涨幅区间 (避开涨停惯性)
    "AMOUNT_MIN": 80000000,     # 流动性红线：下调至 0.8 亿
    "HS_GOLDEN": (5.0, 15.0),   # 换手黄金区
    "HS_MAX": 35.0,             # 筹码崩溃红线
    "LB_MIN": 1.5,              # 量比进攻底线
    "LB_OPTIMAL": (1.5, 2.5),   # 量比黄金加权区
    "SCORE_THRESHOLD": 75       # 入场门槛：降至 70-75 增加容错
}

def fetch_data():
    url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=2000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f6,f8,f10,f20,f100"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        time.sleep(random.uniform(1.0, 2.5))
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {}).get('diff', [])
            print(f"DEBUG: 成功抓取全市场原始数据 {len(data)} 条")
            return data
    except Exception as e:
        print(f"Fetch Error: {e}")
    return []

def run_strategy_11():
    raw_data = fetch_data()
    final_pool = []
    now_bj = datetime.utcnow() + timedelta(hours=8)
    update_time = now_bj.strftime('%Y-%m-%d %H:%M:%S')

    # 统计行业合力
    industry_map = {}
    for item in raw_data:
        ind = item.get('f100', '其他')
        industry_map[ind] = industry_map.get(ind, 0) + 1

    for item in raw_data:
        try:
            price = float(item['f2'])
            zf = float(item['f3'])
            amount = float(item['f6'])
            hs = float(item['f8'])
            lb = float(item['f10'])
            code, name = item['f12'], item['f14']
            industry = item.get('f100', '其他')

            # 核心拦截逻辑
            if not (CONFIG["PRICE"][0] <= price <= CONFIG["PRICE"][1]): continue
            if not (CONFIG["ZF"][0] <= zf <= CONFIG["ZF"][1]): continue
            if amount < CONFIG["AMOUNT_MIN"]: continue
            if hs > CONFIG["HS_MAX"]: continue

            # 评分系统
            score = 60
            if CONFIG["LB_OPTIMAL"][0] <= lb <= CONFIG["LB_OPTIMAL"][1]: score += 20
            if CONFIG["HS_GOLDEN"][0] <= hs <= CONFIG["HS_GOLDEN"][1]: score += 10
            if industry_map.get(industry, 0) > 5: score += 10

            if score >= CONFIG["SCORE_THRESHOLD"]:
                final_pool.append({
                    "代码": code, "名称": name, "价格": price, "涨幅%": zf,
                    "量比": lb, "换手%": hs, "成交额(亿)": round(amount/1e8, 2),
                    "行业": industry, "综合评分": score, "更新时间": update_time
                })
        except: continue

    # 关键点：保底生成 index.xlsx
    if final_pool:
        df = pd.DataFrame(final_pool).sort_values(by="综合评分", ascending=False)
        df.to_excel("index.xlsx", index=False)
        print(f"SUCCESS: 筛选出 {len(df)} 只标的")
    else:
        pd.DataFrame([{"提醒": "当前快照无符合因子标的", "更新时间": update_time, "FINGERPRINT": random.random()}]).to_excel("index.xlsx", index=False)
        print("RESULT: 生成空报告，未发现匹配标的")

if __name__ == "__main__":
    run_strategy_11()
