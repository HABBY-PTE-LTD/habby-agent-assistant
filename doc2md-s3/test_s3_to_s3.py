#!/usr/bin/env python3
"""
Test script for S3 to S3 document conversion
Tests the lambda_function with actual S3 files
"""

import json
import sys
import os

# Add the current directory to path so we can import lambda_function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler

def test_s3_conversion():
    """Test converting a PDF from S3 and saving back to S3"""
    
    # Create test event for Lambda with correct format
    event = {
        "source_bucket": "habby-documents-test",
        "source_key": "original/finance/美术外包合同审核共同点AI总结-V3.pdf",
        "output_bucket": "habby-documents-test",
        "output_key": "md/finance/美术外包合同审核共同点AI总结-V3.md",
        "metadata_key": "md/finance/美术外包合同审核共同点AI总结-V3_metadata.json"
    }
    
    # Create mock context
    class MockContext:
        def __init__(self):
            self.aws_request_id = "test-s3-to-s3-conversion"
            self.function_name = "doc2md-s3-test"
            self.memory_limit_in_mb = "1024"
            self.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789:function:doc2md-s3-test"
    
    context = MockContext()
    
    print("Testing S3 to S3 conversion...")
    print(f"Input: s3://{event['source_bucket']}/{event['source_key']}")
    print(f"Output: s3://{event['output_bucket']}/{event['output_key']}")
    print(f"Metadata: s3://{event['output_bucket']}/{event['metadata_key']}")
    print("-" * 50)
    
    try:
        # Call the lambda handler
        result = lambda_handler(event, context)
        
        # Print results
        print("\nConversion completed successfully!")
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            # Extract outputs from the response body
            outputs = body.get('outputs', {})
            print(f"Markdown S3 URI: {outputs.get('markdown_s3_uri', 'N/A')}")
            print(f"Metadata S3 URI: {outputs.get('metadata_s3_uri', 'N/A')}")
            
            # Show processing summary
            summary = body.get('processing_summary', {})
            if summary:
                print("\nProcessing Summary:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            
            # Show performance metrics
            metrics = body.get('performance_metrics', {})
            if metrics:
                print("\nPerformance Metrics:")
                for key, value in metrics.items():
                    print(f"  {key}: {value:.2f}s")
            
            if 'summary' in body:
                print("\nDocument Summary:")
                for key, value in body['summary'].items():
                    print(f"  {key}: {value}")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"\nError during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    # Set AWS profile to AITest
    os.environ['AWS_PROFILE'] = 'AITest'
    os.environ['AWS_REGION'] = 'us-west-2'
    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
    
    # Import boto3 after setting the profile
    import boto3
    # Force boto3 to use the profile
    boto3.setup_default_session(profile_name='AITest')
    
    print("Using AWS Profile: AITest")
    print("Using AWS Region: us-west-2")
    print("=" * 50)
    
    exit_code = test_s3_conversion()
    sys.exit(exit_code)