import pytest
from config import Settings
from engine.pipeline import Pipeline
from fastapi.testclient import TestClient
from main import create_app
from storage.store import Store


class StubLLM:
    model_version = "transformer:stub"

    def __init__(self):
        self.reply = []

    async def load(self):
        pass

    def predict(self, text: str):
        return self.reply


@pytest.fixture
def client(tmp_path):
    stub = StubLLM()
    test_db = tmp_path / "test.db"
    s = Settings(db_path=test_db)
    store = Store(test_db)
    pipeline = Pipeline(s)
    pipeline.llm = stub

    app = create_app(
        settings_override=s,
        store_override=store,
        pipeline_override=pipeline,
    )
    with TestClient(app) as c:
        c.stub = stub
        yield c
