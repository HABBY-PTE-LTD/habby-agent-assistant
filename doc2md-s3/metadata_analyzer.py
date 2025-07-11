"""
Metadata Analyzer Module for doc2md-s3 Lambda Function
Generates comprehensive metadata and analysis reports for processed documents
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class MetadataAnalyzer:
    """Document metadata analyzer and report generator"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize metadata analyzer
        
        Args:
            options: Analysis options
        """
        self.options = options or {}
        self.processing_log = []
    
    def generate_metadata(self, 
                         filename: str,
                         docling_result: Dict[str, Any],
                         markdown_stats: Dict[str, Any],
                         processing_times: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for the processed document
        
        Args:
            filename: Original filename
            docling_result: Results from Docling processing
            markdown_stats: Markdown optimization statistics
            processing_times: Processing time breakdown
            
        Returns:
            Dict containing comprehensive metadata
        """
        
        # Log metadata generation start
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": "INFO",
            "service": "doc2md-s3",
            "action": "generate_metadata",
            "filename": filename
        }
        print(json.dumps(log_entry))
        
        try:
            # Basic document information
            doc_info = docling_result.get("document_info", {})
            
            # Calculate total processing time
            total_time = sum(processing_times.values())
            
            # Generate comprehensive metadata
            metadata = {
                "document_info": {
                    "filename": filename,
                    "processed_at": datetime.utcnow().isoformat() + "Z",
                    "total_processing_time": f"{total_time:.2f}s",
                    "processing_breakdown": {
                        "s3_download": f"{processing_times.get('s3_download', 0):.2f}s",
                        "docling_processing": f"{processing_times.get('docling_processing', 0):.2f}s",
                        "markdown_optimization": f"{processing_times.get('markdown_optimization', 0):.2f}s",
                        "s3_upload": f"{processing_times.get('s3_upload', 0):.2f}s"
                    }
                },
                "content_analysis": {
                    "page_count": doc_info.get("page_count", 0),
                    "total_characters": doc_info.get("total_characters", 0),
                    "total_words": doc_info.get("total_words", 0),
                    "table_count": doc_info.get("table_count", 0),
                    "heading_count": doc_info.get("heading_count", 0),
                    "paragraph_count": doc_info.get("paragraph_count", 0),
                    "list_count": doc_info.get("list_count", 0),
                    "formula_count": doc_info.get("formula_count", 0)
                },
                "markdown_output": {
                    "original_length": markdown_stats.get("original_length", 0),
                    "optimized_length": markdown_stats.get("optimized_length", 0),
                    "optimization_ratio": self._calculate_optimization_ratio(markdown_stats),
                    "optimizations_applied": markdown_stats.get("optimizations_applied", []),
                    "tables_processed": markdown_stats.get("tables_processed", 0),
                    "headings_processed": markdown_stats.get("headings_processed", 0),
                    "links_processed": markdown_stats.get("links_processed", 0)
                },
                "processing_options": {
                    "ocr_enabled": self.options.get("ocr_enabled", True),
                    "preserve_tables": self.options.get("preserve_tables", True),
                    "preserve_formatting": self.options.get("preserve_formatting", True),
                    "markdown_optimization": self.options.get("markdown_optimization", True)
                },
                "system_info": {
                    "docling_version": "2.41.0",
                    "processor": "doc2md-s3",
                    "lambda_version": "1.0.0"
                }
            }
            
            # Add page-level analysis if available
            if "page_analysis" in docling_result:
                metadata["page_breakdown"] = docling_result["page_analysis"]
            
            # Add table analysis if available
            if "tables" in docling_result:
                metadata["table_analysis"] = docling_result["tables"]
            
            # Add processing log
            metadata["processing_log"] = self.processing_log.copy()
            
            # Log success
            success_log = {
                **log_entry,
                "result": "success",
                "metadataKeys": list(metadata.keys())
            }
            print(json.dumps(success_log))
            
            return metadata
            
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            
            # Return minimal metadata on error
            return {
                "document_info": {
                    "filename": filename,
                    "processed_at": datetime.utcnow().isoformat() + "Z",
                    "status": "error",
                    "error_message": str(e)
                },
                "system_info": {
                    "docling_version": "2.41.0",
                    "processor": "doc2md-s3",
                    "lambda_version": "1.0.0"
                }
            }
    
    def _calculate_optimization_ratio(self, markdown_stats: Dict[str, Any]) -> float:
        """Calculate optimization ratio"""
        original = markdown_stats.get("original_length", 0)
        optimized = markdown_stats.get("optimized_length", 0)
        
        if original == 0:
            return 0.0
        
        return round((original - optimized) / original * 100, 2)
    
    def add_processing_log(self, level: str, message: str, **kwargs):
        """
        Add entry to processing log
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            **kwargs: Additional log data
        """
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": level,
            "message": message,
            **kwargs
        }
        self.processing_log.append(log_entry)
    
    def generate_processing_report(self, 
                                 metadata: Dict[str, Any],
                                 success: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive processing report
        
        Args:
            metadata: Document metadata
            success: Whether processing was successful
            
        Returns:
            Dict containing processing report
        """
        try:
            doc_info = metadata.get("document_info", {})
            content_analysis = metadata.get("content_analysis", {})
            markdown_output = metadata.get("markdown_output", {})
            
            report = {
                "processing_summary": {
                    "status": "success" if success else "failed",
                    "filename": doc_info.get("filename", "Unknown"),
                    "processed_at": doc_info.get("processed_at", "Unknown"),
                    "total_time": doc_info.get("total_processing_time", "Unknown")
                },
                "document_metrics": {
                    "pages": content_analysis.get("page_count", 0),
                    "words": content_analysis.get("total_words", 0),
                    "characters": content_analysis.get("total_characters", 0),
                    "tables": content_analysis.get("table_count", 0),
                    "headings": content_analysis.get("heading_count", 0),
                    "paragraphs": content_analysis.get("paragraph_count", 0)
                },
                "output_metrics": {
                    "markdown_length": markdown_output.get("optimized_length", 0),
                    "optimization_ratio": f"{markdown_output.get('optimization_ratio', 0)}%",
                    "optimizations_count": len(markdown_output.get("optimizations_applied", [])),
                    "tables_processed": markdown_output.get("tables_processed", 0)
                },
                "performance_metrics": {
                    "processing_breakdown": doc_info.get("processing_breakdown", {}),
                    "words_per_second": self._calculate_words_per_second(
                        content_analysis.get("total_words", 0),
                        doc_info.get("total_processing_time", "0s")
                    )
                },
                "quality_indicators": {
                    "has_tables": content_analysis.get("table_count", 0) > 0,
                    "has_headings": content_analysis.get("heading_count", 0) > 0,
                    "has_lists": content_analysis.get("list_count", 0) > 0,
                    "has_formulas": content_analysis.get("formula_count", 0) > 0,
                    "content_richness": self._calculate_content_richness(content_analysis)
                }
            }
            
            return report
            
        except Exception as e:
            return {
                "processing_summary": {
                    "status": "error",
                    "error_message": str(e)
                }
            }
    
    def _calculate_words_per_second(self, total_words: int, processing_time_str: str) -> float:
        """Calculate processing speed in words per second"""
        try:
            # Extract numeric value from processing time string
            time_value = float(processing_time_str.replace('s', ''))
            if time_value > 0:
                return round(total_words / time_value, 2)
            return 0.0
        except:
            return 0.0
    
    def _calculate_content_richness(self, content_analysis: Dict[str, Any]) -> str:
        """Calculate content richness level"""
        try:
            score = 0
            
            # Points for different content types
            if content_analysis.get("table_count", 0) > 0:
                score += 2
            if content_analysis.get("heading_count", 0) > 0:
                score += 1
            if content_analysis.get("list_count", 0) > 0:
                score += 1
            if content_analysis.get("formula_count", 0) > 0:
                score += 2
            
            # Points for content volume
            word_count = content_analysis.get("total_words", 0)
            if word_count > 10000:
                score += 3
            elif word_count > 5000:
                score += 2
            elif word_count > 1000:
                score += 1
            
            # Determine richness level
            if score >= 7:
                return "Very High"
            elif score >= 5:
                return "High"
            elif score >= 3:
                return "Medium"
            elif score >= 1:
                return "Low"
            else:
                return "Very Low"
                
        except:
            return "Unknown"
    
    def export_metadata_json(self, metadata: Dict[str, Any]) -> str:
        """
        Export metadata as formatted JSON string
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted JSON string
        """
        try:
            return json.dumps(metadata, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to export metadata: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }, indent=2)
    
    def generate_summary_text(self, metadata: Dict[str, Any]) -> str:
        """
        Generate human-readable summary text
        
        Args:
            metadata: Document metadata
            
        Returns:
            Human-readable summary
        """
        try:
            doc_info = metadata.get("document_info", {})
            content_analysis = metadata.get("content_analysis", {})
            markdown_output = metadata.get("markdown_output", {})
            
            summary_lines = [
                f"# Document Processing Summary",
                f"",
                f"**File**: {doc_info.get('filename', 'Unknown')}",
                f"**Processed**: {doc_info.get('processed_at', 'Unknown')}",
                f"**Total Time**: {doc_info.get('total_processing_time', 'Unknown')}",
                f"",
                f"## Content Analysis",
                f"- **Pages**: {content_analysis.get('page_count', 0)}",
                f"- **Words**: {content_analysis.get('total_words', 0):,}",
                f"- **Characters**: {content_analysis.get('total_characters', 0):,}",
                f"- **Tables**: {content_analysis.get('table_count', 0)}",
                f"- **Headings**: {content_analysis.get('heading_count', 0)}",
                f"- **Paragraphs**: {content_analysis.get('paragraph_count', 0)}",
                f"",
                f"## Output Quality",
                f"- **Markdown Length**: {markdown_output.get('optimized_length', 0):,} characters",
                f"- **Optimization**: {markdown_output.get('optimization_ratio', 0)}% reduction",
                f"- **Optimizations Applied**: {len(markdown_output.get('optimizations_applied', []))}",
                f"",
                f"## Processing Performance",
            ]
            
            # Add processing breakdown
            breakdown = doc_info.get("processing_breakdown", {})
            for step, time_taken in breakdown.items():
                step_name = step.replace('_', ' ').title()
                summary_lines.append(f"- **{step_name}**: {time_taken}")
            
            return '\n'.join(summary_lines)
            
        except Exception as e:
            return f"Error generating summary: {str(e)}" 