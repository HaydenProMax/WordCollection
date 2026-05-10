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

    def __init__(self) -> None:
        self.calls = 0

    async def explain(self, text: str) -> LookupExplanation:
        self.calls += 1
        query_type = "sentence" if " " in text else "word"
        return LookupExplanation(
            original=text,
            query_type=query_type,
            pronunciation="/test/",
            explanation=f"Test explanation {self.calls}.",
            examples=[
                {
                    "english": "This is a test.",
                    "chinese": "This is a test.",
                }
            ],
            raw_response={"provider": "fake", "calls": self.calls},
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

    provider = FakeProvider()
    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm_provider] = lambda: provider
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


def test_search_lookup_history() -> None:
    client = build_client()

    client.post("/api/lookups", json={"text": "subtle"})
    client.post("/api/lookups", json={"text": "dawn on"})

    found = client.get("/api/lookups", params={"q": "dawn"})

    assert found.status_code == 200
    items = found.json()["items"]
    assert len(items) == 1
    assert items[0]["original"] == "dawn on"


def test_filter_lookup_history_by_type() -> None:
    client = build_client()

    client.post("/api/lookups", json={"text": "subtle"})
    client.post("/api/lookups", json={"text": "dawn on"})

    found = client.get("/api/lookups", params={"query_type": "sentence"})

    assert found.status_code == 200
    items = found.json()["items"]
    assert len(items) == 1
    assert items[0]["original"] == "dawn on"


def test_delete_lookup() -> None:
    client = build_client()
    created = client.post("/api/lookups", json={"text": "subtle"}).json()

    deleted = client.delete(f"/api/lookups/{created['id']}")

    assert deleted.status_code == 204
    listed = client.get("/api/lookups")
    assert listed.json()["items"] == []


def test_regenerate_lookup_updates_existing_record() -> None:
    client = build_client()
    created = client.post("/api/lookups", json={"text": "subtle"}).json()

    regenerated = client.post(f"/api/lookups/{created['id']}/regenerate")

    assert regenerated.status_code == 200
    body = regenerated.json()
    assert body["id"] == created["id"]
    assert body["explanation"] == "Test explanation 2."
