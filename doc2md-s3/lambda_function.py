"""
doc2md-s3 Lambda Function
Main Lambda handler for PDF to Markdown conversion using S3 storage
"""

import json
import time
import os
from typing import Dict, Any

# Import our custom modules
from s3_handler import S3Handler
from docling_processor import DoclingProcessor
from markdown_optimizer import MarkdownOptimizer
from metadata_analyzer import MetadataAnalyzer

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for doc2md-s3 processing
    
    Args:
        event: Lambda event containing S3 paths and options
        context: Lambda context object
        
    Returns:
        Dict: Response with processing results
    """
    
    # Initialize processing times tracking
    processing_times = {
        "s3_download": 0.0,
        "docling_processing": 0.0,
        "markdown_optimization": 0.0,
        "s3_upload": 0.0
    }
    
    # Create base log entry
    request_id = context.aws_request_id if context else "local-test"
    base_log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "service": "doc2md-s3",
        "action": "lambda_handler",
        "requestId": request_id
    }
    
    # Log processing start
    start_log = {
        **base_log,
        "message": "Starting doc2md-s3 processing",
        "event": event
    }
    print(json.dumps(start_log))
    
    # Initialize components
    s3_handler = None
    temp_files = []
    
    try:
        # Validate input event
        validation_result = validate_event(event)
        if not validation_result["valid"]:
            error_response = {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Invalid input",
                    "message": validation_result["error"],
                    "request_id": request_id
                })
            }
            
            error_log = {
                **base_log,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": validation_result["error"]
            }
            print(json.dumps(error_log))
            return error_response
        
        # Extract event parameters
        source_bucket = event["source_bucket"]
        source_key = event["source_key"]
        output_bucket = event["output_bucket"]
        output_key = event["output_key"]
        metadata_key = event.get("metadata_key", output_key.replace('.md', '_metadata.json'))
        options = event.get("options", {})
        
        # Initialize handlers
        s3_handler = S3Handler()
        docling_processor = DoclingProcessor(options)
        markdown_optimizer = MarkdownOptimizer(options)
        metadata_analyzer = MetadataAnalyzer(options)
        
        # Step 1: Download PDF from S3
        download_start = time.time()
        temp_pdf_path = s3_handler.create_temp_file(suffix='.pdf')
        temp_files.append(temp_pdf_path)
        
        download_success = s3_handler.download_file(source_bucket, source_key, temp_pdf_path)
        if not download_success:
            raise Exception("Failed to download PDF from S3")
        
        processing_times["s3_download"] = time.time() - download_start
        
        # Step 2: Process document with Docling
        docling_start = time.time()
        docling_result = docling_processor.process_document(temp_pdf_path)
        
        if not docling_result["success"]:
            raise Exception(f"Docling processing failed: {docling_result.get('error', 'Unknown error')}")
        
        processing_times["docling_processing"] = time.time() - docling_start
        
        # Step 3: Optimize Markdown output
        markdown_start = time.time()
        markdown_content = docling_result["markdown_content"]
        optimization_result = markdown_optimizer.optimize_markdown(markdown_content)
        
        if not optimization_result["success"]:
            # Use original content if optimization fails
            optimized_content = markdown_content
            markdown_stats = {"original_length": len(markdown_content), "optimized_length": len(markdown_content)}
        else:
            optimized_content = optimization_result["optimized_content"]
            markdown_stats = optimization_result["stats"]
        
        processing_times["markdown_optimization"] = time.time() - markdown_start
        
        # Step 4: Generate metadata
        filename = os.path.basename(source_key)
        metadata = metadata_analyzer.generate_metadata(
            filename=filename,
            docling_result=docling_result,
            markdown_stats=markdown_stats,
            processing_times=processing_times
        )
        
        # Step 5: Upload results to S3
        upload_start = time.time()
        
        # Upload Markdown content
        markdown_upload_success = s3_handler.upload_content(
            content=optimized_content,
            bucket=output_bucket,
            key=output_key,
            content_type='text/markdown'
        )
        
        if not markdown_upload_success:
            raise Exception("Failed to upload Markdown to S3")
        
        # Upload metadata
        metadata_json = metadata_analyzer.export_metadata_json(metadata)
        metadata_upload_success = s3_handler.upload_content(
            content=metadata_json,
            bucket=output_bucket,
            key=metadata_key,
            content_type='application/json'
        )
        
        if not metadata_upload_success:
            raise Exception("Failed to upload metadata to S3")
        
        processing_times["s3_upload"] = time.time() - upload_start
        
        # Calculate total processing time
        total_time = sum(processing_times.values())
        
        # Generate processing report
        processing_report = metadata_analyzer.generate_processing_report(metadata, success=True)
        
        # Success response
        success_response = {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "request_id": request_id,
                "outputs": {
                    "markdown_s3_uri": f"s3://{output_bucket}/{output_key}",
                    "metadata_s3_uri": f"s3://{output_bucket}/{metadata_key}"
                },
                "processing_summary": {
                    "total_time": f"{total_time:.2f}s",
                    "page_count": docling_result["document_info"].get("page_count", 0),
                    "content_length": len(optimized_content),
                    "table_count": docling_result["document_info"].get("table_count", 0)
                },
                "performance_metrics": processing_times,
                "processing_report": processing_report
            }, ensure_ascii=False)
        }
        
        # Log success
        success_log = {
            **base_log,
            "result": "success",
            "totalTime": f"{total_time:.2f}s",
            "pageCount": docling_result["document_info"].get("page_count", 0),
            "contentLength": len(optimized_content),
            "outputS3Uri": f"s3://{output_bucket}/{output_key}"
        }
        print(json.dumps(success_log))
        
        return success_response
        
    except Exception as e:
        # Calculate processing time up to failure
        total_time = sum(processing_times.values())
        
        # Error response
        error_response = {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "request_id": request_id,
                "error": str(e),
                "processing_time": f"{total_time:.2f}s",
                "performance_metrics": processing_times
            })
        }
        
        # Log error
        error_log = {
            **base_log,
            "level": "ERROR",
            "result": "fail",
            "totalTime": f"{total_time:.2f}s",
            "errorMessage": str(e)
        }
        print(json.dumps(error_log))
        
        return error_response
        
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            if s3_handler:
                s3_handler.cleanup_temp_file(temp_file)

def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Lambda event structure
    
    Args:
        event: Lambda event to validate
        
    Returns:
        Dict with validation result
    """
    required_fields = ["source_bucket", "source_key", "output_bucket", "output_key"]
    
    for field in required_fields:
        if field not in event:
            return {
                "valid": False,
                "error": f"Missing required field: {field}"
            }
    
    # Validate S3 paths
    s3_handler = S3Handler()
    
    # Validate source path
    source_valid, source_error = s3_handler.validate_s3_path(
        event["source_bucket"], 
        event["source_key"]
    )
    if not source_valid:
        return {
            "valid": False,
            "error": f"Invalid source S3 path: {source_error}"
        }
    
    # Validate output path
    output_valid, output_error = s3_handler.validate_s3_path(
        event["output_bucket"], 
        event["output_key"]
    )
    if not output_valid:
        return {
            "valid": False,
            "error": f"Invalid output S3 path: {output_error}"
        }
    
    # Validate file extension
    if not event["source_key"].lower().endswith('.pdf'):
        return {
            "valid": False,
            "error": "Source file must be a PDF"
        }
    
    if not event["output_key"].lower().endswith('.md'):
        return {
            "valid": False,
            "error": "Output file must have .md extension"
        }
    
    return {"valid": True, "error": None}

def create_test_event(source_bucket: str, source_key: str, 
                     output_bucket: str, output_key: str) -> Dict[str, Any]:
    """
    Create a test event for local testing
    
    Args:
        source_bucket: Source S3 bucket
        source_key: Source S3 key
        output_bucket: Output S3 bucket
        output_key: Output S3 key
        
    Returns:
        Dict: Test event structure
    """
    return {
        "source_bucket": source_bucket,
        "source_key": source_key,
        "output_bucket": output_bucket,
        "output_key": output_key,
        "metadata_key": output_key.replace('.md', '_metadata.json'),
        "options": {
            "ocr_enabled": True,
            "preserve_tables": True,
            "preserve_formatting": True,
            "markdown_optimization": True
        }
    }

# Local testing code
if __name__ == "__main__":
    # Mock context for local testing
    class MockContext:
        aws_request_id = "test-request-123"
        function_name = "doc2md-s3"
        function_version = "1.0.0"
        memory_limit_in_mb = 3008
        remaining_time_in_millis = lambda: 300000
    
    # Test configuration
    print("🧪 Testing doc2md-s3 Lambda function locally...")
    
    # You can modify these values for testing
    test_event = create_test_event(
        source_bucket="my-test-bucket",
        source_key="test-documents/sample.pdf",
        output_bucket="my-output-bucket",
        output_key="processed/sample.md"
    )
    
    print(f"📄 Test event: {json.dumps(test_event, indent=2)}")
    
    # Create mock context
    context = MockContext()
    
    # Run the Lambda function
    try:
        response = lambda_handler(test_event, context)
        print(f"✅ Lambda function completed")
        print(f"📊 Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"🎉 Success! Processing time: {body['processing_summary']['total_time']}")
            print(f"📝 Output: {body['outputs']['markdown_s3_uri']}")
            print(f"📋 Metadata: {body['outputs']['metadata_s3_uri']}")
        else:
            body = json.loads(response['body'])
            print(f"❌ Error: {body.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Local test failed: {str(e)}")
        
    print("\n📝 Note: This is a local test. For actual S3 operations, ensure:")
    print("   - AWS credentials are configured")
    print("   - S3 buckets exist and are accessible")
    print("   - Source PDF file exists in the specified location") 