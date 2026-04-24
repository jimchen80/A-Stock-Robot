import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """首席策略 10.2：严谨拦截逻辑"""
    try:
        # 1. 字段预处理
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4')): return None

        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        # 2. 核心拦截条件
        if pd.isna(price) or price <= 0: return None
        if not (1.5 <= zf <= 4.85) or not (1.5e8 <= amount <= 8.5e8): return None

        # 3. 价格博弈位算法
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2)
        stop_loss = round(low * 0.98, 2)

        # 4. 综合评分
        score = 50.0 + (lb * 15) + (hs * 5)
        energy = "🔥 黄金堆积" if (1.5 <= lb <= 3.5 and 4.0 <= hs <= 9.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 30
        signal = "💎 潜伏种子" if score >= 105 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    cols = ['信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    try:
        # 1. 抗干扰抓取
        df = None
        for i in range(5):
            try:
                time.sleep(random.uniform(3, 8))
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty: break
            except: continue
        
        if df is None: raise Exception("数据源连接超时")

        # 2. 严谨计算与空值保护
        results = []
        for _, row in df.iterrows():
            res = analyze_logic(row)
            if res:
                # 组合 代码+名称+结果
                results.append([row['代码'], row['名称']] + res)
        
        # 3. 构建结果表 (彻底解决维度对不上的问题)
        full_cols = ['代码', '名称'] + cols
        if not results:
            report = pd.DataFrame(columns=full_cols)
        else:
            report = pd.DataFrame(results, columns=full_cols).sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(60)
        
        # 4. 生成带指纹的输出
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V10.4", f"T:{bj_time}", "", "", "", "", "", random.random(), "", "", "", ""]], columns=full_cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False, engine='openpyxl')
        print(f"✅ 任务完成。拦截到 {len(report)} 只个股。")

    except Exception as e:
        pd.DataFrame({"状态": ["逻辑崩溃"], "原因": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
