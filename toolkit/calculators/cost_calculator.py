"""
AI服务成本计算器
估算各种AI模型的使用成本
"""

import json
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

@dataclass
class AIModelPricing:
    """AI模型定价信息"""
    name: str
    provider: str
    input_price_per_1k: float  # 每1000个输入token的价格（美元）
    output_price_per_1k: float  # 每1000个输出token的价格（美元）
    context_window: int  # 上下文窗口大小
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算给定token数量的成本"""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost


class AICostCalculator:
    """AI成本计算器主类"""
    
    def __init__(self):
        self.models = self._load_model_pricing()
    
    def _load_model_pricing(self) -> Dict[str, AIModelPricing]:
        """加载模型定价数据"""
        # 实际数据会从配置文件或API获取，这里使用硬编码示例
        return {
            "deepseek-v3": AIModelPricing(
                name="DeepSeek V3",
                provider="DeepSeek",
                input_price_per_1k=0.00014,  # 示例价格
                output_price_per_1k=0.00028,
                context_window=128000
            ),
            "gpt-4o": AIModelPricing(
                name="GPT-4o",
                provider="OpenAI",
                input_price_per_1k=0.005,
                output_price_per_1k=0.015,
                context_window=128000
            ),
            "claude-3.5-sonnet": AIModelPricing(
                name="Claude 3.5 Sonnet",
                provider="Anthropic",
                input_price_per_1k=0.003,
                output_price_per_1k=0.015,
                context_window=200000
            ),
            "qwen-max": AIModelPricing(
                name="Qwen Max",
                provider="Alibaba",
                input_price_per_1k=0.0008,
                output_price_per_1k=0.0024,
                context_window=32000
            )
        }
    
    def estimate(self, 
                model: str, 
                input_tokens: int, 
                output_tokens: int,
                currency: str = "USD") -> Dict:
        """
        估算AI服务成本
        
        Args:
            model: 模型标识符
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            currency: 货币类型（目前仅支持USD）
            
        Returns:
            包含成本详情的字典
        """
        if model not in self.models:
            available = list(self.models.keys())
            raise ValueError(f"模型 '{model}' 不存在。可用模型: {available}")
        
        model_info = self.models[model]
        cost_usd = model_info.calculate_cost(input_tokens, output_tokens)
        
        # 转换为其他货币（简化版）
        exchange_rates = {
            "USD": 1.0,
            "CNY": 7.2,  # 简化汇率
            "EUR": 0.92,
            "JPY": 150.0
        }
        
        result = {
            "model": model_info.name,
            "provider": model_info.provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "cost_local": {},
            "calculation_time": datetime.now().isoformat(),
            "details": {
                "input_cost_usd": (input_tokens / 1000) * model_info.input_price_per_1k,
                "output_cost_usd": (output_tokens / 1000) * model_info.output_price_per_1k,
                "input_rate": model_info.input_price_per_1k,
                "output_rate": model_info.output_price_per_1k
            }
        }
        
        # 添加本地货币成本
        for curr, rate in exchange_rates.items():
            if curr != "USD":
                result["cost_local"][curr] = cost_usd * rate
        
        return result
    
    def compare_models(self, 
                      input_tokens: int, 
                      output_tokens: int) -> Dict:
        """
        比较不同模型的成本
        
        Args:
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            
        Returns:
            各模型成本对比
        """
        comparison = {}
        for model_id, model_info in self.models.items():
            cost = model_info.calculate_cost(input_tokens, output_tokens)
            comparison[model_id] = {
                "name": model_info.name,
                "provider": model_info.provider,
                "cost_usd": cost,
                "cost_per_token": cost / (input_tokens + output_tokens) if (input_tokens + output_tokens) > 0 else 0
            }
        
        # 按成本排序
        sorted_comparison = dict(sorted(
            comparison.items(), 
            key=lambda x: x[1]["cost_usd"]
        ))
        
        return sorted_comparison
    
    def batch_estimate(self, 
                      requests: list) -> list:
        """
        批量估算多个请求的成本
        
        Args:
            requests: 请求列表，每个元素为(model, input_tokens, output_tokens)
            
        Returns:
            成本估算结果列表
        """
        results = []
        for req in requests:
            if len(req) != 3:
                continue
            model, input_tokens, output_tokens = req
            try:
                estimate = self.estimate(model, input_tokens, output_tokens)
                results.append(estimate)
            except ValueError as e:
                results.append({
                    "error": str(e),
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                })
        
        return results
    
    def generate_report(self, 
                       estimates: list, 
                       output_format: str = "text") -> str:
        """
        生成成本报告
        
        Args:
            estimates: 成本估算结果列表
            output_format: 输出格式 (text, json, markdown)
            
        Returns:
            格式化报告
        """
        if not estimates:
            return "无估算数据"
        
        total_cost = sum(e.get("cost_usd", 0) for e in estimates if isinstance(e, dict))
        total_tokens = sum(e.get("total_tokens", 0) for e in estimates if isinstance(e, dict))
        
        if output_format == "json":
            return json.dumps({
                "summary": {
                    "total_requests": len(estimates),
                    "total_tokens": total_tokens,
                    "total_cost_usd": total_cost,
                    "average_cost_per_request": total_cost / len(estimates) if estimates else 0
                },
                "details": estimates
            }, indent=2, ensure_ascii=False)
        
        elif output_format == "markdown":
            report = f"# AI成本分析报告\n\n"
            report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report += f"## 摘要\n"
            report += f"- 总请求数: {len(estimates)}\n"
            report += f"- 总token数: {total_tokens:,}\n"
            report += f"- 总成本: ${total_cost:.6f}\n"
            report += f"- 平均每请求成本: ${total_cost/len(estimates):.6f}\n\n"
            
            report += f"## 详细分析\n"
            for i, est in enumerate(estimates, 1):
                if isinstance(est, dict) and "error" not in est:
                    report += f"### 请求 #{i}\n"
                    report += f"- 模型: {est.get('model', '未知')}\n"
                    report += f"- 输入token: {est.get('input_tokens', 0):,}\n"
                    report += f"- 输出token: {est.get('output_tokens', 0):,}\n"
                    report += f"- 总成本: ${est.get('cost_usd', 0):.6f}\n\n"
            
            return report
        
        else:  # text格式
            report = "=" * 50 + "\n"
            report += "AI成本分析报告\n"
            report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += "=" * 50 + "\n\n"
            report += f"摘要:\n"
            report += f"  总请求数: {len(estimates)}\n"
            report += f"  总token数: {total_tokens:,}\n"
            report += f"  总成本: ${total_cost:.6f}\n"
            report += f"  平均每请求成本: ${total_cost/len(estimates):.6f}\n\n"
            
            for i, est in enumerate(estimates, 1):
                if isinstance(est, dict) and "error" not in est:
                    report += f"请求 #{i}:\n"
                    report += f"  模型: {est.get('model', '未知')}\n"
                    report += f"  输入token: {est.get('input_tokens', 0):,}\n"
                    report += f"  输出token: {est.get('output_tokens', 0):,}\n"
                    report += f"  总成本: ${est.get('cost_usd', 0):.6f}\n\n"
            
            return report


# 示例使用
if __name__ == "__main__":
    calculator = AICostCalculator()
    
    # 单个估算
    print("单个请求成本估算:")
    result = calculator.estimate("deepseek-v3", 10000, 500)
    print(f"成本: ${result['cost_usd']:.6f}")
    print(f"人民币: ¥{result['cost_local'].get('CNY', 0):.4f}")
    
    # 模型对比
    print("\n模型成本对比 (输入10k, 输出1k):")
    comparison = calculator.compare_models(10000, 1000)
    for model, info in comparison.items():
        print(f"{model}: ${info['cost_usd']:.6f}")
    
    # 批量估算
    print("\n批量估算:")
    requests = [
        ("deepseek-v3", 5000, 200),
        ("gpt-4o", 3000, 500),
        ("claude-3.5-sonnet", 8000, 1000)
    ]
    batch_results = calculator.batch_estimate(requests)
    print(f"批量估算完成，共 {len(batch_results)} 个结果")
    
    # 生成报告
    report = calculator.generate_report(batch_results, "text")
    print(f"\n报告预览（前500字符）:\n{report[:500]}...")