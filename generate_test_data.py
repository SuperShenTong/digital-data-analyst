"""
生成销售分析测试数据
- 产品维度表：product_catalog.csv (500条)
- 核心交易表：sales_transactions.csv (10,000条)
- 区域目标表：regional_targets.csv (50条)
支持多表关联分析、毛利分析、分类下钻分析、目标达成分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# 设置随机种子确保可复现
np.random.seed(42)
random.seed(42)

# ============ 产品数据配置 ============

# 产品分类体系
CATEGORIES = {
    "电子产品": {
        "音频设备": ["耳机", "音箱", "麦克风", "声卡", "播放器"],
        "手机通讯": ["智能手机", "老人机", "对讲机", "手机配件"],
        "电脑办公": ["笔记本电脑", "台式机", "平板电脑", "键盘鼠标", "显示器", "打印机"],
        "智能穿戴": ["智能手表", "手环", "AR眼镜", "智能戒指"],
        "存储设备": ["移动硬盘", "U盘", "固态硬盘", "存储卡"],
    },
    "家居用品": {
        "厨房电器": ["电饭煲", "破壁机", "空气炸锅", "微波炉", "电磁炉", "电水壶"],
        "清洁电器": ["吸尘器", "扫地机器人", "洗衣机", "干衣机"],
        "生活电器": ["电风扇", "空调", "加湿器", "除湿机", "空气净化器"],
        "家具": ["办公椅", "升降桌", "沙发", "床", "衣柜", "书架"],
    },
    "食品饮料": {
        "休闲零食": ["薯片", "坚果", "巧克力", "饼干", "糖果"],
        "早餐谷物": ["燕麦片", "麦片", "玉米片", "豆浆粉"],
        "饮料": ["矿泉水", "碳酸饮料", "果汁", "茶饮料", "咖啡"],
        "粮油调味": ["大米", "食用油", "酱油", "醋", "盐"],
    },
    "服装鞋帽": {
        "男装": ["T恤", "衬衫", "裤子", "外套", "羽绒服"],
        "女装": ["连衣裙", "T恤", "半身裙", "外套", "大衣"],
        "童装": ["儿童T恤", "儿童裤子", "儿童外套", "儿童鞋"],
        "鞋": ["运动鞋", "皮鞋", "凉鞋", "拖鞋", "靴子"],
    },
    "运动户外": {
        "健身器材": ["哑铃", "跑步机", "动感单车", "瑜伽垫", "拉力器"],
        "球类": ["篮球", "足球", "羽毛球拍", "乒乓球拍", "网球拍"],
        "户外装备": ["帐篷", "睡袋", "登山包", "折叠椅", "野餐垫"],
    },
    "美妆护肤": {
        "护肤": ["面霜", "精华", "面膜", "洗面奶", "化妆水"],
        "彩妆": ["口红", "眼影", "粉底", "睫毛膏", "眉笔"],
        "个护": ["洗发水", "护发素", "沐浴露", "牙膏", "牙刷"],
    },
    "母婴用品": {
        "奶粉": ["婴儿奶粉", "儿童奶粉", "特殊配方奶粉"],
        "尿裤": ["纸尿裤", "拉拉裤", "尿片"],
        "喂养": ["奶瓶", "奶嘴", "温奶器", "消毒器"],
        "玩具": ["积木", "毛绒玩具", "遥控玩具", "拼图"],
    },
    "图书文具": {
        "图书": ["小说", "童书", "教辅", "漫画", "传记"],
        "文具": ["笔记本", "中性笔", "铅笔", "橡皮", "订书机"],
        "办公": ["文件柜", "白板", "投影仪", "碎纸机"],
    },
}

# 产品数量配置
NUM_PRODUCTS = 500
NUM_TRANSACTIONS = 10000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)

# 异常日期配置
ANOMALY_DATES = {
    "2024-06-15": {"type": "销量突增", "multiplier": 5, "description": "618大促"},
    "2024-11-11": {"type": "销量突增", "multiplier": 8, "description": "双11大促"},
    "2024-08-05": {"type": "退款率激增", "multiplier": 1, "description": "质量问题导致退款", "return_rate": 0.5},
}

def generate_product_catalog():
    """生成产品目录表"""
    print("生成产品目录表...")

    products = []
    product_id = 1

    # 按分类生成产品
    for l1_cat, l2_dict in CATEGORIES.items():
        for l2_cat, l2_products in l2_dict.items():
            for product_name in l2_products:
                # 生成产品变体（不同规格/颜色/版本）
                variants = random.randint(3, 8)
                for var_idx in range(variants):
                    # 产品基础价（根据分类设定范围）
                    if l1_cat == "电子产品":
                        base_price = random.uniform(50, 5000)
                    elif l1_cat == "家居用品":
                        base_price = random.uniform(30, 3000)
                    elif l1_cat == "食品饮料":
                        base_price = random.uniform(5, 200)
                    elif l1_cat == "服装鞋帽":
                        base_price = random.uniform(20, 1500)
                    elif l1_cat == "运动户外":
                        base_price = random.uniform(30, 2000)
                    elif l1_cat == "美妆护肤":
                        base_price = random.uniform(20, 800)
                    elif l1_cat == "母婴用品":
                        base_price = random.uniform(10, 500)
                    else:  # 图书文具
                        base_price = random.uniform(5, 300)

                    # 成本价约为售价的40-70%
                    cost_rate = random.uniform(0.4, 0.7)
                    cost_price = round(base_price * cost_rate, 2)
                    unit_price = round(base_price * random.uniform(0.95, 1.05), 2)

                    # 上架日期（2023-2024年）
                    launch_days = random.randint(0, 730)
                    launch_date = (datetime(2022, 1, 1) + timedelta(days=launch_days)).strftime("%Y-%m-%d")

                    # 状态（大部分在售，少部分下架/缺货）
                    status_roll = random.random()
                    if status_roll < 0.85:
                        status = "在售"
                    elif status_roll < 0.95:
                        status = "缺货"
                    else:
                        status = "下架"

                    # 产品名称变体
                    variant_name = product_name
                    if variants > 1:
                        variant_suffixes = ["标准版", "升级版", "豪华版", "青春版", "Pro版", "Plus版",
                                          "迷你版", "大容量版", "无线版", "有线版"]
                        variant_name = f"{product_name} {variant_suffixes[var_idx % len(variant_suffixes)]}"

                    products.append({
                        "product_id": f"P{product_id:04d}",
                        "product_name": variant_name,
                        "category_l1": l1_cat,
                        "category_l2": l2_cat,
                        "cost_price": cost_price,
                        "launch_date": launch_date,
                        "status": status,
                        "_base_price": unit_price
                    })

                    product_id += 1

                    if product_id > NUM_PRODUCTS:
                        break

                if product_id > NUM_PRODUCTS:
                    break
            if product_id > NUM_PRODUCTS:
                break
        if product_id > NUM_PRODUCTS:
            break

    # 如果产品数不足500，补充一些通用产品
    while product_id <= NUM_PRODUCTS:
        l1_cat = random.choice(list(CATEGORIES.keys()))
        l2_cat = random.choice(list(CATEGORIES[l1_cat].keys()))
        base_price = random.uniform(20, 1000)
        cost_price = round(base_price * random.uniform(0.5, 0.7), 2)

        products.append({
            "product_id": f"P{product_id:04d}",
            "product_name": f"通用{random.choice(['商品', '产品', '物品', '配件'])}-{product_id}",
            "category_l1": l1_cat,
            "category_l2": l2_cat,
            "cost_price": cost_price,
            "launch_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "status": "在售",
            "_base_price": round(base_price, 2)
        })
        product_id += 1

    df = pd.DataFrame(products)

    output_df = df.drop(columns=["_base_price"])
    output_df.to_csv("data/product_catalog.csv", index=False, encoding="utf-8-sig")

    print(f"  产品目录生成完成: {len(df)} 条记录")
    print(f"  一级分类: {df['category_l1'].nunique()} 个")
    print(f"  二级分类: {df['category_l2'].nunique()} 个")

    return df

def generate_transactions(product_df):
    """生成交易表（与产品表关联）"""
    print("\n生成交易表...")

    records = []
    date_range = (END_DATE - START_DATE).days + 1
    record_index = 0

    # 获取在售产品
    available_products = product_df[product_df["status"] == "在售"].copy()

    for day_offset in range(date_range):
        current_date = START_DATE + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        is_anomaly_day = date_str in ANOMALY_DATES

        # 每天生成约27条记录
        records_per_day = 25 + random.randint(0, 10)

        if is_anomaly_day:
            anomaly = ANOMALY_DATES[date_str]
            records_per_day = int(records_per_day * anomaly["multiplier"])

        for _ in range(records_per_day):
            record_index += 1

            # 选择产品
            product = available_products.sample(1).iloc[0]
            product_id = product["product_id"]
            base_price = product["_base_price"]

            # 获取数量
            month = current_date.month
            seasonal_factor = 1.0 + 0.2 * np.sin((month - 1) * np.pi / 6)
            weekday_factor = 1.0 if current_date.weekday() < 5 else 0.6

            quantity = max(1, int(random.randint(1, 5) * seasonal_factor * weekday_factor))

            if is_anomaly_day:
                anomaly = ANOMALY_DATES[date_str]
                if anomaly["type"] == "销量突增":
                    quantity = int(quantity * anomaly["multiplier"])

            # 价格
            unit_price = round(base_price * random.uniform(0.95, 1.05), 2)

            # 折扣
            if random.random() < 0.2:
                discount_rate = round(random.uniform(0.05, 0.30), 2)
            else:
                discount_rate = 0.0

            # 退款判断
            return_rate = 0.02 + random.uniform(0, 0.03)
            if is_anomaly_day and ANOMALY_DATES[date_str].get("type") == "退款率激增":
                return_rate = ANOMALY_DATES[date_str]["return_rate"]

            is_returned = "是" if random.random() < return_rate else "否"

            # 地区和渠道
            regions = ["华东", "华南", "华北", "华中", "西南", "西北", "东北"]
            channels = ["线上官网", "线上第三方", "线下直营店", "线下经销商", "企业团购"]

            records.append({
                "order_id": f"ORD{current_date.strftime('%Y%m%d')}{record_index:05d}",
                "date": date_str,
                "product_id": product_id,
                "region": random.choice(regions),
                "channel": random.choice(channels),
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_rate": discount_rate,
                "is_returned": is_returned
            })

    df = pd.DataFrame(records)

    # 打乱顺序
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 确保记录数
    if len(df) > NUM_TRANSACTIONS:
        df = df.head(NUM_TRANSACTIONS)

    output_df = df.drop(columns=[] if "_base_price" not in df.columns else ["_base_price"])
    output_df.to_csv("data/sales_transactions.csv", index=False, encoding="utf-8-sig")

    print(f"  交易表生成完成: {len(df)} 条记录")
    print(f"  关联产品数: {df['product_id'].nunique()} 个")

    return df

def generate_regional_targets():
    """生成区域目标表"""
    print("\n生成区域目标表...")

    regions = ["华东", "华南", "华北", "华中", "西南", "西北", "东北"]
    months = [f"2024-{month:02d}" for month in range(1, 13)]

    targets = []

    # 各区域基础目标（根据区域经济水平设定）
    region_base_targets = {
        "华东": 150000,    # 经济发达地区，目标较高
        "华南": 140000,
        "华北": 135000,
        "华中": 110000,
        "西南": 100000,
        "西北": 85000,
        "东北": 90000,
    }

    # 各月调整系数（考虑季节性）
    month_factors = {
        1: 0.85,   # 年初淡季
        2: 0.80,   # 春节
        3: 0.90,
        4: 0.95,
        5: 1.00,
        6: 1.20,   # 618大促
        7: 0.95,
        8: 0.90,
        9: 1.00,
        10: 1.05,
        11: 1.40,  # 双11
        12: 1.15,  # 年底冲刺
    }

    target_id = 1
    for region in regions:
        base_target = region_base_targets[region]

        for month_str in months:
            month = int(month_str.split("-")[1])
            month_factor = month_factors[month]

            # 计算月度目标
            monthly_target = int(base_target * month_factor * random.uniform(0.98, 1.02))

            # 毛利目标（毛利率约40-45%）
            profit_target = int(monthly_target * random.uniform(0.40, 0.45))

            # 新客目标
            new_customer_target = int(500 + random.randint(-100, 200) * (base_target / 100000))

            targets.append({
                "target_id": f"T{target_id:04d}",
                "region": region,
                "month": month_str,
                "sales_target": monthly_target,
                "profit_target": profit_target,
                "new_customer_target": new_customer_target,
                # 实际完成情况（用于验证，会在交易表生成后计算填入）
                "actual_sales": None,
                "actual_profit": None,
                "actual_new_customers": None,
            })

            target_id += 1

    df = pd.DataFrame(targets)

    # 保存
    df.to_csv("data/regional_targets.csv", index=False, encoding="utf-8-sig")

    print(f"  区域目标表生成完成: {len(df)} 条记录")
    print(f"  覆盖区域: {len(regions)} 个")
    print(f"  覆盖月份: {len(months)} 个月")

    return df

def update_regional_targets_with_actual(target_df, trans_df, product_df):
    """根据交易数据更新区域目标的实际完成情况"""
    print("\n计算区域目标实际完成情况...")

    # 确保日期格式一致
    trans_df = trans_df.copy()
    trans_df["month"] = trans_df["date"].str[:7]

    # 合并产品信息获取成本
    merged = trans_df.merge(
        product_df[["product_id", "cost_price", "product_name"]],
        on="product_id",
        how="left"
    )

    # 计算每笔交易的收入和成本
    merged["revenue"] = merged["quantity"] * merged["unit_price"] * (1 - merged["discount_rate"])
    merged["cost"] = merged["quantity"] * merged["cost_price"]
    merged["profit"] = merged["revenue"] - merged["cost"]

    # 按区域和月份汇总
    actual_stats = merged.groupby(["region", "month"]).agg({
        "revenue": "sum",
        "profit": "sum",
        "order_id": "nunique"  # 订单数作为新客代理指标
    }).reset_index()
    actual_stats.columns = ["region", "month", "actual_sales", "actual_profit", "actual_new_customers"]

    # 更新目标表
    for idx, row in target_df.iterrows():
        match = actual_stats[
            (actual_stats["region"] == row["region"]) &
            (actual_stats["month"] == row["month"])
        ]
        if len(match) > 0:
            target_df.at[idx, "actual_sales"] = int(match.iloc[0]["actual_sales"])
            target_df.at[idx, "actual_profit"] = int(match.iloc[0]["actual_profit"])
            target_df.at[idx, "actual_new_customers"] = int(match.iloc[0]["actual_new_customers"])

    # 填充未完成的为0
    target_df["actual_sales"] = target_df["actual_sales"].fillna(0).astype(int)
    target_df["actual_profit"] = target_df["actual_profit"].fillna(0).astype(int)
    target_df["actual_new_customers"] = target_df["actual_new_customers"].fillna(0).astype(int)

    # 保存更新后的目标表
    target_df.to_csv("data/regional_targets.csv", index=False, encoding="utf-8-sig")

    # 计算达成率
    target_df["sales_achievement_rate"] = (target_df["actual_sales"] / target_df["sales_target"] * 100).round(2)
    target_df["profit_achievement_rate"] = (target_df["actual_profit"] / target_df["profit_target"] * 100).round(2)

    print("  实际完成情况已计算并更新到目标表")

    return target_df

def print_summary(product_df, trans_df, target_df):
    """打印数据概要"""
    print("\n" + "=" * 60)
    print("数据生成完成 - 概要统计")
    print("=" * 60)

    print("\n【产品维度表 product_catalog.csv】")
    print(f"  总记录数: {len(product_df)}")
    print(f"  一级分类分布:")
    for cat, count in product_df["category_l1"].value_counts().items():
        print(f"    {cat}: {count}")

    print("\n【核心交易表 sales_transactions.csv】")
    print(f"  总记录数: {len(trans_df)}")
    print(f"  日期范围: {trans_df['date'].min()} 至 {trans_df['date'].max()}")
    print(f"  关联产品数: {trans_df['product_id'].nunique()}")

    print("\n【区域目标表 regional_targets.csv】")
    print(f"  总记录数: {len(target_df)}")
    print(f"  覆盖区域: {target_df['region'].nunique()} 个")
    print(f"  覆盖月份: {target_df['month'].nunique()} 个月")

    # 目标达成率统计
    target_df["sales_achievement_rate"] = (target_df["actual_sales"] / target_df["sales_target"] * 100).round(2)
    target_df["profit_achievement_rate"] = (target_df["actual_profit"] / target_df["profit_target"] * 100).round(2)

    print("\n【目标达成率汇总】")
    overall_sales_rate = (target_df["actual_sales"].sum() / target_df["sales_target"].sum() * 100).round(2)
    overall_profit_rate = (target_df["actual_profit"].sum() / target_df["profit_target"].sum() * 100).round(2)
    print(f"  整体销售达成率: {overall_sales_rate}%")
    print(f"  整体毛利达成率: {overall_profit_rate}%")

    print("\n【各区域年度销售达成率】")
    region_yearly = target_df.groupby("region").agg({
        "sales_target": "sum",
        "actual_sales": "sum"
    })
    region_yearly["achievement_rate"] = (region_yearly["actual_sales"] / region_yearly["sales_target"] * 100).round(2)
    region_yearly = region_yearly.sort_values("achievement_rate", ascending=False)

    for region, row in region_yearly.iterrows():
        status = "达标" if row["achievement_rate"] >= 100 else "未达标"
        print(f"    {region}: {row['achievement_rate']}% ({status})")

    print("\n【异常日期验证】")
    for date_str, anomaly in ANOMALY_DATES.items():
        day_data = trans_df[trans_df["date"] == date_str]
        print(f"  {date_str} ({anomaly['description']}): {len(day_data)} 条记录", end="")
        if anomaly["type"] == "销量突增":
            print(f", 总销量 {day_data['quantity'].sum()}")
        else:
            return_rate = (day_data["is_returned"] == "是").sum() / len(day_data) * 100
            print(f", 退款率 {return_rate:.1f}%")

    print("\n【使用说明】")
    print("  1. 先上传 product_catalog.csv 建立产品维度表")
    print("  2. 再上传 sales_transactions.csv 建立交易事实表")
    print("  3. 上传 regional_targets.csv 建立区域目标表")
    print("  4. 系统支持多表关联分析、毛利分析、分类下钻分析、目标达成分析")

def main():
    os.makedirs("data", exist_ok=True)

    print("=" * 60)
    print("AI智能数据分析系统 - 测试数据生成")
    print("=" * 60)
    print()

    # 生成产品目录
    product_df = generate_product_catalog()

    # 生成交易表
    trans_df = generate_transactions(product_df)

    # 生成区域目标表
    target_df = generate_regional_targets()

    # 根据交易数据更新目标实际完成情况
    target_df = update_regional_targets_with_actual(target_df, trans_df, product_df)

    # 打印概要
    print_summary(product_df, trans_df, target_df)

    print("\n数据文件已生成完毕！")

if __name__ == "__main__":
    main()
