import pandas as pd
import requests
import random
import time
from datetime import datetime, timedelta

class AlphaRobot13:
    def __init__(self):
        self.target_url = "http://push2.eastmoney.com/api/qt/clist/get"
        self.now_bj = datetime.utcnow() + timedelta(hours=8)
        self.raw_data = []
        self.selected_pool = []
        
        # 策略核心参数：三维立体拦截
        self.STRATEGY = {
            "BASE_FILTER": {"PRICE": (10, 30), "ZF": (1.0, 7.0), "AMOUNT_MIN": 70000000},
            "WEIGHTS": {"LB": 0.4, "HS": 0.3, "INDUSTRY": 0.3} # 因子权重
        }

    def _get_headers(self):
        """反爬防火墙：动态指纹仿真"""
        return {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 124)}.0.0.0 Safari/537.36",
            "Referer": "https://quote.eastmoney.com/center/gridlist.html",
            "Cookie": f"qgqt=1; st_pvi={random.randint(10000, 99999)}; st_si={random.randint(10000, 99999)}"
        }

    def fetch_market_snapshot(self):
        """全量抓取：规避 WAF 陷阱"""
        params = {
            "pn": "1", "pz": "3000", "po": "1", "np": "1", "fltt": "2", "invt": "2",
            "fid": "f3", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f6,f8,f10,f12,f14,f100", # 核心字段
            "_": int(time.time() * 1000)
        }
        try:
            time.sleep(random.uniform(2, 4)) # 模拟人类阅读延迟
            res = requests.get(self.target_url, params=params, headers=self._get_headers(), timeout=20)
            if res.status_code == 200:
                self.raw_data = res.json().get('data', {}).get('diff', [])
                print(f"✅ 成功穿透防火墙，捕获全市场数据：{len(self.raw_data)} 条")
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

    def _calculate_score(self, item):
        """策略内核：多因子共振评分逻辑"""
        score = 0
        lb = self._safe_float(item.get('f10')) # 量比
        hs = self._safe_float(item.get('f8'))  # 换手
        
        # 1. 量比评分 (偏好 1.5-3.0 之间的温和放量)
        if 1.5 <= lb <= 3.0: score += 40
        elif lb > 3.0: score += 20
        
        # 2. 换手率评分 (偏好 3%-10% 的活跃状态)
        if 3.0 <= hs <= 10.0: score += 40
        elif hs > 10.0: score += 15
        
        return score

    def _safe_float(self, val):
        try: return float(val) if val not in ["-", None, ""] else 0.0
        except: return 0.0

    def apply_strategy(self):
        """深度筛选：不仅仅是拦截，更是优选"""
        for item in self.raw_data:
            price = self._safe_float(item.get('f2'))
            zf = self._safe_float(item.get('f3'))
            amount = self._safe_float(item.get('f6'))
            
            # 基础门槛拦截
            if not (self.STRATEGY["BASE_FILTER"]["PRICE"][0] <= price <= self.STRATEGY["BASE_FILTER"]["PRICE"][1]): continue
            if not (self.STRATEGY["BASE_FILTER"]["ZF"][0] <= zf <= self.STRATEGY["BASE_FILTER"]["ZF"][1]): continue
            if amount < self.STRATEGY["BASE_FILTER"]["AMOUNT_MIN"]: continue
            
            # 因子加权计算
            score = self._calculate_score(item)
            if score >= 50: # 仅保留及格以上的标的
                self.selected_pool.append({
                    "代码": item.get('f12'),
                    "名称": item.get('f14'),
                    "行业": item.get('f100'),
                    "现价": price,
                    "涨幅%": zf,
                    "量比": self._safe_float(item.get('f10')),
                    "换手%": self._safe_float(item.get('f8')),
                    "成交额(亿)": round(amount/100000000, 2),
                    "策略评分": score
                })
        self.selected_pool = sorted(self.selected_pool, key=lambda x: x['策略评分'], reverse=True)

    def generate_professional_report(self):
        """报告生成逻辑：深度分析体现"""
        if not self.selected_pool:
            # 哪怕没选出来，也要生成“市场情绪诊断报告”
            diag_df = pd.DataFrame([{
                "诊断时间": self.now_bj.strftime('%Y-%m-%d %H:%M'),
                "市场状态": "因子共振缺失",
                "建议": "继续空仓观望，策略门槛未被触发"
            }])
            diag_df.to_excel("index.xlsx", index=False)
            return

        df = pd.DataFrame(self.selected_pool)
        
        # 深度修饰：增加行业分布统计
        industry_analysis = df['行业'].value_counts().to_dict()
        df['行业热度'] = df['行业'].map(industry_analysis)
        
        # 最终保存
        df.to_excel("index.xlsx", index=False)
        print(f"📊 报告生成完毕，入选标的：{len(df)} 只")

if __name__ == "__main__":
    robot = AlphaRobot13()
    robot.fetch_market_snapshot()
    robot.apply_strategy()
    robot.generate_professional_report()
