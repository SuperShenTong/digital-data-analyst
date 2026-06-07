"""
根据业务需求补充测试数据
业务场景：工单、销售、运维、项目

当前已生成：销售数据
待补充：工单数据、运维数据、项目数据

按业务场景组织文件夹结构
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# 创建目录结构
def create_directory_structure():
    """创建业务场景目录结构"""
    dirs = [
        "data/sales",          # 销售数据
        "data/workorder",      # 工单数据
        "data/operations",     # 运维数据
        "data/project",        # 项目数据
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print("创建目录: {}".format(dir_path))

def generate_workorder_data():
    """生成工单数据"""
    print("\n生成工单数据...")
    
    records = []
    departments = ["客服部", "技术部", "运维部", "财务部", "人力资源", "市场部"]
    priorities = ["紧急", "高", "中", "低"]
    statuses = ["待处理", "处理中", "已解决", "已关闭", "待回访"]
    issue_types = [
        "系统故障", "功能异常", "性能问题", "数据错误", "权限问题",
        "咨询", "建议", "投诉", "需求变更", "其他"
    ]
    
    for i in range(1000):
        created_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        
        # 处理时间（随机延迟）
        hours_delay = random.randint(0, 72)
        resolved_date = created_date + timedelta(hours=hours_delay) if random.random() > 0.3 else None
        
        # 处理时长（分钟）
        duration = hours_delay * 60 if resolved_date else None
        
        records.append({
            "ticket_id": f"TKT{202401010000 + i}",
            "created_at": created_date.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_date.strftime("%Y-%m-%d %H:%M:%S") if resolved_date else None,
            "department": random.choice(departments),
            "priority": random.choice(priorities),
            "status": random.choice(statuses),
            "issue_type": random.choice(issue_types),
            "reporter": f"user_{random.randint(1001, 1100)}",
            "assignee": f"agent_{random.randint(2001, 2020)}",
            "title": f"工单标题{i+1}",
            "description": f"这是工单{i+1}的详细描述内容",
            "duration_minutes": duration,
            "satisfaction_score": random.randint(1, 5) if random.random() > 0.4 else None,
        })
    
    df = pd.DataFrame(records)
    df.to_csv("data/workorder/workorders.csv", index=False, encoding="utf-8-sig")
    print("  工单数据: 1000条")
    
    # 工单分类维度表
    categories = []
    for i, issue_type in enumerate(issue_types):
        categories.append({
            "category_id": f"CAT{i+1:03d}",
            "category_name": issue_type,
            "category_group": "技术问题" if issue_type in ["系统故障", "功能异常", "性能问题", "数据错误", "权限问题"] else "业务问题",
            "average_resolution_hours": random.randint(2, 48),
            "escalation_threshold_hours": random.randint(4, 24),
        })
    
    cat_df = pd.DataFrame(categories)
    cat_df.to_csv("data/workorder/issue_categories.csv", index=False, encoding="utf-8-sig")
    print("  工单分类维度表: {}条".format(len(cat_df)))

def generate_operations_data():
    """生成运维数据"""
    print("\n生成运维数据...")
    
    # 服务器性能日志（模拟连续时间序列）
    servers = [f"server_{chr(ord('A')+i)}" for i in range(10)]
    metrics = ["cpu_usage", "memory_usage", "disk_usage", "network_io", "response_time"]
    
    perf_records = []
    base_date = datetime(2024, 1, 1)
    
    for day in range(30):
        for hour in range(24):
            for server in servers:
                timestamp = base_date + timedelta(days=day, hours=hour)
                
                # 添加异常点（CPU飙升等）
                is_anomaly = False
                if (day == 15 and hour == 10) or (day == 20 and hour == 14):
                    is_anomaly = True
                
                for metric in metrics:
                    base_value = random.uniform(20, 80)
                    if is_anomaly:
                        if metric == "cpu_usage":
                            value = random.uniform(90, 99)
                        elif metric == "response_time":
                            value = random.uniform(500, 2000)
                        else:
                            value = base_value
                    else:
                        value = base_value
                    
                    perf_records.append({
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "server": server,
                        "metric": metric,
                        "value": round(value, 2),
                        "unit": "%" if metric.endswith("_usage") else "ms" if metric == "response_time" else "MB/s",
                        "is_anomaly": "是" if is_anomaly and (metric == "cpu_usage" or metric == "response_time") else "否"
                    })
    
    perf_df = pd.DataFrame(perf_records)
    perf_df.to_csv("data/operations/server_performance.csv", index=False, encoding="utf-8-sig")
    print("  服务器性能日志: {}条".format(len(perf_df)))
    
    # 告警事件
    alarm_records = []
    alarm_types = ["CPU过高", "内存不足", "磁盘告警", "网络异常", "服务宕机", "响应超时"]
    
    for i in range(200):
        created_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
        duration = random.randint(5, 180)
        alarm_records.append({
            "alarm_id": f"ALM{20240101000 + i}",
            "server": random.choice(servers),
            "alarm_type": random.choice(alarm_types),
            "severity": random.choice(["严重", "警告", "提示"]),
            "threshold": random.uniform(80, 95),
            "actual_value": random.uniform(85, 100),
            "created_at": created_date.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": (created_date + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S") if random.random() > 0.1 else None,
            "duration_minutes": duration,
            "status": random.choice(["已恢复", "处理中", "待确认"]),
            "handled_by": f"admin_{random.randint(3001, 3010)}",
        })
    
    alarm_df = pd.DataFrame(alarm_records)
    alarm_df.to_csv("data/operations/alarm_events.csv", index=False, encoding="utf-8-sig")
    print("  告警事件: {}条".format(len(alarm_df)))

def generate_project_data():
    """生成项目数据"""
    print("\n生成项目数据...")
    
    # 项目主表
    projects = []
    project_statuses = ["规划中", "进行中", "已完成", "暂停", "取消"]
    project_types = ["研发项目", "运维项目", "市场项目", "内部项目", "客户项目"]
    
    for i in range(50):
        start_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 300))
        duration_days = random.randint(30, 365)
        end_date = start_date + timedelta(days=duration_days)
        
        projects.append({
            "project_id": f"PRJ{i+1:04d}",
            "project_name": f"项目{i+1}: {random.choice(['电商平台升级', '数据中台建设', 'CRM系统改造', '移动App开发', '智能客服系统', '供应链优化'])}",
            "project_type": random.choice(project_types),
            "status": random.choice(project_statuses),
            "priority": random.choice(["高", "中", "低"]),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "budget": random.randint(50000, 2000000),
            "actual_cost": random.randint(0, 2000000),
            "manager": f"manager_{random.randint(4001, 4015)}",
            "team_members": random.randint(3, 20),
            "progress": random.randint(0, 100),
            "description": f"项目{i+1}的详细描述",
        })
    
    project_df = pd.DataFrame(projects)
    project_df.to_csv("data/project/projects.csv", index=False, encoding="utf-8-sig")
    print("  项目主表: {}条".format(len(project_df)))
    
    # 项目任务表
    tasks = []
    task_statuses = ["待开始", "进行中", "已完成", "阻塞", "取消"]
    
    for project_id in [f"PRJ{i+1:04d}" for i in range(50)]:
        num_tasks = random.randint(5, 30)
        for j in range(num_tasks):
            tasks.append({
                "task_id": f"TASK{project_id[3:]}{j+1:03d}",
                "project_id": project_id,
                "task_name": f"任务{j+1}: {random.choice(['需求分析', '设计评审', '开发实现', '测试验证', '部署上线', '文档编写'])}",
                "status": random.choice(task_statuses),
                "priority": random.choice(["高", "中", "低"]),
                "assignee": f"dev_{random.randint(5001, 5050)}",
                "start_date": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "due_date": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "progress": random.randint(0, 100),
                "estimated_hours": random.randint(8, 160),
                "actual_hours": random.randint(0, 160),
            })
    
    task_df = pd.DataFrame(tasks)
    task_df.to_csv("data/project/tasks.csv", index=False, encoding="utf-8-sig")
    print("  项目任务表: {}条".format(len(task_df)))

def reorganize_existing_data():
    """整理已有的销售数据到对应目录"""
    print("\n整理已有的销售数据...")
    
    files_to_move = [
        ("data/product_catalog.csv", "data/sales/product_catalog.csv"),
        ("data/sales_transactions.csv", "data/sales/sales_transactions.csv"),
        ("data/regional_targets.csv", "data/sales/regional_targets.csv"),
    ]
    
    for src, dst in files_to_move:
        if os.path.exists(src):
            os.replace(src, dst)
            print("  移动: {} -> {}".format(src, dst))

def print_summary():
    """打印数据汇总"""
    print("\n" + "=" * 60)
    print("测试数据生成完成")
    print("=" * 60)
    
    print("\n【目录结构】")
    for root, dirs, files in os.walk("data"):
        level = root.replace("data", "").count(os.sep)
        indent = "  " * level
        print("{}{}/".format(indent, os.path.basename(root)))
        subindent = "  " * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            df = pd.read_csv(file_path)
            print("{}{}: {}条记录".format(subindent, file, len(df)))

def main():
    print("=" * 60)
    print("AI智能数据分析系统 - 测试数据生成")
    print("=" * 60)
    
    # 创建目录结构
    create_directory_structure()
    
    # 生成工单数据
    generate_workorder_data()
    
    # 生成运维数据
    generate_operations_data()
    
    # 生成项目数据
    generate_project_data()
    
    # 整理已有的销售数据
    reorganize_existing_data()
    
    # 打印汇总
    print_summary()
    
    print("\n所有测试数据已生成完毕！")

if __name__ == "__main__":
    main()
