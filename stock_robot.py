import akshare as ak
import pandas as pd
import datetime
import os

def analyze_v19_stealth(row):
    """
    V19.1 潜伏者逻辑：拦截 D0 转 D1
    新增：提取“抓取实时价”到报告列中
    """
    try:
        symbol = str(row.get('代码', ''))
        name = row.get('名称', '')
        # 提取实时价格
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- 核心拦截：只选涨幅 1.5% - 4.8% 的潜伏标的 ---
        if not (1.5 <= zf <= 4.8):
            return None
            
        # 流动性过滤
        if not (150000000 <= amount <= 800000000):
            return None

        # 暗盘资金分析
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        risk_shield = "🛡️ 安全"
        
        if energy_per_pct < 60000000:
            hidden_money = "🏹 箭在弦上(高度控盘)"
            risk_shield = "✅ 极强"
        elif energy_per_pct > 250000000:
            hidden_money = "对敲承接 | 压力沉重"
            risk_shield = "⚠️ 预警"

        # 能量核心分析
        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5:
            energy_core = "🔥 黄金堆积(D0转D1)"
        elif lb > 3.5:
            energy_core = "🚀 动能初显"

        # 评分系统
        score = 50 + (lb * 15) + (hs * 5)
        if energy_core == "🔥 黄金堆积(D0转D1)": score += 25
        if hidden_money == "🏹 箭在弦上(高度控盘)": score += 15
        
        signal = "低位观察"
        if score > 105: signal = "💎 潜伏种子(D0重点)"
        elif score > 85: signal = "🚩 异动拦截"

        # 止损位参考
        min_buy = round(price * 0.995, 2)
        d3_exit = round(price * 0.98, 2)

        # 返回包含“抓取实时价”的数据流
        return pd.Series([
            signal, price, energy_core, hidden_money, risk_shield, 
            min_buy, d3_exit, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    print(f"🚀 V19.1 系统启动：拦截 D0 转 D1 潜伏信号...")
    try:
        full_market = ak.stock_zh_a_spot_em()
        
        # 在列项中加入 '抓取实时价'
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        res_df = full_market.apply(analyze_v19_stealth, axis=1)
        full_market[cols] = res_df
        
        # 提取潜伏标的
        report = full_market.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(30)
        
        # 保存 Excel
        index_path = "index.xlsx"
        report[['代码', '名称'] + cols].to_excel(index_path, index=False)
        print(f"✅ 报告已更新，已添加实时价格列。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    run_task()
