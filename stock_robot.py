import akshare as ak
import pandas as pd
import datetime
import random

def analyze_logic(row):
    try:
        # 1. 基础因子提取
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- 核心拦截：硬性剔除涨幅 > 4.8% 的个股 (严格执行 D0 潜伏) ---
        if not (1.5 <= zf <= 4.8): 
            return None
            
        # 2. 流动性拦截 (1.5亿 - 8.0亿)
        if not (150000000 <= amount <= 800000000): 
            return None

        # 3. 博弈因子：能效比计算 (反推筹码锁定度)
        energy_ratio = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        risk_shield = "安全"
        
        if energy_ratio < 65000000:
            hidden_money = "🏹 箭在弦上(高度控盘)"
            risk_shield = "极强"
        elif energy_ratio > 250000000:
            hidden_money = "对敲承接 | 压力沉重"
            risk_shield = "警惕"

        # 4. 能量转换因子 (判定 D0 转 D1)
        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5:
            energy_core = "🔥 黄金堆积(D0转D1)"

        # 5. 综合评分量化 (含补偿项)
        score = 50 + (lb * 15) + (hs * 5)
        if "D0转D1" in energy_core: score += 25
        if "高度控盘" in hidden_money: score += 15
        
        signal = "低位观察"
        if score > 105: signal = "💎 潜伏种子"
        elif score > 85: signal = "🚩 异动拦截"

        # 6. 风险锚点计算
        min_buy = round(price * 0.995, 2)  # 回踩 -0.5%
        d3_exit = round(price * 0.98, 2)   # 止损 -2.0%

        return pd.Series([
            signal, price, energy_core, hidden_money, risk_shield, 
            min_buy, d3_exit, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    # 获取北京时间 (UTC+8)
    bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 抓取 A 股实时快照
        df = ak.stock_zh_a_spot_em()
        
        # 因子输出矩阵列名
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        # 执行全量扫描
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        
        # 提取结果并排序
        report = df.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(35)
        
        # --- 物理保鲜机制：强制在第一行植入时间与随机指纹 ---
        fingerprint = pd.DataFrame([[
            f"UPDATE_TIME: {bj_time}", "指纹验证通过", "", "", "", "", "", 
            random.random(), "", "", "", ""
        ]], columns=['代码', '名称'] + cols)
        
        final_report = pd.concat([fingerprint, report[['代码', '名称'] + cols]], ignore_index=True)
        
        # 物理覆盖
        final_report.to_excel(file_name, index=False)
        print(f"✅ 扫描完成。拦截时间: {bj_time}")
            
    except Exception as e:
        print(f"❌ 运行崩溃: {e}")

if __name__ == "__main__":
    run_task()
