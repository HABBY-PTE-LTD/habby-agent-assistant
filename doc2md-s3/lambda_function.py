"""
Simplified doc2md-s3 Lambda Function
Directly uses Docling output without additional optimization
"""

import json
import time
import os
from typing import Dict, Any

# Import our custom modules
from s3_handler import S3Handler
from docling_processor import DoclingProcessor

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified Lambda handler for doc2md-s3 processing
    
    Args:
        event: Lambda event containing S3 paths
        context: Lambda context object
        
    Returns:
        Dict: Response with processing results
    """
    
    # Create base log entry
    request_id = context.aws_request_id if context else "local-test"
    start_time = time.time()
    
    # Temporary files tracking
    temp_files = []
    
    try:
        # Validate input event
        validation_result = validate_event(event)
        if not validation_result["valid"]:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Invalid input",
                    "message": validation_result["error"],
                    "request_id": request_id
                })
            }
        
        # Extract event parameters
        source_bucket = event["source_bucket"]
        source_key = event["source_key"]
        output_bucket = event["output_bucket"]
        output_key = event["output_key"]
        
        # Initialize handlers
        s3_handler = S3Handler()
        docling_processor = DoclingProcessor()
        
        # Step 1: Get source file info (including version)
        source_file_info = s3_handler.get_object_info(source_bucket, source_key)
        
        # Step 2: Download PDF from S3
        temp_pdf_path = s3_handler.create_temp_file(suffix='.pdf')
        temp_files.append(temp_pdf_path)
        
        download_success = s3_handler.download_file(source_bucket, source_key, temp_pdf_path)
        if not download_success:
            raise Exception("Failed to download PDF from S3")
        
        # Step 3: Process document with Docling
        docling_result = docling_processor.process_document(temp_pdf_path)
        
        if not docling_result.get("success", False):
            raise Exception(f"Document processing failed: {docling_result.get('error', 'Unknown error')}")
        
        # Get the raw markdown content from Docling
        markdown_content = docling_result["markdown_content"]
        
        # Step 4: Upload markdown to S3
        markdown_upload_success = s3_handler.upload_content(
            bucket=output_bucket,
            key=output_key,
            content=markdown_content,
            content_type='text/markdown'
        )
        
        if not markdown_upload_success:
            raise Exception("Failed to upload markdown to S3")
        
        # Calculate total processing time
        total_time = time.time() - start_time
        
        # Create metadata with source file version info
        metadata = {
            "source_file": {
                "s3_uri": f"s3://{source_bucket}/{source_key}",
                "version_id": source_file_info.get("version_id", "null"),
                "etag": source_file_info.get("etag", ""),
                "last_modified": source_file_info.get("last_modified", ""),
                "content_length": source_file_info.get("content_length", 0),
                "content_type": source_file_info.get("content_type", "")
            },
            "output_file": f"s3://{output_bucket}/{output_key}",
            "processing_time": f"{total_time:.2f}s",
            "docling_processing_time": f"{docling_result.get('processing_time', 0):.2f}s",
            "page_count": docling_result["document_info"].get("page_count", 0),
            "content_length": len(markdown_content),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Upload metadata if metadata key is provided
        metadata_key = event.get("metadata_key")
        if metadata_key:
            metadata_upload_success = s3_handler.upload_content(
                bucket=output_bucket,
                key=metadata_key,
                content=json.dumps(metadata, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            
            if not metadata_upload_success:
                print("Warning: Failed to upload metadata to S3")
        
        # Success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "request_id": request_id,
                "outputs": {
                    "markdown_s3_uri": f"s3://{output_bucket}/{output_key}",
                    "metadata_s3_uri": f"s3://{output_bucket}/{metadata_key}" if metadata_key else None
                },
                "processing_summary": metadata
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        # Error response
        error_message = str(e)
        print(f"Error: {error_message}")
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Processing failed",
                "message": error_message,
                "request_id": request_id
            })
        }
        
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
    
    return {"valid": True}