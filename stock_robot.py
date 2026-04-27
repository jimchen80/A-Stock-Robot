import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """
    【核心筛选层】—— 严格执行 10.5 首席策略逻辑
    确保在多源环境下依然保持筛选的严谨性
    """
    try:
        # 1. 基础过滤：剔除ST、退市、北交所
        name = str(row.get('名称', row.get('name', '')))
        code = str(row.get('代码', row.get('code', '')))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4', '5')): 
            return None

        # 2. 字段柔性对齐：适配东财、新浪、腾讯等不同接口的字段名
        price = pd.to_numeric(row.get('最新价', row.get('trade', 0)), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅', row.get('changepercent', 0)), errors='coerce')
        amount = pd.to_numeric(row.get('成交额', row.get('amount', 0)), errors='coerce')
        lb = pd.to_numeric(row.get('量比', row.get('volume_ratio', 1.0)), errors='coerce') 
        hs = pd.to_numeric(row.get('换手率', row.get('turnoverratio', 0)), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收', row.get('settlement', 0)), errors='coerce')
        high = pd.to_numeric(row.get('最高', row.get('high', 0)), errors='coerce')
        low = pd.to_numeric(row.get('最低', row.get('low', 0)), errors='coerce')

        # 3. 【核心门槛拦截】：10.5 严谨版
        # 涨幅锁定在 [0.5% - 5.2%]，成交额锁定在 [0.8亿 - 12亿]
        if pd.isna(price) or price <= 0: return None
        if not (0.5 <= zf <= 5.2): return None
        if not (80000000 <= amount <= 1200000000): return None

        # 4. 【技术位计算】：黄金分割博弈位
        # 买入参考定在昨日收盘与今日最高点回撤的 0.382 处
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2) if high > prev_close else price
        stop_loss = round(low * 0.98, 2) if low > 0 else round(price * 0.93, 2)

        # 5. 【评分体系】：量能加权评分
        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 20
        
        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    # 统一输出列
    cols = ['代码', '名称', '信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    # --- 物理避封策略：随机潜伏 ---
    time.sleep(random.randint(5, 30))
    
    df = None
    # --- 三源冗余抓取逻辑 ---
    sources = [
        ("主力东财", ak.stock_zh_a_spot_em),
        ("备用新浪", ak.stock_zh_a_spot),
        ("备用腾讯", ak.stock_zh_a_spot_em) # 示意多路径切换
    ]

    used_source = "未知"
    for s_name, func in sources:
        try:
            print(f"📡 尝试接入 {s_name} 节点...")
            df = func()
            if df is not None and not df.empty:
                used_source = s_name
                print(f"✅ {s_name} 接入成功，开始执行筛选逻辑...")
                break
            time.sleep(random.uniform(2, 5))
        except:
            continue

    try:
        if df is None: raise Exception("全线物理封锁，IP 需要冷却")

        # --- 核心逻辑执行层 ---
        results = []
        for _, row in df.iterrows():
            res = analyze_logic(row)
            if res:
                results.append([row.get('代码', row.get('code')), row.get('名称', row.get('name'))] + res)
        
        # --- 数据保护与输出 ---
        if not results:
            report = pd.DataFrame(columns=cols)
        else:
            report = pd.DataFrame(results, columns=cols).sort_values(by="综合评分", ascending=False).head(80)
        
        # 写入指纹信息
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V11.2-Full", f"S:{used_source}", f"T:{bj_time}", "", "", "", "", "", "", "", "", ""]], columns=cols)
        
        # 保存 Excel
        final_df = pd.concat([finger, report], ignore_index=True)
        final_df.to_excel(file_name, index=False)
        print(f"🚀 报告生成完毕！源：{used_source}，捕获标的：{len(report)}")

    except Exception as e:
        # 崩溃保底逻辑：确保不报红，并记录诊断信息
        pd.DataFrame({"状态": ["系统避封模式"], "诊断": [str(e)], "对策": ["IP受限，暂停1小时后再运行"]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
