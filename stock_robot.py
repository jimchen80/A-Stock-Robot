import akshare as ak
import pandas as pd
import datetime
import os

def analyze_logic(row):
    try:
        # 基础数据提取
        price = pd.to_numeric(row.get('最新价'), errors='coerce') or 0
        zf = pd.to_numeric(row.get('涨跌幅'), errors='coerce') or 0
        hs = pd.to_numeric(row.get('换手率'), errors='coerce') or 0
        lb = pd.to_numeric(row.get('量比'), errors='coerce') or 0
        amount = pd.to_numeric(row.get('成交额'), errors='coerce') or 0
        
        # --- D0 潜伏者核心逻辑 ---
        # 1. 严格拦截：剔除涨幅超过 4.8% 的个股（拒绝明牌）
        if not (1.5 <= zf <= 4.8):
            return None
            
        # 2. 流动性筛选：1.5亿 - 8.0亿（适合潜伏的活跃度）
        if not (150000000 <= amount <= 800000000):
            return None

        # 3. 暗盘能量分析
        energy_per_pct = amount / zf if zf > 0 else 999999999
        hidden_money = "温和试盘"
        risk_shield = "🛡️ 安全"
        if energy_per_pct < 65000000:
            hidden_money = "🏹 箭在弦上(高度控盘)"
            risk_shield = "✅ 极强"
        elif energy_per_pct > 250000000:
            hidden_money = "对敲承接 | 压力沉重"
            risk_shield = "⚠️ 预警"

        # 4. 能量因子：D0 转 D1 异动
        energy_core = "潜伏蓄势"
        if 1.2 <= lb <= 2.8 and 3.0 <= hs <= 7.5:
            energy_core = "🔥 黄金堆积(D0转D1)"
        elif lb > 3.0:
            energy_core = "🚀 动能初显"

        # 5. 综合评分
        score = 50 + (lb * 15) + (hs * 5)
        if "D0转D1" in energy_core: score += 25
        if "高度控盘" in hidden_money: score += 15
        
        signal = "低位观察"
        if score > 105: signal = "💎 潜伏种子(D0重点)"
        elif score > 85: signal = "🚩 异动拦截"

        # 6. 量化参考位
        min_buy = round(price * 0.995, 2)
        d3_exit = round(price * 0.98, 2)

        return pd.Series([
            signal, price, energy_core, hidden_money, risk_shield, 
            min_buy, d3_exit, round(score, 1), 
            zf, hs, lb, round(amount / 100000000, 2)
        ])
    except:
        return None

def run_task():
    # 路径兼容性处理：Win7/Linux 通用
    file_name = "index.xlsx"
    target_path = os.path.join(os.getcwd(), file_name)
    
    print(f"🚀 [V19.2] 正在进行全量扫描 (Win7/Linux 兼容版)...")
    try:
        # 获取实时数据
        df = ak.stock_zh_a_spot_em()
        
        # 定义报告列项
        cols = ['信号', '抓取实时价', '能量核心分析', '暗盘资金分析(对敲)', '风险盾', 
                '最低买入价', 'D3逃生线', '综合评分', '涨幅%', '换手率%', '量比', '成交额(亿)']
        
        # 执行策略分析
        res = df.apply(analyze_logic, axis=1)
        df[cols] = res
        
        # 筛选评分前 30 的潜伏标的
        report = df.dropna(subset=['信号']).sort_values(by="综合评分", ascending=False).head(30)
        
        # 强制保存文件
        final_df = report[['代码', '名称'] + cols]
        final_df.to_excel(target_path, index=False, engine='openpyxl')
        
        if os.path.exists(target_path):
            print(f"✅ 成功生成报告: {target_path}")
            print(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ 文件保存失败，请检查目录权限！")
            
    except Exception as e:
        print(f"❌ 运行中出现错误: {e}")

if __name__ == "__main__":
    run_task()
