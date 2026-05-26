from datetime import date

from reviewer.retrieval.types import RetrievedPaper
from reviewer.tools.retrieval_tool import RetrievalTool


class FakeSemanticScholarClient:
    def __init__(self):
        self.calls = []

    def search(self, query, limit):
        self.calls.append((query, limit))
        return [
            RetrievedPaper(
                title="Prior Work",
                abstract="Relevant baseline.",
                year=2023,
                publication_date=date(2023, 5, 1),
                url="https://example.com/prior",
                citation_count=12,
            )
        ]


class MultiResultSemanticScholarClient:
    def search(self, query, limit):
        return [
            RetrievedPaper(title="First", abstract="A", year=2021),
            RetrievedPaper(title="Second", abstract="B", year=2022),
            RetrievedPaper(title="Third", abstract="C", year=2023),
        ]


class FakeReranker:
    calls = []

    def __init__(self, config):
        self.config = config

    def rerank(self, query, papers, top_k):
        self.calls.append((query, [paper.title for paper in papers], top_k))
        return [papers[2], papers[0]][:top_k]


def test_retrieval_tool_uses_answer_agent_query_verbatim():
    config = {
        "retrieval": {
            "enabled": True,
            "search": {"limit_per_query": 7},
            "time_filter": {"enabled": True},
        }
    }
    tool = RetrievalTool(config)
    fake_client = FakeSemanticScholarClient()
    tool.client = fake_client

    results = tool.search(
        "ImageNet long-tailed recognition state of the art baselines",
        {"title": "Reviewed Paper Title", "submission_date": "2024-01-01"},
    )

    assert fake_client.calls == [
        ("ImageNet long-tailed recognition state of the art baselines", 7)
    ]
    assert results == [
        {
            "title": "Prior Work",
            "abstract": "Relevant baseline.",
            "year": 2023,
            "publication_date": "2023-05-01",
            "url": "https://example.com/prior",
            "citation_count": 12,
        }
    ]


def test_retrieval_tool_skips_empty_query():
    tool = RetrievalTool({"retrieval": {"enabled": True}})
    fake_client = FakeSemanticScholarClient()
    tool.client = fake_client

    assert tool.search("   ", {"title": "Reviewed Paper Title"}) == []
    assert fake_client.calls == []


def test_retrieval_tool_calls_reranker_when_enabled(monkeypatch):
    config = {
        "retrieval": {
            "enabled": True,
            "search": {"limit_per_query": 3},
            "time_filter": {"enabled": False},
            "rerank": {"enabled": True, "top_k": 2, "min_candidates": 2},
        }
    }
    FakeReranker.calls = []
    monkeypatch.setattr("reviewer.tools.retrieval_tool.Reranker", FakeReranker)
    tool = RetrievalTool(config)
    tool.client = MultiResultSemanticScholarClient()

    results = tool.search("agent-selected query", {})

    assert FakeReranker.calls == [("agent-selected query", ["First", "Second", "Third"], 2)]
    assert [result["title"] for result in results] == ["Third", "First"]
