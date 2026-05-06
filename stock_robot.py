import pandas as pd
import requests
import random
import time
from datetime import datetime, timedelta

class QuantumEngine:
    """深度仿真抓取引擎：模拟真实浏览器协议栈"""
    def __init__(self):
        self.session = requests.Session()
        self.bj_time = datetime.utcnow() + timedelta(hours=8)
        
    def _init_session(self):
        """模拟首屏访问，获取服务器分配的初始 Cookie"""
        base_url = "https://quote.eastmoney.com/center/gridlist.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.eastmoney.com/"
        }
        try:
            self.session.get(base_url, headers=headers, timeout=10)
        except:
            pass

    def get_market_data(self):
        """多重逻辑自愈的抓取函数"""
        self._init_session()
        
        # 动态字段定义：f2-价格, f3-涨幅, f6-额, f8-换手, f10-量比, f12-代码, f14-名称, f100-行业
        fields = "f2,f3,f6,f8,f10,f12,f14,f100"
        url = f"http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "4000", "po": "1", "np": "1", 
            "fltt": "2", "invt": "2", "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": fields,
            "_": int(time.time() * 1000)
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://quote.eastmoney.com/center/gridlist.html",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

        for retry in range(3):
            try:
                time.sleep(random.uniform(1.5, 3.5))
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
                json_data = resp.json()
                diff = json_data.get('data', {}).get('diff', [])
                
                if isinstance(diff, list) and len(diff) > 0:
                    return diff
                print(f"第 {retry+1} 次尝试：数据为空，WAF 可能正在反击...")
            except Exception as e:
                print(f"链路异常: {e}")
        return []

class AlphaStrategy:
    """策略决策中心：多维度因子筛选与评分"""
    def __init__(self, raw_data):
        self.data = raw_data
        self.results = []
        
    def _safe(self, val):
        try: return float(val) if val not in ["-", None, ""] else 0.0
        except: return 0.0

    def process(self):
        for item in self.data:
            # 1. 基础数据清洗
            p = self._safe(item.get('f2'))   # 价格
            zf = self._safe(item.get('f3'))  # 涨幅
            amt = self._safe(item.get('f6')) # 成交额
            lb = self._safe(item.get('f10')) # 量比
            hs = self._safe(item.get('f8'))  # 换手
            
            # 2. 策略硬性门槛（首席策略14.0基准）
            if not (10 <= p <= 35): continue
            if not (1.5 <= zf <= 7.5): continue
            if amt < 80000000: continue # 0.8亿门槛
            
            # 3. 评分矩阵
            score = 50 
            if 1.5 < lb < 3.5: score += 20 # 攻击性量比
            if 4.0 < hs < 12.0: score += 20 # 活跃筹码
            if zf > 5.0: score += 10 # 强势基因
            
            self.results.append({
                "代码": item.get('f12'),
                "名称": item.get('f14'),
                "现价": p,
                "涨幅%": zf,
                "成交额(亿)": round(amt/1e8, 2),
                "量比": lb,
                "换手%": hs,
                "行业": item.get('f100'),
                "综合评分": score
            })
        
        # 按评分降序，取前 50 名
        return sorted(self.results, key=lambda x: x['综合评分'], reverse=True)[:50]

# --- 主执行链路 ---
if __name__ == "__main__":
    engine = QuantumEngine()
    raw_list = engine.get_market_data()
    
    update_str = engine.bj_time.strftime('%Y-%m-%d %H:%M:%S')
    
    if raw_list:
        strategy = AlphaStrategy(raw_list)
        final_list = strategy.process()
        
        if final_list:
            df = pd.DataFrame(final_list)
            df.to_excel("index.xlsx", index=False)
            print(f"SUCCESS: 捕获并分析了 {len(raw_list)} 只个股，筛选出 {len(final_list)} 只精选标的")
        else:
            pd.DataFrame([{"提醒": "数据抓取成功但无共振标的", "样本量": len(raw_list), "更新时间": update_str}]).to_excel("index.xlsx", index=False)
    else:
        pd.DataFrame([{"错误": "抓取失败：防火墙拦截或接口变更", "更新时间": update_str}]).to_excel("index.xlsx", index=False)
