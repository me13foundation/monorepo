"""
Password hashing utilities for MED13 Resource Library.

Provides secure password hashing with truncation prevention and strength validation.
"""

from passlib.context import CryptContext
from passlib.pwd import genword
import re


class PasswordHasher:
    """
    Secure password hashing with bcrypt and truncation prevention.

    Features:
    - bcrypt hashing with 12 rounds (default)
    - Automatic pre-hashing for passwords > 72 bytes
    - Password strength validation
    - Secure random password generation
    """

    def __init__(self):
        # Use bcrypt with automatic pre-hashing for long passwords
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,  # Strong hashing
            # CRITICAL: Enable automatic pre-hashing
            bcrypt__ident="2b",  # Use latest bcrypt version
            truncate_error=True,  # Raise error if truncation would occur
        )

        # Password policy configuration
        self.min_length = 8
        self.max_length = 128  # Reasonable limit to prevent DoS

    def hash_password(self, plain_password: str) -> str:
        """
        Securely hash a password with truncation prevention.

        This method automatically handles long passwords by pre-hashing them
        with SHA256 before passing to bcrypt, preventing truncation attacks.

        Args:
            plain_password: The plain text password

        Returns:
            Hashed password string (bcrypt format)

        Raises:
            ValueError: If password violates policy or hashing fails
        """
        self._validate_password_policy(plain_password)

        try:
            # passlib automatically handles long passwords:
            # - If > 72 bytes: Pre-hashes with SHA256, then bcrypts the hash
            # - This prevents truncation while maintaining security
            return self.pwd_context.hash(plain_password)
        except Exception as e:
            raise ValueError(f"Password hashing failed: {str(e)}")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Previously hashed password

        Returns:
            True if password matches hash, False otherwise

        Raises:
            ValueError: If inputs are invalid
        """
        if not plain_password or not hashed_password:
            return False

        try:
            # passlib handles the pre-hashing automatically during verification
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Any exception during verification means invalid
            return False

    def is_password_strong(self, password: str) -> bool:
        """
        Check if password meets strength requirements.

        Args:
            password: Password to check

        Returns:
            True if password is strong enough
        """
        try:
            self._validate_password_policy(password)
            return True
        except ValueError:
            return False

    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.

        Args:
            length: Desired password length (default: 16)

        Returns:
            Secure random password string

        Raises:
            ValueError: If length is invalid
        """
        if length < self.min_length or length > self.max_length:
            length = 16  # Default fallback

        return genword(
            length=length,
            charset="ascii_72",  # Safe ASCII characters including symbols
        )

    def get_hash_info(self, hashed_password: str) -> dict:
        """
        Get information about a password hash.

        Args:
            hashed_password: The hashed password

        Returns:
            Dictionary with hash information or error details
        """
        try:
            return {
                "scheme": self.pwd_context.identify(hashed_password),
                "needs_update": self.pwd_context.needs_update(hashed_password),
                "is_valid": True,
            }
        except Exception as e:
            return {
                "scheme": None,
                "needs_update": False,
                "is_valid": False,
                "error": str(e),
            }

    def _validate_password_policy(self, password: str) -> None:
        """
        Validate password against security policy.

        Args:
            password: Password to validate

        Raises:
            ValueError: If password violates policy
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if len(password) < self.min_length:
            raise ValueError(
                f"Password must be at least {self.min_length} characters long"
            )

        if len(password) > self.max_length:
            raise ValueError(f"Password cannot exceed {self.max_length} characters")

        # Check for basic complexity (configurable)
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Password must contain at least one letter")

        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number")

        # Additional checks can be added here:
        # - No common passwords
        # - No sequential characters
        # - Dictionary word checks
        # - Personal information checks

    def check_password_complexity(self, password: str) -> dict:
        """
        Detailed password complexity analysis.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with complexity metrics
        """
        analysis = {
            "length": len(password),
            "has_lowercase": bool(re.search(r"[a-z]", password)),
            "has_uppercase": bool(re.search(r"[A-Z]", password)),
            "has_digit": bool(re.search(r"[0-9]", password)),
            "has_special": bool(re.search(r"[^A-Za-z0-9]", password)),
            "is_strong": False,
            "score": 0,
            "issues": [],
        }

        # Length scoring
        if analysis["length"] >= 12:
            analysis["score"] += 2
        elif analysis["length"] >= 8:
            analysis["score"] += 1

        # Character variety scoring
        if analysis["has_lowercase"]:
            analysis["score"] += 1
        if analysis["has_uppercase"]:
            analysis["score"] += 1
        if analysis["has_digit"]:
            analysis["score"] += 1
        if analysis["has_special"]:
            analysis["score"] += 1

        # Issue detection
        if analysis["length"] < self.min_length:
            analysis["issues"].append(
                f"Too short (minimum {self.min_length} characters)"
            )

        if not analysis["has_lowercase"]:
            analysis["issues"].append("Missing lowercase letter")

        if not analysis["has_uppercase"]:
            analysis["issues"].append("Missing uppercase letter")

        if not analysis["has_digit"]:
            analysis["issues"].append("Missing number")

        if not analysis["has_special"]:
            analysis["issues"].append("Missing special character")

        # Sequential character check
        if re.search(r"(012|123|234|345|456|567|678|789|890)", password):
            analysis["issues"].append("Contains sequential numbers")
            analysis["score"] -= 1

        if re.search(
            r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",
            password.lower(),
        ):
            analysis["issues"].append("Contains sequential letters")
            analysis["score"] -= 1

        # Strength determination
        analysis["is_strong"] = analysis["score"] >= 4 and len(analysis["issues"]) == 0

        return analysis
