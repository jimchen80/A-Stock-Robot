import pandas as pd
import requests
import random
import time
import os
from datetime import datetime, timedelta

# --- 首席策略 10.0 调优配置 ---
STRATEGY_CONFIG = {
    "ZF_MIN": 1.5,
    "ZF_MAX": 4.8,
    "AMOUNT_MIN": 80000000,  # 拓宽流动性拦截网：从1.5亿降至0.8亿
    "AMOUNT_MAX": 800000000,
    "RATIO_STRONG": 65000000,
    "RATIO_RISK": 250000000,
    "LB_MIN": 1.2,
    "LB_MAX": 2.8,
    "HS_MIN": 3.0,
    "HS_MAX": 7.5,
    "SCORE_BASE": 50,
    "SCORE_THRESHOLD": 75   # 适当降低评分门槛，增加容错性
}

def fetch_market_data():
    """全仿真数据抓取引擎"""
    url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=2000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f6,f8,f10"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/center/gridlist.html"
    }
    
    try:
        # 随机延迟对抗 WAF
        time.sleep(random.uniform(1.0, 2.5))
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {}).get('diff', [])
            print(f"DEBUG: 成功连接接口，获取原始快照数据 {len(data)} 条")
            return data
    except Exception as e:
        print(f"Fetch Error: {e}")
    return []

def run_strategy_10():
    """全时段执行 10.0 因子矩阵筛选"""
    raw_list = fetch_market_data()
    final_results = []
    
    # 修正北京时间
    now_bj = datetime.utcnow() + timedelta(hours=8)
    update_time = now_bj.strftime('%Y-%m-%d %H:%M:%S')

    if not raw_list:
        print("CRITICAL: 未获取到任何原始数据，请检查接口有效性或IP状态。")

    for item in raw_list:
        try:
            # 提取核心指标
            price = item.get('f2')     # Price_Anchor
            zf = item.get('f3')        # 涨幅因子
            amount = item.get('f6')    # 流动性因子
            hs = item.get('f8')        # 换手率
            lb = item.get('f10')       # 量比
            code = item.get('f12')
            name = item.get('f14')

            # 排除非交易状态数据
            if price == "-" or zf == "-" or amount == "-": 
                continue

            # --- 一、物理空间拦截 (拓宽后的门槛) ---
            curr_zf = float(zf)
            curr_amount = float(amount)
            if not (STRATEGY_CONFIG["ZF_MIN"] <= curr_zf <= STRATEGY_CONFIG["ZF_MAX"]): continue
            if not (STRATEGY_CONFIG["AMOUNT_MIN"] <= curr_amount <= STRATEGY_CONFIG["AMOUNT_MAX"]): continue

            # --- 二、筹码博弈模块 (能效比) ---
            ratio = curr_amount / curr_zf
            control_state = "高度控盘" if ratio < STRATEGY_CONFIG["RATIO_STRONG"] else ("风险" if ratio > STRATEGY_CONFIG["RATIO_RISK"] else "平稳")

            # --- 三、能量转换模块 (强弱转折) ---
            curr_lb = float(lb)
            curr_hs = float(hs)
            energy_signal = "黄金堆积" if (STRATEGY_CONFIG["LB_MIN"] <= curr_lb <= STRATEGY_CONFIG["LB_MAX"] and 
                                          STRATEGY_CONFIG["HS_MIN"] <= curr_hs <= STRATEGY_CONFIG["HS_MAX"]) else "观察"
            if curr_lb > 3.0: energy_signal = "动能初显"

            # --- 四、综合评分矩阵 ---
            score = STRATEGY_CONFIG["SCORE_BASE"] + (curr_lb * 15) + (curr_hs * 5)
            if energy_signal == "黄金堆积": score += 25
            if control_state == "高度控盘": score += 15

            # --- 五、风控与数据封装 ---
            if score >= STRATEGY_CONFIG["SCORE_THRESHOLD"]:
                final_results.append({
                    "代码": code,
                    "名称": name,
                    "实时价": price,
                    "涨幅%": zf,
                    "成交额": f"{round(curr_amount/1e8, 2)}亿",
                    "量比": lb,
                    "换手%": hs,
                    "能效比": int(ratio),
                    "控盘信号": control_state,
                    "能量状态": energy_signal,
                    "买入参考(-0.5%)": round(float(price) * 0.995, 2),
                    "止损线(-2%)": round(float(price) * 0.98, 2),
                    "综合评分": score,
                    "逻辑筛选时间": update_time
                })
        except Exception:
            continue

    # --- 六、输出与二进制哈希保障 ---
    if final_results:
        df = pd.DataFrame(final_results)
        df = df.sort_values(by="综合评分", ascending=False)
        # 植入随机指纹因子确保哈希变动
        fingerprint = {"代码": "SYNC_LOGIC", "综合评分": random.random(), "逻辑筛选时间": update_time}
        df = pd.concat([df, pd.DataFrame([fingerprint])], ignore_index=True)
        df.to_excel("index.xlsx", index=False)
        print(f"SUCCESS: 基于当前数据逻辑筛选出 {len(df)-1} 个标的。")
    else:
        # 休市或无匹配时的保底逻辑
        empty_df = pd.DataFrame([{
            "提醒": "当前时段行情快照无符合因子标的", 
            "建议": "流动性网已拓宽至0.8亿，请在交易日 9:45 重新观察",
            "更新时间": update_time, 
            "FINGERPRINT": random.random()
        }])
        empty_df.to_excel("index.xlsx", index=False)
        print("RESULT: 行情快照扫描完成，未发现符合 10.0 矩阵的标的。")

if __name__ == "__main__":
    # 文件自毁确保覆盖
    if os.path.exists("index.xlsx"):
        os.remove("index.xlsx")
    run_strategy_10()
