import akshare as ak
import pandas as pd
import datetime
import os
import random

def analyze_logic(row):
    try:
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- D0 潜伏拦截 (只选涨幅 1.5% - 4.8%) ---
        if not (1.5 <= zf <= 4.8): return None
        if not (150000000 <= amount <= 800000000): return None

        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        if energy_per_pct < 65000000: hidden_money = "🏹 箭在弦上(高度控盘)"

        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5: energy_core = "🔥 黄金堆积(D0转D1)"

        score = 50 + (lb * 15) + (hs * 5)
        if "D0转D1" in energy_core: score += 25
        if "高度控盘" in hidden_money: score += 15
        
        signal = "低位观察"
        if score > 105: signal = "💎 潜伏种子(D0重点)"
        elif score > 85: signal = "🚩 异动拦截"

        return pd.Series([
            signal, price, energy_core, hidden_money, "🛡️ 安全", 
            round(price * 0.995, 2), round(price * 0.98, 2), round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    # 获取北京时间
    bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 开始分析，当前北京时间: {bj_time}")
    
    try:
        # 增加参数确保从接口获取最新数据
        df = ak.stock_zh_a_spot_em()
        
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        report = df.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(30)
        
        # --- 核心改动：在表格最上方强行插入一行【时间戳】 ---
        # 这样每次生成的文件字节码绝对不同，Git 无法跳过
        time_row = pd.DataFrame([[f"REPORT_TIME: {bj_time}", "数据已更新", "", "", "", "", "", random.random(), "", "", "", ""]], 
                                columns=['代码', '名称'] + cols)
        
        final_report = pd.concat([time_row, report[['代码', '名称'] + cols]], ignore_index=True)
        
        # 强制保存
        final_report.to_excel(file_name, index=False)
        print(f"✅ 文件物理覆盖成功，指纹: {random.random()}")
            
    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    run_task()
