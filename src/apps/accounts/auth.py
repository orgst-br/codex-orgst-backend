from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

User = get_user_model()

DEFAULT_ACCESS_MINUTES: int = getattr(settings, "JWT_ACCESS_MINUTES", 15)
JWT_ALGORITHM: str = getattr(settings, "JWT_ALGORITHM", "HS256")


def _jwt_secret() -> str:
    """
    Em produção, prefira usar uma env separada (JWT_SECRET).
    Se não existir, cai no SECRET_KEY do Django.
    """
    return getattr(settings, "JWT_SECRET", settings.SECRET_KEY)


def create_access_token(user: User, *, minutes: int | None = None) -> str:
    """
    Gera um JWT de acesso curto.
    Claims:
      - sub: id do usuário
      - typ: "access"
      - iat/exp: timestamps UTC
    """
    ttl = minutes if minutes is not None else DEFAULT_ACCESS_MINUTES
    now = datetime.now(UTC)

    payload = {
        "sub": str(user.id),
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }

    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


class JWTAuth(HttpBearer):
    """
    Autenticação Bearer para Django Ninja:
    - Lê Authorization: Bearer <token>
    - Valida JWT (HS256 por padrão)
    - Seta request.user com o usuário autenticado
    """

    def authenticate(self, request, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                _jwt_secret(),
                algorithms=[JWT_ALGORITHM],
                options={"require": ["exp", "iat", "sub"]},
            )

            # Só aceita access token aqui
            if payload.get("typ") != "access":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            user = User.objects.filter(id=user_id, is_active=True).first()
            if not user:
                return None

            # importante: manter request.user consistente para o resto do código
            request.user = user
            return user

        except jwt.ExpiredSignatureError:
            return None
        except jwt.PyJWTError:
            return None
