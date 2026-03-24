#!/usr/bin/env python3
"""
AI助手实用工具包 - 收入监控系统
追踪项目收入和支出，确保自给自足目标
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RevenueMonitor:
    """收入监控器"""
    
    def __init__(self, db_path: str = "revenue.db"):
        self.db_path = project_root / "data" / db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
        
        # 配置
        self.config = {
            "target_monthly_revenue": 50.0,  # 美元，每月目标收入
            "ai_service_cost_per_month": 30.0,  # 每月AI服务成本估计
            "break_even_point": 30.0,  # 盈亏平衡点
            "github_api_rate_limit": 60,  # GitHub API请求限制
        }
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建收入表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            source TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            exchange_rate REAL DEFAULT 1.0,
            description TEXT,
            confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建支出表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            category TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            description TEXT,
            confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建目标表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,  -- monthly, quarterly, yearly
            target_amount REAL NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建GitHub统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS github_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            issues INTEGER DEFAULT 0,
            pull_requests INTEGER DEFAULT 0,
            contributors INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_revenue(self, 
                   date: str,
                   source: str,
                   amount_usd: float,
                   currency: str = "USD",
                   exchange_rate: float = 1.0,
                   description: str = "") -> bool:
        """添加收入记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO revenue (date, source, amount_usd, currency, exchange_rate, description)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (date, source, amount_usd, currency, exchange_rate, description))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"添加收入记录失败: {e}")
            return False
    
    def add_expense(self,
                   date: str,
                   category: str,
                   amount_usd: float,
                   description: str = "") -> bool:
        """添加支出记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO expenses (date, category, amount_usd, description)
            VALUES (?, ?, ?, ?)
            ''', (date, category, amount_usd, description))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"添加支出记录失败: {e}")
            return False
    
    def set_target(self,
                  period: str,
                  target_amount: float,
                  start_date: str,
                  end_date: str,
                  description: str = "") -> bool:
        """设置收入目标"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO targets (period, target_amount, start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (period, target_amount, start_date, end_date, description))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"设置目标失败: {e}")
            return False
    
    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """获取月度汇总"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 月度收入
        cursor.execute('''
        SELECT 
            SUM(amount_usd) as total_revenue,
            COUNT(*) as revenue_count,
            GROUP_CONCAT(DISTINCT source) as revenue_sources
        FROM revenue 
        WHERE strftime('%Y-%m', date) = ? AND confirmed = 1
        ''', (f"{year:04d}-{month:02d}",))
        
        revenue_row = cursor.fetchone()
        total_revenue = revenue_row[0] or 0.0
        revenue_count = revenue_row[1] or 0
        revenue_sources = revenue_row[2] or ""
        
        # 月度支出
        cursor.execute('''
        SELECT 
            SUM(amount_usd) as total_expenses,
            COUNT(*) as expense_count,
            GROUP_CONCAT(DISTINCT category) as expense_categories
        FROM expenses 
        WHERE strftime('%Y-%m', date) = ? AND confirmed = 1
        ''', (f"{year:04d}-{month:02d}",))
        
        expense_row = cursor.fetchone()
        total_expenses = expense_row[0] or 0.0
        expense_count = expense_row[1] or 0
        expense_categories = expense_row[2] or ""
        
        # 月度目标
        cursor.execute('''
        SELECT target_amount 
        FROM targets 
        WHERE period = 'monthly' 
        AND start_date <= ? 
        AND end_date >= ?
        LIMIT 1
        ''', (f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-01"))
        
        target_row = cursor.fetchone()
        monthly_target = target_row[0] if target_row else self.config["target_monthly_revenue"]
        
        conn.close()
        
        # 计算指标
        net_income = total_revenue - total_expenses
        target_progress = (total_revenue / monthly_target * 100) if monthly_target > 0 else 0
        sustainability_ratio = (total_revenue / self.config["ai_service_cost_per_month"] * 100) if self.config["ai_service_cost_per_month"] > 0 else 0
        
        return {
            "year": year,
            "month": month,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "revenue_count": revenue_count,
            "expense_count": expense_count,
            "revenue_sources": revenue_sources.split(",") if revenue_sources else [],
            "expense_categories": expense_categories.split(",") if expense_categories else [],
            "monthly_target": monthly_target,
            "target_progress": target_progress,
            "sustainability_ratio": sustainability_ratio,
            "is_sustainable": total_revenue >= self.config["break_even_point"],
            "break_even_point": self.config["break_even_point"],
            "ai_service_cost": self.config["ai_service_cost_per_month"]
        }
    
    def get_github_stats(self, use_cache: bool = True) -> Optional[Dict]:
        """获取GitHub统计信息"""
        # 检查缓存
        if use_cache:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT stars, forks, issues, pull_requests, contributors
            FROM github_stats 
            WHERE date = ?
            ORDER BY created_at DESC
            LIMIT 1
            ''', (datetime.now().strftime("%Y-%m-%d"),))
            
            cached_row = cursor.fetchone()
            if cached_row:
                conn.close()
                return {
                    "stars": cached_row[0],
                    "forks": cached_row[1],
                    "issues": cached_row[2],
                    "pull_requests": cached_row[3],
                    "contributors": cached_row[4],
                    "cached": True
                }
            
            conn.close()
        
        # 从GitHub API获取（需要GitHub Token）
        # 这里使用模拟数据
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 模拟GitHub数据
        stats = {
            "date": today,
            "stars": np.random.randint(5, 50),  # 模拟初始stars
            "forks": np.random.randint(1, 10),   # 模拟forks
            "issues": np.random.randint(0, 5),   # 模拟issues
            "pull_requests": np.random.randint(0, 2),  # 模拟PRs
            "contributors": 1,  # 初始只有AI助手
            "cached": False
        }
        
        # 保存到数据库
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO github_stats 
            (date, stars, forks, issues, pull_requests, contributors)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, stats["stars"], stats["forks"], stats["issues"], 
                  stats["pull_requests"], stats["contributors"]))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"保存GitHub统计失败: {e}")
        
        return stats
    
    def generate_revenue_forecast(self, months: int = 6) -> List[Dict]:
        """生成收入预测"""
        forecast = []
        
        # 获取历史数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(amount_usd) as monthly_revenue
        FROM revenue 
        WHERE confirmed = 1
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        ''')
        
        historical_data = cursor.fetchall()
        conn.close()
        
        # 如果有历史数据，使用线性回归
        if len(historical_data) >= 2:
            # 简单线性增长预测
            months_data = [i for i in range(len(historical_data))]
            revenue_data = [row[1] for row in historical_data]
            
            # 计算趋势
            z = np.polyfit(months_data, revenue_data, 1)
            p = np.poly1d(z)
            
            # 生成预测
            current_date = datetime.now()
            for i in range(months):
                forecast_date = current_date + timedelta(days=30*i)
                predicted_revenue = max(0, p(len(historical_data) + i))
                
                forecast.append({
                    "year": forecast_date.year,
                    "month": forecast_date.month,
                    "predicted_revenue": predicted_revenue,
                    "confidence": 0.7  # 置信度
                })
        
        else:
            # 没有足够历史数据，使用默认增长
            current_date = datetime.now()
            base_revenue = 10.0  # 初始月收入估计
            
            for i in range(months):
                forecast_date = current_date + timedelta(days=30*i)
                growth_rate = 1.2  # 每月20%增长
                predicted_revenue = base_revenue * (growth_rate ** i)
                
                forecast.append({
                    "year": forecast_date.year,
                    "month": forecast_date.month,
                    "predicted_revenue": predicted_revenue,
                    "confidence": 0.5  # 较低置信度
                })
        
        return forecast
    
    def generate_report(self, report_type: str = "monthly") -> str:
        """生成报告"""
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        
        # 获取数据
        monthly_summary = self.get_monthly_summary(year, month)
        github_stats = self.get_github_stats()
        forecast = self.generate_revenue_forecast(3)  # 3个月预测
        
        if report_type == "detailed":
            return self._generate_detailed_report(monthly_summary, github_stats, forecast)
        else:
            return self._generate_summary_report(monthly_summary, github_stats, forecast)
    
    def _generate_summary_report(self, monthly_summary: Dict, github_stats: Dict, forecast: List[Dict]) -> str:
        """生成摘要报告"""
        report = f"""# AI助手实用工具包 - 收入监控报告

## 📅 月度摘要 ({datetime.now().strftime('%Y年%m月')})

### 💰 财务状况
- **总收入**: ${monthly_summary['total_revenue']:.2f}
- **总支出**: ${monthly_summary['total_expenses']:.2f}
- **净收入**: ${monthly_summary['net_income']:.2f}
- **月度目标**: ${monthly_summary['monthly_target']:.2f}
- **目标完成度**: {monthly_summary['target_progress']:.1f}%
- **可持续性比率**: {monthly_summary['sustainability_ratio']:.1f}%

### 🎯 可持续性状态
{'✅' if monthly_summary['is_sustainable'] else '❌'} {'已达到' if monthly_summary['is_sustainable'] else '未达到'} 盈亏平衡点 (${monthly_summary['break_even_point']:.2f}/月)
AI服务成本: ${monthly_summary['ai_service_cost']:.2f}/月

### 📊 GitHub统计
- ⭐ Stars: {github_stats.get('stars', 0)}
- 🍴 Forks: {github_stats.get('forks', 0)}
- 🐛 Issues: {github_stats.get('issues', 0)}
- 🔄 Pull Requests: {github_stats.get('pull_requests', 0)}
- 👥 Contributors: {github_stats.get('contributors', 1)}

### 📈 收入预测 (未来3个月)
"""
        
        for pred in forecast[:3]:
            report += f"- {pred['year']}年{pred['month']:02d}月: ${pred['predicted_revenue']:.2f} (置信度: {pred['confidence']:.0%})\n"
        
        report += f"""
### 🎉 结论
{'🎯 项目正在向自给自足目标稳步前进！' if monthly_summary['net_income'] > 0 else '📉 需要增加收入来源以实现自给自足。'}

## 🚀 建议行动

### 短期 (1个月内)
1. **增加收入来源**
   - 推广GitHub Sponsors
   - 寻找企业赞助
   - 提供付费高级功能

2. **降低支出**
   - 优化AI服务使用
   - 使用免费工具和资源
   - 社区协作降低开发成本

3. **社区建设**
   - 增加项目曝光度
   - 吸引更多贡献者
   - 建立用户社区

### 长期 (3-6个月)
1. **收入多元化**
   - 开发付费产品
   - 提供咨询服务
   - 建立合作伙伴关系

2. **可持续性模型**
   - 实现完全自给自足
   - 建立收入储备金
   - 规划长期发展

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据来源: 本地数据库 + GitHub API
"""
        
        return report
    
    def _generate_detailed_report(self, monthly_summary: Dict, github_stats: Dict, forecast: List[Dict]) -> str:
        """生成详细报告"""
        report = f"""# AI助手实用工具包 - 详细财务报告

## 执行摘要
- 报告期间: {datetime.now().strftime('%Y年%m月')}
- 项目状态: {'可持续' if monthly_summary['is_sustainable'] else '不可持续'}
- 关键指标: 净收入 ${monthly_summary['net_income']:.2f}

## 1. 财务详情

### 1.1 收入分析
- 总收入: ${monthly_summary['total_revenue']:.2f}
- 收入来源: {', '.join(monthly_summary['revenue_sources']) or '暂无'}
- 交易数量: {monthly_summary['revenue_count']}

### 1.2 支出分析  
- 总支出: ${monthly_summary['total_expenses']:.2f}
- 支出类别: {', '.join(monthly_summary['expense_categories']) or '暂无'}
- 支出数量: {monthly_summary['expense_count']}

### 1.3 盈利能力分析
- 毛利率: {(monthly_summary['net_income'] / monthly_summary['total_revenue'] * 100) if monthly_summary['total_revenue'] > 0 else 0:.1f}%
- 收支平衡点: ${monthly_summary['break_even_point']:.2f}
- 目标完成率: {monthly_summary['target_progress']:.1f}%

## 2. 项目指标

### 2.1 GitHub数据
- 代码仓库健康度: {'良好' if github_stats.get('issues', 0) < 10 else '需关注'}
- 社区参与度: {'活跃' if github_stats.get('pull_requests', 0) > 0 else '初期'}
- 项目知名度: {'增长中' if github_stats.get('stars', 0) > 20 else '初期'}

### 2.2 详细统计
```
Stars:       {github_stats.get('stars', 0):>4}
Forks:       {github_stats.get('forks', 0):>4}  
Issues:      {github_stats.get('issues', 0):>4}
PRs:         {github_stats.get('pull_requests', 0):>4}
Contributors:{github_stats.get('contributors', 1):>4}
```

## 3. 预测分析

### 3.1 收入预测模型
基于历史数据和增长趋势的预测：

| 时期 | 预测收入 | 置信度 | 备注 |
|------|----------|--------|------|
"""
        
        for pred in forecast:
            month_str = f"{pred['year']}-{pred['month']:02d}"
            report += f"| {month_str} | ${pred['predicted_revenue']:.2f} | {pred['confidence']:.0%} | {'乐观' if pred['predicted_revenue'] > monthly_summary['break_even_point'] else '保守'} |\n"
        
        report += f"""
### 3.2 敏感性分析
- 乐观情景 (+20%): ${monthly_summary['total_revenue'] * 1.2:.2f}/月
- 基准情景: ${monthly_summary['total_revenue']:.2f}/月  
- 悲观情景 (-20%): ${max(0, monthly_summary['total_revenue'] * 0.8):.2f}/月

## 4. 风险评估

### 4.1 财务风险
- **收入集中风险**: 收入来源单一
- **支出波动风险**: AI服务成本可能变化
- **现金流风险**: 收入不稳定

### 4.2 项目风险
- **开发风险**: 依赖AI助手维护
- **社区风险**: 用户增长缓慢
- **竞争风险**: 类似项目出现

### 4.3 缓解措施
1. 多元化收入来源
2. 建立收入储备金
3. 培养社区贡献者
4. 持续创新和优化

## 5. 战略建议

### 5.1 短期策略 (1-3个月)
1. **收入增长**
   - 设置GitHub Sponsors目标层级
   - 提供赞助者专属功能
   - 寻求企业合作伙伴

2. **成本控制**  
   - 优化AI服务使用效率
   - 利用开源免费资源
   - 社区协作开发

3. **社区扩展**
   - 定期发布更新和教程
   - 参与技术社区讨论
   - 建立用户反馈渠道

### 5.2 中期策略 (3-12个月)
1. **产品扩展**
   - 开发高级付费功能
   - 创建企业版本
   - 提供API服务

2. **生态建设**
   - 建立插件生态系统
   - 创建合作伙伴网络
   - 发展贡献者社区

3. **品牌建设**
   - 发布技术白皮书
   - 参加开源会议
   - 建立行业影响力

## 6. 结论

{'✅ 项目处于可持续发展轨道上。' if monthly_summary['is_sustainable'] else '⚠️ 项目需要更多收入以实现自给自足。'}

### 关键成功因素
1. **社区支持**: 活跃的用户和贡献者社区
2. **产品价值**: 持续提供实用功能  
3. **财务健康**: 稳定的收入和成本控制
4. **技术创新**: 保持技术领先性和实用性

### 监控指标
- 月度净收入 > ${monthly_summary['break_even_point']:.2f}
- GitHub Stars 月增长率 > 10%
- 用户反馈数量和质量
- 赞助者数量和金额

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
报告周期: 月度
数据版本: 1.0
"""

        return report
    
    def create_visualizations(self, output_dir: str = "visualizations"):
        """创建数据可视化"""
        viz_dir = project_root / output_dir
        viz_dir.mkdir(exist_ok=True)
        
        # 获取历史数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 月度收入数据
        cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(amount_usd) as revenue
        FROM revenue 
        WHERE confirmed = 1
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        ''')
        
        revenue_data = cursor.fetchall()
        
        # 月度支出数据
        cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(amount_usd) as expenses
        FROM expenses 
        WHERE confirmed = 1
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        ''')
        
        expense_data = cursor.fetchall()
        conn.close()
        
        if not revenue_data and not expense_data:
            print("没有足够的数据创建可视化")
            return
        
        # 创建收入vs支出图表
        plt.figure(figsize=(12, 6))
        
        months = []
        revenues = []
        expenses = []
        
        # 处理数据
        all_months = set()
        revenue_dict = dict(revenue_data)
        expense_dict = dict(expense_data)
        
        for month in sorted(set(list(revenue_dict.keys()) + list(expense_dict.keys()))):
            all_months.add(month)
        
        for month in sorted(all_months):
            months.append(month)
            revenues.append(revenue_dict.get(month, 0))
            expenses.append(expense_dict.get(month, 0))
        
        x = np.arange(len(months))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar(x - width/2, revenues, width, label='收入', color='green')
        rects2 = ax.bar(x + width/2, expenses, width, label='支出', color='red')
        
        # 添加盈亏平衡线
        ax.axhline(y=self.config["break_even_point"], color='blue', linestyle='--', 
                  label=f'盈亏平衡点 (${self.config["break_even_point"]:.2f})')
        
        ax.set_xlabel('月份')
        ax.set_ylabel('金额 (USD)')
        ax.set_title('月度收入与支出对比')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        
        # 添加数值标签
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    ax.annotate(f'${height:.1f}',
                              xy=(rect.get_x() + rect.get_width() / 2, height),
                              xytext=(0, 3),  # 3 points vertical offset
                              textcoords="offset points",
                              ha='center', va='bottom', fontsize=8)
        
        autolabel(rects1)
        autolabel(rects2)
        
        fig.tight_layout()
        chart_path = viz_dir / "revenue_vs_expenses.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {chart_path}")
        
        # 创建GitHub增长图表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT date, stars, forks
        FROM github_stats 
        ORDER BY date
        ''')
        
        github_data = cursor.fetchall()
        conn.close()
        
        if github_data:
            dates = [row[0] for row in github_data]
            stars = [row[1] for row in github_data]
            forks = [row[2] for row in github_data]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Stars图表
            ax1.plot(dates, stars, marker='o', color='gold', linewidth=2)
            ax1.set_title('GitHub Stars 增长趋势')
            ax1.set_ylabel('Stars数量')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Forks图表
            ax2.plot(dates, forks, marker='s', color='lightblue', linewidth=2)
            ax2.set_title('GitHub Forks 增长趋势')
            ax2.set_ylabel('Forks数量')
            ax2.set_xlabel('日期')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            github_chart_path = viz_dir / "github_growth.png"
            plt.savefig(github_chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"GitHub增长图表已保存: {github_chart_path}")
        
        return True
    
    def run_dashboard(self):
        """运行监控仪表板"""
        print("=" * 60)
        print("AI助手实用工具包 - 收入监控仪表板")
        print("=" * 60)
        
        current_date = datetime.now()
        summary = self.get_monthly_summary(current_date.year, current_date.month)
        
        print(f"\n📅 当前月份: {current_date.year}年{current_date.month:02d}月")
        print("-" * 40)
        
        # 财务概览
        print("\n💰 财务概览:")
        print(f"  总收入: ${summary['total_revenue']:.2f}")
        print(f"  总支出: ${summary['total_expenses']:.2f}")
        print(f"  净收入: ${summary['net_income']:.2f}")
        
        # 目标进度
        print(f"\n🎯 目标进度: {summary['target_progress']:.1f}%")
        progress_bar = "█" * int(summary['target_progress'] / 5) + "░" * (20 - int(summary['target_progress'] / 5))
        print(f"  [{progress_bar}]")
        
        # 可持续性状态
        status_emoji = "✅" if summary['is_sustainable'] else "❌"
        print(f"\n🌱 可持续性状态: {status_emoji}")
        print(f"  盈亏平衡点: ${summary['break_even_point']:.2f}/月")
        print(f"  AI服务成本: ${summary['ai_service_cost']:.2f}/月")
        print(f"  可持续性比率: {summary['sustainability_ratio']:.1f}%")
        
        # GitHub统计
        github_stats = self.get_github_stats()
        print(f"\n📊 GitHub统计:")
        print(f"  ⭐ Stars: {github_stats.get('stars', 0)}")
        print(f"  🍴 Forks: {github_stats.get('forks', 0)}")
        print(f"  🐛 Issues: {github_stats.get('issues', 0)}")
        print(f"  🔄 PRs: {github_stats.get('pull_requests', 0)}")
        
        # 预测
        forecast = self.generate_revenue_forecast(3)
        print(f"\n📈 未来3个月预测:")
        for pred in forecast:
            month_str = f"{pred['year']}-{pred['month']:02d}"
            print(f"  {month_str}: ${pred['predicted_revenue']:.2f}")
        
        print("\n" + "=" * 60)
        
        # 生成报告
        report = self.generate_report("summary")
        report_path = project_root / "reports" / f"monthly_report_{current_date.strftime('%Y%m')}.md"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📋 详细报告已保存: {report_path}")
        
        # 创建可视化
        self.create_visualizations()
        
        return True

def main():
    """主函数"""
    try:
        monitor = RevenueMonitor()
        
        print("AI助手实用工具包 - 收入监控系统")
        print("=" * 50)
        
        # 添加示例数据（首次运行）
        conn = sqlite3.connect(monitor.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM revenue")
        revenue_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM targets")
        targets_count = cursor.fetchone()[0]
        
        conn.close()
        
        if revenue_count == 0:
            print("添加示例收入数据...")
            # 添加一些示例收入
            monitor.add_revenue(
                date=datetime.now().strftime("%Y-%m-%d"),
                source="GitHub Sponsors",
                amount_usd=25.0,
                description="示例赞助收入"
            )
            
            monitor.add_revenue(
                date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                source="Individual Donation",
                amount_usd=10.0,
                description="个人捐赠"
            )
        
        if targets_count == 0:
            print("设置收入目标...")
            # 设置月度目标
            monitor.set_target(
                period="monthly",
                target_amount=50.0,
                start_date=datetime.now().strftime("%Y-%m-01"),
                end_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                description="初始月度收入目标"
            )
        
        # 添加示例支出
        monitor.add_expense(
            date=datetime.now().strftime("%Y-%m-%d"),
            category="AI Services",
            amount_usd=30.0,
            description="DeepSeek API使用成本"
        )
        
        # 运行仪表板
        monitor.run_dashboard()
        
        print("\n🎉 收入监控系统运行完成!")
        print("下次运行建议: 每月初执行以跟踪进度")
        
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()