# PDF to Markdown Converter Lambda

使用 [Docling](https://github.com/docling-project/docling) 实现的 PDF 转 Markdown 的 AWS Lambda 函数。

## 功能特性

- 🔄 **高质量转换**: 使用 Docling 进行 PDF 解析和 Markdown 转换
- 📊 **详细元数据**: 提供处理时间、页数、内容长度等信息
- 🏗️ **结构化日志**: 符合 JSON 格式的结构化日志输出
- 🔒 **错误处理**: 完善的错误处理和异常捕获
- 🧪 **本地测试**: 支持本地测试和调试

## 项目结构

```
pdf2md/
├── lambda_function.py      # Lambda 函数主文件
├── test_local_fixed.py     # 本地测试脚本
├── requirements.txt        # Python 依赖
├── deploy.sh              # 部署脚本
├── README.md              # 项目说明
└── output/                # 输出目录
    ├── *.md               # 转换后的 Markdown 文件
    └── *_metadata.json    # 元数据文件
```

## 本地开发

### 1. 环境设置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install docling
```

### 2. 本地测试

```bash
# 测试单个 PDF 文件
python test_local_fixed.py

# 测试 Lambda 函数
python lambda_function.py
```

### 3. 测试结果

本地测试成功转换了测试文件：
- **文件**: `美术外包合同审核共同点AI总结-V3.pdf`
- **页数**: 2 页
- **处理时间**: ~10-21 秒
- **输出长度**: 1976 字符

## Lambda 部署

### 1. 前置条件

- 配置 AWS CLI 和相应的 IAM 权限
- 创建 Lambda 执行角色 `lambda-execution-role`

### 2. 部署命令

```bash
# 使用部署脚本
./deploy.sh

# 或手动部署
pip install -r requirements.txt -t package/
cp lambda_function.py package/
cd package && zip -r ../lambda-deployment.zip .
aws lambda create-function --function-name pdf2md-converter ...
```

### 3. 函数配置

- **运行时**: Python 3.9
- **内存**: 3008 MB
- **超时**: 300 秒 (5 分钟)
- **处理器**: `lambda_function.lambda_handler`

## API 使用

### 请求格式

```json
{
  "pdf_content": "base64_encoded_pdf_data",
  "filename": "document.pdf",
  "options": {
    "preserve_formatting": true,
    "extract_images": false
  }
}
```

### 响应格式

**成功响应 (200)**:
```json
{
  "markdown_content": "# 标题\n\n内容...",
  "metadata": {
    "filename": "document.pdf",
    "processing_time": "10.08s",
    "page_count": 2,
    "content_length": 1976,
    "status": "success"
  }
}
```

**错误响应 (4xx/5xx)**:
```json
{
  "error": "错误类型",
  "message": "详细错误信息"
}
```

## 日志格式

所有日志采用结构化 JSON 格式：

```json
{
  "timestamp": "2025-07-11T05:57:40Z",
  "level": "INFO",
  "service": "pdf2md-lambda",
  "action": "convert_pdf_to_markdown",
  "requestId": "test-request-123",
  "result": "success",
  "filename": "document.pdf",
  "processingTime": "10.08s",
  "pageCount": 2,
  "contentLength": 1976
}
```

## 性能说明

- **首次调用**: 需要下载 Docling 模型，可能需要额外时间
- **后续调用**: 模型已缓存，处理速度较快
- **内存使用**: 建议配置 3GB 以上内存
- **处理时间**: 取决于 PDF 复杂度，通常 10-30 秒

## 注意事项

1. **SSL 证书**: 代码中包含 SSL 证书验证绕过，适用于 Lambda 环境
2. **临时文件**: 使用临时文件处理 PDF，自动清理
3. **中文支持**: 完全支持中文 PDF 和 Markdown 输出
4. **错误处理**: 包含完善的错误处理和日志记录

## 依赖说明

- **docling**: 主要的 PDF 解析和转换库
- **boto3**: AWS SDK (Lambda 环境中已预装)
- **标准库**: json, base64, tempfile, os, ssl, time

## 许可证

本项目基于 MIT 许可证。Docling 库遵循其原始许可证。 