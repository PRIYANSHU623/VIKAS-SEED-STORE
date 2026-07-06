"""
Security Utilities
Rate limiting, file upload validation, SQL injection prevention
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set
import logging
from fastapi import UploadFile
from app.core.config import MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates file uploads"""
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'scr', 'vbs', 'js', 'jar',
        'zip', 'rar', '7z', 'tar', 'gz',
        'php', 'asp', 'aspx', 'jsp', 'py', 'pl', 'sh'
    }
    
    @staticmethod
    def validate_extension(filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Check against dangerous extensions
        if ext in FileValidator.DANGEROUS_EXTENSIONS:
            logger.warning(f"Dangerous file extension attempted: {ext}")
            return False
        
        # Check against allowed extensions
        if ALLOWED_EXTENSIONS and ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Disallowed file extension: {ext}")
            return False
        
        return True
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Check if file size is within limits"""
        if file_size > MAX_UPLOAD_SIZE:
            logger.warning(f"File size {file_size} exceeds limit {MAX_UPLOAD_SIZE}")
            return False
        return True
    
    @staticmethod
    async def validate_upload_file(file: UploadFile) -> bool:
        """Validate an uploaded file"""
        # Check filename
        if not FileValidator.validate_extension(file.filename):
            raise ValidationError(
                message=f"File type not allowed: {file.filename}",
                field="file"
            )
        
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        
        if not FileValidator.validate_file_size(file_size):
            raise ValidationError(
                message=f"File size {file_size} exceeds maximum {MAX_UPLOAD_SIZE}",
                field="file"
            )
        
        # Reset file position for reading
        await file.seek(0)
        
        return True


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # {ip: [(timestamp, endpoint), ...]}
    
    def is_rate_limited(
        self,
        client_ip: str,
        endpoint: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """Check if client has exceeded rate limit"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        
        key = f"{client_ip}:{endpoint}"
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            (ts, ep) for ts, ep in self.requests[key]
            if ts > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return True
        
        # Add current request
        self.requests[key].append((now, endpoint))
        
        # Cleanup old entries
        if len(self.requests) > 10000:
            expired_keys = [k for k, v in self.requests.items() if not v]
            for k in expired_keys:
                del self.requests[k]
        
        return False


class SQLInjectionProtection:
    """SQL Injection detection and prevention"""
    
    # Dangerous SQL keywords often used in injection
    DANGEROUS_KEYWORDS = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION',
        'EXEC', 'EXECUTE', ';', '--', '/*', '*/', 'xp_', 'sp_'
    }
    
    @staticmethod
    def has_sql_injection_pattern(value: str) -> bool:
        """Check if string contains SQL injection patterns"""
        if not isinstance(value, str):
            return False
        
        # Convert to uppercase for comparison
        upper_value = value.upper()
        
        # Check for dangerous keywords
        for keyword in SQLInjectionProtection.DANGEROUS_KEYWORDS:
            if keyword in upper_value:
                # Allow ; in specific cases (like comma-separated lists)
                if keyword == ';' and upper_value.count(';') > 1:
                    return True
                if keyword != ';':
                    return True
        
        # Check for common injection patterns
        patterns = [
            "' OR '1'='1",
            "' OR 1=1",
            "admin' --",
            "' UNION SELECT",
            "'; DROP TABLE",
        ]
        
        for pattern in patterns:
            if pattern.upper() in upper_value:
                return True
        
        return False
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Basic sanitization of user input"""
        if not isinstance(value, str):
            return value
        
        # Remove potentially dangerous characters (but keep reasonable ones)
        # This is a basic example; use parameterized queries instead
        dangerous_chars = ['<', '>', '"', "'", '\\']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()


class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token(session_id: str) -> str:
        """Generate CSRF token"""
        import secrets
        token = secrets.token_urlsafe(32)
        return token
    
    @staticmethod
    def validate_token(token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        # This is a simplified version
        # In production, store tokens in session and verify them
        return len(token) > 0 and len(session_id) > 0


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return rate_limiter
