"""
S3 Handler Module for doc2md-s3 Lambda Function
Handles S3 file operations including download, upload, and path management
"""

import boto3
import json
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
import time

class S3Handler:
    """S3 file operations handler"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize S3 handler
        
        Args:
            region_name: AWS region name
        """
        try:
            self.s3_client = boto3.client('s3', region_name=region_name)
            self.region_name = region_name
        except Exception as e:
            raise Exception(f"Failed to initialize S3 client: {str(e)}")
    
    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """
        Download file from S3 to local path
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local file path to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log download start
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "service": "doc2md-s3",
                "action": "s3_download",
                "bucket": bucket,
                "key": key,
                "localPath": local_path
            }
            print(json.dumps(log_entry))
            
            # Download file
            self.s3_client.download_file(bucket, key, local_path)
            
            # Verify file exists and get size
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                success_log = {
                    **log_entry,
                    "result": "success",
                    "fileSize": file_size
                }
                print(json.dumps(success_log))
                return True
            else:
                error_log = {
                    **log_entry,
                    "level": "ERROR",
                    "result": "fail",
                    "errorMessage": "File not found after download"
                }
                print(json.dumps(error_log))
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorCode": error_code,
                "errorMessage": error_msg
            }
            print(json.dumps(error_log))
            return False
            
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            return False
    
    def upload_file(self, local_path: str, bucket: str, key: str, 
                   content_type: str = None) -> bool:
        """
        Upload file from local path to S3
        
        Args:
            local_path: Local file path
            bucket: S3 bucket name
            key: S3 object key
            content_type: Content type for the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log upload start
            file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "service": "doc2md-s3",
                "action": "s3_upload",
                "bucket": bucket,
                "key": key,
                "localPath": local_path,
                "fileSize": file_size
            }
            print(json.dumps(log_entry))
            
            # Prepare upload arguments
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload file
            self.s3_client.upload_file(local_path, bucket, key, ExtraArgs=extra_args)
            
            # Verify upload by checking object existence
            try:
                response = self.s3_client.head_object(Bucket=bucket, Key=key)
                uploaded_size = response.get('ContentLength', 0)
                
                success_log = {
                    **log_entry,
                    "result": "success",
                    "uploadedSize": uploaded_size,
                    "s3Uri": f"s3://{bucket}/{key}"
                }
                print(json.dumps(success_log))
                return True
                
            except ClientError:
                error_log = {
                    **log_entry,
                    "level": "ERROR",
                    "result": "fail",
                    "errorMessage": "Upload verification failed"
                }
                print(json.dumps(error_log))
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorCode": error_code,
                "errorMessage": error_msg
            }
            print(json.dumps(error_log))
            return False
            
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            return False
    
    def upload_content(self, content: str, bucket: str, key: str, 
                      content_type: str = 'text/plain') -> bool:
        """
        Upload string content directly to S3
        
        Args:
            content: String content to upload
            bucket: S3 bucket name
            key: S3 object key
            content_type: Content type for the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log upload start
            content_size = len(content.encode('utf-8'))
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "service": "doc2md-s3",
                "action": "s3_upload_content",
                "bucket": bucket,
                "key": key,
                "contentSize": content_size,
                "contentType": content_type
            }
            print(json.dumps(log_entry))
            
            # Upload content
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            
            success_log = {
                **log_entry,
                "result": "success",
                "s3Uri": f"s3://{bucket}/{key}"
            }
            print(json.dumps(success_log))
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorCode": error_code,
                "errorMessage": error_msg
            }
            print(json.dumps(error_log))
            return False
            
        except Exception as e:
            error_log = {
                **log_entry,
                "level": "ERROR",
                "result": "fail",
                "errorMessage": str(e)
            }
            print(json.dumps(error_log))
            return False
    
    def validate_s3_path(self, bucket: str, key: str) -> Tuple[bool, str]:
        """
        Validate S3 bucket and key
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Validate bucket name
        if not bucket or len(bucket) < 3 or len(bucket) > 63:
            return False, "Invalid bucket name length"
        
        # Validate key
        if not key or len(key) > 1024:
            return False, "Invalid key length"
        
        # Check for invalid characters
        if '//' in key or key.startswith('/') or key.endswith('/'):
            return False, "Invalid key format"
        
        return True, ""
    
    def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if S3 object exists
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                # Re-raise other errors
                raise e
    
    def get_object_info(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get S3 object metadata
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Optional[Dict]: Object metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                raise e
    
    def create_temp_file(self, suffix: str = '.tmp') -> str:
        """
        Create a temporary file and return its path
        
        Args:
            suffix: File suffix
            
        Returns:
            str: Temporary file path
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        return temp_file.name
    
    def get_object_info(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Get object metadata including version ID
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict containing object metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            
            return {
                "version_id": response.get('VersionId', 'null'),
                "etag": response.get('ETag', '').strip('"'),
                "content_length": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified', '').isoformat() if response.get('LastModified') else None,
                "content_type": response.get('ContentType', ''),
                "metadata": response.get('Metadata', {})
            }
        except Exception as e:
            print(f"Error getting object info: {str(e)}")
            return {}
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary file
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to cleanup temp file {file_path}: {str(e)}")
            return False 