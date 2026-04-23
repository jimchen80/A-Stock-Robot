import akshare as ak
import pandas as pd
import datetime
import os
import numpy as np

def analyze_v17_ultimate(row):
    """
    首席策略 V17.0 核心引擎
    集成：D0能量堆积、暗盘对敲分析、风险盾、D3强制逃生
    """
    try:
        symbol = str(row.get('代码', ''))
        name = row.get('名称', '')
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # 1. 刚性过滤（根据你的要求：全A股5000只扫描，但必须有流动性）
        if amount < 220000000: return None
        if (symbol.startswith(('00', '60')) and zf > 9.4) or (symbol.startswith(('30', '68')) and zf > 17.5):
            return None
        if zf < 3.0: return None

        # 2. 暗盘资金分析（对敲监控）
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "正常进场"
        risk_shield = "🛡️ 安全"
        
        if energy_per_pct > 500000000:
            hidden_money = "⚠️ 虚假对敲"
            risk_shield = "🚨 高风险"
        elif energy_per_pct < 85000000 and zf > 4:
            hidden_money = "🚀 强力锁仓"
            risk_shield = "✅ 极强"

        # 3. 能量核心分析（D0潜伏因子）
        energy_core = "温和观察"
        if 1.6 <= lb <= 3.8 and 4.5 <= hs <= 13.5:
            energy_core = "🔥 能量堆积(主建仓)"
        elif lb > 4.0:
            energy_core = "⚡ 动能喷发"

        # 4. 信号与评分
        score = 65 + (lb * 10) + (zf * 1.5)
        if energy_core == "🔥 能量堆积(主建仓)": score += 15
        if hidden_money == "🚀 强力锁仓": score += 12
        if risk_shield == "🚨 高风险": score -= 40

        signal = "观察"
        if score > 108: signal = "💎 绝佳金种"
        elif score > 90: signal = "🚩 重点关注"

        # 5. 关键价格量化
        min_buy_price = round(price * 0.992, 2)
        d3_exit_line = round(price * 1.01, 2)

        return pd.Series([
            signal, energy_core, hidden_money, risk_shield, 
            min_buy_price, d3_exit_line, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    print(f"🚀 V17.0 系统正在抓取全 A 股数据进行深度分析...")
    try:
        # 获取数据
        full_market = ak.stock_zh_a_spot_em()
        
        # 定义列
        cols = [
            '信号', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
            '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)'
        ]
        
        # 应用策略
        res_df = full_market.apply(analyze_v17_ultimate, axis=1)
        full_market[cols] = res_df
        
        # 筛选高价值结果
        report = full_market.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(50)
        final_out = report[['代码', '名称'] + cols]

        # 设置北京时间
        bj_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y%m%d_%H%M')
        
        # --- 核心文件保存逻辑 ---
        # 1. 保存固定名称的 index.xlsx 用于链接下载
        index_path = os.path.join(os.getcwd(), "index.xlsx")
        final_out.to_excel(index_path, index=False)
        
        # 2. 保存带时间戳的文件用于历史存档
        history_path = os.path.join(os.getcwd(), f"Report_{bj_time}.xlsx")
        final_out.to_excel(history_path, index=False)
        
        # 确认文件是否真的生成了
        if os.path.exists(index_path):
            print(f"✅ 成功：index.xlsx 已生成，大小: {os.path.getsize(index_path)} 字节")
        else:
            print("❌ 错误：index.xlsx 生成失败！")

    except Exception as e:
        print(f"❌ 运行过程中出现异常: {e}")

if __name__ == "__main__":
    run_task()
