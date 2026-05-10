from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.llm.provider_factory import get_llm_provider
from app.main import create_app
from app.schemas import LookupExplanation


class FakeProvider:
    name = "fake"
    model_name = "fake-model"

    async def explain(self, text: str) -> LookupExplanation:
        return LookupExplanation(
            original=text,
            query_type="word",
            pronunciation="/test/",
            explanation="测试解释。",
            examples=[
                {
                    "english": "This is a test.",
                    "chinese": "这是一个测试。",
                }
            ],
            raw_response={"provider": "fake"},
        )


def build_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    return TestClient(app)


def test_create_and_list_lookup() -> None:
    client = build_client()

    created = client.post("/api/lookups", json={"text": "subtle"})

    assert created.status_code == 200
    body = created.json()
    assert body["original"] == "subtle"
    assert body["pronunciation"] == "/test/"
    assert body["examples"][0]["english"] == "This is a test."

    listed = client.get("/api/lookups")

    assert listed.status_code == 200
    assert listed.json()["items"][0]["original"] == "subtle"
