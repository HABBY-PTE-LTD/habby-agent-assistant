#!/usr/bin/env python3
"""
Simple test script to see raw Docling output without any optimization
"""

import os
import sys
import json
import boto3
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s3_handler import S3Handler
from docling_processor import DoclingProcessor

def test_raw_docling_conversion():
    """Test Docling conversion without any optimization"""
    
    # S3 paths
    source_bucket = "habby-documents-test"
    source_key = "original/finance/美术外包合同审核共同点AI总结-V3.pdf"
    
    print("=" * 50)
    print("Testing Raw Docling Conversion")
    print("=" * 50)
    print(f"Source: s3://{source_bucket}/{source_key}")
    print("-" * 50)
    
    # Initialize handlers
    s3_handler = S3Handler()
    docling_processor = DoclingProcessor()
    
    # Download PDF from S3
    print("\n1. Downloading PDF from S3...")
    temp_pdf_path = s3_handler.create_temp_file(suffix='.pdf')
    
    if not s3_handler.download_file(source_bucket, source_key, temp_pdf_path):
        print("Failed to download PDF from S3")
        return 1
    
    print(f"   Downloaded to: {temp_pdf_path}")
    
    # Process with Docling
    print("\n2. Processing with Docling (raw output)...")
    result = docling_processor.process_document(temp_pdf_path)
    
    if result.get("success", False):
        print(f"   Success! Processing time: {result['processing_time']}")
        print(f"   Page count: {result['document_info']['page_count']}")
        print(f"   Content length: {len(result['markdown_content'])} characters")
        
        # Save raw markdown to file
        output_path = "test_raw_docling_output.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['markdown_content'])
        print(f"\n3. Raw Markdown saved to: {output_path}")
        
        # Save document info
        info_path = "test_raw_docling_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump({
                "document_info": result['document_info'],
                "processing_time": result['processing_time'],
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        print(f"4. Document info saved to: {info_path}")
        
        # Print first 500 characters of content
        print("\n5. First 500 characters of raw Markdown:")
        print("-" * 50)
        print(result['markdown_content'][:500])
        print("-" * 50)
        
    else:
        print(f"   Failed! Error: {result.get('error', 'Unknown error')}")
        return 1
    
    # Cleanup
    s3_handler.cleanup_temp_file(temp_pdf_path)
    
    return 0

if __name__ == "__main__":
    # Set AWS profile
    os.environ['AWS_PROFILE'] = 'AITest'
    os.environ['AWS_REGION'] = 'us-west-2'
    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
    
    # Force boto3 to use the profile
    boto3.setup_default_session(profile_name='AITest')
    
    print("Using AWS Profile: AITest")
    print("Using AWS Region: us-west-2")
    
    exit_code = test_raw_docling_conversion()
    sys.exit(exit_code)