"""Auth routes: register, login, refresh, forgot/reset password, profile using MongoDB Atlas."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import get_database
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    create_email_verification_token, create_password_reset_token,
    decode_token
)
from app.core.deps import get_current_user
from app.core.utils import serialize_doc
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest,
    UserUpdate, ChangePasswordRequest
)
from app.services.email_service import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
):
    db = get_database()

    # Check email uniqueness
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username uniqueness
    if await db.users.find_one({"username": user_data.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Generate int ID for backward compatibility
    count = await db.users.count_documents({})
    user_doc = {
        "id": count + 1,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": hash_password(user_data.password),
        "avatar_url": None,
        "bio": None,
        "is_active": True,
        "is_admin": False,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_login": None,
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)

    # Send verification email
    token = create_email_verification_token(user_data.email)
    background_tasks.add_task(send_verification_email, user_data.email, user_data.username, token)

    return {"message": "Registration successful. Please check your email to verify your account."}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    db = get_database()
    user = await db.users.find_one({"email": credentials.email})

    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is deactivated")

    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    user_id_str = str(user.get("id", user["_id"]))
    access_token = create_access_token({"sub": user_id_str})
    refresh_token = create_refresh_token({"sub": user_id_str})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(serialize_doc(user)),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(data: RefreshRequest):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    db = get_database()
    user = await db.users.find_one({"$or": [{"id": int(user_id) if user_id.isdigit() else -1}, {"email": user_id}]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": str(user.get("id", user["_id"]))})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email")
async def verify_email(token: str):
    payload = decode_token(token)
    if payload.get("type") != "email_verify":
        raise HTTPException(status_code=400, detail="Invalid verification token")

    email = payload.get("sub")
    db = get_database()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one({"_id": user["_id"]}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
):
    db = get_database()
    user = await db.users.find_one({"email": data.email})
    if user:
        token = create_password_reset_token(user["email"])
        background_tasks.add_task(send_password_reset_email, user["email"], user["username"], token)
    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    payload = decode_token(data.token)
    if payload.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid reset token")

    email = payload.get("sub")
    db = get_database()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hash_password(data.new_password)}}
    )
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    update_data = {}
    if data.full_name is not None:
        update_data["full_name"] = data.full_name
    if data.bio is not None:
        update_data["bio"] = data.bio
    if data.avatar_url is not None:
        update_data["avatar_url"] = data.avatar_url

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.users.update_one({"id": current_user["id"]}, {"$set": update_data})
        current_user.update(update_data)

    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    db = get_database()
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"hashed_password": hash_password(data.new_password)}}
    )
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}
