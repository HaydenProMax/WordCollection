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
        is_chinese = any("\u4e00" <= char <= "\u9fff" for char in text)
        query_type = "sentence" if " " in text or is_chinese else "word"
        return LookupExplanation(
            original=text,
            source_language="zh" if is_chinese else "en",
            target_language="en" if is_chinese else "zh",
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


def test_create_chinese_to_english_lookup() -> None:
    client = build_client()

    created = client.post("/api/lookups", json={"text": "我突然意识到我错了"})

    assert created.status_code == 200
    body = created.json()
    assert body["original"] == "我突然意识到我错了"
    assert body["source_language"] == "zh"
    assert body["target_language"] == "en"
    assert body["query_type"] == "sentence"


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


def test_export_json() -> None:
    client = build_client()
    client.post("/api/lookups", json={"text": "subtle"})

    exported = client.get("/api/export/json")

    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("application/json")
    assert "attachment" in exported.headers["content-disposition"]
    assert exported.json()["items"][0]["original"] == "subtle"
    assert exported.json()["items"][0]["source_language"] == "en"


def test_export_csv() -> None:
    client = build_client()
    client.post("/api/lookups", json={"text": "subtle"})

    exported = client.get("/api/export/csv")

    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert "attachment" in exported.headers["content-disposition"]
    assert "original" in exported.text
    assert "source_language" in exported.text
    assert "subtle" in exported.text
