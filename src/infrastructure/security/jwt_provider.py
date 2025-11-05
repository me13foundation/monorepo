"""
JWT token provider for MED13 Resource Library.

Provides secure JWT token creation, validation, and management.
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, cast
from uuid import UUID


class JWTProvider:
    """
    JWT token provider with secure token management.

    Features:
    - HS256 signing for security
    - Configurable token expiration
    - Token validation with error handling
    - Access and refresh token support
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT provider.

        Args:
            secret_key: Secret key for signing tokens (must be strong)
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

        # Validate secret key strength
        if not secret_key or len(secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")

    def create_access_token(
        self, user_id: UUID, role: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's unique identifier
            role: User's role
            expires_delta: Token expiration time (default: 15 minutes)

        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)  # Short-lived access tokens

        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "med13-resource-library",
        }

        return self._encode_token(to_encode)

    def create_refresh_token(
        self, user_id: UUID, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User's unique identifier
            expires_delta: Token expiration time (default: 7 days)

        Returns:
            JWT refresh token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=7)  # Long-lived refresh tokens

        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "med13-resource-library",
        }

        return self._encode_token(to_encode)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer="med13-resource-library",
            )

            # Additional validation
            self._validate_payload(payload)

            return cast(Dict[str, Any], payload)

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except jwt.InvalidIssuerError:
            raise ValueError("Invalid token issuer")
        except Exception as e:
            raise ValueError(f"Token validation failed: {str(e)}")

    def get_token_expiration(self, token: str) -> datetime:
        """
        Get token expiration time without full validation.

        Args:
            token: JWT token string

        Returns:
            Token expiration datetime

        Raises:
            ValueError: If token is malformed
        """
        try:
            # Decode without verification to get expiration
            payload = jwt.decode(token, options={"verify_signature": False})

            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                raise ValueError("Token has no expiration")

            return datetime.fromtimestamp(exp_timestamp)

        except Exception as e:
            raise ValueError(f"Cannot parse token expiration: {str(e)}")

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full validation.

        Args:
            token: JWT token string

        Returns:
            True if token is expired
        """
        try:
            expiration = self.get_token_expiration(token)
            return datetime.utcnow() > expiration
        except ValueError:
            return True  # Treat unparseable tokens as expired

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Create new access token from valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new access token and expiration info

        Raises:
            ValueError: If refresh token is invalid
        """
        # Validate refresh token
        payload = self.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = UUID(payload["sub"])
        role = payload.get("role", "viewer")  # Default role if not in refresh token

        # Create new access token
        new_access_token = self.create_access_token(user_id, role)

        # Get expiration info
        expiration = self.get_token_expiration(new_access_token)

        return {
            "access_token": new_access_token,
            "expires_at": expiration,
            "user_id": str(user_id),
            "role": role,
        }

    def _encode_token(self, payload: Dict[str, Any]) -> str:
        """
        Encode payload into JWT token.

        Args:
            payload: Token payload

        Returns:
            JWT token string
        """
        try:
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            raise ValueError(f"Token encoding failed: {str(e)}")

    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validate decoded token payload.

        Args:
            payload: Decoded token payload

        Raises:
            ValueError: If payload is invalid
        """
        required_fields = ["sub", "type", "exp", "iat", "iss"]

        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Token missing required field: {field}")

        # Validate subject (user ID)
        try:
            UUID(payload["sub"])
        except (ValueError, TypeError):
            raise ValueError("Invalid user ID in token")

        # Validate token type
        if payload["type"] not in ["access", "refresh"]:
            raise ValueError("Invalid token type")

        # Validate issuer
        if payload["iss"] != "med13-resource-library":
            raise ValueError("Invalid token issuer")

        # Additional security checks can be added here
        # - Check if user still exists and is active
        # - Check if token has been revoked
        # - Check IP address consistency
        # - Check user agent consistency

    def generate_secure_secret(self, length: int = 64) -> str:
        """
        Generate a cryptographically secure secret for JWT signing.

        Args:
            length: Length of secret (default: 64)

        Returns:
            Secure random string
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + string.punctuation
        return "".join(secrets.choice(alphabet) for _ in range(length))
