"""
OAuth 2.0 and OpenID Connect Handler
Handles OAuth authentication and token management
"""

import time
import json
import secrets
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import jwt


@dataclass
class OAuthClient:
    """OAuth 2.0 client configuration"""
    client_id: str
    client_secret_hash: str
    redirect_uris: list = field(default_factory=list)
    scopes: list = field(default_factory=list)
    grant_types: list = field(default_factory=lambda: ["authorization_code", "refresh_token"])
    is_active: bool = True


@dataclass
class OAuthToken:
    """OAuth token information"""
    access_token: str
    refresh_token: str
    client_id: str
    user_id: str
    scopes: list = field(default_factory=list)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    refresh_expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))


class OAuthHandler:
    """OAuth 2.0 and OpenID Connect handler"""
    
    def __init__(self, secret_key: str, issuer: str = "agenticquote"):
        self.secret_key = secret_key
        self.issuer = issuer
        self.clients: Dict[str, OAuthClient] = {}
        self.tokens: Dict[str, OAuthToken] = {}
        self.authorization_codes: Dict[str, Dict[str, Any]] = {}
        self.access_token_expiry = 3600  # 1 hour
        self.refresh_token_expiry = 2592000  # 30 days
    
    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: list,
        scopes: Optional[list] = None,
        grant_types: Optional[list] = None
    ) -> OAuthClient:
        """Register a new OAuth client"""
        client_secret_hash = self._hash_secret(client_secret)
        
        client = OAuthClient(
            client_id=client_id,
            client_secret_hash=client_secret_hash,
            redirect_uris=redirect_uris,
            scopes=scopes or ["read", "write"],
            grant_types=grant_types or ["authorization_code", "refresh_token"]
        )
        
        self.clients[client_id] = client
        return client
    
    def validate_client(self, client_id: str, client_secret: str) -> bool:
        """Validate OAuth client credentials"""
        client = self.clients.get(client_id)
        if not client or not client.is_active:
            return False
        
        client_secret_hash = self._hash_secret(client_secret)
        return client.client_secret_hash == client_secret_hash
    
    def generate_authorization_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scopes: list,
        state: Optional[str] = None
    ) -> str:
        """Generate an authorization code"""
        code = secrets.token_urlsafe(32)
        
        self.authorization_codes[code] = {
            "client_id": client_id,
            "user_id": user_id,
            "redirect_uri": redirect_uri,
            "scopes": scopes,
            "state": state,
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        return code
    
    def validate_authorization_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str
    ) -> Optional[Dict[str, Any]]:
        """Validate an authorization code"""
        auth_data = self.authorization_codes.get(code)
        
        if not auth_data:
            return None
        
        if auth_data["used"]:
            return None
        
        if auth_data["expires_at"] < datetime.now():
            return None
        
        if auth_data["client_id"] != client_id:
            return None
        
        if auth_data["redirect_uri"] != redirect_uri:
            return None
        
        # Mark as used
        auth_data["used"] = True
        return auth_data
    
    def generate_tokens(
        self,
        client_id: str,
        user_id: str,
        scopes: list
    ) -> OAuthToken:
        """Generate access and refresh tokens"""
        access_token = self._generate_jwt_token(
            user_id=user_id,
            scopes=scopes,
            token_type="access",
            expiry=self.access_token_expiry
        )
        
        refresh_token = self._generate_jwt_token(
            user_id=user_id,
            scopes=scopes,
            token_type="refresh",
            expiry=self.refresh_token_expiry
        )
        
        token = OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=datetime.now() + timedelta(seconds=self.access_token_expiry),
            refresh_expires_at=datetime.now() + timedelta(seconds=self.refresh_token_expiry)
        )
        
        self.tokens[access_token] = token
        return token
    
    def refresh_access_token(self, refresh_token: str) -> Optional[OAuthToken]:
        """Refresh an access token using a refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=["HS256"],
                issuer=self.issuer
            )
            
            if payload.get("token_type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            scopes = payload.get("scopes", [])
            client_id = payload.get("client_id")
            
            # Generate new tokens
            return self.generate_tokens(client_id, user_id, scopes)
        except jwt.InvalidTokenError:
            return None
    
    def validate_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token"""
        try:
            payload = jwt.decode(
                access_token,
                self.secret_key,
                algorithms=["HS256"],
                issuer=self.issuer
            )
            
            if payload.get("token_type") != "access":
                return None
            
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return None
    
    def revoke_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        tokens_to_revoke = [
            token for token, token_data in self.tokens.items()
            if token_data.user_id == user_id
        ]
        
        for token in tokens_to_revoke:
            del self.tokens[token]
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client information"""
        client = self.clients.get(client_id)
        if not client:
            return None
        
        return {
            "client_id": client.client_id,
            "redirect_uris": client.redirect_uris,
            "scopes": client.scopes,
            "grant_types": client.grant_types,
            "is_active": client.is_active
        }
    
    def _hash_secret(self, secret: str) -> str:
        """Hash a client secret"""
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _generate_jwt_token(
        self,
        user_id: str,
        scopes: list,
        token_type: str,
        expiry: int
    ) -> str:
        """Generate a JWT token"""
        now = datetime.now()
        
        payload = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": "agenticquote-api",
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=expiry)).timestamp(),
            "scopes": scopes,
            "token_type": token_type
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """Introspect a token (RFC 7662)"""
        token_data = self.tokens.get(token)
        
        if not token_data:
            return {"active": False}
        
        if token_data.expires_at < datetime.now():
            return {"active": False}
        
        return {
            "active": True,
            "scope": " ".join(token_data.scopes),
            "client_id": token_data.client_id,
            "user_id": token_data.user_id,
            "exp": int(token_data.expires_at.timestamp())
        }


# Global OAuth handler instance
oauth_handler = None


def get_oauth_handler(secret_key: str, issuer: str = "agenticquote") -> OAuthHandler:
    """Get or create the global OAuth handler"""
    global oauth_handler
    if oauth_handler is None:
        oauth_handler = OAuthHandler(secret_key, issuer)
    return oauth_handler
