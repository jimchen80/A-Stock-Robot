import akshare as ak
import pandas as pd
import datetime
import random
import time

def get_stealth_config():
    """生成具备物理穿透力的指纹库"""
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]
    return {
        "User-Agent": random.choice(uas),
        "Referer": "https://quote.eastmoney.com/center/gridlist.html"
    }

def analyze_logic(row):
    """【核心层】首席策略 10.5 严谨逻辑"""
    try:
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        # 1. 物理过滤：剔除干扰项
        if any(x in name for x in ['ST', '退']) or code.startswith(('8', '4', '5')): return None

        # 2. 字段提取
        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        # 3. 数据完整性硬检查（防52分僵尸报告）
        # 如果检测到备用源导致的缺失，直接视为无效，不录入结果
        if pd.isna(lb) or (lb == 1.0 and hs == 0.0): return None

        # 4. 10.5 策略拦截门槛
        if not (0.5 <= zf <= 5.2) or not (80000000 <= amount <= 1200000000): return None

        # 5. 技术位与评分
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2) if high > prev_close else price
        stop_loss = round(low * 0.98, 2)
        
        score = 40.0 + (lb * 12) + (hs * 4)
        energy = "🔥 黄金堆积" if (lb > 1.5 and hs > 3.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 20
        
        signal = "💎 潜伏种子" if score >= 85 else "🚩 异动拦截"

        return [signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)]
    except: return None

def run_task():
    file_name = "index.xlsx"
    cols = ['代码', '名称', '信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    # --- 拟人化执行引擎 ---
    print(f"🕵️ 拟人化引擎启动，模拟真人看盘...")
    time.sleep(random.uniform(10, 20)) # 启动前长观察

    try:
        # 使用更稳健的接口，模拟真人翻页逻辑
        # 这里的 ak.stock_zh_a_spot_em 内部已经适配了最新的爬虫协议
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            raise Exception("物理链路受限：无法建立握手连接")

        results = []
        for index, row in df.iterrows():
            # 模拟真人阅读速度，每分析100行随机微停顿
            if index % 100 == 0: time.sleep(random.uniform(0.1, 0.3))
            
            res = analyze_logic(row)
            if res:
                results.append([row['代码'], row['名称']] + res)

        # 结果组装
        if not results:
            print("⚠️ 扫描完成：当前行情环境下无符合条件的异动种子")
            final_report = pd.DataFrame(columns=cols)
        else:
            final_report = pd.DataFrame(results, columns=cols).sort_values(by="综合评分", ascending=False).head(80)

        # 交付指纹
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V11.7-Shield", f"T:{bj_time}", "", "", "", "", "", "", "", "", "", ""]], columns=cols)
        
        pd.concat([finger, final_report], ignore_index=True).to_excel(file_name, index=False)
        print(f"🚀 拦截任务圆满成功！捕获 {len(final_report)} 只个股。")

    except Exception as e:
        # 故障输出：不留死角
        pd.DataFrame({"系统诊断": ["物理避封"], "故障原因": [str(e)], "对策": ["IP受限，静默6小时"]}).to_excel(file_name, index=False)

if __name__ == "__main__":
    run_task()
