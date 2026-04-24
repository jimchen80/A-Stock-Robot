import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """首席策略 10.5：适度放宽后的严谨拦截逻辑"""
    try:
        # 1. 物理层过滤
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4')): return None

        # 2. 数值强转
        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        if pd.isna(price) or price <= 0: return None

        # --- 3. 核心放宽调整区 ---
        # 涨幅放宽：0.5% 到 5.2% (捕捉更早，容忍更强)
        if not (0.5 <= zf <= 5.2): return None
        # 成交额放宽：0.8亿 到 12.0亿 (覆盖更多市值规模)
        if not (80000000 <= amount <= 1200000000): return None
        # --- ----------------- ---

        # 4. 买入博弈位算法
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2)
        stop_loss = round(low * 0.98, 2)

        # 5. 评分权重 (保持严谨)
        score = 40.0 
        score += (lb * 12)  # 量比权重
        score += (hs * 4)   # 换手权重
        
        energy = "潜伏蓄势"
        if lb > 1.5 and hs > 3.0:
            energy = "🔥 黄金堆积"
            score += 20
        
        if amount > 500000000: # 大单介入加分
            score += 15

        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    cols = ['信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    full_cols = ['代码', '名称'] + cols
    
    try:
        # 抗干扰多级抓取
        df = None
        for i in range(5):
            try:
                time.sleep(random.uniform(2, 5))
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty: break
            except: continue
        
        if df is None: raise Exception("数据源超时，请尝试重新运行 Actions")

        # 执行拦截
        matches = []
        for _, row in df.iterrows():
            logic_res = analyze_logic(row)
            if logic_res:
                matches.append([row['代码'], row['名称']] + logic_res)
        
        # 结果组装
        if not matches:
            report = pd.DataFrame(columns=full_cols)
        else:
            # 排序逻辑：评分高且涨幅适中的优先
            report = pd.DataFrame(matches, columns=full_cols).sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(80)
        
        # 物理指纹与时间戳
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V10.5-Broad", f"T:{bj_time}", "", "", "", "", "", random.random(), "", "", "", ""]], columns=full_cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False, engine='openpyxl')
        print(f"✅ 宽放版扫描完成。捕获数量: {len(report)}")

    except Exception as e:
        pd.DataFrame({"状态": ["系统波动"], "原因": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
