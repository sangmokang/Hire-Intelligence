import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_user():
    """일반 STARTER 사용자 픽스처"""
    user = {"id": "test-uuid", "email": "test@test.com", "role": "USER", "plan": "STARTER"}

    async def override():
        return user

    app.dependency_overrides[get_current_user] = override
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_pro_user():
    """PRO 플랜 사용자 픽스처"""
    user = {"id": "pro-uuid", "email": "pro@test.com", "role": "USER", "plan": "PRO"}

    async def override():
        return user

    app.dependency_overrides[get_current_user] = override
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_admin():
    """SUPER_ADMIN 픽스처"""
    user = {"id": "admin-uuid", "email": "admin@test.com", "role": "SUPER_ADMIN", "plan": "ENTERPRISE"}

    async def override():
        return user

    app.dependency_overrides[get_current_user] = override
    yield user
    app.dependency_overrides.pop(get_current_user, None)
