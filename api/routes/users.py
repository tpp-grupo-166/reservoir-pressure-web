"""User and auth endpoints. Thin HTTP adapter over System."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.system import System
from domain.errors import (
    InvalidEmailError,
    InvalidPasswordError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from schemas.user_login_schema import UserLogin
from schemas.user_register_schema import UserRegister
from schemas.user_response_schema import UserResponse
from schemas.token_schema import Token
from routes.dependencies import get_system

router = APIRouter(prefix="/api")
_bearer = HTTPBearer()


def _get_system_from_bearer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    system: System = Depends(get_system),
) -> tuple[str, System]:
    """Extract bearer token and return it alongside the System instance."""
    return credentials.credentials, system


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, system: System = Depends(get_system)) -> UserResponse:
    try:
        user = await system.register_user(user_data.email, user_data.password)
        return UserResponse(id=user.id, email=user.email)
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/auth/token", response_model=Token)
async def login(user_data: UserLogin, system: System = Depends(get_system)) -> Token:
    try:
        token = await system.login(user_data.email, user_data.password)
        return Token(access_token=token, token_type="bearer")
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e),
                            headers={"WWW-Authenticate": "Bearer"})


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    payload: tuple = Depends(_get_system_from_bearer),
) -> UserResponse:
    token, system = payload
    try:
        user = await system.get_user_from_token(token)
        return UserResponse(id=user.id, email=user.email)
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials",
                            headers={"WWW-Authenticate": "Bearer"})


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(system: System = Depends(get_system)) -> list[UserResponse]:
    users = await system.get_all_users()
    return [UserResponse(id=u.id, email=u.email) for u in users]
