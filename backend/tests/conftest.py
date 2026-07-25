import pytest
import pytest_asyncio
import httpx
from mongomock_motor import AsyncMongoMockClient
from app.main import app
from app.core import database


@pytest.fixture(autouse=True)
def mock_mongo():
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["test_db"]
    database.client = mock_client
    database.db = mock_db
    yield
    mock_client.close()


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
