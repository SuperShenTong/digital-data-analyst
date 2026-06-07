# AI智能数据分析系统 - 项目部署说明文档

## 1. 项目概述

本项目是基于多智能体技术的企业轻量化智能数据分析平台，实现自然语言提问、自动数据解析、智能统计分析、异常检测、图表可视化、自动化报告生成的全流程闭环。

## 2. 环境要求

### 2.1 硬件要求
- CPU: 双核以上
- 内存: 4GB以上
- 存储: 至少1GB可用空间

### 2.2 软件要求
| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| pip | 20.0+ | 包管理工具 |
| Git | 2.0+ | 版本控制 |

## 3. 安装步骤

### 3.1 克隆项目

```bash
git clone <repository-url>
cd digital-data-analyst_v1
```

### 3.2 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3.3 安装依赖

```bash
pip install -r requirements.txt
```

### 3.4 配置环境变量

创建 `.env` 文件：

```env
# 大模型配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 阿里云通义千问配置（可选）
QIANWEN_API_KEY=your_qianwen_api_key_here
DASHSCOPE_API_KEY=your_dashscope_key_here

# 应用配置
DATA_DIR=data
STATIC_DIR=app/static
LOG_DIR=logs
DATABASE_URL=sqlite:///./data/example_db.sqlite
DEBUG=true
```

> **注意**: 请将 `your_openai_api_key_here` 替换为您的实际API密钥

## 4. 启动服务

### 4.1 开发模式

```bash
python main.py
```

服务将在 http://localhost:8000 启动。

### 4.2 生产模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4.3 使用启动脚本

```bash
# Windows
start.bat

# Linux/Mac
bash start.sh
```

## 5. 访问系统

### 5.1 前端界面

打开浏览器访问：
- 主页面: http://localhost:8000
- 或直接打开本地文件: `frontend/index.html`

### 5.2 API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/data/upload` | POST | 上传数据文件 |
| `/api/data/sources` | GET | 获取数据源列表 |
| `/api/analysis/execute` | POST | 执行数据分析 |
| `/api/analysis/history` | GET | 获取分析历史 |
| `/api/tools/list` | GET | 获取工具列表 |

## 6. 快速上手

### 6.1 上传数据

1. 点击"数据管理"菜单
2. 选择CSV或Excel文件上传
3. 等待文件解析完成

### 6.2 执行分析

1. 选择已上传的数据源
2. 在"快速分析"输入框中输入问题
3. 例如："分析销售数据是否存在异常"
4. 点击"开始分析"按钮
5. 等待分析完成，查看报告和图表

### 6.3 示例问题

```
- 分析销售额的统计数据
- 检测销售数据中的异常值
- 分析销售趋势
- 对比不同地区的销售情况
```

## 7. 项目结构

```
digital-data-analyst_v1/
├── app/                    # 应用主目录
│   ├── agents/             # 智能体模块
│   ├── tools/              # 工具调用模块
│   ├── services/           # 业务服务
│   ├── api/                # API接口
│   ├── models/             # 数据模型
│   ├── prompts/            # 提示词配置
│   ├── utils/              # 工具函数
│   └── static/             # 静态资源
├── frontend/               # 前端代码
├── data/                   # 数据目录
├── docs/                   # 文档目录
├── test_results/           # 测试结果
├── main.py                 # 启动文件
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
```

## 8. 配置说明

### 8.1 数据库配置

默认使用SQLite数据库，数据库文件位于 `data/example_db.sqlite`。

如需使用PostgreSQL，修改 `.env` 文件：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 8.2 日志配置

日志文件存储在 `logs/` 目录下，包含：
- 应用日志
- Agent执行日志
- 工具调用日志

### 8.3 数据存储

上传的文件存储在 `data/` 目录下，支持：
- CSV文件 (.csv)
- Excel文件 (.xlsx, .xls)

## 9. 故障排除

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 依赖安装失败 | 网络问题或Python版本不兼容 | 检查网络连接，确保Python 3.10+ |
| API调用失败 | API密钥配置错误 | 检查 `.env` 文件中的API密钥 |
| 数据上传失败 | 文件格式不正确 | 确保上传CSV/Excel文件 |
| 图表不显示 | 前端加载问题 | 检查浏览器控制台错误信息 |

### 9.2 日志查看

```bash
# 查看应用日志
cat logs/app.log

# 查看Agent执行日志
cat logs/agent.log
```

### 9.3 重置数据库

```bash
# 删除数据库文件（会清除所有数据）
rm data/example_db.sqlite

# 重启服务，系统会自动创建新数据库
python main.py
```

## 10. 维护与更新

### 10.1 更新代码

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 10.2 备份数据

```bash
# 备份数据库
cp data/example_db.sqlite data/example_db_backup.sqlite

# 备份上传文件
zip -r data_backup.zip data/
```

## 11. 技术支持

如有问题，请联系技术支持团队或查看项目文档目录 `docs/` 获取详细信息。

## 12. 许可证

MIT License - 详见 LICENSE 文件
