import akshare as ak
import pandas as pd
import datetime
import random

def analyze_logic(row):
    try:
        # 获取基础数据
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- 核心拦截：D0潜伏区间 (1.5% - 4.8%)，绝对剔除 5% 以上个股 ---
        if not (1.5 <= zf <= 4.8): return None
        if not (1.5e8 <= amount <= 8e8): return None

        # 博弈因子：能耗比 (amount/zf)
        energy_ratio = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        if energy_ratio < 65000000: hidden_money = "🏹 箭在弦上(高度控盘)"
        elif energy_ratio > 250000000: hidden_money = "对敲承接 | 压力沉重"

        # 能量核心：D0转D1判定
        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5: energy_core = "🔥 黄金堆积(D0转D1)"

        # 评分计算
        score = 50 + (lb * 15) + (hs * 5)
        if "D0转D1" in energy_core: score += 25
        if "高度控盘" in hidden_money: score += 15
        
        signal = "💎 潜伏种子" if score > 105 else ("🚩 异动拦截" if score > 85 else "低位观察")

        return pd.Series([
            signal, price, energy_core, hidden_money, "🛡️ 安全", 
            round(price * 0.995, 2), round(price * 0.98, 2), round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    # 强制北京时间保鲜指纹
    bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        df = ak.stock_zh_a_spot_em()
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        report = df.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(40)
        
        # 插入物理指纹，强制 Git 识别二进制变化
        fingerprint = pd.DataFrame([[f"UPDATE: {bj_time}", "指纹验证", "", "", "", "", "", random.random(), "", "", "", ""]], 
                                  columns=['代码', '名称'] + cols)
        
        final_df = pd.concat([fingerprint, report[['代码', '名称'] + cols]], ignore_index=True)
        final_df.to_excel(file_name, index=False)
        print(f"✅ 物理报告生成成功: {bj_time}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    run_task()
