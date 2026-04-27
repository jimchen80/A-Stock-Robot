import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """首席策略 10.5 宽放版逻辑"""
    try:
        # 1. 过滤非A股和ST
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

        # 2. 核心拦截条件（采用宽放版 10.5）
        if pd.isna(price) or price <= 0: return None
        if not (0.5 <= zf <= 5.2) or not (80000000 <= amount <= 1200000000): return None

        # 3. 黄金分割博弈位
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2)
        stop_loss = round(low * 0.98, 2)

        # 4. 评分体系
        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 20
        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    cols = ['信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    full_cols = ['代码', '名称'] + cols
    
    try:
        # A. 强化抓取（带 5 次重试）
        df = None
        for i in range(5):
            try:
                time.sleep(random.uniform(3, 6))
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty: break
            except: continue
        
        if df is None: raise Exception("接口连接失败")

        # B. 严谨遍历（弃用 apply，改用显式列表收集，彻底避开维度错误）
        final_list = []
        for _, row in df.iterrows():
            res = analyze_logic(row)
            if res:
                final_list.append([row['代码'], row['名称']] + res)
        
        # C. 稳健构建 DataFrame
        if not final_list:
            report = pd.DataFrame(columns=full_cols)
            print("⚠️ 扫描完成，今日暂无符合条件的种子")
        else:
            report = pd.DataFrame(final_list, columns=full_cols)
            report = report.sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(80)
        
        # D. 指纹与输出
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V10.6-Final", f"T:{bj_time}", "", "", "", "", "", random.random(), "", "", "", ""]], columns=full_cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False, engine='openpyxl')
        print(f"✅ 运行成功！捕获标的：{len(report)} 只")

    except Exception as e:
        # 最后的保底：如果真的崩了，输出带报错信息的表格，方便排查
        pd.DataFrame({"状态": ["逻辑崩溃"], "诊断信息": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
