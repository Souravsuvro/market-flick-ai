"""JWT token management utilities."""
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
import os
import logging

logger = logging.getLogger(__name__)


class JWTManager:
    """Manages JWT token creation and validation."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        if self.secret_key == "your-secret-key-change-in-production":
            logger.warning("⚠️  WARNING: Using default JWT secret key. Change JWT_SECRET_KEY in production!")
    
    def create_access_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Create access token.
        
        Args:
            user_id: User identifier
            additional_claims: Additional claims to include
            
        Returns:
            Encoded JWT token
        """
        to_encode = {
            "sub": user_id,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            Encoded JWT token
        """
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """Verify and decode token.
        
        Args:
            token: JWT token to verify
            token_type: Type of token (access or refresh)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from token.
        
        Args:
            token: JWT token
            
        Returns:
            User ID or None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


# Global JWT manager instance
jwt_manager = JWTManager()
