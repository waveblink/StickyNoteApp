"""Test encryption functionality."""

import pytest
from src.aurora_notes.crypto.encryption import EncryptionService


class TestEncryption:
    """Test encryption service."""
    
    def test_encrypt_decrypt(self):
        """Test basic encryption/decryption."""
        service = EncryptionService()
        service._key = b'a' * 32  # Test key
        
        plaintext = "Hello, Aurora Notes!"
        encrypted = service.encrypt(plaintext)
        
        assert encrypted != plaintext.encode()
        assert len(encrypted) > len(plaintext)
        
        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_json(self):
        """Test JSON encryption."""
        service = EncryptionService()
        service._key = b'b' * 32
        
        data = {"theme": "dark", "hotkey": "ctrl+n"}
        encrypted = service.encrypt_json(data)
        decrypted = service.decrypt_json(encrypted)
        
        assert decrypted == data
    
    def test_different_nonces(self):
        """Test that encryption produces different outputs."""
        service = EncryptionService()
        service._key = b'c' * 32
        
        plaintext = "Same text"
        enc1 = service.encrypt(plaintext)
        enc2 = service.encrypt(plaintext)
        
        # Different nonces should produce different ciphertexts
        assert enc1 != enc2
        
        # But both should decrypt to same plaintext
        assert service.decrypt(enc1) == plaintext
        assert service.decrypt(enc2) == plaintext