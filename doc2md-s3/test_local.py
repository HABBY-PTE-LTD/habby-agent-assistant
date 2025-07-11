#!/usr/bin/env python3
"""
Local testing script for doc2md-s3 Lambda function
Tests the function with real PDF files without S3 dependencies
"""

import json
import time
import os
import tempfile
from pathlib import Path

# Import our modules
from docling_processor import DoclingProcessor
from markdown_optimizer import MarkdownOptimizer
from metadata_analyzer import MetadataAnalyzer

def test_docling_processing():
    """Test Docling processing with local PDF file"""
    
    print("🧪 Testing Docling processing...")
    
    # Look for test PDF in parent directory
    test_pdf_path = "../test_data/美术外包合同审核共同点AI总结-V3.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found: {test_pdf_path}")
        print("Please ensure the test PDF file exists")
        return False
    
    try:
        # Initialize processor
        options = {
            "ocr_enabled": True,
            "preserve_tables": True,
            "preserve_formatting": True
        }
        
        processor = DoclingProcessor(options)
        
        # Process document
        start_time = time.time()
        result = processor.process_document(test_pdf_path)
        processing_time = time.time() - start_time
        
        if result["success"]:
            print(f"✅ Docling processing successful!")
            print(f"   - Processing time: {processing_time:.2f}s")
            print(f"   - Page count: {result['document_info'].get('page_count', 0)}")
            print(f"   - Content length: {len(result['markdown_content'])} characters")
            print(f"   - Table count: {result['document_info'].get('table_count', 0)}")
            
            return result
        else:
            print(f"❌ Docling processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Docling processing: {str(e)}")
        return False

def test_markdown_optimization(markdown_content):
    """Test Markdown optimization"""
    
    print("\n🧪 Testing Markdown optimization...")
    
    try:
        options = {
            "add_metadata_header": False,
            "generate_toc": False
        }
        
        optimizer = MarkdownOptimizer(options)
        
        start_time = time.time()
        result = optimizer.optimize_markdown(markdown_content)
        processing_time = time.time() - start_time
        
        if result["success"]:
            print(f"✅ Markdown optimization successful!")
            print(f"   - Processing time: {processing_time:.2f}s")
            print(f"   - Original length: {result['stats']['original_length']}")
            print(f"   - Optimized length: {result['stats']['optimized_length']}")
            print(f"   - Optimizations applied: {len(result['stats']['optimizations_applied'])}")
            
            return result
        else:
            print(f"❌ Markdown optimization failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Markdown optimization: {str(e)}")
        return False

def test_metadata_generation(docling_result, markdown_stats):
    """Test metadata generation"""
    
    print("\n🧪 Testing metadata generation...")
    
    try:
        options = {}
        analyzer = MetadataAnalyzer(options)
        
        processing_times = {
            "s3_download": 1.2,
            "docling_processing": docling_result["processing_time"],
            "markdown_optimization": markdown_stats["processing_time"],
            "s3_upload": 0.8
        }
        
        filename = "美术外包合同审核共同点AI总结-V3.pdf"
        
        start_time = time.time()
        metadata = analyzer.generate_metadata(
            filename=filename,
            docling_result=docling_result,
            markdown_stats=markdown_stats["stats"],
            processing_times=processing_times
        )
        processing_time = time.time() - start_time
        
        print(f"✅ Metadata generation successful!")
        print(f"   - Processing time: {processing_time:.2f}s")
        print(f"   - Metadata keys: {list(metadata.keys())}")
        
        # Generate processing report
        report = analyzer.generate_processing_report(metadata, success=True)
        print(f"   - Processing report generated")
        
        return metadata, report
        
    except Exception as e:
        print(f"❌ Error during metadata generation: {str(e)}")
        return False, False

def save_test_results(markdown_content, metadata, report):
    """Save test results to files"""
    
    print("\n💾 Saving test results...")
    
    try:
        # Create output directory
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save Markdown content
        markdown_file = os.path.join(output_dir, "test_output.md")
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save metadata
        metadata_file = os.path.join(output_dir, "test_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Save processing report
        report_file = os.path.join(output_dir, "test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test results saved to {output_dir}/")
        print(f"   - Markdown: {markdown_file}")
        print(f"   - Metadata: {metadata_file}")
        print(f"   - Report: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving test results: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Starting doc2md-s3 local testing...")
    print("=" * 50)
    
    # Test 1: Docling processing
    docling_result = test_docling_processing()
    if not docling_result:
        print("💥 Docling processing test failed. Stopping.")
        return False
    
    # Test 2: Markdown optimization
    markdown_result = test_markdown_optimization(docling_result["markdown_content"])
    if not markdown_result:
        print("💥 Markdown optimization test failed. Stopping.")
        return False
    
    # Test 3: Metadata generation
    metadata, report = test_metadata_generation(docling_result, markdown_result)
    if not metadata:
        print("💥 Metadata generation test failed. Stopping.")
        return False
    
    # Test 4: Save results
    save_success = save_test_results(
        markdown_result["optimized_content"],
        metadata,
        report
    )
    
    if not save_success:
        print("💥 Failed to save test results.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"   - Pages processed: {docling_result['document_info'].get('page_count', 0)}")
    print(f"   - Content length: {len(markdown_result['optimized_content'])} characters")
    print(f"   - Tables found: {docling_result['document_info'].get('table_count', 0)}")
    print(f"   - Optimizations applied: {len(markdown_result['stats']['optimizations_applied'])}")
    print(f"   - Total processing time: ~{docling_result['processing_time'] + markdown_result['processing_time']:.2f}s")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 