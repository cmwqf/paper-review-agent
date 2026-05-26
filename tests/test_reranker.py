from datetime import date

from reviewer.models.reranker_client import RerankerClient
from reviewer.retrieval.reranker import Reranker
from reviewer.retrieval.types import RetrievedPaper


class FakeRankLLM:
    def __init__(self, output):
        self.output = output
        self.messages = None
        self.kwargs = None

    def generate(self, messages, **kwargs):
        self.messages = messages
        self.kwargs = kwargs
        return self.output


class FakeRankClient:
    def __init__(self, ranked_ids=None, error=None):
        self.ranked_ids = ranked_ids or []
        self.error = error
        self.calls = []

    def rank(self, query, candidates):
        self.calls.append((query, candidates))
        if self.error:
            raise self.error
        return self.ranked_ids


def test_reranker_client_parses_ranked_ids_from_chat_json():
    client = RerankerClient.__new__(RerankerClient)
    client.model_config = {"temperature": 0, "max_tokens": 128}
    client.client = FakeRankLLM('{"ranked_ids":["R2","R1"]}')

    ranked_ids = client.rank(
        "long-tailed recognition baselines",
        [
            {"id": "R1", "title": "First", "year": "2022", "abstract": "A"},
            {"id": "R2", "title": "Second", "year": "2023", "abstract": "B"},
        ],
    )

    assert ranked_ids == ["R2", "R1"]
    assert "long-tailed recognition baselines" in client.client.messages[1]["content"]
    assert client.client.kwargs["temperature"] == 0


def test_reranker_orders_model_ranked_papers_first():
    reranker = Reranker.__new__(Reranker)
    reranker.config = {}
    reranker.client = FakeRankClient(["R3", "R1"])
    papers = [
        RetrievedPaper(title="One", abstract="A", year=2021),
        RetrievedPaper(title="Two", abstract="B", year=2022),
        RetrievedPaper(title="Three", abstract="C", year=2023),
    ]

    ranked = reranker.rerank("query", papers, top_k=3)

    assert [paper.title for paper in ranked] == ["Three", "One", "Two"]


def test_reranker_falls_back_to_original_order_on_failure():
    reranker = Reranker.__new__(Reranker)
    reranker.config = {}
    reranker.client = FakeRankClient(error=RuntimeError("down"))
    papers = [
        RetrievedPaper(title="One", abstract="A", year=2021),
        RetrievedPaper(title="Two", abstract="B", year=2022),
    ]

    ranked = reranker.rerank("query", papers, top_k=1)

    assert [paper.title for paper in ranked] == ["One"]


def test_reranker_candidates_include_title_year_and_abstract():
    reranker = Reranker.__new__(Reranker)
    reranker.config = {}
    fake_client = FakeRankClient(["R1"])
    reranker.client = fake_client
    papers = [
        RetrievedPaper(
            title="Prior Work",
            abstract="Relevant abstract.",
            year=2023,
            publication_date=date(2023, 1, 1),
        )
    ]

    reranker.rerank("query", papers, top_k=1)

    assert fake_client.calls[0][1] == [
        {
            "id": "R1",
            "title": "Prior Work",
            "year": "2023",
            "abstract": "Relevant abstract.",
        }
    ]
