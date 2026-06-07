# AI智能数据分析系统

基于多智能体的企业轻量化智能数据分析平台，实现自然语言提问、自动数据解析、智能统计分析、异常检测、图表可视化、自动化报告生成的全流程闭环。

## 功能特性

### 1. 基础数据能力
- 支持 Excel/CSV 文件上传接入
- 数据自动预览、字段识别、结构解析

### 2. 自然语言智能问答分析
- 用户通过自然语言提出业务数据分析问题
- 系统自动完成意图识别、数据匹配、分析逻辑生成
- 输出可视化结果与通俗化业务解读

### 3. 多智能体核心设计
- **数据理解Agent**: 识别用户分析意图、匹配数据源、生成标准化分析计划
- **数据分析Agent**: 执行数据查询、统计计算、指标核算、数据异常识别
- **报告生成Agent**: 生成通俗易懂的业务结论、图表解读、优化建议

### 4. Tool Calling工具调用
- 数据读取工具
- 结构检测工具
- 统计分析工具
- 异常检测工具
- 图表生成工具
- 报告生成工具

### 5. 核心智能化能力
- 多步骤任务规划
- 智能图表生成
- 数据异常洞察（环比、同比、突变、极值异常）
- 多轮上下文追问
- 执行过程可观测

## 技术栈

- **后端**: Python 3.10+, FastAPI
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **数据处理**: Pandas, NumPy, SciPy
- **可视化**: Plotly, Matplotlib
- **大模型**: LangChain, OpenAI API
- **前端**: HTML5, JavaScript (单页应用)

## 快速开始

### 环境要求
- Python 3.10+
- pip 20.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
DATA_DIR=data
STATIC_DIR=app/static
LOG_DIR=logs
DATABASE_URL=sqlite:///./data/example_db.sqlite
DEBUG=true
```

### 启动服务

```bash
python main.py
```

服务将在 http://localhost:8000 启动

### 访问前端页面

打开 `frontend/index.html` 文件或在浏览器中访问 http://localhost:8000/static/index.html

## API接口

### 数据管理

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/data/upload` | POST | 上传数据文件 |
| `/api/data/sources` | GET | 获取数据源列表 |
| `/api/data/sources/{id}` | GET | 获取数据源详情 |
| `/api/data/sources/{id}/preview` | GET | 获取数据预览 |
| `/api/data/sources/{id}` | DELETE | 删除数据源 |

### 分析服务

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/analysis/execute` | POST | 执行数据分析 |
| `/api/analysis/history` | GET | 获取分析历史 |
| `/api/analysis/{id}` | GET | 获取分析详情 |

### 聊天服务

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/chat/message` | POST | 发送消息 |

### 工具列表

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/tools/list` | GET | 获取工具列表 |

## 项目结构

```
├── app/                    # 应用主目录
│   ├── agents/             # 智能体模块
│   │   ├── base_agent.py           # Agent基类
│   │   ├── data_understanding_agent.py  # 数据理解Agent
│   │   ├── data_analysis_agent.py      # 数据分析Agent
│   │   ├── report_generation_agent.py  # 报告生成Agent
│   │   └── agent_coordinator.py        # 智能体协调器
│   ├── tools/              # 工具调用模块
│   │   ├── base_tool.py             # Tool基类
│   │   ├── data_tools.py            # 数据工具
│   │   ├── anomaly_tools.py         # 异常检测工具
│   │   ├── chart_tools.py           # 图表生成工具
│   │   └── report_tools.py          # 报告生成工具
│   ├── services/           # 业务服务
│   │   └── data_service.py          # 数据服务
│   ├── api/                # API接口
│   │   └── router.py                # 路由定义
│   ├── models/             # 数据模型
│   │   ├── database.py              # 数据库模型
│   │   └── schemas.py               # Pydantic schemas
│   ├── utils/              # 工具函数
│   │   └── logger.py                # 日志工具
│   └── static/             # 静态资源
├── frontend/               # 前端代码
│   └── index.html          # 主页面
├── data/                   # 数据目录（示例数据文件）
├── docs/                   # 文档目录
│   ├── agent_design.md          # Agent智能体设计文档
│   ├── tool_calling_schema.md   # Tool Calling工具调用Schema文档
│   ├── technical_design.md      # 系统技术设计文档
│   ├── deployment_guide.md      # 项目部署说明文档
│   ├── deliverables.md          # 项目交付物清单
│   ├── sample_report.md         # 系统自动生成的分析报告样例
│   ├── iteration_history.md     # 功能迭代记录
│   └── demo_materials.md        # 项目演示材料
├── test_results/           # 测试结果（截图和日志）
├── .env                    # 环境变量配置
├── requirements.txt        # 依赖列表
├── main.py                 # 启动文件
└── README.md               # 项目说明
```

## 使用示例

### 1. 上传数据

```bash
curl -X POST http://localhost:8000/api/data/upload \
  -F "file=@sales_data.csv"
```

### 2. 执行分析

```bash
curl -X POST http://localhost:8000/api/analysis/execute \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "user_query": "分析销售额的统计数据，检测异常值"
  }'
```

### 3. 获取分析结果

```bash
curl http://localhost:8000/api/analysis/1
```

## 许可证

MIT License

# digital-data-analyst

