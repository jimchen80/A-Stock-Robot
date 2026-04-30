import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """【核心层】首席策略 10.5 严谨逻辑"""
    try:
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        # 1. 过滤非A股和ST
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4', '5')): return None

        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        # 2. 物理数据补全检查（防僵尸数据）
        if pd.isna(lb) or (lb == 1.0 and hs == 0.0): return None

        # 3. 核心拦截门槛 [0.5% - 5.2%] & [0.8亿 - 12亿]
        if not (0.5 <= zf <= 5.2) or not (80000000 <= amount <= 1200000000): return None

        # 4. 技术位计算
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2) if high > prev_close else price
        stop_loss = round(low * 0.98, 2)
        
        # 5. 评分体系
        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 20
        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except: return None

def run_task():
    file_name = "index.xlsx"
    cols = ['代码', '名称', '信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    # --- 拟人化行为：启动前随机犹豫 ---
    time.sleep(random.uniform(15, 30))

    try:
        # 抓取数据
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty: raise Exception("物理链路受阻")

        # --- 维度防爆处理：改用列表组装，避免 apply 导致的维度错误 ---
        final_list = []
        for index, row in df.iterrows():
            # 模拟真人阅读停顿，打破机器执行指纹
            if index % 200 == 0: time.sleep(0.1)
            
            res = analyze_logic(row)
            if res:
                # 显式拼接：[代码, 名称] + [信号...额(亿)] 共12列
                final_list.append([row['代码'], row['名称']] + res)

        # 构建 DataFrame
        if not final_list:
            # 如果没鱼，生成带表头的空表，绝不报错
            report = pd.DataFrame(columns=cols)
            print("⚠️ 扫描完成：当前环境无符合条件的种子")
        else:
            report = pd.DataFrame(final_list, columns=cols)
            report = report.sort_values(by="综合评分", ascending=False).head(80)

        # 写入指纹信息
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V11.8-Shield", f"T:{bj_time}", "", "", "", "", "", "", "", "", "", ""]], columns=cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False)
        print(f"✅ 任务成功，拦截标的：{len(report)} 只")

    except Exception as e:
        # 故障时的优雅退出
        pd.DataFrame({"诊断": ["系统静默"], "原因": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
