"""Input validation utilities."""
import re
from typing import Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    MAX_STRING_LENGTH = 10000
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    ALLOWED_FILE_TYPES = {'pdf', 'txt', 'doc', 'docx', 'xlsx', 'csv'}
    
    @staticmethod
    def validate_string(value: str, field_name: str, min_length: int = 1, max_length: int = MAX_STRING_LENGTH) -> str:
        """Validate and sanitize string input.
        
        Args:
            value: String to validate
            field_name: Name of the field (for error messages)
            min_length: Minimum length
            max_length: Maximum length
            
        Returns:
            Sanitized string
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters")
        
        if len(value) > max_length:
            raise ValueError(f"{field_name} must not exceed {max_length} characters")
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address.
        
        Args:
            email: Email to validate
            
        Returns:
            Validated email
            
        Raises:
            ValueError: If email is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email = email.strip().lower()
        
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email address")
        
        if len(email) > 254:
            raise ValueError("Email address too long")
        
        return email
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            ValueError: If URL is invalid
        """
        try:
            url = url.strip()
            result = urlparse(url)
            
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
            
            if result.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP and HTTPS URLs are allowed")
            
            if len(url) > 2048:
                raise ValueError("URL too long")
            
            return url
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> str:
        """Validate file upload.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            
        Returns:
            Validated filename
            
        Raises:
            ValueError: If file is invalid
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        filename = filename.strip()
        
        # Get file extension
        if '.' not in filename:
            raise ValueError("File must have an extension")
        
        ext = filename.rsplit('.', 1)[-1].lower()
        
        if ext not in InputValidator.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type .{ext} not allowed. Allowed types: {', '.join(InputValidator.ALLOWED_FILE_TYPES)}")
        
        if file_size > InputValidator.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {InputValidator.MAX_FILE_SIZE / (1024*1024):.0f}MB")
        
        if file_size == 0:
            raise ValueError("File cannot be empty")
        
        return filename
    
    @staticmethod
    def validate_sector(sector: str) -> str:
        """Validate business sector.
        
        Args:
            sector: Sector name
            
        Returns:
            Validated sector
            
        Raises:
            ValueError: If sector is invalid
        """
        return InputValidator.validate_string(sector, "Sector", min_length=2, max_length=100)
    
    @staticmethod
    def validate_location(location: str) -> str:
        """Validate business location.
        
        Args:
            location: Location name
            
        Returns:
            Validated location
            
        Raises:
            ValueError: If location is invalid
        """
        return InputValidator.validate_string(location, "Location", min_length=2, max_length=100)
    
    @staticmethod
    def validate_idea(idea: str) -> str:
        """Validate business idea description.
        
        Args:
            idea: Business idea
            
        Returns:
            Validated idea
            
        Raises:
            ValueError: If idea is invalid
        """
        return InputValidator.validate_string(idea, "Business idea", min_length=10, max_length=5000)
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potentially dangerous HTML/script tags.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove script tags and content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove event handlers
        text = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)
        # Remove javascript: protocol
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        return text
