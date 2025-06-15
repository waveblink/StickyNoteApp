"""Encryption layer using OS keychain and AES-256-GCM."""

import os
import json
import base64
from typing import Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import keyring


class EncryptionService:
    """Handles AES-256-GCM encryption with OS keychain integration."""
    
    SERVICE_NAME = "AuroraNotes"
    KEY_NAME = "master_key"
    
    def __init__(self):
        self._key: Optional[bytes] = None
        self._backend = default_backend()
    
    def initialize(self) -> bool:
        """Initialize encryption key from OS keychain or create new."""
        try:
            # Try to get existing key from OS keychain
            stored_key = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
            
            if stored_key:
                self._key = base64.b64decode(stored_key)
            else:
                # Generate new 256-bit key
                self._key = os.urandom(32)
                # Store in OS keychain
                keyring.set_password(
                    self.SERVICE_NAME,
                    self.KEY_NAME,
                    base64.b64encode(self._key).decode()
                )
            
            return True
        except Exception as e:
            print(f"Failed to initialize encryption: {e}")
            return False
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt string to bytes using AES-256-GCM."""
        if not self._key:
            raise RuntimeError("Encryption not initialized")
        
        # Generate random 96-bit nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.GCM(nonce),
            backend=self._backend
        )
        encryptor = cipher.encryptor()
        
        # Encrypt
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        
        # Return nonce + ciphertext + tag
        return nonce + ciphertext + encryptor.tag
    
    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt bytes to string using AES-256-GCM."""
        if not self._key:
            raise RuntimeError("Encryption not initialized")
        
        # Extract components
        nonce = encrypted[:12]
        tag = encrypted[-16:]
        ciphertext = encrypted[12:-16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.GCM(nonce, tag),
            backend=self._backend
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()
    
    def encrypt_json(self, data: Any) -> bytes:
        """Encrypt JSON-serializable data."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_json(self, encrypted: bytes) -> Any:
        """Decrypt to JSON data."""
        json_str = self.decrypt(encrypted)
        return json.loads(json_str)
    
    def clear_key(self):
        """Clear key from memory (called on app exit)."""
        if self._key:
            # Overwrite key bytes
            self._key = b'\x00' * len(self._key)
            self._key = None


# Global instance
encryption_service = EncryptionService()