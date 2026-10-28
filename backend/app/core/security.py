import base64
import os
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple, Union

from jose import jwt, JWTError
import bcrypt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


# JWT Tokens
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return {}

# AES-256-GCM Encryption / Decryption for PII at rest
def _get_aes_key() -> bytes:
    key_str = settings.AES_SECRET_KEY
    key_bytes = key_str.encode("utf-8")
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b"0")
    return key_bytes[:32]

def encrypt_pii(plain_text: Optional[str]) -> Optional[str]:
    """Encrypts plaintext string using AES-256-GCM with a fresh 12-byte nonce."""
    if not plain_text:
        return None
    aesgcm = AESGCM(_get_aes_key())
    nonce = os.urandom(12)
    encrypted_bytes = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    # Store nonce + ciphertext encoded in base64
    combined = nonce + encrypted_bytes
    return base64.b64encode(combined).decode("utf-8")

def decrypt_pii(cipher_b64: Optional[str]) -> Optional[str]:
    """Decrypts base64-encoded AES-256-GCM ciphertext."""
    if not cipher_b64:
        return None
    try:
        combined = base64.b64decode(cipher_b64.encode("utf-8"))
        if len(combined) < 13:
            return cipher_b64  # Return as is if not encrypted format
        nonce = combined[:12]
        ciphertext = combined[12:]
        aesgcm = AESGCM(_get_aes_key())
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # If decryption fails (e.g. unencrypted mock data), return raw string safely
        return cipher_b64

# Ed25519 Verifiable Credential Signatures
# Generate deterministic or environment-provided master key pair
_cached_ed25519_private_key: Optional[ed25519.Ed25519PrivateKey] = None

def get_ed25519_keys() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    global _cached_ed25519_private_key
    if _cached_ed25519_private_key is None:
        if settings.ED25519_PRIVATE_KEY_B64:
            try:
                raw_bytes = base64.b64decode(settings.ED25519_PRIVATE_KEY_B64)
                _cached_ed25519_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)
            except Exception:
                _cached_ed25519_private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            # Deterministic seed for demo consistency if not configured
            demo_seed = hashlib.sha256(b"SATYA_APAAR_MASTER_ED25519_SEED_2026").digest()
            _cached_ed25519_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(demo_seed)
    
    return _cached_ed25519_private_key, _cached_ed25519_private_key.public_key()

def get_public_key_b64() -> str:
    _, pub_key = get_ed25519_keys()
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(pub_bytes).decode("utf-8")

def sign_claim(claim_dict: Dict[str, Any]) -> str:
    """Signs canonical JSON claim with AICTE Master Ed25519 Private Key."""
    canonical_json = json.dumps(claim_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
    priv_key, _ = get_ed25519_keys()
    signature = priv_key.sign(canonical_json)
    return base64.b64encode(signature).decode("utf-8")

def verify_claim_signature(claim_dict: Dict[str, Any], signature_b64: str, public_key_b64: Optional[str] = None) -> bool:
    """Verifies Ed25519 signature offline using public key only."""
    try:
        canonical_json = json.dumps(claim_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        sig_bytes = base64.b64decode(signature_b64)
        
        if public_key_b64:
            pub_bytes = base64.b64decode(public_key_b64)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        else:
            _, pub_key = get_ed25519_keys()
            
        pub_key.verify(sig_bytes, canonical_json)
        return True
    except Exception:
        return False

# SHA-256 Hash Chaining
def compute_sha256(data: Union[str, bytes, Dict[str, Any]]) -> str:
    if isinstance(data, dict):
        raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    elif isinstance(data, str):
        raw = data.encode('utf-8')
    else:
        raw = data
    return hashlib.sha256(raw).hexdigest()

def compute_audit_hash(sequence_number: int, timestamp_iso: str, user_id: str, action: str, entity_type: str, entity_id: str, payload_hash: str, previous_hash: str) -> str:
    """Computes tamper-evident SHA-256 block hash for audit log chaining."""
    block_content = f"{sequence_number}|{timestamp_iso}|{user_id}|{action}|{entity_type}|{entity_id}|{payload_hash}|{previous_hash}"
    return hashlib.sha256(block_content.encode("utf-8")).hexdigest()
