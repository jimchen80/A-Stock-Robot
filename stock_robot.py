import akshare as ak
import pandas as pd
import datetime
import os
import numpy as np

def analyze_v17_ultimate(row):
    try:
        symbol = str(row.get('代码', ''))
        name = row.get('名称', '')
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # 1. 过滤：确保具备接力价值的流动性 (2亿以上)
        if amount < 200000000: return None
        if zf < 2.0: return None # 排除织布机行情

        # 2. 暗盘资金分析（对敲逻辑）
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "主力扫盘 | 存量博弈"
        risk_shield = "🛡️ 安全"
        
        if energy_per_pct > 500000000:
            hidden_money = "对敲派发 | 诱多嫌疑"
            risk_shield = "🚨 高风险"
        elif energy_per_pct < 85000000 and zf > 5:
            hidden_money = "高度锁仓 | 算法控盘"
            risk_shield = "✅ 极强"

        # 3. 能量核心分析（D0潜伏判定）
        energy_core = "温和蓄势"
        if 1.8 <= lb <= 3.8 and 5.0 <= hs <= 13.0:
            energy_core = "🔥 能量堆积(黄金倍量)"
        elif lb > 4.5:
            energy_core = "🚀 动量爆发(主升)"

        # 4. 信号判定
        score = 65 + (lb * 10) + (zf * 2)
        if "能量堆积" in energy_core: score += 15
        if "高度锁仓" in hidden_money: score += 12
        
        signal = "短线关注"
        if score > 110: signal = "💎 爆发点(必看)"
        elif score > 95: signal = "🚩 强势接力"

        # 5. 量化建议
        min_buy = round(price * 0.99, 2)
        d3_exit = round(price * 1.015, 2)

        return pd.Series([
            signal, energy_core, hidden_money, risk_shield, 
            min_buy, d3_exit, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    print(f"🚀 V17.0 策略逻辑回归，正在分析全 A 股...")
    try:
        full_market = ak.stock_zh_a_spot_em()
        cols = ['信号', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        res_df = full_market.apply(analyze_v17_ultimate, axis=1)
        full_market[cols] = res_df
        
        # 筛选结果
        report = full_market.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(50)
        
        # 保存文件
        index_path = "index.xlsx"
        report[['代码', '名称'] + cols].to_excel(index_path, index=False)
        print(f"✅ 实战版报告生成完毕。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    run_task()
