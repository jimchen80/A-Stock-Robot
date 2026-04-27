import akshare as ak
import pandas as pd
import datetime
import random
import time

def analyze_logic(row):
    """首席策略 10.5 严谨拦截逻辑"""
    try:
        # 1. 字段映射兼容（不同接口字段名对齐）
        name = str(row.get('名称', row.get('name', '')))
        code = str(row.get('代码', row.get('code', '')))
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4')): return None

        # 动态提取核心数值
        price = pd.to_numeric(row.get('最新价', row.get('trade', 0)), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅', row.get('changepercent', 0)), errors='coerce')
        amount = pd.to_numeric(row.get('成交额', row.get('amount', 0)), errors='coerce')
        lb = pd.to_numeric(row.get('量比', row.get('volume_ratio', 1.0)), errors='coerce') 
        hs = pd.to_numeric(row.get('换手率', row.get('turnoverratio', 0)), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收', row.get('settlement', 0)), errors='coerce')
        high = pd.to_numeric(row.get('最高', 0), errors='coerce')

        # 2. 核心拦截门槛 (10.5 宽放版)
        if pd.isna(price) or price <= 0: return None
        if not (0.5 <= zf <= 5.2) or not (80000000 <= amount <= 1200000000): return None

        # 3. 黄金分割博弈位
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2) if high > 0 else price
        
        # 4. 评分体系
        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except: return None

def run_task():
    file_name = "index.xlsx"
    full_cols = ['代码', '名称', '信号', '价格', '买入参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    df = None
    # --- 策略：三源冗余抓取 ---
    sources = [
        ("东方财富", ak.stock_zh_a_spot_em),
        ("同花顺", ak.stock_zh_a_spot_em), # akshare 内部同花顺接口调用方式视版本而定，此处示意逻辑
        ("新浪财经", ak.stock_zh_a_spot)
    ]

    for source_name, func in sources:
        try:
            print(f"📡 正在尝试连接 {source_name} 接口...")
            time.sleep(random.uniform(3, 8)) # 随机避峰
            df = func()
            if df is not None and not df.empty:
                print(f"✅ {source_name} 抓取成功！数据规模: {len(df)}")
                break
        except Exception as e:
            print(f"⚠️ {source_name} 连接失败: {str(e)[:50]}")
            continue

    try:
        if df is None: raise Exception("全线接口崩溃，触发 IP 保护机制")

        # 数据分析
        matches = []
        for _, row in df.iterrows():
            res = analyze_logic(row)
            if res:
                matches.append([row.get('代码', row.get('code')), row.get('名称', row.get('name'))] + res)
        
        # 结果对齐
        if not matches:
            report = pd.DataFrame(columns=full_cols)
        else:
            report = pd.DataFrame(matches, columns=full_cols).sort_values(by="综合评分", ascending=False).head(80)
        
        # 指纹输出
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V10.8-Triple", f"T:{bj_time}", "", "", "", "", "", "", "", "", ""]], columns=full_cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False)
        print(f"✅ 拦截任务完成：捕获 {len(report)} 只个股")

    except Exception as e:
        pd.DataFrame({"状态": ["多源熔断"], "诊断": [str(e)]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
