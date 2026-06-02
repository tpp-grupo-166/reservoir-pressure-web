"""Authentication router with register, login, and protected endpoints."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.user import User
from schemas.user_login_schema import UserLogin
from schemas.user_register_schema import UserRegister
from schemas.user_response_schema import UserResponse
from schemas.token_schema import Token

from repositories.user_service import UserService
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, decode_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/api")
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    user = UserService.find_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister) -> UserResponse:
    """Register a new user."""
    if UserService.find_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = User.create(user_data.email, hashed_password)
    UserService.save(user)
    return UserResponse(id=user.id, email=user.email)


@router.post("/auth/token", response_model=Token)
async def login(user_data: UserLogin) -> Token:
    """Login and return JWT token."""
    user = UserService.find_by_email(user_data.email)
    
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user's information."""
    return UserResponse(id=current_user.id, email=current_user.email)

@router.get("/users", response_model=list[UserResponse])
async def get_all_users() -> list[UserResponse]:
    """Get all users."""
    users = UserService.get_all()
    return [UserResponse(id=user.id, email=user.email) for user in users]

