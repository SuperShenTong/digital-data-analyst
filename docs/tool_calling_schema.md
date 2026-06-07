# AI智能数据分析系统 - Tool Calling工具调用Schema文档

## 1. 工具调用系统概述

本系统的工具调用(Tool Calling)模块提供了一套标准化的工具注册、发现和调用机制，支持智能体自动调度各类分析工具。

### 1.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Calling System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ BaseTool     │  │ Tool Registry│  │ Tool Executor│      │
│  │   (基类)     │  │  (工具注册)  │  │  (执行引擎)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                │
│         ▼                 ▼                 ▼                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              工具实现层                              │    │
│  │  data_reader | structure_check | stat_analysis     │    │
│  │  anomaly_detection | chart_generator               │    │
│  │  report_generator                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 工具调用流程

```
智能体请求 → 工具名称解析 → 参数验证 → 工具执行 → 结果返回 → 日志记录
```

## 2. BaseTool 基类

### 2.1 类定义

```python
class BaseTool(ABC):
    name: str                     # 工具名称(唯一标识)
    description: str              # 工具描述
    parameters: Dict[str, dict]   # 参数定义Schema
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
```

### 2.2 核心方法

| 方法名 | 功能说明 | 参数 | 返回值 |
|--------|----------|------|--------|
| `execute(**kwargs)` | 执行工具 | 工具特定参数 | `Any` |
| `get_schema()` | 获取工具Schema | 无 | `dict` |
| `validate_parameters(**kwargs)` | 验证参数 | 输入参数 | `bool` |

### 2.3 Schema结构

```python
{
    "name": str,                  # 工具名称
    "description": str,           # 工具描述
    "parameters": {
        "param_name": {
            "type": str,          # 参数类型: string, integer, number, boolean
            "description": str,   # 参数描述
            "required": bool      # 是否必填
        }
    }
}
```

## 3. 工具清单

### 3.1 data_reader - 数据读取工具

#### 功能描述
读取数据源中的数据，支持过滤、排序等操作

#### Schema定义

```python
{
    "name": "data_reader",
    "description": "读取数据源中的数据，支持过滤、排序等操作",
    "parameters": {
        "data_source_id": {
            "type": "integer",
            "description": "数据源ID",
            "required": true
        },
        "filter_conditions": {
            "type": "string",
            "description": "过滤条件（JSON格式）",
            "required": false
        },
        "sort_by": {
            "type": "string",
            "description": "排序字段",
            "required": false
        },
        "limit": {
            "type": "integer",
            "description": "返回行数限制",
            "required": false
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data_source_id | integer | 是 | 数据源ID |
| filter_conditions | string | 否 | JSON格式的过滤条件，如 `{"status": "active"}` |
| sort_by | string | 否 | 排序字段名 |
| limit | integer | 否 | 返回行数上限 |

#### 输出格式

```python
list[dict]  # 数据记录列表
```

---

### 3.2 structure_check - 结构检测工具

#### 功能描述
检测数据源的结构信息，包括字段类型、空值统计、数据摘要等

#### Schema定义

```python
{
    "name": "structure_check",
    "description": "检测数据源的结构信息，包括字段类型、空值统计、数据摘要等",
    "parameters": {
        "data_source_id": {
            "type": "integer",
            "description": "数据源ID",
            "required": true
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data_source_id | integer | 是 | 数据源ID |

#### 输出格式

```python
{
    "row_count": int,              # 总行数
    "column_count": int,           # 总列数
    "columns": list[str],          # 字段名称列表
    "column_info": list[dict]      # 字段详细信息
}
```

**column_info 结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| name | string | 字段名称 |
| type | string | 字段类型 |
| null_count | integer | 空值数量 |
| null_percent | number | 空值占比(%) |
| unique_count | integer | 唯一值数量 |

---

### 3.3 stat_analysis - 统计分析工具

#### 功能描述
对数值型字段进行统计分析，包括均值、中位数、标准差、最值等

#### Schema定义

```python
{
    "name": "stat_analysis",
    "description": "对数值型字段进行统计分析，包括均值、中位数、标准差、最值等",
    "parameters": {
        "data_source_id": {
            "type": "integer",
            "description": "数据源ID",
            "required": true
        },
        "target_columns": {
            "type": "string",
            "description": "目标字段列表（逗号分隔）",
            "required": false
        },
        "group_by": {
            "type": "string",
            "description": "分组字段",
            "required": false
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data_source_id | integer | 是 | 数据源ID |
| target_columns | string | 否 | 目标字段，逗号分隔，如 "销售额,订单数量" |
| group_by | string | 否 | 分组字段名 |

#### 输出格式

```python
{
    "字段名": {
        "mean": float,    # 均值
        "median": float,  # 中位数
        "std": float,     # 标准差
        "min": float,     # 最小值
        "max": float,     # 最大值
        "sum": float,     # 总和
        "count": int,     # 非空计数
        "unique": int     # 唯一值数量
    }
}
```

---

### 3.4 anomaly_detection - 异常检测工具

#### 功能描述
检测数据中的异常值，支持环比、同比异常、数值突变、极值异常等检测

#### Schema定义

```python
{
    "name": "anomaly_detection",
    "description": "检测数据中的异常值，支持环比、同比异常、数值突变、极值异常等检测",
    "parameters": {
        "data_source_id": {
            "type": "integer",
            "description": "数据源ID",
            "required": true
        },
        "target_column": {
            "type": "string",
            "description": "目标字段",
            "required": true
        },
        "time_column": {
            "type": "string",
            "description": "时间字段（用于环比/同比分析）",
            "required": false
        },
        "method": {
            "type": "string",
            "description": "检测方法：zscore, iqr, change_point, seasonality",
            "required": false
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data_source_id | integer | 是 | 数据源ID |
| target_column | string | 是 | 目标字段名 |
| time_column | string | 否 | 时间字段名 |
| method | string | 否 | 检测方法，默认 zscore |

#### 检测方法说明

| 方法名 | 说明 |
|--------|------|
| zscore | Z-score异常检测，检测极值异常 |
| iqr | IQR四分位数范围检测 |
| change_point | 突变检测，检测数值突变 |
| seasonality | 季节性异常检测 |

#### 输出格式

```python
{
    "anomalies": list[dict],     # 异常记录列表
    "total_detected": int         # 检测到的异常总数
}
```

**异常记录结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| type | string | 异常类型：极值异常、IQR异常、突变异常、季节性异常 |
| index | integer | 数据行索引 |
| value | float | 异常值 |
| severity | string | 严重程度：high, medium, low |
| description | string | 异常描述 |
| recommendation | string | 处理建议 |
| z_score | float | Z-score值(仅zscore方法) |
| expected_range | list[float] | 预期范围 |
| previous_value | float | 前一个值(仅change_point方法) |
| change_amount | float | 变化量(仅change_point方法) |

---

### 3.5 chart_generator - 图表生成工具

#### 功能描述
根据数据生成可视化图表，支持柱状图、折线图、饼图、散点图等

#### Schema定义

```python
{
    "name": "chart_generator",
    "description": "根据数据生成可视化图表，支持柱状图、折线图、饼图、散点图等",
    "parameters": {
        "data_source_id": {
            "type": "integer",
            "description": "数据源ID",
            "required": true
        },
        "chart_type": {
            "type": "string",
            "description": "图表类型：bar, line, pie, scatter, histogram",
            "required": true
        },
        "x_column": {
            "type": "string",
            "description": "X轴字段",
            "required": true
        },
        "y_column": {
            "type": "string",
            "description": "Y轴字段",
            "required": false
        },
        "group_column": {
            "type": "string",
            "description": "分组字段",
            "required": false
        },
        "title": {
            "type": "string",
            "description": "图表标题",
            "required": false
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data_source_id | integer | 是 | 数据源ID |
| chart_type | string | 是 | 图表类型 |
| x_column | string | 是 | X轴字段名 |
| y_column | string | 否 | Y轴字段名(饼图可选) |
| group_column | string | 否 | 分组字段名(用于多系列) |
| title | string | 否 | 图表标题 |

#### 图表类型说明

| 类型 | 说明 |
|------|------|
| bar | 柱状图 |
| line | 折线图 |
| pie | 饼图 |
| scatter | 散点图 |
| histogram | 直方图 |

#### 输出格式

```python
{
    "chart_type": str,        # 图表类型
    "title": str,             # 图表标题
    "file_path": str,         # 生成的文件路径
    "url": str,               # 可访问的URL
    "data_points": int        # 数据点数量
}
```

---

### 3.6 report_generator - 报告生成工具

#### 功能描述
将分析结果生成为结构化的数据分析报告

#### Schema定义

```python
{
    "name": "report_generator",
    "description": "将分析结果生成为结构化的数据分析报告",
    "parameters": {
        "analysis_result": {
            "type": "string",
            "description": "分析结果（JSON格式）",
            "required": true
        },
        "report_type": {
            "type": "string",
            "description": "报告类型：summary, detailed, executive",
            "required": false
        },
        "include_charts": {
            "type": "boolean",
            "description": "是否包含图表",
            "required": false
        }
    }
}
```

#### 输入参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| analysis_result | string | 是 | JSON格式的分析结果 |
| report_type | string | 否 | 报告类型，默认 summary |
| include_charts | boolean | 否 | 是否包含图表，默认 false |

#### 报告类型说明

| 类型 | 说明 |
|------|------|
| summary | 摘要报告，简洁版 |
| detailed | 详细报告，包含完整分析 |
| executive | 执行报告，面向管理层 |

#### analysis_result 结构

```python
{
    "user_query": str,           # 用户查询问题
    "summary": str,              # 分析摘要
    "statistics": dict,          # 统计分析结果
    "anomalies": list[dict],     # 异常检测结果
    "recommendations": list[str], # 业务建议
    "charts": list[dict]         # 图表列表
}
```

#### 输出格式

```python
{
    "report_content": str,    # Markdown格式的报告内容
    "report_type": str        # 报告类型
}
```

## 4. 工具调用日志

### 4.1 日志记录结构

```python
{
    "tool_name": str,                 # 工具名称
    "input_params": dict,             # 输入参数
    "output_result": dict,            # 输出结果
    "execution_time_ms": int,         # 执行时间(毫秒)
    "timestamp": str                  # 时间戳
}
```

### 4.2 日志存储

日志存储在 `tool_call_logs` 表中，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| analysis_record_id | INTEGER | 关联的分析记录ID |
| tool_name | VARCHAR | 工具名称 |
| input_params | JSON | 输入参数 |
| output_result | JSON | 输出结果 |
| execution_time_ms | INTEGER | 执行时间 |
| timestamp | DATETIME | 时间戳 |

## 5. 工具扩展规范

### 5.1 新增工具步骤

1. 创建工具类，继承 `BaseTool`
2. 定义 `name`, `description`, `parameters` 属性
3. 实现 `execute()` 方法
4. 在 Agent 中注册工具

### 5.2 工具类模板

```python
from app.tools.base_tool import BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "自定义工具描述"
    parameters = {
        "param1": {
            "type": "string",
            "description": "参数说明",
            "required": true
        }
    }
    
    def execute(self, **kwargs):
        # 工具逻辑实现
        param1 = kwargs.get("param1")
        # ...
        return result
```

## 6. 工具调用API

### 6.1 获取工具列表

**接口**: `GET /api/tools/list`

**响应**:

```json
{
    "tools": [
        {
            "name": "data_reader",
            "description": "...",
            "parameters": {...}
        }
    ]
}
```