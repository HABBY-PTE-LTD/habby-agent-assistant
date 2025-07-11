#!/usr/bin/env python3
"""
PDF to Markdown converter using Docling
Test script for local PDF files
"""

import os
import sys
import json
import time
from pathlib import Path
from docling.document_converter import DocumentConverter

def convert_pdf_to_markdown(pdf_path: str, output_dir: str = "output") -> dict:
    """
    Convert PDF to Markdown using Docling
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the output files
        
    Returns:
        dict: Conversion results with metadata
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize the document converter
        converter = DocumentConverter()
        
        # Record start time
        start_time = time.time()
        
        # Convert the document
        print(f"Converting PDF: {pdf_path}")
        result = converter.convert(pdf_path)
        
        # Record end time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Get the markdown content
        markdown_content = result.document.export_to_markdown()
        
        # Get document metadata
        metadata = {
            "filename": os.path.basename(pdf_path),
            "processing_time": f"{processing_time:.2f}s",
            "page_count": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
            "content_length": len(markdown_content),
            "status": "success"
        }
        
        # Save markdown to file
        pdf_name = Path(pdf_path).stem
        markdown_file = os.path.join(output_dir, f"{pdf_name}.md")
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save metadata to JSON file
        metadata_file = os.path.join(output_dir, f"{pdf_name}_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Conversion completed successfully!")
        print(f"   - Processing time: {processing_time:.2f}s")
        print(f"   - Page count: {metadata['page_count']}")
        print(f"   - Content length: {metadata['content_length']} characters")
        print(f"   - Output saved to: {markdown_file}")
        
        return {
            "success": True,
            "markdown_content": markdown_content,
            "metadata": metadata,
            "output_file": markdown_file
        }
        
    except Exception as e:
        error_msg = f"Error converting PDF: {str(e)}"
        print(f"❌ {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "metadata": {
                "filename": os.path.basename(pdf_path),
                "status": "failed",
                "error_message": str(e)
            }
        }

def main():
    """Main function to test PDF conversion"""
    
    # Test PDF file path
    test_pdf = "../test_data/美术外包合同审核共同点AI总结-V3.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF file not found: {test_pdf}")
        print("Please ensure the test file exists in the test_data directory")
        sys.exit(1)
    
    print("🚀 Starting PDF to Markdown conversion test...")
    print(f"📄 Input file: {test_pdf}")
    print("-" * 50)
    
    # Convert the PDF
    result = convert_pdf_to_markdown(test_pdf)
    
    print("-" * 50)
    
    if result["success"]:
        print("🎉 Test completed successfully!")
        print(f"📝 Markdown preview (first 500 chars):")
        print("-" * 30)
        print(result["markdown_content"][:500])
        if len(result["markdown_content"]) > 500:
            print("...")
        print("-" * 30)
    else:
        print("💥 Test failed!")
        print(f"Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main() 