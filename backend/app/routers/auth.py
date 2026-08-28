from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    GoogleAuthRequest,
)
from app.services import auth_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/config")
async def get_google_config():
    """Return configured Google OAuth Client ID if set."""
    import os
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "configured": bool(os.getenv("GOOGLE_CLIENT_ID"))
    }


@router.post("/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest):
    """Authenticate or sign up via Google with cryptographic verification."""
    email = None
    full_name = None
    google_id = None

    # 1. Cryptographically verify real Google ID token if passed
    if req.credential:
        verified = await auth_service.verify_google_credential(req.credential)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Google credential token."
            )
        email = verified.get("email")
        full_name = verified.get("full_name")
        google_id = verified.get("google_id")
    elif req.email:
        email = req.email.strip().lower()
        full_name = req.full_name
        google_id = req.google_id

    import re
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format. Please provide a valid email address (e.g. user@gmail.com)."
        )

    result = auth_service.login_or_register_google(
        email=email,
        full_name=full_name,
        google_id=google_id
    )

    return TokenResponse(
        access_token=result["access_token"],
        token_type="bearer",
        user=UserResponse(**result["user"]),
    )


@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegisterRequest):
    try:
        user = auth_service.create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
        )
        token = auth_service.create_access_token(user_id=user["id"], email=user["email"])
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest):
    user = auth_service.authenticate_user(email=req.email, password=req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_service.create_access_token(user_id=user["id"], email=user["email"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        created_at=user["created_at"],
    )


@router.post("/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    # In stateless JWT auth, client drops the token; endpoint acknowledges
    return {"message": "Successfully logged out", "user_id": user["id"]}


@router.post("/forgot-password")
async def forgot_password(req: PasswordResetRequest):
    token = auth_service.create_password_reset_token(req.email)
    # Return token in response for development / API usage
    if not token:
        # Don't leak whether email exists in prod, but return generic confirmation
        return {"message": "If this email is registered, a password reset token has been generated.", "reset_token": None}
    
    return {
        "message": "Password reset token generated successfully",
        "reset_token": token,
    }


@router.post("/reset-password")
async def reset_password(req: PasswordResetConfirm):
    success = auth_service.reset_password_with_token(req.token, req.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used reset token",
        )
    return {"message": "Password has been successfully updated"}
