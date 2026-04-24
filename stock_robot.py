import akshare as ak
import pandas as pd
import datetime
import random
import os

def analyze_logic(row):
    """
    严谨的数据清洗与逻辑分析
    """
    try:
        # 1. 字段预处理：确保全部为浮点数，报错则转为 NaN
        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')

        # 2. 严谨过滤：剔除停牌、空值、非潜伏区间
        if pd.isna(price) or price <= 0: return None
        if not (1.5 <= zf <= 4.85): return None
        if not (1.5e8 <= amount <= 8.5e8): return None

        # 3. 核心计算：参考买入位 (黄金分割)
        ref_buy = round(prev_close + (high - prev_close) * 0.382, 2)
        stop_loss = round(low * 0.98, 2)

        # 4. 评分
        score = 50.0 + (lb * 15) + (hs * 5)
        energy = "🔥 黄金堆积" if (1.5 <= lb <= 3.5 and 4.0 <= hs <= 9.0) else "潜伏蓄势"
        if energy == "🔥 黄金堆积": score += 30
        
        signal = "💎 潜伏种子" if score >= 105 else "🚩 异动拦截"

        return pd.Series([signal, price, ref_buy, stop_loss, energy, round(score, 1), zf, hs, lb, round(amount/1e8, 2)])
    except:
        return None

def run_task():
    file_name = "index.xlsx"
    cols = ['信号', '价格', '买入参考', '止损参考', '能量状态', '综合评分', '涨幅%', '换手%', '量比', '额(亿)']
    
    try:
        # 从东方财富抓取全A股快照
        df = ak.stock_zh_a_spot_em()
        
        # 处理逻辑：增加显式的结果对齐
        results = df.apply(analyze_logic, axis=1)
        res_df = pd.DataFrame(results.tolist(), index=df.index, columns=cols)
        final = pd.concat([df[['代码', '名称']], res_df], axis=1).dropna(subset=['信号'])
        
        # 排序并截取
        report = final.sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(60)
        
        # 指纹防缓存
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"V10.2", f"T:{bj_time}", "", "", "", random.random(), "", "", "", ""]], columns=['代码', '名称'] + cols)
        
        pd.concat([finger, report], ignore_index=True).to_excel(file_name, index=False, engine='openpyxl')
        print("✅ Excel 生成成功")
    except Exception as e:
        # 终极容错：如果崩溃，生成带有错误提示的 Excel，绝不让 Actions 报红
        error_df = pd.DataFrame({"系统状态": ["抓取失败"], "原因": [str(e)], "建议": ["稍后手动重试 Run Workflow"]})
        error_df.to_excel(file_name, index=False)
        print(f"❌ 运行中断，已生成错误报告: {e}")

if __name__ == "__main__":
    run_task()
