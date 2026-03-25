#!/usr/bin/env python3
"""
AI助手实用工具包 - 命令行界面
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from toolkit.calculators.cost_calculator import AICostCalculator
    from toolkit.automation.file_organizer import FileOrganizer
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装依赖: pip install -r requirements.txt")
    sys.exit(1)


def cost_calculator():
    """AI成本计算器命令行接口"""
    parser = argparse.ArgumentParser(description="AI服务成本计算器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # estimate命令
    estimate_parser = subparsers.add_parser("estimate", help="估算单个请求成本")
    estimate_parser.add_argument("--model", required=True, help="模型名称 (deepseek-v3, gpt-4o, claude-3.5-sonnet, qwen-max)")
    estimate_parser.add_argument("--input", type=int, required=True, help="输入token数量")
    estimate_parser.add_argument("--output", type=int, required=True, help="输出token数量")
    estimate_parser.add_argument("--currency", default="CNY", help="输出货币 (USD, CNY, EUR, JPY)")
    estimate_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    # compare命令
    compare_parser = subparsers.add_parser("compare", help="比较不同模型成本")
    compare_parser.add_argument("--input", type=int, required=True, help="输入token数量")
    compare_parser.add_argument("--output", type=int, required=True, help="输出token数量")
    compare_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    # batch命令
    batch_parser = subparsers.add_parser("batch", help="批量估算成本")
    batch_parser.add_argument("--file", help="包含请求列表的JSON文件")
    batch_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    args = parser.parse_args(sys.argv[2:] if len(sys.argv) > 2 else ["--help"])
    
    calculator = AICostCalculator()
    
    if args.command == "estimate":
        result = calculator.estimate(args.model, args.input, args.output, args.currency)
        
        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.format == "markdown":
            print(f"# AI成本估算\n")
            print(f"**模型**: {result['model']} ({result['provider']})\n")
            print(f"**输入token**: {result['input_tokens']:,}")
            print(f"**输出token**: {result['output_tokens']:,}")
            print(f"**总token**: {result['total_tokens']:,}\n")
            print(f"**成本**: ${result['cost_usd']:.6f}")
            if args.currency != "USD" and args.currency in result['cost_local']:
                print(f"**{args.currency}**: {result['cost_local'][args.currency]:.4f}")
        else:
            print("=" * 50)
            print(f"AI成本估算结果")
            print("=" * 50)
            print(f"模型: {result['model']} ({result['provider']})")
            print(f"输入token: {result['input_tokens']:,}")
            print(f"输出token: {result['output_tokens']:,}")
            print(f"总token: {result['total_tokens']:,}")
            print(f"成本: ${result['cost_usd']:.6f}")
            if args.currency != "USD" and args.currency in result['cost_local']:
                print(f"{args.currency}: {result['cost_local'][args.currency]:.4f}")
    
    elif args.command == "compare":
        comparison = calculator.compare_models(args.input, args.output)
        
        if args.format == "json":
            print(json.dumps(comparison, indent=2, ensure_ascii=False))
        elif args.format == "markdown":
            print(f"# 模型成本对比\n")
            print(f"输入token: {args.input:,}")
            print(f"输出token: {args.output:,}\n")
            print("| 模型 | 供应商 | 成本(USD) | 每token成本 |")
            print("|------|--------|-----------|-------------|")
            for model_id, info in comparison.items():
                cost_per_token = info['cost_per_token'] * 1000000  # 转换为每百万token
                print(f"| {model_id} | {info['provider']} | ${info['cost_usd']:.6f} | ${cost_per_token:.4f}/M |")
        else:
            print("=" * 60)
            print(f"模型成本对比 (输入: {args.input:,}, 输出: {args.output:,})")
            print("=" * 60)
            for model_id, info in comparison.items():
                cost_per_token = info['cost_per_token'] * 1000000  # 转换为每百万token
                print(f"{model_id} ({info['provider']}):")
                print(f"  成本: ${info['cost_usd']:.6f}")
                print(f"  每百万token: ${cost_per_token:.4f}")
                print()
    
    elif args.command == "batch":
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
            except Exception as e:
                print(f"读取文件失败: {e}")
                return
        else:
            # 示例数据
            requests = [
                ["deepseek-v3", 10000, 500],
                ["gpt-4o", 8000, 1000],
                ["claude-3.5-sonnet", 12000, 1500]
            ]
        
        results = calculator.batch_estimate(requests)
        report = calculator.generate_report(results, args.format)
        print(report)


def file_organizer():
    """文件整理助手命令行接口"""
    parser = argparse.ArgumentParser(description="文件整理助手")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # scan命令
    scan_parser = subparsers.add_parser("scan", help="扫描目录")
    scan_parser.add_argument("--path", default=".", help="要扫描的目录路径")
    scan_parser.add_argument("--recursive", action="store_true", help="递归扫描子目录")
    scan_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    # organize命令
    organize_parser = subparsers.add_parser("organize", help="整理文件")
    organize_parser.add_argument("--path", default=".", help="要整理的目录路径")
    organize_parser.add_argument("--by", default="category", choices=["category", "date"], help="整理方式")
    organize_parser.add_argument("--dry-run", action="store_true", help="模拟运行（不实际移动文件）")
    organize_parser.add_argument("--remove-duplicates", action="store_true", help="删除重复文件")
    organize_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    # symlink命令
    symlink_parser = subparsers.add_parser("symlink", help="创建符号链接")
    symlink_parser.add_argument("--path", default=".", help="目录路径")
    symlink_parser.add_argument("--category", help="特定类别（默认所有类别）")
    symlink_parser.add_argument("--dry-run", action="store_true", help="模拟运行")
    symlink_parser.add_argument("--format", default="text", choices=["text", "json", "markdown"], help="输出格式")
    
    args = parser.parse_args(sys.argv[2:] if len(sys.argv) > 2 else ["--help"])
    
    if args.command == "scan":
        organizer = FileOrganizer(args.path)
        result = organizer.scan_directory(recursive=args.recursive)
        
        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            report = organizer.generate_report(result, output_format=args.format)
            print(report)
    
    elif args.command == "organize":
        organizer = FileOrganizer(args.path)
        
        if args.by == "category":
            result = organizer.organize_by_category(
                dry_run=args.dry_run,
                remove_duplicates=args.remove_duplicates
            )
        else:  # date
            result = organizer.organize_by_date(dry_run=args.dry_run)
        
        scan_result = organizer.scan_directory()
        report = organizer.generate_report(scan_result, result, args.format)
        print(report)
        
        if args.dry_run:
            print("\n⚠️  注意：这是模拟运行。要实际执行，请移除 --dry-run 参数。")
    
    elif args.command == "symlink":
        organizer = FileOrganizer(args.path)
        result = organizer.create_symlinks(
            category=args.category,
            dry_run=args.dry_run
        )
        
        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.format == "markdown":
            print(f"# 符号链接创建报告\n")
            print(f"目录: {args.path}")
            print(f"类别: {args.category or '全部'}")
            print(f"模拟运行: {'是' if args.dry_run else '否'}\n")
            print(f"已创建符号链接: {result['symlinks_created']}")
            
            if result['errors']:
                print(f"\n## 错误信息\n")
                for error in result['errors']:
                    print(f"- {error}")
        else:
            print("=" * 50)
            print("符号链接创建报告")
            print("=" * 50)
            print(f"目录: {args.path}")
            print(f"类别: {args.category or '全部'}")
            print(f"模拟运行: {'是' if args.dry_run else '否'}")
            print(f"已创建符号链接: {result['symlinks_created']}")
            
            if result['errors']:
                print(f"\n错误信息:")
                for error in result['errors']:
                    print(f"  - {error}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI助手实用工具包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ai-cost estimate --model deepseek-v3 --input 10000 --output 500
  ai-cost compare --input 10000 --output 1000
  ai-organize scan --path ./downloads
  ai-organize organize --path ./downloads --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest="tool", help="可用工具", required=True)
    
    # cost工具
    cost_parser = subparsers.add_parser("cost", help="AI成本计算器")
    cost_parser.set_defaults(func=cost_calculator)
    
    # organize工具
    organize_parser = subparsers.add_parser("organize", help="文件整理助手")
    organize_parser.set_defaults(func=file_organizer)
    
    args = parser.parse_args()
    
    try:
        args.func()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()