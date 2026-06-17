"""
一键生成所有mock数据

依次执行:
1. generate_products.py - 生成商品数据
2. generate_reviews.py - 生成评价数据
3. generate_monthly_sales.py - 生成销量数据
"""

import subprocess
import sys
import os

def run_script(script_name: str):
    """执行指定的Python脚本"""
    print(f"\n{'='*60}")
    print(f"  正在执行: {script_name}")
    print('='*60)

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 执行脚本
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, script_name)],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    # 打印输出
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"标准错误:\n{result.stderr}", file=sys.stderr)

    if result.returncode != 0:
        print(f"脚本 {script_name} 执行失败，返回码: {result.returncode}")
        return False

    print(f"脚本 {script_name} 执行成功")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("  电商数据洞察平台 - Mock 数据批量生成工具")
    print("=" * 60)

    scripts = [
        'generate_products.py',
        'generate_reviews.py',
        'generate_monthly_sales.py',
    ]

    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"  数据生成完成！成功 {success_count}/{len(scripts)} 个脚本")
    print("=" * 60)

    return 0 if success_count == len(scripts) else 1


if __name__ == "__main__":
    sys.exit(main())
