# 快速开始指南

欢迎使用AI助手实用工具包！这个指南将帮助你快速上手。

## 🚀 安装

### 方法1: 从源码安装（推荐）
```bash
# 克隆仓库
git clone https://github.com/ai-assistant/ai-assistant-toolkit.git
cd ai-assistant-toolkit

# 安装开发版本
pip install -e .
```

### 方法2: 从PyPI安装（即将推出）
```bash
pip install ai-assistant-toolkit
```

## 📋 系统要求

- Python 3.7 或更高版本
- 任何支持Python的操作系统（Windows, macOS, Linux）
- 至少100MB可用磁盘空间

## 🔧 基本使用

### 使用命令行工具

#### AI成本计算器
```bash
# 计算单个请求成本
ai-cost-calc --model deepseek-v3 --input 10000 --output 500

# 比较不同模型
ai-cost-calc --compare --input 5000 --output 1000

# 批量计算
ai-cost-calc --batch '[[\"deepseek-v3\", 5000, 200], [\"gpt-4o\", 3000, 500]]'

# 生成Markdown报告
ai-cost-calc --model deepseek-v3 --input 15000 --output 800 --format markdown --output-file report.md
```

#### 文件整理助手
```bash
# 扫描目录
file-organizer --scan --path /path/to/directory

# 整理文件（试运行）
file-organizer --organize --path /path/to/directory --dry-run

# 整理文件（实际执行）
file-organizer --organize --path /path/to/directory --move --target /path/to/organized

# 查找重复文件
file-organizer --find-duplicates --path /path/to/directory --by-name --by-hash

# 清理空文件夹
file-organizer --cleanup --path /path/to/directory
```

### 使用Python API

#### AI成本计算器
```python
from toolkit.calculators.cost_calculator import AICostCalculator

# 创建计算器
calculator = AICostCalculator()

# 单个估算
result = calculator.estimate("deepseek-v3", 10000, 500)
print(f"成本: ${result['cost_usd']:.6f}")
print(f"人民币: ¥{result['cost_local'].get('CNY', 0):.4f}")

# 模型对比
comparison = calculator.compare_models(20000, 2000)
for model_id, info in comparison.items():
    print(f"{model_id}: ${info['cost_usd']:.6f}")

# 批量估算
requests = [
    ("deepseek-v3", 5000, 300),
    ("gpt-4o", 3000, 500)
]
results = calculator.batch_estimate(requests)

# 生成报告
report = calculator.generate_report(results, "markdown")
print(report)
```

#### 文件整理助手
```python
from toolkit.automation.file_organizer import FileOrganizer

# 创建整理器
organizer = FileOrganizer("/path/to/directory")

# 扫描目录
categorized = organizer.scan_directory()
for category, files in categorized.items():
    if files:
        print(f"{category}: {len(files)} 个文件")

# 整理文件
results = organizer.organize_files(
    target_base="/path/to/organized",
    move_files=True,
    create_date_folders=True,
    dry_run=False  # 设置为True进行试运行
)

# 查找重复文件
duplicates = organizer.find_duplicates(by_name=True, by_hash=True)

# 清理空文件夹
deleted = organizer.cleanup_empty_folders()
```

## 🎯 实用示例

### 示例1: 监控AI项目成本
```python
from toolkit.calculators.cost_calculator import AICostCalculator
import json
from datetime import datetime

def track_project_costs(project_name, daily_usage):
    """跟踪项目AI使用成本"""
    calculator = AICostCalculator()
    
    monthly_report = {
        "project": project_name,
        "month": datetime.now().strftime("%Y-%m"),
        "daily_costs": []
    }
    
    total_cost = 0
    for date, usage in daily_usage.items():
        daily_cost = 0
        for request in usage:
            result = calculator.estimate(request["model"], request["input"], request["output"])
            daily_cost += result["cost_usd"]
        
        monthly_report["daily_costs"].append({
            "date": date,
            "cost_usd": daily_cost,
            "requests": len(usage)
        })
        total_cost += daily_cost
    
    monthly_report["total_cost"] = total_cost
    
    # 保存报告
    with open(f"{project_name}_cost_report_{datetime.now().strftime('%Y%m')}.json", "w") as f:
        json.dump(monthly_report, f, indent=2)
    
    return monthly_report
```

### 示例2: 自动化文件整理工作流
```python
from toolkit.automation.file_organizer import FileOrganizer
import schedule
import time
from datetime import datetime

def auto_organize_downloads():
    """自动整理下载文件夹"""
    downloads_path = "/Users/username/Downloads"
    organized_path = "/Users/username/Documents/Organized"
    
    organizer = FileOrganizer(downloads_path)
    
    # 扫描并整理
    results = organizer.organize_files(
        target_base=organized_path,
        move_files=True,
        create_date_folders=True
    )
    
    # 生成报告
    report = organizer.generate_report(results, "text")
    
    # 保存日志
    with open("auto_organize_log.txt", "a") as f:
        f.write(f"[{datetime.now()}] 整理完成\n")
        f.write(f"处理文件: {results['total_files']}\n")
        f.write(f"错误数: {len(results['errors'])}\n\n")
    
    return results

# 每天凌晨2点自动整理
schedule.every().day.at("02:00").do(auto_organize_downloads)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 示例3: 成本优化建议
```python
from toolkit.calculators.cost_calculator import AICostCalculator

def get_cost_optimization_suggestions(monthly_usage, budget):
    """获取成本优化建议"""
    calculator = AICostCalculator()
    
    suggestions = []
    
    # 分析使用模式
    total_cost = 0
    model_usage = {}
    
    for usage in monthly_usage:
        model = usage["model"]
        input_tokens = usage["input"]
        output_tokens = usage["output"]
        
        cost = calculator.models[model].calculate_cost(input_tokens, output_tokens)
        total_cost += cost
        
        if model not in model_usage:
            model_usage[model] = {"cost": 0, "tokens": 0}
        model_usage[model]["cost"] += cost
        model_usage[model]["tokens"] += input_tokens + output_tokens
    
    # 预算检查
    if total_cost > budget:
        overspend = total_cost - budget
        suggestions.append(f"⚠️ 超出预算 ${overspend:.2f} (${total_cost:.2f} / ${budget:.2f})")
    
    # 模型优化建议
    for model, data in model_usage.items():
        model_info = calculator.models[model]
        alternative_costs = []
        
        for alt_model in calculator.models:
            if alt_model != model:
                alt_cost = calculator.models[alt_model].calculate_cost(
                    data["tokens"] * 0.5,  # 假设输入输出比例
                    data["tokens"] * 0.5
                )
                alternative_costs.append((alt_model, alt_cost))
        
        alternative_costs.sort(key=lambda x: x[1])
        
        if alternative_costs and alternative_costs[0][1] < data["cost"] * 0.8:
            savings = data["cost"] - alternative_costs[0][1]
            suggestions.append(
                f"💡 考虑将 {model} 的部分任务切换到 {alternative_costs[0][0]}，"
                f"预计节省 ${savings:.2f}"
            )
    
    return suggestions
```

## 🆘 故障排除

### 常见问题

**Q: 安装时出现权限错误**
```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
pip install -e .
```

**Q: 命令行工具无法找到**
```bash
# 确保在正确环境中
which ai-cost-calc  # 检查路径

# 重新安装
pip uninstall ai-assistant-toolkit
pip install -e .
```

**Q: 文件操作权限错误**
```python
# 检查目录权限
import os
print(os.access("/path/to/directory", os.R_OK | os.W_OK))

# 使用管理员权限或更改目录所有者
```

### 获取帮助

1. **查看帮助文档**
   ```bash
   ai-cost-calc --help
   file-organizer --help
   ```

2. **查看示例代码**
   ```bash
   cd examples
   python basic_usage.py
   ```

3. **报告问题**
   - GitHub Issues: https://github.com/ai-assistant/ai-assistant-toolkit/issues
   - 使用Issue模板详细描述问题

## 📚 下一步

- 查看 [API文档](API.md) 了解所有可用功能
- 阅读 [贡献指南](CONTRIBUTING.md) 参与开发
- 查看 [赞助信息](SPONSOR.md) 支持项目发展
- 加入社区讨论和分享使用经验