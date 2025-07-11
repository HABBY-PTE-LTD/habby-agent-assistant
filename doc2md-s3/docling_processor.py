"""
Docling Processor Module for doc2md-s3 Lambda Function
Handles document processing using Docling library with advanced features
"""

import json
import time
import ssl
from typing import Dict, Any, Optional, List
from pathlib import Path

# Fix SSL certificate verification issue for Lambda environment
ssl._create_default_https_context = ssl._create_unverified_context

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

class DoclingProcessor:
    """Advanced document processor using Docling"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize Docling processor
        
        Args:
            options: Processing options
        """
        self.options = options or {}
        self.converter = None
        self._initialize_converter()
    
    def _initialize_converter(self):
        """Initialize DocumentConverter with optimized settings"""
        try:
            # Log initialization
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "service": "doc2md-s3",
                "action": "docling_init",
                "options": self.options
            }
            print(json.dumps(log_entry))
            
            # Configure PDF pipeline options for better performance
            pdf_options = PdfPipelineOptions()
            pdf_options.do_ocr = self.options.get('ocr_enabled', True)
            pdf_options.do_table_structure = self.options.get('preserve_tables', True)
            pdf_options.table_structure_options.do_cell_matching = True
            
            # Initialize converter with options
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdf_options
                )
            }
            
            self.converter = DocumentConverter(
                format_options=format_options
            )
            
            success_log = {
                **log_entry,
                "result": "success",
                "converterInitialized": True
            }
            print(json.dumps(success_log))
            
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            raise Exception(f"Failed to initialize Docling converter: {str(e)}")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process document using Docling
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing processing results
        """
        start_time = time.time()
        
        # Log processing start
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": "INFO",
            "service": "doc2md-s3",
            "action": "docling_process",
            "filePath": file_path
        }
        print(json.dumps(log_entry))
        
        try:
            # Convert document
            result = self.converter.convert(file_path)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract document information
            doc_info = self._extract_document_info(result)
            
            # Generate markdown content
            markdown_content = result.document.export_to_markdown()
            
            # Generate HTML content (optional)
            html_content = result.document.export_to_html() if self.options.get('generate_html', False) else None
            
            # Generate JSON content (optional)
            json_content = result.document.export_to_json() if self.options.get('generate_json', False) else None
            
            # Prepare processing results
            processing_results = {
                "success": True,
                "processing_time": processing_time,
                "document_info": doc_info,
                "markdown_content": markdown_content,
                "html_content": html_content,
                "json_content": json_content,
                "docling_result": result  # Keep original result for advanced analysis
            }
            
            # Log success
            success_log = {
                **log_entry,
                "result": "success",
                "processingTime": f"{processing_time:.2f}s",
                "pageCount": doc_info.get("page_count", 0),
                "contentLength": len(markdown_content),
                "tableCount": doc_info.get("table_count", 0)
            }
            print(json.dumps(success_log))
            
            return processing_results
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "processingTime": f"{processing_time:.2f}s",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            
            return {
                "success": False,
                "processing_time": processing_time,
                "error": str(e),
                "document_info": {},
                "markdown_content": "",
                "html_content": None,
                "json_content": None
            }
    
    def _extract_document_info(self, result) -> Dict[str, Any]:
        """
        Extract detailed document information from Docling result
        
        Args:
            result: Docling conversion result
            
        Returns:
            Dict containing document information
        """
        try:
            doc = result.document
            
            # Basic document info
            doc_info = {
                "page_count": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "table_count": 0,
                "heading_count": 0,
                "paragraph_count": 0,
                "list_count": 0,
                "formula_count": 0,
                "total_characters": 0,
                "total_words": 0
            }
            
            # Analyze document structure
            if hasattr(doc, 'pages'):
                for page in doc.pages:
                    if hasattr(page, 'elements'):
                        for element in page.elements:
                            element_type = getattr(element, 'label', '').lower()
                            
                            if 'table' in element_type:
                                doc_info["table_count"] += 1
                            elif 'heading' in element_type or 'title' in element_type:
                                doc_info["heading_count"] += 1
                            elif 'paragraph' in element_type or 'text' in element_type:
                                doc_info["paragraph_count"] += 1
                            elif 'list' in element_type:
                                doc_info["list_count"] += 1
                            elif 'formula' in element_type or 'equation' in element_type:
                                doc_info["formula_count"] += 1
                            
                            # Count characters and words
                            if hasattr(element, 'text') and element.text:
                                text = str(element.text)
                                doc_info["total_characters"] += len(text)
                                doc_info["total_words"] += len(text.split())
            
            return doc_info
            
        except Exception as e:
            print(f"Error extracting document info: {str(e)}")
            return {
                "page_count": 0,
                "table_count": 0,
                "heading_count": 0,
                "paragraph_count": 0,
                "list_count": 0,
                "formula_count": 0,
                "total_characters": 0,
                "total_words": 0,
                "extraction_error": str(e)
            }
    
    def analyze_page_structure(self, result) -> List[Dict[str, Any]]:
        """
        Analyze structure of each page
        
        Args:
            result: Docling conversion result
            
        Returns:
            List of page analysis results
        """
        page_analysis = []
        
        try:
            if hasattr(result.document, 'pages'):
                for i, page in enumerate(result.document.pages):
                    page_info = {
                        "page_number": i + 1,
                        "element_count": 0,
                        "table_count": 0,
                        "heading_count": 0,
                        "paragraph_count": 0,
                        "character_count": 0,
                        "word_count": 0
                    }
                    
                    if hasattr(page, 'elements'):
                        page_info["element_count"] = len(page.elements)
                        
                        for element in page.elements:
                            element_type = getattr(element, 'label', '').lower()
                            
                            if 'table' in element_type:
                                page_info["table_count"] += 1
                            elif 'heading' in element_type or 'title' in element_type:
                                page_info["heading_count"] += 1
                            elif 'paragraph' in element_type or 'text' in element_type:
                                page_info["paragraph_count"] += 1
                            
                            # Count characters and words
                            if hasattr(element, 'text') and element.text:
                                text = str(element.text)
                                page_info["character_count"] += len(text)
                                page_info["word_count"] += len(text.split())
                    
                    page_analysis.append(page_info)
            
            return page_analysis
            
        except Exception as e:
            print(f"Error analyzing page structure: {str(e)}")
            return []
    
    def extract_tables(self, result) -> List[Dict[str, Any]]:
        """
        Extract table information from document
        
        Args:
            result: Docling conversion result
            
        Returns:
            List of table information
        """
        tables = []
        
        try:
            if hasattr(result.document, 'pages'):
                for page_num, page in enumerate(result.document.pages):
                    if hasattr(page, 'elements'):
                        for element_num, element in enumerate(page.elements):
                            element_type = getattr(element, 'label', '').lower()
                            
                            if 'table' in element_type:
                                table_info = {
                                    "page_number": page_num + 1,
                                    "element_number": element_num + 1,
                                    "table_type": element_type,
                                    "text_content": str(getattr(element, 'text', '')),
                                    "row_count": 0,
                                    "column_count": 0
                                }
                                
                                # Try to extract table structure if available
                                if hasattr(element, 'table_data'):
                                    table_data = element.table_data
                                    if table_data:
                                        table_info["row_count"] = len(table_data)
                                        if table_data:
                                            table_info["column_count"] = len(table_data[0]) if table_data[0] else 0
                                
                                tables.append(table_info)
            
            return tables
            
        except Exception as e:
            print(f"Error extracting tables: {str(e)}")
            return []
    
    def get_processing_summary(self, result) -> Dict[str, Any]:
        """
        Get comprehensive processing summary
        
        Args:
            result: Docling conversion result
            
        Returns:
            Dict containing processing summary
        """
        try:
            doc_info = self._extract_document_info(result)
            page_analysis = self.analyze_page_structure(result)
            tables = self.extract_tables(result)
            
            summary = {
                "document_info": doc_info,
                "page_analysis": page_analysis,
                "tables": tables,
                "processing_options": self.options,
                "docling_version": "2.41.0"  # Current version
            }
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "processing_options": self.options,
                "docling_version": "2.41.0"
            } 