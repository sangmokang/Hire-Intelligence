import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """각 테스트 후 dependency overrides 정리"""
    yield
    app.dependency_overrides.clear()


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


@pytest.fixture
def mock_db():
    """SQLAlchemy Session mock — query(), add(), commit(), refresh() 등 지원"""
    from unittest.mock import MagicMock
    from app.database import get_db

    db = MagicMock()
    # query chain mock: db.query(Model).filter(...).first() 등
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    # count chain
    db.query.return_value.filter.return_value.count.return_value = 0

    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_supabase():
    """Supabase 클라이언트 mock"""
    from unittest.mock import MagicMock
    from app.dependencies import get_supabase_client

    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "role": "USER",
        "plan": "STARTER",
    }
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    app.dependency_overrides[get_supabase_client] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_supabase_client, None)


@pytest.fixture
def authed_client(client, mock_user):
    """인증된 STARTER 사용자 클라이언트"""
    return client


@pytest.fixture
def pro_client(client, mock_pro_user):
    """인증된 PRO 사용자 클라이언트"""
    return client


@pytest.fixture
def admin_client(client, mock_admin):
    """인증된 ADMIN 클라이언트"""
    return client
