from pydantic import BaseModel


class Token(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
