import akshare as ak
import pandas as pd
import datetime
import random
import numpy as np

def analyze_logic(row):
    try:
        # 1. 物理层严选
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4')): return None

        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')

        if not all([price, hs, lb, amount, prev_close]) or price <= 0: return None

        # 2. 空间拦截 (1.5% - 4.85%)
        if not (1.5 <= zf <= 4.85) or not (1.5e8 <= amount <= 8.5e8): return None

        # 3. 严谨位计算
        # 参考买入：回踩今日涨幅的 0.618 位置 (博弈强支撑)
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2)
        # 动态止损：破今日最低价 2% 强制离场
        stop_loss = round(low * 0.98, 2)

        # 4. 评分矩阵
        score = 50.0 + (lb * 15) + (hs * 5)
        energy_core = "🔥 黄金堆积" if (1.5 <= lb <= 3.5 and 4.0 <= hs <= 9.0) else "潜伏蓄势"
        if energy_core == "🔥 黄金堆积": score += 30
        
        signal = "💎 潜伏种子" if score >= 105 else "🚩 异动拦截"

        return pd.Series([signal, price, ref_buy, stop_loss, energy_core, round(score, 1), zf, hs, lb, round(amount/1e8, 2)])
    except: return None

def run_task():
    try:
        df = ak.stock_zh_a_spot_em()
        cols = ['信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
        # 解决碎片化：显式构建结果集，确保数据对齐
        results = df.apply(analyze_logic, axis=1)
        res_df = pd.DataFrame(results.tolist(), index=df.index, columns=cols)
        final = pd.concat([df[['代码', '名称']], res_df], axis=1).dropna(subset=['信号'])
        
        report = final.sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(60)
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        # 指纹防缓存
        finger = pd.DataFrame([[f"V10.2", f"T:{bj_time}", "", "", "", random.random(), "", "", "", ""]], columns=['代码', '名称'] + cols)
        pd.concat([finger, report], ignore_index=True).to_excel("index.xlsx", index=False, engine='openpyxl')
    except Exception as e: print(f"FAIL: {e}")

if __name__ == "__main__": run_task()
