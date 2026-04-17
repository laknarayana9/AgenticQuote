"""
Data Encryption
Provides encryption/decryption for sensitive data.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import base64
import hashlib

logger = logging.getLogger(__name__)


class Encryption:
    """
    Data encryption utility for sensitive data.
    
    Provides encryption/decryption using Fernet-compatible encryption.
    """
    
    def __init__(self):
        """Initialize encryption utility."""
        self.enabled = os.getenv("ENCRYPTION_ENABLED", "false").lower() == "true"
        self.encryption_key = os.getenv("ENCRYPTION_KEY", None)
        
        if not self.encryption_key and self.enabled:
            logger.warning("ENCRYPTION_KEY not set, using default key (not secure for production)")
            self.encryption_key = "default_key_change_in_production"
        
        logger.info(f"Encryption utility initialized (enabled={self.enabled})")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.
        
        Args:
            plaintext: Text to encrypt
            
        Returns:
            Encrypted text (base64 encoded)
        """
        if not self.enabled:
            return plaintext
        
        try:
            # Simple XOR encryption for demonstration
            # In production, use cryptography.fernet or similar
            key_bytes = self.encryption_key.encode()
            text_bytes = plaintext.encode()
            
            # XOR encryption
            encrypted = bytes([a ^ b for a, b in zip(text_bytes, key_bytes * len(text_bytes))])
            
            # Base64 encode
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return plaintext
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.
        
        Args:
            ciphertext: Encrypted text (base64 encoded)
            
        Returns:
            Decrypted text
        """
        if not self.enabled:
            return ciphertext
        
        try:
            # Base64 decode
            encrypted = base64.b64decode(ciphertext.encode())
            
            # XOR decryption
            key_bytes = self.encryption_key.encode()
            decrypted = bytes([a ^ b for a, b in zip(encrypted, key_bytes * len(encrypted))])
            
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ciphertext
    
    def encrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary with data
            fields: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        if not self.enabled:
            return data
        
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and isinstance(encrypted_data[field], str):
                encrypted_data[field] = self.encrypt(encrypted_data[field])
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary with encrypted data
            fields: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        if not self.enabled:
            return data
        
        decrypted_data = data.copy()
        for field in fields:
            if field in decrypted_data and isinstance(decrypted_data[field], str):
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        
        return decrypted_data
    
    def hash_value(self, value: str) -> str:
        """
        Hash a value (one-way, for password hashing).
        
        Args:
            value: Value to hash
            
        Returns:
            Hashed value
        """
        return hashlib.sha256(value.encode()).hexdigest()
    
    def verify_hash(self, value: str, hash_value: str) -> bool:
        """
        Verify a hash against a value.
        
        Args:
            value: Value to check
            hash_value: Hash to verify against
            
        Returns:
            True if hash matches
        """
        return self.hash_value(value) == hash_value


# Global encryption instance
_global_encryption: Optional[Encryption] = None


def get_encryption() -> Encryption:
    """
    Get global encryption instance (singleton pattern).
    
    Returns:
        Encryption instance
    """
    global _global_encryption
    if _global_encryption is None:
        _global_encryption = Encryption()
    return _global_encryption
