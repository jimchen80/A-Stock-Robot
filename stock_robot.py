import akshare as ak
import pandas as pd
import datetime
import os
import random

def analyze_logic(row):
    try:
        # 基础数据转换
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- 核心逻辑 1：【潜伏拦截】剔除涨幅超过 4.8% 的明牌个股 ---
        if not (1.5 <= zf <= 4.8):
            return None
            
        # --- 核心逻辑 2：【流动性筛选】只看 1.5亿 - 8.0亿成交额 ---
        if not (150000000 <= amount <= 800000000):
            return None

        # 3. 暗盘资金分析（D0潜伏判定）
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        risk_shield = "🛡️ 安全"
        if energy_per_pct < 65000000:
            hidden_money = "🏹 箭在弦上(高度控盘)"
            risk_shield = "✅ 极强"
        elif energy_per_pct > 250000000:
            hidden_money = "对敲承接 | 压力沉重"
            risk_shield = "⚠️ 预警"

        # 4. 能量核心分析（寻找 D0 转 D1 异动）
        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5:
            energy_core = "🔥 黄金堆积(D0转D1)"
        elif lb > 3.0:
            energy_core = "🚀 动能初显"

        # 5. 评分体系
        score = 50 + (lb * 15) + (hs * 5)
        if "D0转D1" in energy_core: score += 25
        if "高度控盘" in hidden_money: score += 15
        
        signal = "低位观察"
        if score > 105: signal = "💎 潜伏种子(D0重点)"
        elif score > 85: signal = "🚩 异动拦截"

        # 6. 价格位计算
        min_buy = round(price * 0.995, 2)
        d3_exit = round(price * 0.98, 2)

        return pd.Series([
            signal, price, energy_core, hidden_money, risk_shield, 
            min_buy, d3_exit, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    # 获取北京时间
    bj_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    bj_time_str = bj_now.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"🚀 系统执行中... 北京时间: {bj_time_str}")
    
    try:
        # 抓取数据
        df = ak.stock_zh_a_spot_em()
        
        # 定义最终列名（包含抓取实时价）
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        # 运行分析逻辑
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        
        # 筛选结果
        report = df.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(30)
        
        # --- 核心改动：在首行插入【时间指纹】，彻底击碎 Git 缓存 ---
        time_fingerprint = pd.DataFrame([[
            f"REPORT_TIME: {bj_time_str}", 
            "数据实时更新", "", "", "", "", "", 
            random.random(), # 随机数确保文件二进制层面必变
            "", "", "", ""
        ]], columns=['代码', '名称'] + cols)
        
        final_df = pd.concat([time_fingerprint, report[['代码', '名称'] + cols]], ignore_index=True)
        
        # 强制保存到当前目录
        final_df.to_excel(file_name, index=False)
        print(f"✅ 物理文件覆盖成功。")
            
    except Exception as e:
        print(f"❌ 运行崩溃: {e}")

if __name__ == "__main__":
    run_task()
