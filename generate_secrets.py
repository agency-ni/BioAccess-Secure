#!/usr/bin/env python3
"""
BioAccess-Secure: Secure Key Generation Tool

Generates cryptographically secure keys for:
- Flask SECRET_KEY (session/CSRF protection)
- JWT_SECRET_KEY (JWT token signing)
- Additional security credentials

Usage:
    python generate_secrets.py
    
Or programmatically:
    from generate_secrets import SecureKeyGenerator
    generator = SecureKeyGenerator()
    keys = generator.generate_all()
"""

import os
import sys
import json
import secrets
import hashlib
from datetime import datetime
from pathlib import Path


class SecureKeyGenerator:
    """Generate cryptographically secure keys for BioAccess-Secure."""
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """
        Generate a secure SECRET_KEY for Flask.
        
        Args:
            length: Key length in bytes (default 32 = 256 bits)
            
        Returns:
            Hex-encoded secure random string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """
        Generate a secure JWT_SECRET_KEY.
        
        Args:
            length: Key length in bytes (default 64 = 512 bits)
            
        Returns:
            Base64-compatible secure random string
        """
        # Use URL-safe base64 characters for JWT
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a secure API key for client authentication.
        
        Args:
            length: Key length in bytes
            
        Returns:
            Hex-encoded API key
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_password_salt(length: int = 16) -> str:
        """
        Generate a secure salt for password hashing.
        
        Args:
            length: Salt length in bytes
            
        Returns:
            Hex-encoded salt
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_encryption_key(length: int = 32) -> str:
        """
        Generate a secure encryption key (256-bit for AES-256).
        
        Args:
            length: Key length in bytes
            
        Returns:
            Hex-encoded encryption key
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_refresh_token_secret(length: int = 64) -> str:
        """
        Generate a secure refresh token secret.
        
        Args:
            length: Key length in bytes
            
        Returns:
            URL-safe secure random string
        """
        return secrets.token_urlsafe(length)
    
    def generate_all(self) -> dict:
        """
        Generate all required security keys.
        
        Returns:
            Dictionary with all generated keys
        """
        return {
            "SECRET_KEY": self.generate_secret_key(),
            "JWT_SECRET_KEY": self.generate_jwt_secret(),
            "API_KEY": self.generate_api_key(),
            "PASSWORD_SALT": self.generate_password_salt(),
            "ENCRYPTION_KEY": self.generate_encryption_key(),
            "REFRESH_TOKEN_SECRET": self.generate_refresh_token_secret(),
            "generated_at": datetime.utcnow().isoformat(),
            "algorithm": "HS512",
            "key_rotation_days": 90
        }
    
    @staticmethod
    def validate_key(key: str, min_length: int = 32) -> bool:
        """
        Validate that a key meets security requirements.
        
        Args:
            key: Key to validate
            min_length: Minimum key length in bytes
            
        Returns:
            True if key is valid, False otherwise
        """
        if not key or len(key) < min_length:
            return False
        # Check for randomness (very basic check)
        return len(set(key)) > len(key) // 2
    
    @staticmethod
    def hash_key(key: str) -> str:
        """
        Create a hash of the key for logging/identification.
        
        Args:
            key: Key to hash
            
        Returns:
            SHA-256 hash of key (first 16 chars)
        """
        return hashlib.sha256(key.encode()).hexdigest()[:16]


class EnvironmentManager:
    """Manage environment file creation and updates."""
    
    def __init__(self, env_file_path: str = ".env"):
        """Initialize with .env file path."""
        self.env_file_path = Path(env_file_path)
        self.env_file_prod_path = Path(".env.production")
        self.env_file_dev_path = Path(".env.development")
    
    def create_env_file(self, keys: dict, env_type: str = "development"):
        """
        Create .env file with generated keys.
        
        Args:
            keys: Dictionary of keys to store
            env_type: Type of environment (development/production)
        """
        env_path = self.env_file_prod_path if env_type == "production" else self.env_file_dev_path
        
        content = f"""# BioAccess-Secure Environment Variables
# Generated: {datetime.utcnow().isoformat()}
# Environment: {env_type.upper()}
#
# SECURITY WARNING
# - Never commit this file to git repository
# - Never share these keys with unauthorized persons
# - Rotate keys every 90 days
# - Use strong, unique keys in production

# Flask Configuration
FLASK_ENV={env_type}
SECRET_KEY={keys.get('SECRET_KEY')}
DEBUG={"true" if env_type == "development" else "false"}

# JWT Configuration
JWT_SECRET_KEY={keys.get('JWT_SECRET_KEY')}
JWT_ALGORITHM=HS512
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=30

# Security Keys
API_KEY={keys.get('API_KEY')}
PASSWORD_SALT={keys.get('PASSWORD_SALT')}
ENCRYPTION_KEY={keys.get('ENCRYPTION_KEY')}
REFRESH_TOKEN_SECRET={keys.get('REFRESH_TOKEN_SECRET')}

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/bioaccess_secure
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_SSL_MODE={"require" if env_type == "production" else "prefer"}

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@bioaccess-secure.com

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Application Configuration
APP_NAME=BioAccess-Secure
APP_VERSION=2.0.0
LOG_LEVEL={"DEBUG" if env_type == "development" else "INFO"}
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Key Rotation
KEY_ROTATION_DAYS=90
NEXT_KEY_ROTATION={datetime.utcnow().isoformat()}

# Generated Keys Information
# SECRET_KEY_HASH: {SecureKeyGenerator.hash_key(keys.get('SECRET_KEY'))}
# JWT_SECRET_KEY_HASH: {SecureKeyGenerator.hash_key(keys.get('JWT_SECRET_KEY'))}
"""
        
        env_path.write_text(content, encoding='utf-8')
        return env_path
    
    def create_env_template(self):
        """Create .env.example template for distribution."""
        template = """# BioAccess-Secure Environment Variables Template
# Copy this file to .env and fill in your values

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-min-32-chars
DEBUG=false

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here-min-64-chars
JWT_ALGORITHM=HS512
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=30

# Security Keys
API_KEY=your-api-key-here
PASSWORD_SALT=your-password-salt-here
ENCRYPTION_KEY=your-encryption-key-here
REFRESH_TOKEN_SECRET=your-refresh-token-secret-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/bioaccess_secure
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_SSL_MODE=prefer

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@bioaccess-secure.com

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Application Configuration
APP_NAME=BioAccess-Secure
APP_VERSION=2.0.0
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Key Rotation
KEY_ROTATION_DAYS=90
"""
        Path(".env.example").write_text(template, encoding='utf-8')
        return Path(".env.example")


def generate_and_display():
    """Generate keys and display them."""
    print("\n" + "=" * 80)
    print("🔐 BioAccess-Secure: Secure Key Generator")
    print("=" * 80)
    
    generator = SecureKeyGenerator()
    keys = generator.generate_all()
    
    print("\n📋 Generated Secure Keys:")
    print("-" * 80)
    
    # Display keys (masked for security)
    print(f"\n✅ SECRET_KEY (Flask)")
    print(f"   Value: {keys['SECRET_KEY'][:16]}...{keys['SECRET_KEY'][-8:]}")
    print(f"   Full Length: {len(keys['SECRET_KEY'])} chars")
    print(f"   Hash: {SecureKeyGenerator.hash_key(keys['SECRET_KEY'])}")
    
    print(f"\n✅ JWT_SECRET_KEY")
    print(f"   Value: {keys['JWT_SECRET_KEY'][:16]}...{keys['JWT_SECRET_KEY'][-8:]}")
    print(f"   Full Length: {len(keys['JWT_SECRET_KEY'])} chars")
    print(f"   Hash: {SecureKeyGenerator.hash_key(keys['JWT_SECRET_KEY'])}")
    
    print(f"\n✅ API_KEY")
    print(f"   Value: {keys['API_KEY'][:16]}...{keys['API_KEY'][-8:]}")
    print(f"   Hash: {SecureKeyGenerator.hash_key(keys['API_KEY'])}")
    
    print(f"\n✅ ENCRYPTION_KEY (AES-256)")
    print(f"   Value: {keys['ENCRYPTION_KEY'][:16]}...{keys['ENCRYPTION_KEY'][-8:]}")
    print(f"   Hash: {SecureKeyGenerator.hash_key(keys['ENCRYPTION_KEY'])}")
    
    print(f"\n✅ REFRESH_TOKEN_SECRET")
    print(f"   Value: {keys['REFRESH_TOKEN_SECRET'][:16]}...{keys['REFRESH_TOKEN_SECRET'][-8:]}")
    print(f"   Hash: {SecureKeyGenerator.hash_key(keys['REFRESH_TOKEN_SECRET'])}")
    
    print("\n" + "=" * 80)
    print("📁 Creating Environment Files:")
    print("-" * 80)
    
    manager = EnvironmentManager()
    
    # Create development .env file
    dev_path = manager.create_env_file(keys, "development")
    print(f"\n✅ Created: {dev_path}")
    print(f"   Size: {dev_path.stat().st_size} bytes")
    print("   ⚠️  Keep this file secure - never commit to git!")
    
    # Create production .env file
    prod_path = manager.create_env_file(keys, "production")
    print(f"\n✅ Created: {prod_path}")
    print(f"   Size: {prod_path.stat().st_size} bytes")
    print("   ⚠️  Store this securely in production environment!")
    
    # Create template
    template_path = manager.create_env_template()
    print(f"\n✅ Created: {template_path}")
    print("   Template for distribution (safe to commit)")
    
    print("\n" + "=" * 80)
    print("🔐 Security Checklist:")
    print("-" * 80)
    print("✅ Keys generated with cryptographic randomness")
    print("✅ SECRET_KEY: 32 bytes (256 bits)")
    print("✅ JWT_SECRET_KEY: 64 bytes (512 bits)")
    print("✅ API_KEY: 32 bytes (256 bits)")
    print("✅ ENCRYPTION_KEY: 32 bytes (AES-256 compatible)")
    
    print("\n" + "=" * 80)
    print("📋 Quick Summary:")
    print("-" * 80)
    print(f"Generated at: {keys['generated_at']}")
    print(f"Algorithm: {keys['algorithm']}")
    print(f"Key Rotation: Every {keys['key_rotation_days']} days")
    
    print("\n" + "=" * 80)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("-" * 80)
    print("1. These keys are sensitive security credentials")
    print("2. Never commit .env files to git repository")
    print("3. Add .env to .gitignore immediately")
    print("4. Share only .env.example template")
    print("5. Rotate keys every 90 days")
    print("6. Use different keys for dev/production")
    print("7. Store production keys in secure vault")
    print("8. Never log or display full keys")
    
    print("\n" + "=" * 80)
    print("🚀 Next Steps:")
    print("-" * 80)
    print("1. Copy keys from .env.development to your Flask config")
    print("2. Update Backend/config.py with SECRET_KEY and JWT_SECRET_KEY")
    print("3. Test authentication with generated keys")
    print("4. Deploy .env.production to production server")
    print("5. Set up key rotation alerts")
    
    print("\n" + "=" * 80)
    
    return keys


if __name__ == "__main__":
    keys = generate_and_display()
    
    # Write keys to JSON for programmatic use (in-memory only)
    print("\n✅ All files generated successfully!")
    print("✅ Keep .env files secure and never share them!")
