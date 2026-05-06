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
    "AMOUNT_MIN": 100000000,    # 流动性红线 (1亿)
    "HS_GOLDEN": (5.0, 15.0),   # 换手黄金区
    "HS_MAX": 35.0,             # 筹码崩溃红线
    "LB_MIN": 1.5,              # 量比进攻底线
    "LB_OPTIMAL": (1.5, 2.5),   # 量比黄金加权区
    "SCORE_THRESHOLD": 85       # 入场门槛
}

def fetch_data():
    """多维度数据抓取"""
    # 包含价格(f2)、涨幅(f3)、成交额(f6)、换手(f8)、量比(f10)、市值(f20)、行业(f100)等字段
    url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=2000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f6,f8,f10,f20,f100"
    headers = {"User-Agent": "Mozilla/5.0 (Windows)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json().get('data', {}).get('diff', [])
    except:
        return []

def run_strategy_11():
    raw_data = fetch_data()
    if not raw_data: return
    
    # 统计行业合力 (风口效应)
    industry_map = {}
    for item in raw_data:
        ind = item.get('f100', '其他')
        industry_map[ind] = industry_map.get(ind, 0) + 1

    final_pool = []
    now_bj = datetime.utcnow() + timedelta(hours=8)

    for item in raw_data:
        try:
            # 基础因子提取
            code, name = item['f12'], item['f14']
            price = float(item['f2'])
            zf = float(item['f3'])
            amount = float(item['f6'])
            hs = float(item['f8'])
            lb = float(item['f10'])
            mkt_cap = float(item.get('f20', 0)) / 1e8 # 市值(亿)
            industry = item.get('f100', '其他')

            # --- 一、核心准入门槛拦截 ---
            if not (CONFIG["PRICE"][0] <= price <= CONFIG["PRICE"][1]): continue
            if not (CONFIG["ZF"][0] <= zf <= CONFIG["ZF"][1]): continue
            if amount < CONFIG["AMOUNT_MIN"]: continue
            if hs > CONFIG["HS_MAX"]: continue # 筹码崩溃直接踢出

            # --- 二、动态评分系统 ---
            score = 60 # 基础起步分
            
            # 1. 量比进攻逻辑
            if CONFIG["LB_OPTIMAL"][0] <= lb <= CONFIG["LB_OPTIMAL"][1]:
                score += 20 # 连板高发加权
            elif lb > 15 and zf < 3:
                score -= 10 # 主力对敲诱多校验
            
            # 2. 筹码状态校验
            if hs > 25:
                score -= 20 # 筹码松动扣分
            elif CONFIG["HS_GOLDEN"][0] <= hs <= CONFIG["HS_GOLDEN"][1]:
                score += 10 # 换手黄金区加分

            # 3. 行业风口效应
            if industry_map.get(industry, 0) > 5:
                score += 10 # 板块合力加分

            # --- 三、策略结果输出 ---
            if score >= CONFIG["SCORE_THRESHOLD"]:
                final_pool.append({
                    "代码": code, "名称": name, "价格": price, "涨幅%": zf,
                    "量比": lb, "换手%": hs, "成交额(亿)": round(amount/1e8, 2),
                    "行业": industry, "综合评分": score,
                    "B列信号": "海龟突破" if price > price*0.98 else "动量接力", # 简化模拟
                    "C列分析": "板块强度高" if industry_map.get(industry, 0) > 5 else "个股异动",
                    "止损线": round(price * 0.97, 2),
                    "更新时间": now_bj.strftime('%H:%M:%S')
                })
        except: continue

    # 导出结果
    df = pd.DataFrame(final_pool)
    if not df.empty:
        df = df.sort_values(by="综合评分", ascending=False)
        # 植入物理指纹
        df.loc[len(df)] = {"代码": "FINGERPRINT", "综合评分": random.random(), "更新时间": now_bj.strftime('%H:%M:%S')}
        df.to_excel("index.xlsx", index=False)
        print(f"策略 11.0 执行成功，拦截有效标的 {len(df)-1} 只")
    else:
        pd.DataFrame([{"提醒": "当前时段因子未共振", "时间": now_bj}]).to_excel("index.xlsx", index=False)

if __name__ == "__main__":
    run_strategy_11()
