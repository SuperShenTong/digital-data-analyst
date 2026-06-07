# AI智能数据分析系统 - 技术设计文档

## 1. 系统概述

本系统是一款基于多智能体技术的企业轻量化智能数据分析平台，旨在解决传统数据分析效率低、智能化不足的痛点。系统实现自然语言提问到自动化报告生成的全流程闭环。

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           前端界面层                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│   │ 数据管理 │  │ 问答分析 │  │ 报告中心 │  │ 执行日志 │  │ 图表展示 │   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└────────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────┘
         │             │             │             │             │
┌────────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────┐
│                           API网关层                                     │
│   FastAPI Router: /api/data, /api/analysis, /api/chat, /api/tools        │
└────────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────┘
         │             │             │             │             │
┌────────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────┐
│                           业务逻辑层                                     │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                        Agent Coordinator                         │  │
│   │  ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐  │  │
│   │  │DataUnderstanding │ │  DataAnalysis    │ │ ReportGeneration   │  │  │
│   │  │     Agent        │ │     Agent        │ │      Agent        │  │  │
│   │  └────────┬─────────┘ └────────┬─────────┘ └─────────┬─────────┘  │  │
│   │           │                    │                    │            │  │
│   │           └────────────────────┼────────────────────┘            │  │
│   │                                ↓                                 │  │
│   │  ┌───────────────────────────────────────────────────────────┐  │  │
│   │  │                     Tool Calling System                    │  │  │
│   │  │  data_reader | structure_check | stat_analysis            │  │  │
│   │  │  anomaly_detection | chart_generator | report_generator   │  │  │
│   │  └───────────────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                         服务层 (Services)                        │  │
│   │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐  │  │
│   │  │  LLM Service    │ │  LLM Chart       │ │  Enhanced Chart  │  │  │
│   │  │  (大模型服务)    │ │  Selector        │ │  Generator       │  │  │
│   │  └──────────────────┘ │  (LLM图表选择器) │ │  (增强图表生成器) │  │  │
│   │  ┌──────────────────┐ └──────────────────┘ └──────────────────┘  │  │
│   │  │  Context Service │ ┌──────────────────┐ ┌──────────────────┐  │  │
│   │  │  (上下文服务)     │ │ Observability   │ │  Data Service   │  │  │
│   │  └──────────────────┘ │    Service      │ │   (数据服务)     │  │  │
│   └───────────────────────└─────────────────┘ └──────────────────┘  │  │
└────────┼───────────────────────────────────────────────────────────────┘
         │             │             │             │
┌────────┼─────────────┼─────────────┼─────────────┼──────────┐
│                           数据存储层                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │   SQLite     │  │   文件存储    │  │    日志文件   │      │
│   │   (元数据)   │  │ (上传文件)   │  │              │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 智能体协作流程

```
用户提问 → DataUnderstandingAgent → 分析计划生成 → DataAnalysisAgent → 工具执行 → ReportGenerationAgent → 报告输出+图表
                  ↓                                              ↓                                    ↓
            意图识别/字段匹配                              统计分析/异常检测                    LLM智能图表决策
```

### 2.3 图表生成流程 (LLM智能决策)

```
数据分析结果 ──┬──→ 数据摘要生成 ──→ LLM图表选择器 ──→ LLM决定是否需要图表
              │                           ↓
              │                    需要哪些图表?
              │                           ↓
              └──→ 增强图表生成器 ←─── 图表类型和数据映射
                                        ↓
                                  ECharts图表配置
                                        ↓
                                  前端渲染展示
```

## 3. 核心模块设计

### 3.1 智能体模块

#### 3.1.1 BaseAgent 基类

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `execute()` | 执行任务 | `task: str`, `context: dict` | `dict` |
| `log_execution()` | 记录执行日志 | `task: str`, `status: str`, `details: str` | `None` |
| `get_execution_history()` | 获取执行历史 | 无 | `list[dict]` |

#### 3.1.2 DataUnderstandingAgent

**职责**: 识别用户分析意图、匹配数据源、梳理所需字段、生成标准化分析计划

**核心逻辑**:
1. 解析用户自然语言查询
2. 匹配数据源字段
3. 根据关键词生成分析步骤
4. 判断是否需要追问

**关键词映射**:
| 关键词类型 | 关键词示例 | 对应工具 |
|-----------|-----------|---------|
| 数值统计 | 统计、平均、总和、最大、最小 | stat_analysis |
| 趋势分析 | 趋势、变化、增长、下降、环比、同比 | stat_analysis |
| 异常检测 | 异常、问题、波动、突变 | anomaly_detection |
| 对比分析 | 对比、比较、差异 | stat_analysis |
| 可视化 | 图表、图、可视化 | chart_generator |

#### 3.1.3 DataAnalysisAgent

**职责**: 执行数据查询、统计计算、指标核算、数据异常识别

**核心逻辑**:
1. 接收分析计划
2. 依次调用对应工具
3. 收集工具执行结果
4. 生成分析摘要

#### 3.1.4 ReportGenerationAgent

**职责**: 生成通俗易懂的业务结论、图表解读、优化建议

**核心逻辑**:
1. 整合分析结果
2. 生成可视化图表
3. 生成业务建议
4. 输出结构化报告

### 3.2 服务模块 (Services)

#### 3.2.1 LLM Service (llm_service.py)

**职责**: 提供统一的大语言模型调用接口

**核心功能**:
| 方法 | 功能 | 说明 |
|------|------|------|
| `chat()` | 对话生成 | 支持中英文双语 |
| `get_structured_output()` | 结构化输出 | 返回JSON格式结果 |

#### 3.2.2 LLM Chart Selector (llm_chart_selector.py)

**职责**: 由LLM智能决定是否需要图表及图表类型

**核心功能**:
| 方法 | 功能 | 说明 |
|------|------|------|
| `analyze_and_select_charts()` | 分析并选择图表 | 基于用户问题和数据特征 |
| `_generate_data_summary()` | 生成数据摘要 | 包含统计信息和异常数据 |

**决策流程**:
1. 接收用户问题、数据摘要、最大图表数量
2. 调用LLM分析是否需要图表
3. 如果需要，返回图表类型和建议
4. 如果不需要，返回空列表

#### 3.2.3 Enhanced Chart Generator (enhanced_chart_generator.py)

**职责**: 基于LLM决策生成ECharts图表配置

**核心功能**:
| 方法 | 功能 | 说明 |
|------|------|------|
| `generate_charts()` | 生成图表 | 完全由LLM决定 |
| `_fill_chart_data()` | 填充数据 | 将数据映射到图表配置 |

**支持的图表类型**:
- 折线图 (line)
- 柱状图 (bar)
- 散点图 (scatter)
- 饼图 (pie)

#### 3.2.4 Context Service (context_service.py)

**职责**: 管理对话上下文，支持多轮对话

**核心功能**:
| 方法 | 功能 | 说明 |
|------|------|------|
| `get_context()` | 获取上下文 | 返回历史对话记录 |
| `add_to_context()` | 添加消息 | 追加用户/助手消息 |

#### 3.2.5 Observability Service (observability_service.py)

**职责**: 记录和分析系统执行日志

**核心功能**:
| 方法 | 功能 | 说明 |
|------|------|------|
| `log_execution()` | 记录执行 | 记录Agent/Tool执行 |
| `get_execution_trace()` | 获取追踪 | 返回完整执行链路 |

### 3.3 工具模块

#### 3.3.1 BaseTool 基类

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `execute()` | 执行工具 | `**kwargs` | `Any` |
| `get_schema()` | 获取工具Schema | 无 | `dict` |
| `validate_parameters()` | 验证参数 | `**kwargs` | `bool` |

#### 3.3.2 工具列表

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `data_reader` | 读取数据源数据 | `data_source_id`, `filter_conditions`, `sort_by`, `limit` |
| `structure_check` | 检测数据结构 | `data_source_id` |
| `stat_analysis` | 统计分析 | `data_source_id`, `target_columns`, `group_by` |
| `anomaly_detection` | 异常检测 | `data_source_id`, `target_column`, `time_column`, `method` |
| `chart_generator` | 图表生成 | `data_source_id`, `chart_type`, `x_column`, `y_column`, `group_column`, `title` |
| `report_generator` | 报告生成 | `analysis_result`, `report_type`, `include_charts` |

### 3.3 数据模型

#### 3.3.1 数据库表结构

**data_sources 表**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 数据源名称 |
| filename | VARCHAR | 文件名 |
| filepath | VARCHAR | 文件路径 |
| file_type | VARCHAR | 文件类型 |
| columns | JSON | 字段列表 |
| row_count | INTEGER | 行数 |
| size_bytes | INTEGER | 文件大小 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**analysis_records 表**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| data_source_id | INTEGER | 数据源ID |
| user_query | TEXT | 用户查询 |
| analysis_plan | JSON | 分析计划 |
| tool_calls | JSON | 工具调用记录 |
| final_result | JSON | 最终结果 |
| report_content | TEXT | 报告内容 |
| status | VARCHAR | 状态 |
| created_at | DATETIME | 创建时间 |

**tool_call_logs 表**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| analysis_record_id | INTEGER | 分析记录ID |
| tool_name | VARCHAR | 工具名称 |
| input_params | JSON | 输入参数 |
| output_result | JSON | 输出结果 |
| execution_time_ms | INTEGER | 执行时间(毫秒) |
| timestamp | DATETIME | 时间戳 |

**conversations 表**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| session_id | VARCHAR | 会话ID |
| user_message | TEXT | 用户消息 |
| assistant_message | TEXT | 助手回复 |
| context | JSON | 上下文 |
| created_at | DATETIME | 创建时间 |

## 4. API接口设计

### 4.1 数据管理接口

| 接口路径 | HTTP方法 | 功能描述 |
|----------|----------|----------|
| `/api/data/upload` | POST | 上传数据文件 |
| `/api/data/sources` | GET | 获取数据源列表 |
| `/api/data/sources/{id}` | GET | 获取数据源详情 |
| `/api/data/sources/{id}/preview` | GET | 获取数据预览 |
| `/api/data/sources/{id}` | DELETE | 删除数据源 |

### 4.2 分析服务接口

| 接口路径 | HTTP方法 | 功能描述 |
|----------|----------|----------|
| `/api/analysis/execute` | POST | 执行数据分析 |
| `/api/analysis/history` | GET | 获取分析历史 |
| `/api/analysis/{id}` | GET | 获取分析详情 |

### 4.3 聊天服务接口

| 接口路径 | HTTP方法 | 功能描述 |
|----------|----------|----------|
| `/api/chat/message` | POST | 发送消息 |

### 4.4 工具列表接口

| 接口路径 | HTTP方法 | 功能描述 |
|----------|----------|----------|
| `/api/tools/list` | GET | 获取工具列表 |

## 5. 部署与运行

### 5.1 环境依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.110+ | Web框架 |
| Uvicorn | 0.29+ | ASGI服务器 |
| Pandas | 2.2+ | 数据处理 |
| NumPy | 1.26+ | 数值计算 |
| SciPy | 1.12+ | 科学计算 |
| ECharts | 5.x | 前端可视化 |
| SQLAlchemy | 2.0+ | ORM |
| OpenAI | 1.13+ | 大模型API |
| PyYAML | 6.0+ | YAML配置解析 |

### 5.2 配置说明

环境变量配置文件 `.env`:

```env
LLM_API_KEY=your_api_key_here    # 大模型API密钥
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1    # API基础地址(阿里云通义千问)
LLM_MODEL=qwen-plus              # 模型名称
LLM_TEMPERATURE=0.1              # 生成温度
LLM_PROVIDER=aliyun              # 提供商(aliyun/openai)
```

### 5.3 启动命令

```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 6. 安全性考虑

1. **文件上传安全**: 限制文件类型为CSV/Excel，校验文件大小
2. **输入验证**: 所有API参数进行严格验证
3. **日志脱敏**: 日志中不记录敏感数据
4. **错误处理**: 统一异常处理，避免暴露系统信息
5. **CORS配置**: 限制跨域访问来源

## 7. AI Prompt 配置

### 7.1 Prompt 文件结构

```
app/prompts/
├── __init__.py
├── data_understanding_agent_prompt.yaml   # 数据理解Agent Prompt
├── data_analysis_agent_prompt.yaml         # 数据分析Agent Prompt
└── report_generation_agent_prompt.yaml     # 报告生成Agent Prompt
```

### 7.2 Prompt 配置说明

| 文件 | 对应Agent | 主要功能 |
|------|-----------|----------|
| `data_understanding_agent_prompt.yaml` | DataUnderstandingAgent | 意图识别、字段匹配、分析计划生成 |
| `data_analysis_agent_prompt.yaml` | DataAnalysisAgent | 数据统计、异常检测、指标计算 |
| `report_generation_agent_prompt.yaml` | ReportGenerationAgent | 报告结构、洞察总结、业务建议 |

### 7.3 Prompt 设计原则

1. **双语支持**: 所有Prompt支持中英文输入和输出
2. **结构化输出**: 定义清晰的输出格式要求
3. **角色定义**: 明确定义Agent的角色和能力
4. **约束条件**: 设置输出长度和格式限制

## 8. 扩展性设计

1. **插件化工具**: 工具采用统一接口，易于扩展新工具
2. **多模型支持**: 支持接入多种大模型（阿里云、OpenAI等）
3. **配置化**: 智能体行为通过YAML配置文件管理
4. **可观测性**: 完整的执行日志和追踪能力