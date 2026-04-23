import akshare as ak
import pandas as pd
import datetime
import random

def analyze_logic(row):
    try:
        # --- 1. 基础硬性过滤 ---
        name = str(row.get('名称', ''))
        if any(x in name for x in ['ST', '退', '北']): return None # 剔除风险股及北交所

        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        if not all([price, hs, lb, amount]) or price <= 0: return None

        # --- 2. 空间拦截 (1.5% - 4.85%) ---
        if not (1.5 <= zf <= 4.85): return None
        if not (1.5e8 <= amount <= 8.5e8): return None

        # --- 3. 核心数学模型：计算“参考买入价”与“止损价” ---
        # 参考买入价逻辑：取当日波动的中轴线下方 1/3 处作为回踩确认位
        # 公式：$Price_{buy} = Low + (Price_{now} - Low) \times 0.618$
        ref_buy_price = round(low + (price - low) * 0.618, 2)
        
        # 动态止损位：以当日最低价下方 1.5% 作为硬止损
        stop_loss = round(low * 0.985, 2)

        # --- 4. 评分矩阵重构 ---
        energy_ratio = amount / zf if zf > 0 else 999999999
        
        # 筹码集中度评分
        score = 40.0
        score += (lb * 15.0)  # 量比爆发力
        score += (hs * 5.0)   # 换手活跃度
        
        # 能量核心判定
        energy_core = "潜伏蓄势"
        if 1.5 <= lb <= 3.5 and 4.0 <= hs <= 9.0:
            energy_core = "🔥 黄金堆积"
            score += 30.0
            
        # 资金性质判定
        hidden_money = "温和试盘"
        if energy_ratio < 60000000:
            hidden_money = "🏹 箭在弦上"
            score += 15.0

        signal = "💎 潜伏种子" if score > 110 else ("🚩 异动拦截" if score > 85 else "低位观察")

        # --- 5. 输出严谨列项 ---
        return pd.Series([
            signal, 
            price, 
            ref_buy_price,  # 新增：参考买入位
            stop_loss,      # 新增：硬止损位
            energy_core, 
            hidden_money, 
            round(score, 1), 
            zf, 
            hs, 
            lb, 
            round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        df = ak.stock_zh_a_spot_em()
        # 严谨列项定义
        cols = ['信号', '实时价', '参考买入位', '硬止损位', '能量核心', '暗盘分析', '综合评分', '涨幅%', '换手%', '量比', '成交额(亿)']
        
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        
        # 排除掉没有信号的，并按照评分和涨幅二次排序
        report = df.dropna(subset=['信号']).sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(50)
        
        # 加入物理更新指纹
        finger = pd.DataFrame([[f"VER:10.2", f"UPDATE:{bj_time}", "", "", "", "", random.random(), "", "", "", ""]], 
                             columns=['代码', '名称'] + cols)
        
        pd.concat([finger, report[['代码', '名称'] + cols]], ignore_index=True).to_excel(file_name, index=False, engine='openpyxl')
        print(f"✅ 严谨版报告已生成: {bj_time}")
            
    except Exception as e:
        print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    run_task()
