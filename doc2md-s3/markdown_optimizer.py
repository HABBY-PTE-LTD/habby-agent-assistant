"""
Markdown Optimizer Module for doc2md-s3 Lambda Function
Optimizes and enhances Markdown output quality and formatting
"""

import re
import json
import time
from typing import Dict, Any, List, Optional

class MarkdownOptimizer:
    """Markdown content optimizer and formatter"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize Markdown optimizer
        
        Args:
            options: Optimization options
        """
        self.options = options or {}
        self.stats = {
            "original_length": 0,
            "optimized_length": 0,
            "tables_processed": 0,
            "headings_processed": 0,
            "links_processed": 0,
            "optimizations_applied": []
        }
    
    def optimize_markdown(self, markdown_content: str) -> Dict[str, Any]:
        """
        Optimize Markdown content
        
        Args:
            markdown_content: Raw markdown content
            
        Returns:
            Dict containing optimized content and stats
        """
        start_time = time.time()
        
        # Log optimization start
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": "INFO",
            "service": "doc2md-s3",
            "action": "markdown_optimize",
            "originalLength": len(markdown_content)
        }
        print(json.dumps(log_entry))
        
        try:
            # Initialize stats
            self.stats["original_length"] = len(markdown_content)
            optimized_content = markdown_content
            
            # Apply optimizations
            optimized_content = self._clean_whitespace(optimized_content)
            optimized_content = self._optimize_headings(optimized_content)
            optimized_content = self._optimize_tables(optimized_content)
            optimized_content = self._optimize_lists(optimized_content)
            optimized_content = self._optimize_links(optimized_content)
            optimized_content = self._remove_empty_sections(optimized_content)
            optimized_content = self._normalize_line_endings(optimized_content)
            
            # Update final stats
            self.stats["optimized_length"] = len(optimized_content)
            processing_time = time.time() - start_time
            
            # Log success
            success_log = {
                **log_entry,
                "result": "success",
                "processingTime": f"{processing_time:.2f}s",
                "optimizedLength": self.stats["optimized_length"],
                "optimizationsApplied": self.stats["optimizations_applied"]
            }
            print(json.dumps(success_log))
            
            return {
                "success": True,
                "optimized_content": optimized_content,
                "processing_time": processing_time,
                "stats": self.stats.copy()
            }
            
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
                "optimized_content": markdown_content,
                "processing_time": processing_time,
                "error": str(e),
                "stats": self.stats.copy()
            }
    
    def _clean_whitespace(self, content: str) -> str:
        """Clean excessive whitespace"""
        # Remove trailing whitespace from lines
        content = re.sub(r' +$', '', content, flags=re.MULTILINE)
        
        # Normalize multiple consecutive blank lines to maximum 2
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove leading and trailing whitespace
        content = content.strip()
        
        self.stats["optimizations_applied"].append("whitespace_cleanup")
        return content
    
    def _optimize_headings(self, content: str) -> str:
        """Optimize heading formatting"""
        # Ensure proper spacing around headings
        content = re.sub(r'\n(#{1,6})\s*([^\n]+)\n', r'\n\n\1 \2\n\n', content)
        
        # Fix heading at start of document
        content = re.sub(r'^(#{1,6})\s*([^\n]+)\n', r'\1 \2\n\n', content)
        
        # Count headings processed
        headings = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)
        self.stats["headings_processed"] = len(headings)
        
        if headings:
            self.stats["optimizations_applied"].append("heading_optimization")
        
        return content
    
    def _optimize_tables(self, content: str) -> str:
        """Optimize table formatting"""
        # Find and process tables
        table_pattern = r'(\|[^\n]+\|[\n\r]*)+(\|[\s\-:]+\|[\n\r]*)?(\|[^\n]+\|[\n\r]*)*'
        tables = re.findall(table_pattern, content)
        
        if tables:
            # Ensure proper spacing around tables
            content = re.sub(r'\n(\|[^\n]+\|)', r'\n\n\1', content)
            content = re.sub(r'(\|[^\n]+\|)\n([^\|\n])', r'\1\n\n\2', content)
            
            # Clean up table formatting
            lines = content.split('\n')
            processed_lines = []
            
            for line in lines:
                if '|' in line and line.strip().startswith('|'):
                    # Clean up table row
                    line = self._clean_table_row(line)
                processed_lines.append(line)
            
            content = '\n'.join(processed_lines)
            
            self.stats["tables_processed"] = len(tables)
            self.stats["optimizations_applied"].append("table_optimization")
        
        return content
    
    def _clean_table_row(self, row: str) -> str:
        """Clean up individual table row"""
        # Remove excessive whitespace around cell content
        cells = row.split('|')
        cleaned_cells = []
        
        for cell in cells:
            # Keep first and last empty cells for proper table structure
            if cell == '' and (len(cleaned_cells) == 0 or len(cleaned_cells) == len(cells) - 1):
                cleaned_cells.append(cell)
            else:
                cleaned_cells.append(cell.strip())
        
        return '|'.join(cleaned_cells)
    
    def _optimize_lists(self, content: str) -> str:
        """Optimize list formatting"""
        # Ensure proper spacing around lists
        content = re.sub(r'\n([-*+]\s+[^\n]+)', r'\n\n\1', content)
        content = re.sub(r'([-*+]\s+[^\n]+)\n([^\-\*\+\s\n])', r'\1\n\n\2', content)
        
        # Ensure proper spacing around numbered lists
        content = re.sub(r'\n(\d+\.\s+[^\n]+)', r'\n\n\1', content)
        content = re.sub(r'(\d+\.\s+[^\n]+)\n([^\d\s\n])', r'\1\n\n\2', content)
        
        # Count lists
        list_items = re.findall(r'^[-*+]\s+.+$', content, re.MULTILINE)
        numbered_items = re.findall(r'^\d+\.\s+.+$', content, re.MULTILINE)
        
        if list_items or numbered_items:
            self.stats["optimizations_applied"].append("list_optimization")
        
        return content
    
    def _optimize_links(self, content: str) -> str:
        """Optimize link formatting"""
        # Count links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        self.stats["links_processed"] = len(links)
        
        if links:
            # Ensure links are properly formatted (basic validation)
            content = re.sub(r'\[\s*([^\]]+)\s*\]\(\s*([^)]+)\s*\)', r'[\1](\2)', content)
            self.stats["optimizations_applied"].append("link_optimization")
        
        return content
    
    def _remove_empty_sections(self, content: str) -> str:
        """Remove empty sections and unnecessary blank lines"""
        # Remove empty sections (headings with no content)
        content = re.sub(r'\n#{1,6}\s*[^\n]*\n\n(?=#{1,6})', '\n', content)
        
        # Remove excessive blank lines before headings
        content = re.sub(r'\n{3,}(#{1,6})', r'\n\n\1', content)
        
        self.stats["optimizations_applied"].append("empty_section_removal")
        return content
    
    def _normalize_line_endings(self, content: str) -> str:
        """Normalize line endings"""
        # Convert all line endings to Unix style
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Ensure file ends with single newline
        content = content.rstrip('\n') + '\n'
        
        self.stats["optimizations_applied"].append("line_ending_normalization")
        return content
    
    def add_metadata_header(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Add metadata header to Markdown content
        
        Args:
            content: Markdown content
            metadata: Document metadata
            
        Returns:
            Markdown content with metadata header
        """
        if not self.options.get('add_metadata_header', False):
            return content
        
        # Create metadata header
        header_lines = [
            "---",
            f"title: {metadata.get('filename', 'Document')}",
            f"generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            f"pages: {metadata.get('page_count', 0)}",
            f"tables: {metadata.get('table_count', 0)}",
            f"processing_time: {metadata.get('processing_time', 'N/A')}",
            f"docling_version: {metadata.get('docling_version', '2.41.0')}",
            "---",
            ""
        ]
        
        header = '\n'.join(header_lines)
        return header + content
    
    def generate_table_of_contents(self, content: str) -> str:
        """
        Generate table of contents from headings
        
        Args:
            content: Markdown content
            
        Returns:
            Table of contents as Markdown
        """
        if not self.options.get('generate_toc', False):
            return ""
        
        # Find all headings
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        if not headings:
            return ""
        
        toc_lines = ["## Table of Contents", ""]
        
        for level_hashes, title in headings:
            level = len(level_hashes)
            indent = "  " * (level - 1)
            # Create anchor link (simplified)
            anchor = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
            toc_lines.append(f"{indent}- [{title}](#{anchor})")
        
        toc_lines.append("")
        return '\n'.join(toc_lines)
    
    def get_content_statistics(self, content: str) -> Dict[str, Any]:
        """
        Get detailed content statistics
        
        Args:
            content: Markdown content
            
        Returns:
            Dict containing content statistics
        """
        stats = {
            "total_characters": len(content),
            "total_words": len(content.split()),
            "total_lines": len(content.split('\n')),
            "headings": {
                "h1": len(re.findall(r'^#\s+', content, re.MULTILINE)),
                "h2": len(re.findall(r'^##\s+', content, re.MULTILINE)),
                "h3": len(re.findall(r'^###\s+', content, re.MULTILINE)),
                "h4": len(re.findall(r'^####\s+', content, re.MULTILINE)),
                "h5": len(re.findall(r'^#####\s+', content, re.MULTILINE)),
                "h6": len(re.findall(r'^######\s+', content, re.MULTILINE)),
                "total": len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
            },
            "lists": {
                "unordered": len(re.findall(r'^[-*+]\s+', content, re.MULTILINE)),
                "ordered": len(re.findall(r'^\d+\.\s+', content, re.MULTILINE))
            },
            "tables": len(re.findall(r'\|[^\n]+\|', content)),
            "links": len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            "images": len(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)),
            "code_blocks": len(re.findall(r'```', content)) // 2,
            "inline_code": len(re.findall(r'`[^`]+`', content))
        }
        
        return stats 