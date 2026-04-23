import akshare as ak
import pandas as pd
import datetime
import random
import numpy as np

def analyze_logic(row):
    """
    首席策略 10.2：全 A 股“地毯式”启动拦截引擎
    """
    try:
        # --- 1. 物理层：初筛与清洗 ---
        name = str(row.get('名称', ''))
        code = str(row.get('代码', ''))
        # 严格过滤：ST、退市、北交所(8开头)、创业板/科创板(可选,此处暂留保留)
        if any(x in name for x in ['ST', '退']): return None
        if code.startswith(('8', '4')): return None 

        # 转换为数值，处理无效数据
        price = pd.to_numeric(row.get('最新价'), errors='coerce')
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce')
        hs = pd.to_numeric(row.get('换手率'), errors='coerce')
        lb = pd.to_numeric(row.get('量比'), errors='coerce')
        amount = pd.to_numeric(row.get('成交额'), errors='coerce')
        high = pd.to_numeric(row.get('最高'), errors='coerce')
        low = pd.to_numeric(row.get('最低'), errors='coerce')
        prev_close = pd.to_numeric(row.get('昨收'), errors='coerce')

        # 基础校验：剔除停牌及数据缺失
        if not all([price, hs, lb, amount, prev_close]) or price <= 0: return None

        # --- 2. 空间拦截层 (严谨区间：1.5% - 4.85%) ---
        # 理由：低于1.5%强度不足，高于5%已失先手
        if not (1.5 <= zf <= 4.85): return None
        
        # 成交额拦截 (1.5亿 - 8.5亿)：拦截中坚力量，剔除僵尸股和巨型机构股
        if not (1.5e8 <= amount <= 8.5e8): return None

        # --- 3. 交易决策层 (买入位/止损位计算) ---
        # 参考买入位：基于博弈论，取当日分时回踩的强支撑位
        # 公式：昨收价与今日最高价的黄金回撤位
        ref_buy_price = round(prev_close + (high - prev_close) * 0.382, 2)
        
        # 如果当前价已经低于计算出的买入位，则以当前价下浮 0.5% 作为博弈点
        if price < ref_buy_price:
            ref_buy_price = round(price * 0.995, 2)
            
        # 动态止损位：D3 风险线，设为今日最低价的 98%
        stop_loss = round(low * 0.98, 2)

        # --- 4. 评分矩阵 (核心因子分析) ---
        score = 50.0
        
        # 因子 A：量比因子 (爆发力)
        if lb >= 2.5: score += 25
        elif lb >= 1.5: score += 15
        
        # 因子 B：换手因子 (活跃度)
        if 3.5 <= hs <= 8.5: score += 20  # 黄金换手区间
        elif hs > 12: score -= 10         # 换手过高警惕对敲
        
        # 因子 C：筹码能耗比 (暗盘资金)
        energy_ratio = amount / zf
        hidden_money = "温和试盘"
        if energy_ratio < 55000000: 
            hidden_money = "🏹 箭在弦上(高度控盘)"
            score += 20
        elif energy_ratio > 200000000:
            hidden_money = "压力沉重"
            score -= 15

        # 状态判定
        energy_core = "潜伏蓄势"
        if lb > 1.8 and 4.0 <= hs <= 9.0:
            energy_core = "🔥 黄金堆积"
            score += 15

        # 最终信号
        signal = "💎 潜伏种子" if score >= 105 else ("🚩 异动拦截" if score >= 85 else "低位观察")

        return pd.Series([
            signal, price, ref_buy_price, stop_loss, energy_core, 
            hidden_money, round(score, 1), zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        
        # 定义严谨的报告列名
        cols = ['信号', '实时价', '参考买入位', 'D3止损位', '能量核心', 
                '资金暗盘', '综合评分', '涨幅%', '换手%', '量比', '成交额(亿)']
        
        # 运算扫描
        res = df.apply(analyze_logic, axis=1)
        # 显式处理多列赋值
        res_df = pd.DataFrame(res.tolist(), index=df.index, columns=cols)
        df = pd.concat([df[['代码', '名称']], res_df], axis=1)
        
        # 过滤并排序：评分越高、涨幅越小的越靠前（符合拦截逻辑）
        report = df.dropna(subset=['信号']).sort_values(by=["综合评分", "涨幅%"], ascending=[False, True]).head(60)
        
        # 生成时间戳指纹
        bj_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        finger = pd.DataFrame([[f"VER:10.2", f"T:{bj_time}", "", "", "", "", "", random.random(), "", "", "", ""]], 
                             columns=['代码', '名称'] + cols)
        
        # 最终整合输出
        final_df = pd.concat([finger, report], ignore_index=True)
        final_df.to_excel("index.xlsx", index=False, engine='openpyxl')
        
        print(f"✅ 任务完成: {bj_time}, 拦截数量: {len(report)}")
            
    except Exception as e:
        print(f"❌ 严重错误: {e}")

if __name__ == "__main__":
    run_task()
