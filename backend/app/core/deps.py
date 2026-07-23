from fastapi import Depends, HTTPException, status
from bson import ObjectId
from app.core.database import get_database
from app.core.security import get_token_payload
from app.core.utils import serialize_doc


async def get_current_user(
    payload: dict = Depends(get_token_payload),
) -> dict:
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db = get_database()
    # Try finding user by int id or ObjectId string or email
    query = {"$or": [{"id": int(user_id) if user_id.isdigit() else -1}, {"email": user_id}]}
    if ObjectId.is_valid(user_id):
        query["$or"].append({"_id": ObjectId(user_id)})

    user = await db.users.find_one(query)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return serialize_doc(user)


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
