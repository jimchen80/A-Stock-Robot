import akshare as ak
import pandas as pd
import datetime
import random
import time
import requests

def get_proxy():
    """
    【影子层】获取代理IP
    建议：实际生产中可接入付费代理API，如：return {"http": "http://user:pass@ip:port"}
    目前使用免费池逻辑作为占位符，若无代理则返回None直连（保底）
    """
    # 这里可以对接你买的代理池 API
    # proxy_list = ["http://1.2.3.4:8080", "http://5.6.7.8:9090"]
    # return {"http": random.choice(proxy_list), "https": random.choice(proxy_list)}
    return None 

def analyze_logic(row):
    """【策略层】首席策略 10.5 严谨逻辑"""
    try:
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4', '5')): return None

        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')

        # 核心拦截：数据不全（量比1/换手0）则判定为僵尸数据，直接剔除
        if pd.isna(lb) or (lb == 1.0 and hs == 0.0): return None
        # 10.5 拦截门槛
        if not (0.5 <= zf <= 5.2) or not (80000000 <= amount <= 1200000000): return None

        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 20
        
        return [code, name, "💎 潜伏种子" if score >= 85 else "🚩 异动拦截", price, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except: return None

def run_task():
    file_name = "index.xlsx"
    cols = ['代码', '名称', '信号', '价格', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    # 拟人化行为：启动前犹豫
    time.sleep(random.uniform(5, 10))

    try:
        print("🕵️ 正在启用高匿名代理出口...")
        # 实际操作中，akshare 内部请求较难直接挂代理
        # 我们可以通过设置环境变量来强制全局 Requests 走代理
        proxy = get_proxy()
        if proxy:
            import os
            os.environ['http_proxy'] = proxy['http']
            os.environ['https_proxy'] = proxy['https']
            print(f"🛰️ 代理切换成功，正在模拟真人请求...")

        # 抓取数据
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty: raise Exception("物理出口被拦截")

        results = []
        for _, row in df.iterrows():
            res = analyze_logic(row)
            if res: results.append(res)

        # 构建报告
        if not results:
            report = pd.DataFrame(columns=cols)
        else:
            report = pd.DataFrame(results, columns=cols).sort_values(by="综合评分", ascending=False).head(80)

        # 交付指纹
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V12.0-Proxy", f"T:{bj_time}", "", "", "", "", "", "", "", ""]], columns=cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False)
        print(f"🚀 代理模式执行成功！捕获标的：{len(report)}")

    except Exception as e:
        pd.DataFrame({"状态": ["影子模式受限"], "原因": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
