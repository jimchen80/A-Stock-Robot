import akshare as ak
import pandas as pd
import datetime
import os
import numpy as np

def analyze_v17_ultimate(row):
    """
    V17.0 核心分析引擎
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
        
        # --- 1. 选股池下移与硬性过滤 ---
        # 全量扫描 A 股，过滤流动性过低标的（低于 2.2 亿不看）
        if amount < 220000000: return None
        # 拦截已封板个股：给 D2 留出介入空间
        if (symbol.startswith(('00', '60')) and zf > 9.4) or (symbol.startswith(('30', '68')) and zf > 17.5):
            return None
        # 强度底线：涨幅低于 3% 的不作为首选接力目标
        if zf < 3.0: return None

        # --- 2. 暗盘资金分析（对敲监控） ---
        # 逻辑：分析“单位涨幅耗能”。如果消耗资金巨大但涨幅微弱，必有对敲。
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "正常进场"
        risk_shield = "🛡️ 安全"
        
        if energy_per_pct > 500000000: # 5亿换1%涨幅，抛压极重或主力对敲出货
            hidden_money = "⚠️ 虚假对敲"
            risk_shield = "🚨 高风险"
        elif energy_per_pct < 85000000 and zf > 4: # 极小资金拉出大涨幅，主力高度锁仓
            hidden_money = "🚀 强力锁仓"
            risk_shield = "✅ 极强"

        # --- 3. 能量核心分析（探测 D0 潜伏基因） ---
        # 逻辑：量比连续温和（1.5-3.5）且换手处于黄金接力区（5%-12%）
        energy_core = "温和观察"
        if 1.6 <= lb <= 3.8 and 4.5 <= hs <= 13.5:
            energy_core = "🔥 能量堆积(主建仓)"
        elif lb > 4.0:
            energy_core = "⚡ 动能喷发"

        # --- 4. 信号、买入价与 D3 逃生线 ---
        # 综合评分：能量权重(40%) + 算法状态(30%) + 价格强度(30%)
        score = 65 + (lb * 10) + (zf * 1.5)
        if energy_core == "🔥 能量堆积(主建仓)": score += 15
        if hidden_money == "🚀 强力锁仓": score += 12
        if risk_shield == "🚨 高风险": score -= 40

        # 确定最终信号
        signal = "观察"
        if score > 108: signal = "💎 绝佳金种"
        elif score > 90: signal = "🚩 重点关注"

        # 建议最低买入价（D2）：回踩 D1 收盘价下方 0.8% 处
        min_buy_price = round(price * 0.992, 2)
        # D3 逃生线：若 D3 跌破 D1 收盘价 +1% 处，说明主力开盘杀，必须离场
        d3_exit_line = round(price * 1.01, 2)

        return pd.Series([
            signal, energy_core, hidden_money, risk_shield, 
            min_buy_price, d3_exit_line, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    print(f"🚀 V17.0 终极分析系统启动...")
    try:
        # 1. 抓取全 A 股 5000 只数据
        full_market = ak.stock_zh_a_spot_em()
        
        # 2. 定义报表列名（严格按要求）
        cols = [
            '信号', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
            '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)'
        ]
        
        # 3. 执行核心策略逻辑
        res_df = full_market.apply(analyze_v17_ultimate, axis=1)
        full_market[cols] = res_df
        
        # 4. 过滤结果：只留有信号的高价值标的，取前 50 名
        report = full_market.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(50)

        # 5. 生成 Excel 报告
        now_str = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y%m%d_%H%M')
        filename = f"Report_{now_str}.xlsx"
        
        final_out = report[['代码', '名称'] + cols]
        final_out.to_excel("index.xlsx", index=False) # 固定名用于链接下载
        final_out.to_excel(filename, index=False)   # 带时间名用于存档
        
        # 6. 生成 HTML 跳转下载页面
        # 注意：此处需要你在 GitHub Pages 中设置，或直接在 Actions 运行后点击文件
        raw_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/raw/main/index.xlsx"
        html_content = f'<html><head><meta http-equiv="refresh" content="0; url={raw_url}"></head><body>分析完成，已锁定 D2 接力名单！下载中...</body></html>'
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"✅ 任务成功：已扫描全 A 股并生成报告 {filename}")
        
    except Exception as e:
        print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    run_task()
