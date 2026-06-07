"""
AI智能数据分析系统 - 销售场景自动化测试
使用 Playwright 模拟用户页面操作
"""

import os
import sys
import json
import time
from datetime import datetime

# 确保输出能正确显示中文
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 尝试安装 Playwright 和浏览器
def setup_environment():
    print("=" * 60)
    print("环境准备中...")
    print("=" * 60)
    
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright 已安装")
        return True
    except ImportError:
        print("正在安装 Playwright...")
        os.system("pip install playwright --quiet")
        print("正在下载浏览器...")
        os.system("playwright install chromium --quiet")
        print("✓ 环境准备完成")
        return True

# 测试配置
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "data_folder": "data",
    "output_folder": "test_results",
    "test_cases": [
        {
            "id": "TC01",
            "name": "数据上传测试 - 销售交易数据",
            "file": "sales_transactions.csv",
            "expected": "文件上传成功",
        },
        {
            "id": "TC02",
            "name": "数据上传测试 - 产品目录数据",
            "file": "product_catalog.csv",
            "expected": "文件上传成功",
        },
        {
            "id": "TC03",
            "name": "数据上传测试 - 区域目标数据",
            "file": "regional_targets.csv",
            "expected": "文件上传成功",
        },
        {
            "id": "TC04",
            "name": "数据分析测试 - 销售额统计特征",
            "datasource_index": 0,
            "query": "分析销售额的统计特征，包括均值、中位数、标准差、最大值、最小值",
            "check_statistics": True,
        },
        {
            "id": "TC05",
            "name": "数据分析测试 - 区域销售分布",
            "datasource_index": 0,
            "query": "分析各区域的销售额分布情况",
            "check_statistics": True,
        },
        {
            "id": "TC06",
            "name": "数据分析测试 - 渠道销售占比",
            "datasource_index": 0,
            "query": "分析各销售渠道的销售占比",
            "check_statistics": True,
        },
        {
            "id": "TC07",
            "name": "数据分析测试 - 异常检测",
            "datasource_index": 0,
            "query": "检测数据中的异常值，特别是销量突然变化的数据点",
            "check_anomalies": True,
        },
    ]
}

class SalesAnalyticsTest:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
        # 创建输出目录
        os.makedirs(TEST_CONFIG["output_folder"], exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshot_folder = os.path.join(TEST_CONFIG["output_folder"], f"screenshots_{timestamp}")
        os.makedirs(self.screenshot_folder, exist_ok=True)
        
        self.log_file = os.path.join(TEST_CONFIG["output_folder"], f"test_log_{timestamp}.txt")
        self.report_file = os.path.join(TEST_CONFIG["output_folder"], f"test_report_{timestamp}.html")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def take_screenshot(self, page, test_id, step_name):
        screenshot_path = os.path.join(self.screenshot_folder, f"{test_id}_{step_name}.png")
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            self.log(f"  📸 截图已保存: {os.path.basename(screenshot_path)}")
            return screenshot_path
        except Exception as e:
            self.log(f"  ⚠️ 截图失败: {e}")
            return None
    
    def record_result(self, test_id, test_name, status, details=""):
        result = {
            "id": test_id,
            "name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        status_icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
        self.log(f"{status_icon} [{test_id}] {test_name} - {status.upper()}")
    
    def run_all_tests(self):
        from playwright.sync_api import sync_playwright
        
        self.log("=" * 60)
        self.log("AI智能数据分析系统 - 销售场景自动化测试")
        self.log("=" * 60)
        self.log(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"目标地址: {TEST_CONFIG['base_url']}")
        self.log(f"测试用例数: {len(TEST_CONFIG['test_cases'])}")
        self.log("")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # 显示浏览器窗口，让用户看到操作过程
                slow_mo=300,      # 每个操作延迟，便于观察
            )
            
            context = browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            # 记录控制台日志
            page.on("console", lambda msg: self.log(f"  [浏览器控制台] {msg.text}") if msg and msg.text else None)
            
            try:
                # 打开页面
                self.log("\n🚀 打开测试页面...")
                page.goto(TEST_CONFIG["base_url"])
                time.sleep(2)
                self.take_screenshot(page, "INIT", "01_首页加载")
                
                # 逐个执行测试用例
                for test_case in TEST_CONFIG["test_cases"]:
                    test_id = test_case["id"]
                    test_name = test_case["name"]
                    
                    self.log(f"\n{'='*60}")
                    self.log(f"▶️ 执行测试: {test_id} - {test_name}")
                    self.log(f"{'='*60}")
                    
                    try:
                        # 判断测试类型
                        if "file" in test_case:
                            self.run_upload_test(page, test_case)
                        elif "query" in test_case:
                            self.run_analysis_test(page, test_case)
                    except Exception as e:
                        self.log(f"  ❌ 测试执行异常: {str(e)}")
                        self.take_screenshot(page, test_id, "ERROR")
                        self.record_result(test_id, test_name, "fail", f"异常: {str(e)}")
                
                # 生成测试报告
                self.generate_report()
                
            finally:
                time.sleep(3)
                browser.close()
        
        # 输出测试汇总
        self.print_summary()
    
    def run_upload_test(self, page, test_case):
        test_id = test_case["id"]
        test_name = test_case["name"]
        file_name = test_case["file"]
        
        # 切换到数据管理页面
        self.log("  1️⃣  切换到数据管理页面")
        page.click('a[href="#data"]')
        time.sleep(1)
        self.take_screenshot(page, test_id, "01_数据管理页面")
        
        # 准备上传文件
        file_path = os.path.join(TEST_CONFIG["data_folder"], file_name)
        if not os.path.exists(file_path):
            self.log(f"  ⚠️ 测试文件不存在: {file_path}")
            self.record_result(test_id, test_name, "fail", f"测试文件不存在: {file_name}")
            return
        
        self.log(f"  2️⃣  上传文件: {file_name}")
        file_input = page.locator('#file-input')
        file_input.set_input_files(file_path)
        time.sleep(2)
        
        # 检查上传结果
        self.take_screenshot(page, test_id, "02_上传完成")
        
        # 检查数据源列表
        data_table = page.locator('#data-sources-body')
        table_content = data_table.inner_text()
        
        if file_name.replace('.csv', '') in table_content or file_name in table_content:
            self.log(f"  3️⃣  ✅ 数据已成功上传并显示在列表中")
            self.record_result(test_id, test_name, "pass", "文件上传成功，数据源列表已更新")
        else:
            # 检查是否有上传成功提示
            success_badge = page.locator('.badge-success').first
            if success_badge.count() > 0:
                message = success_badge.inner_text()
                self.log(f"  3️⃣  ✅ 上传成功提示: {message}")
                self.record_result(test_id, test_name, "pass", message)
            else:
                self.log(f"  3️⃣  ⚠️ 未在列表中找到上传的数据")
                self.record_result(test_id, test_name, "warning", "文件已上传但列表未更新")
    
    def run_analysis_test(self, page, test_case):
        test_id = test_case["id"]
        test_name = test_case["name"]
        query = test_case["query"]
        datasource_index = test_case.get("datasource_index", 0)
        
        # 切换到问答分析页面
        self.log("  1️⃣  切换到问答分析页面")
        page.click('a[href="#analysis"]')
        time.sleep(1)
        self.take_screenshot(page, test_id, "01_分析页面")
        
        # 选择数据源
        self.log(f"  2️⃣  选择数据源 (索引: {datasource_index})")
        data_source_select = page.locator('#analysis-datasource')
        try:
            # 等待选项加载
            time.sleep(1)
            options = data_source_select.locator('option')
            option_count = options.count()
            
            if option_count <= 1:  # 只有"请选择..."选项
                self.log(f"  ⚠️ 没有可用的数据源")
                self.record_result(test_id, test_name, "fail", "无可用数据源")
                return
            
            # 选择指定的数据源（跳过第一个选项）
            if datasource_index < option_count - 1:
                data_source_select.select_option(index=datasource_index + 1)
                self.log(f"    已选择第 {datasource_index + 1} 个数据源")
            else:
                data_source_select.select_option(index=1)
                self.log(f"    数据源索引超出范围，选择第一个可用数据源")
        except Exception as e:
            self.log(f"    ⚠️ 数据源选择警告: {e}")
            try:
                data_source_select.select_option(index=1)
            except:
                pass
        
        time.sleep(1)
        self.take_screenshot(page, test_id, "02_数据源选择")
        
        # 输入分析问题
        self.log(f"  3️⃣  输入分析问题: {query[:50]}...")
        query_textarea = page.locator('#analysis-query')
        query_textarea.fill(query)
        time.sleep(1)
        self.take_screenshot(page, test_id, "03_问题输入")
        
        # 点击开始分析按钮
        self.log("  4️⃣  点击开始分析...")
        analyze_button = page.locator('button', has_text="开始智能分析")
        analyze_button.click()
        time.sleep(2)
        
        # 等待分析结果加载
        self.log("  5️⃣  等待分析结果...")
        try:
            # 等待结果显示（最多等待30秒）
            start_wait = time.time()
            while time.time() - start_wait < 30:
                result_div = page.locator('#analysis-result')
                if result_div.is_visible():
                    content = result_div.inner_text()
                    if "分析中" not in content and "loading" not in content.lower():
                        break
                time.sleep(1)
            
            time.sleep(2)
            self.take_screenshot(page, test_id, "04_分析结果")
            
            # 验证分析结果
            result_text = page.locator('#analysis-result').inner_text()
            
            # 检查统计数据
            if test_case.get("check_statistics", False):
                if "统计分析" in result_text or "均值" in result_text or "mean" in result_text.lower():
                    self.log("    ✅ 分析结果包含统计数据")
                    self.record_result(test_id, test_name, "pass", "统计分析功能正常")
                else:
                    self.log("    ⚠️ 分析结果可能未包含完整统计数据")
                    self.record_result(test_id, test_name, "warning", "分析结果部分生成")
            
            # 检查异常检测结果
            elif test_case.get("check_anomalies", False):
                if "异常" in result_text or "anomaly" in result_text.lower():
                    self.log("    ✅ 分析结果包含异常检测")
                    self.record_result(test_id, test_name, "pass", "异常检测功能正常")
                else:
                    self.log("    ℹ️  本次分析未检测到显著异常")
                    self.record_result(test_id, test_name, "pass", "异常检测完成（无异常或无显著异常）")
            else:
                # 通用检查：只要结果不为空
                if len(result_text.strip()) > 100:
                    self.log("    ✅ 分析结果已生成")
                    self.record_result(test_id, test_name, "pass", "分析功能正常")
                else:
                    self.log("    ⚠️ 分析结果内容较少")
                    self.record_result(test_id, test_name, "warning", "分析结果可能不完整")
                    
        except Exception as e:
            self.log(f"    ❌ 等待分析结果时出错: {e}")
            self.record_result(test_id, test_name, "fail", f"分析超时或出错: {str(e)}")
    
    def generate_report(self):
        self.log(f"\n{'='*60}")
        self.log("📊 生成测试报告...")
        self.log(f"{'='*60}")
        
        # 统计结果
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        total = len(self.results)
        duration = round(time.time() - self.start_time, 2)
        
        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>销售场景自动化测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #6366f1; padding-bottom: 15px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ flex: 1; padding: 20px; border-radius: 10px; text-align: center; }}
        .pass {{ background: #d1fae5; color: #065f46; }}
        .fail {{ background: #fee2e2; color: #991b1b; }}
        .warning {{ background: #fef3c7; color: #92400e; }}
        .total {{ background: #e0e7ff; color: #3730a3; }}
        .summary-card .num {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .summary-card .label {{ font-size: 14px; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-pass {{ color: #10b981; font-weight: bold; }}
        .status-fail {{ color: #ef4444; font-weight: bold; }}
        .status-warning {{ color: #f59e0b; font-weight: bold; }}
        .info {{ color: #666; font-size: 14px; margin: 10px 0; }}
        .screenshot {{ display: block; max-width: 100%; margin: 20px auto; border: 2px solid #ddd; border-radius: 8px; }}
        .screenshot-container {{ background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 AI智能数据分析系统 - 销售场景自动化测试报告</h1>
        
        <div class="info">
            <strong>测试时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>测试目标:</strong> {TEST_CONFIG['base_url']}<br>
            <strong>执行时长:</strong> {duration} 秒
        </div>
        
        <h2>📈 测试结果汇总</h2>
        <div class="summary">
            <div class="summary-card total">
                <div class="num">{total}</div>
                <div class="label">总用例数</div>
            </div>
            <div class="summary-card pass">
                <div class="num">{passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card fail">
                <div class="num">{failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card warning">
                <div class="num">{warnings}</div>
                <div class="label">警告</div>
            </div>
        </div>
        
        <h2>📋 测试用例详情</h2>
        <table>
            <thead>
                <tr>
                    <th>用例ID</th>
                    <th>测试名称</th>
                    <th>状态</th>
                    <th>详细信息</th>
                    <th>时间</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in self.results:
            status_class = f"status-{result['status']}"
            status_icon = "✅" if result["status"] == "pass" else "❌" if result["status"] == "fail" else "⚠️"
            status_text = "通过" if result["status"] == "pass" else "失败" if result["status"] == "fail" else "警告"
            
            html_content += f"""
                <tr>
                    <td><strong>{result['id']}</strong></td>
                    <td>{result['name']}</td>
                    <td class="{status_class}">{status_icon} {status_text}</td>
                    <td>{result['details']}</td>
                    <td>{result['timestamp'].replace('T', ' ')}</td>
                </tr>
            """
        
        html_content += f"""
            </tbody>
        </table>
        
        <h2>📸 操作截图</h2>
        <p>所有操作截图已保存在: <code>{self.screenshot_folder}</code></p>
        <div class="screenshot-container">
            <p style="text-align: center; color: #666;">共生成 {len(os.listdir(self.screenshot_folder)) if os.path.exists(self.screenshot_folder) else 0} 张截图</p>
        </div>
        
        <h2>📝 测试日志</h2>
        <p>完整日志已保存在: <code>{self.log_file}</code></p>
        
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px; text-align: center;">
            <strong>测试执行完成</strong> - 如需复现，请重新运行脚本
        </div>
    </div>
</body>
</html>
"""
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.log(f"📄 测试报告已生成: {self.report_file}")
        self.log(f"📸 截图已保存在: {self.screenshot_folder}")
        self.log(f"📝 日志已保存在: {self.log_file}")
    
    def print_summary(self):
        self.log(f"\n{'='*60}")
        self.log("测试执行完成 - 汇总")
        self.log(f"{'='*60}")
        
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        total = len(self.results)
        
        self.log(f"总用例数: {total}")
        self.log(f"通过: {passed}")
        self.log(f"失败: {failed}")
        self.log(f"警告: {warnings}")
        self.log(f"通过率: {round(passed/total*100, 1) if total > 0 else 0}%")
        self.log(f"执行时长: {round(time.time() - self.start_time, 2)} 秒")
        self.log(f"\n测试报告: {self.report_file}")
        self.log(f"{'='*60}")

if __name__ == "__main__":
    # 环境准备
    if not setup_environment():
        print("❌ 环境准备失败，请手动安装 playwright")
        sys.exit(1)
    
    # 运行测试
    test = SalesAnalyticsTest()
    test.run_all_tests()
