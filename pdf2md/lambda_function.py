import json
import base64
import tempfile
import os
import ssl
import time
from typing import Dict, Any

# Fix SSL certificate verification issue for Lambda environment
ssl._create_default_https_context = ssl._create_unverified_context

from docling.document_converter import DocumentConverter

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for PDF to Markdown conversion
    
    Args:
        event: Lambda event containing PDF data
        context: Lambda context object
        
    Returns:
        dict: Response with markdown content or error message
    """
    
    # 结构化日志记录
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "service": "pdf2md-lambda",
        "action": "convert_pdf_to_markdown",
        "requestId": context.aws_request_id if context else "local-test"
    }
    
    try:
        # 验证输入
        if not event or 'pdf_content' not in event:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": "Missing pdf_content in event"
            }
            print(json.dumps(error_log))
            
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing pdf_content in event',
                    'message': 'Please provide PDF content as base64 encoded string'
                })
            }
        
        # 获取PDF内容和选项
        pdf_content_b64 = event['pdf_content']
        options = event.get('options', {})
        filename = event.get('filename', 'document.pdf')
        
        # 记录开始处理
        start_time = time.time()
        process_log = {
            **log_entry,
            "filename": filename,
            "hasOptions": bool(options)
        }
        print(json.dumps(process_log))
        
        # 解码PDF内容
        try:
            pdf_content = base64.b64decode(pdf_content_b64)
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": f"Failed to decode base64 PDF content: {str(e)}"
            }
            print(json.dumps(error_log))
            
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid base64 PDF content',
                    'message': str(e)
                })
            }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_pdf_path = temp_file.name
        
        try:
            # 初始化文档转换器
            converter = DocumentConverter()
            
            # 转换PDF
            result = converter.convert(temp_pdf_path)
            
            # 导出为Markdown
            markdown_content = result.document.export_to_markdown()
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 生成元数据
            metadata = {
                "filename": filename,
                "processing_time": f"{processing_time:.2f}s",
                "page_count": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                "content_length": len(markdown_content),
                "status": "success"
            }
            
            # 记录成功日志
            success_log = {
                **log_entry,
                "result": "success",
                "filename": filename,
                "processingTime": f"{processing_time:.2f}s",
                "pageCount": metadata["page_count"],
                "contentLength": metadata["content_length"]
            }
            print(json.dumps(success_log))
            
            # 返回成功响应
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'markdown_content': markdown_content,
                    'metadata': metadata
                }, ensure_ascii=False)
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
    
    except Exception as e:
        # 记录错误日志
        error_log = {
            **log_entry,
            "level": "ERROR",
            "result": "fail",
            "errorMessage": str(e),
            "stackTrace": str(e.__class__.__name__)
        }
        print(json.dumps(error_log))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def create_test_event(pdf_file_path: str) -> Dict[str, Any]:
    """
    Create a test event for local testing
    
    Args:
        pdf_file_path: Path to the PDF file
        
    Returns:
        dict: Test event structure
    """
    with open(pdf_file_path, 'rb') as f:
        pdf_content = f.read()
    
    return {
        'pdf_content': base64.b64encode(pdf_content).decode('utf-8'),
        'filename': os.path.basename(pdf_file_path),
        'options': {
            'preserve_formatting': True,
            'extract_images': False
        }
    }

# 本地测试代码
if __name__ == "__main__":
    # 模拟Lambda context
    class MockContext:
        aws_request_id = "test-request-123"
    
    # 创建测试事件
    test_pdf = "../test_data/美术外包合同审核共同点AI总结-V3.pdf"
    
    if os.path.exists(test_pdf):
        print("🧪 Testing Lambda function locally...")
        
        event = create_test_event(test_pdf)
        context = MockContext()
        
        # 调用Lambda函数
        response = lambda_handler(event, context)
        
        print(f"Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"✅ Success! Content length: {len(body['markdown_content'])} characters")
            print(f"📊 Metadata: {body['metadata']}")
            print(f"📝 Preview: {body['markdown_content'][:200]}...")
        else:
            print(f"❌ Error: {response['body']}")
    else:
        print(f"❌ Test file not found: {test_pdf}") 