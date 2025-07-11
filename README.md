# habby-agent-assistant

**智能助手工具集合项目**

## 🎯 项目概述

`habby-agent-assistant` 是一个模块化的智能助手工具集合项目，包含多个独立的工具模块，每个模块都专注于特定的任务处理能力。

## 🏗️ 项目架构

```
habby-agent-assistant/
├── 📂 doc2md-s3/                 # 高级 PDF 转 Markdown 工具
│   ├── lambda_function.py        # 主 Lambda 处理器
│   ├── s3_handler.py            # S3 文件操作
│   ├── docling_processor.py     # Docling 文档处理
│   ├── markdown_optimizer.py    # Markdown 优化
│   ├── metadata_analyzer.py     # 元数据分析
│   ├── test_local.py           # 本地测试
│   ├── deploy.sh               # 部署脚本
│   └── README.md               # 详细文档
├── 📂 pdf2md/                   # 基础 PDF 转 Markdown 工具
│   ├── lambda_function.py       # 基于 PyMuPDF 的实现
│   ├── requirements.txt         # 依赖配置
│   └── README.md               # 工具文档
├── 📂 test_data/                # 共享测试数据
├── 📂 venv/                     # Python 虚拟环境
└── 📄 README.md                 # 项目总览
```

## 🛠️ 工具模块

### 1. doc2md-s3 - 高级 PDF 转 Markdown 工具

**基于 Docling 的高级 PDF 处理工具，支持 S3 集成**

- 🔄 **高质量转换**: 使用 Docling 进行先进的 PDF 解析
- 📊 **表格支持**: 完整保留表格结构和格式
- 🗂️ **S3 集成**: 使用 S3 作为输入输出存储
- 📈 **详细元数据**: 提供完整的处理报告和文档分析
- 🏗️ **结构化日志**: 符合 JSON 格式的结构化日志输出

**使用场景**: 企业级文档处理、复杂 PDF 转换、批量处理

### 2. pdf2md - 基础 PDF 转 Markdown 工具

**基于 PyMuPDF 的轻量级 PDF 处理工具**

- ⚡ **轻量快速**: 基于 PyMuPDF，处理速度快
- 📝 **简单转换**: 直接的 PDF 到 Markdown 转换
- 🔧 **易于部署**: 依赖少，部署简单

**使用场景**: 简单文档转换、快速原型、轻量级处理

## 🚀 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd habby-agent-assistant

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖（根据需要的工具）
cd doc2md-s3
pip install -r requirements.txt
```

### 使用工具

#### doc2md-s3 工具

```bash
cd doc2md-s3
python test_local.py  # 本地测试
./deploy.sh          # 部署到 AWS Lambda
```

#### pdf2md 工具

```bash
cd pdf2md
python test_local.py  # 本地测试
```

## 📋 工具对比

| 特性 | doc2md-s3 | pdf2md |
|------|-----------|---------|
| 处理引擎 | Docling | PyMuPDF |
| 表格支持 | ✅ 完整保留 | ❌ 基础提取 |
| OCR 支持 | ✅ 内置 | ❌ 无 |
| S3 集成 | ✅ 原生支持 | ❌ 无 |
| 元数据分析 | ✅ 详细报告 | ❌ 基础信息 |
| 部署大小 | ~200MB | ~50MB |
| 处理速度 | 中等 | 快速 |
| 适用场景 | 企业级 | 简单转换 |

## 🔧 开发规范

### 日志格式

所有工具都采用结构化 JSON 日志格式：

```json
{
  "timestamp": "2025-07-11T06:45:46Z",
  "level": "INFO",
  "service": "tool-name",
  "action": "operation",
  "result": "success",
  "processingTime": "9.14s"
}
```

### 模块结构

每个工具模块都遵循以下结构：
- `lambda_function.py` - 主处理器
- `requirements.txt` - 依赖配置
- `test_local.py` - 本地测试
- `deploy.sh` - 部署脚本
- `README.md` - 详细文档

## 🎯 未来规划

### 计划添加的工具

- **img2md**: 图片转 Markdown 工具
- **web2md**: 网页转 Markdown 工具
- **audio2text**: 音频转文本工具
- **video2summary**: 视频摘要工具
- **text2speech**: 文本转语音工具

### 增强功能

- 统一的 API 接口
- 工具链编排
- 批量处理支持
- 监控和告警
- 性能优化

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 遵循代码规范
4. 添加测试用例
5. 提交 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源。

---

**habby-agent-assistant** - 让智能助手工具触手可及！ 