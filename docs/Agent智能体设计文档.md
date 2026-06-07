# AI智能数据分析系统 - Agent智能体设计文档

## 1. 智能体架构概述

本系统采用多智能体协作架构，三个核心智能体分工明确、协同联动，共同完成数据分析全流程任务。

```
用户问题
   ↓
┌─────────────────────┐
│ DataUnderstanding   │ ← 意图识别、计划生成
│      Agent          │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│  DataAnalysis       │ ← 工具执行、数据分析
│      Agent          │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ ReportGeneration    │ ← 报告生成、业务建议
│      Agent          │
└─────────┬───────────┘
          ↓
    最终报告输出
```

## 2. BaseAgent 基类设计

### 2.1 类定义

```python
class BaseAgent(ABC):
    name: str                    # 智能体名称
    role: str                    # 智能体角色描述
    
    def __init__(self):
        self.execution_history   # 执行历史记录
```

### 2.2 核心方法

| 方法名 | 功能说明 | 参数 | 返回值 |
|--------|----------|------|--------|
| `execute(task, context)` | 执行核心任务 | `task`: 任务描述, `context`: 上下文信息 | `dict` 执行结果 |
| `log_execution(task, status, details)` | 记录执行日志 | `task`: 任务, `status`: 状态, `details`: 详情 | `None` |
| `get_execution_history()` | 获取执行历史 | 无 | `list[dict]` |
| `clear_history()` | 清空执行历史 | 无 | `None` |

### 2.3 执行历史数据结构

```python
{
    "agent_name": str,      # 智能体名称
    "task": str,            # 任务描述
    "status": str,          # 状态: pending/in_progress/completed/failed
    "details": str,         # 详细信息
    "timestamp": str        # 时间戳(ISO格式)
}
```

## 3. DataUnderstandingAgent 数据理解智能体

### 3.1 角色定位

**职责**: 识别用户分析意图、匹配数据源、梳理所需字段、生成标准化分析计划、判断是否需要补充提问。

### 3.2 设计思路

```
用户问题 → 意图识别 → 字段匹配 → 分析计划生成 → 判断是否追问
```

### 3.3 核心属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `name` | str | "DataUnderstandingAgent" |
| `role` | str | "数据理解" |
| `data_service` | DataService | 数据服务实例 |

### 3.4 核心方法

#### 3.4.1 `execute(task, context)`

**功能**: 执行数据理解任务，生成分析计划

**输入参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `task` | str | 用户查询问题 |
| `context` | dict | 上下文信息，包含 `data_source_id` |

**输出结果**:
```python
{
    "agent_name": "DataUnderstandingAgent",
    "analysis_plan": {
        "steps": list[dict],      # 分析步骤列表
        "required_fields": list[str],  # 需要的字段
        "description": str,       # 计划描述
        "requires_followup": bool,    # 是否需要追问
        "followup_question": str      # 追问问题
    },
    "data_source_info": dict,     # 数据源信息
    "requires_followup": bool,
    "followup_question": str
}
```

#### 3.4.2 `_generate_analysis_plan(user_query, available_columns)`

**功能**: 根据用户查询和可用字段生成分析计划

**关键词映射规则**:

| 关键词类型 | 关键词示例 | 对应工具 |
|-----------|-----------|---------|
| 数值统计 | 统计、平均、总和、最大、最小、数量、金额、收入、支出 | stat_analysis |
| 趋势分析 | 趋势、变化、增长、下降、环比、同比 | stat_analysis |
| 异常检测 | 异常、问题、波动、突变、异常值 | anomaly_detection |
| 对比分析 | 对比、比较、差异 | stat_analysis |
| 可视化 | 图表、图、可视化 | chart_generator |

**步骤生成逻辑**:
1. 解析用户查询中的关键词
2. 根据关键词匹配对应工具
3. 生成有序的步骤列表
4. 识别所需字段
5. 判断是否需要追问

### 3.5 字段识别规则

#### 3.5.1 数值型字段识别

通过字段名后缀识别：
- 金额、数量、收入、支出、价格、成本、利润、数值、值
- 纯数字字段名

#### 3.5.2 时间字段识别

通过字段名识别：
- 时间、日期、日期时间、时间戳

## 4. DataAnalysisAgent 数据分析智能体

### 4.1 角色定位

**职责**: 调用各类工具执行数据查询、统计计算、指标核算、数据异常识别，输出结构化分析结果。

### 4.2 设计思路

```
分析计划 → 步骤遍历 → 工具调用 → 结果收集 → 生成摘要
```

### 4.3 核心属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `name` | str | "DataAnalysisAgent" |
| `role` | str | "数据分析" |
| `db` | Session | 数据库会话 |
| `tools` | dict | 可用工具字典 |

### 4.4 工具列表

| 工具名 | 工具类 | 功能 |
|--------|--------|------|
| "data_reader" | DataReaderTool | 读取数据源数据 |
| "structure_check" | StructureCheckTool | 检测数据结构 |
| "stat_analysis" | StatAnalysisTool | 统计分析 |
| "anomaly_detection" | AnomalyDetectionTool | 异常检测 |

### 4.5 核心方法

#### 4.5.1 `execute(task, context)`

**功能**: 执行数据分析任务

**输入参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `task` | str | 任务描述 |
| `context` | dict | 包含 `data_source_id`, `analysis_plan` |

**输出结果**:
```python
{
    "agent_name": "DataAnalysisAgent",
    "tool_results": list[dict],    # 工具执行结果列表
    "summary": str,                # 分析摘要
    "statistics": dict,            # 统计结果
    "anomalies": list[dict],       # 异常检测结果
    "structure_info": dict         # 结构信息
}
```

#### 4.5.2 `_get_numeric_columns(data_source_id)`

**功能**: 获取数据源中的数值型字段

#### 4.5.3 `_generate_summary(results)`

**功能**: 根据工具执行结果生成分析摘要

### 4.6 工具执行流程

```
for step in analysis_plan.steps:
    tool_name = step.tool
    if tool_name in self.tools:
        params = {"data_source_id": data_source_id}
        根据工具类型补充参数
        result = tool.execute(**params)
        记录执行时间
        保存结果到 tool_results
```

## 5. ReportGenerationAgent 报告生成智能体

### 5.1 角色定位

**职责**: 将量化分析结果转化为通俗易懂的业务结论，配套图表解读、挖掘数据核心问题、输出可落地的业务优化建议，自动生成完整数据分析报告。

### 5.2 设计思路

```
分析结果 → 图表生成 → 报告内容组装 → 业务建议生成 → 输出报告
```

### 5.3 核心属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `name` | str | "ReportGenerationAgent" |
| `role` | str | "报告生成" |
| `db` | Session | 数据库会话 |
| `chart_tool` | ChartGeneratorTool | 图表生成工具 |
| `report_tool` | ReportGeneratorTool | 报告生成工具 |

### 5.4 核心方法

#### 5.4.1 `execute(task, context)`

**功能**: 生成分析报告

**输入参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `task` | str | 任务描述 |
| `context` | dict | 包含 `data_source_id`, `analysis_results`, `user_query` |

**输出结果**:
```python
{
    "agent_name": "ReportGenerationAgent",
    "report_content": str,    # 报告内容(Markdown格式)
    "charts": list[dict],     # 图表列表
    "summary": str            # 报告摘要
}
```

#### 5.4.2 `_generate_charts(data_source_id, analysis_results)`

**功能**: 根据分析结果生成可视化图表

#### 5.4.3 `_generate_recommendations(analysis_results)`

**功能**: 根据分析结果生成业务优化建议

**建议生成规则**:
1. 若检测到异常 → 建议核实异常数据
2. 若数据波动性大(CV > 0.5) → 建议分析波动原因
3. 通用建议 → 定期数据质量检查、设置告警机制

#### 5.4.4 `_generate_final_summary(report_data)`

**功能**: 生成报告最终摘要

## 6. AgentCoordinator 智能体协调器

### 6.1 角色定位

**职责**: 协调三个核心智能体的执行流程，管理分析记录和工具调用日志。

### 6.2 核心属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `db` | Session | 数据库会话 |
| `data_understanding_agent` | DataUnderstandingAgent | 数据理解智能体 |
| `data_analysis_agent` | DataAnalysisAgent | 数据分析智能体 |
| `report_generation_agent` | ReportGenerationAgent | 报告生成智能体 |

### 6.3 核心方法

#### 6.3.1 `execute_analysis(user_query, data_source_id, session_id)`

**功能**: 执行完整的数据分析流程

**执行流程**:
```
1. 创建分析记录(analysis_records表)
2. 调用 DataUnderstandingAgent.execute() → 获取分析计划
3. 保存分析计划到数据库
4. 调用 DataAnalysisAgent.execute() → 执行数据分析
5. 调用 ReportGenerationAgent.execute() → 生成报告
6. 记录工具调用日志(tool_call_logs表)
7. 更新分析记录状态为completed
8. 返回最终结果
```

**输出结果**:
```python
{
    "analysis_id": int,               # 分析记录ID
    "user_query": str,                # 用户查询
    "data_source_id": int,            # 数据源ID
    "analysis_plan": dict,            # 分析计划
    "tool_calls": list[dict],         # 工具调用记录
    "statistics": dict,               # 统计结果
    "anomalies": list[dict],          # 异常检测结果
    "report_content": str,            # 报告内容
    "summary": str,                   # 摘要
    "charts": list[dict],             # 图表列表
    "created_at": str                 # 创建时间
}
```

#### 6.3.2 `get_analysis_history(data_source_id)`

**功能**: 获取分析历史记录

#### 6.3.3 `get_analysis_detail(analysis_id)`

**功能**: 获取分析详情，包含完整的工具调用日志

## 7. 智能体协作协议

### 7.1 上下文传递规范

上下文字典结构：
```python
{
    "data_source_id": int,       # 必须：数据源ID
    "user_query": str,           # 用户查询
    "session_id": str,           # 会话ID(可选)
    "analysis_record_id": int,   # 分析记录ID
    "analysis_plan": dict,       # 分析计划(由DataUnderstandingAgent生成)
    "analysis_results": dict     # 分析结果(由DataAnalysisAgent生成)
}
```

### 7.2 错误处理流程

```
Agent执行失败 → 返回 {"error": "错误信息"} → Coordinator捕获错误 → 更新记录状态为failed → 返回错误信息
```

### 7.3 日志记录规范

所有智能体执行和工具调用都必须记录日志，包含：
- 执行时间
- 执行状态
- 输入参数
- 输出结果
- 执行耗时

## 8. 扩展设计

### 8.1 新增智能体

遵循 BaseAgent 基类接口，实现 `execute()` 方法：

```python
class CustomAgent(BaseAgent):
    name = "CustomAgent"
    role = "自定义角色"
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 实现核心逻辑
        pass
```

### 8.2 新增工具

遵循 BaseTool 基类接口，实现 `execute()` 方法：

```python
class CustomTool(BaseTool):
    name = "custom_tool"
    description = "自定义工具描述"
    parameters = {
        "param1": {"type": "string", "description": "参数说明", "required": True}
    }
    
    def execute(self, **kwargs) -> Any:
        # 实现工具逻辑
        pass
```