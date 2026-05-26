"""Purpose: Tests for Q&A, dimension, final, and workflow agent loops."""

from __future__ import annotations

from reviewer.agents.answer.agent import AnswerAgent
from reviewer.agents.contribution.agent import ContributionAgent
from reviewer.agents.final.agent import FinalReviewAgent
from reviewer.agents.presentation.agent import PresentationAgent
from reviewer.schemas.qa import QAResult, ReviewImpact


class FakeClient:
    """Return predefined model outputs in order."""

    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls = []

    def generate(self, messages):
        """Return the next fake output and record messages."""
        self.calls.append(messages)
        if not self.outputs:
            raise AssertionError("FakeClient has no outputs left.")
        return self.outputs.pop(0)


SUMMARY_XML = """
<paper_summary>
  <metadata>
    <title>Paper</title>
    <authors>unknown</authors>
    <venue>unknown</venue>
    <submission_date>2024-01-01</submission_date>
  </metadata>
  <paper_map>
    <section>
      <section_id>s1</section_id>
      <title>Experiments</title>
      <summary>Reports baselines.</summary>
      <key_items>
        <item><type>baseline</type><text>Baseline A.</text></item>
      </key_items>
    </section>
  </paper_map>
  <global_index>
    <baselines><item section_ref="s1">Baseline A.</item></baselines>
  </global_index>
</paper_summary>
"""


def test_answer_agent_can_search_file_before_answering(monkeypatch) -> None:
    """AnswerAgent should execute tool actions before parsing qa_result."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
            """,
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The paper mentions one baseline.</answer>
              <evidence><item source="paper">Line evidence from search.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Soundness</dimension>
                <polarity>weakness</polarity>
                <impact_level>C2</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The paper mentions one baseline."
    assert result.review_impact.dimension == "Soundness"
    assert "search_file" in client.calls[1][1]["content"]
    assert "For Soundness questions" in client.calls[0][0]["content"]


def test_answer_agent_can_read_pdf_before_answering(monkeypatch) -> None:
    """AnswerAgent should expose read_pdf as a tool action."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>read_pdf</tool_name>
              <start_page>2</start_page>
              <num_pages>1</num_pages>
              <rationale>Need page-level presentation evidence.</rationale>
            </tool_call>
            """,
            """
            <qa_result>
              <question>Are figures readable?</question>
              <answer>The page text suggests the figures are discussed clearly.</answer>
              <evidence><item source="pdf">Page 2 evidence.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Presentation</dimension>
                <polarity>neutral</polarity>
                <impact_level>C1</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Are figures readable?",
        "Presentation",
        {"pdf_pages": ["page one", "page two"], "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.review_impact.dimension == "Presentation"
    assert "read_pdf(start_page=2, num_pages=1)" in client.calls[1][1]["content"]
    assert "Page 2:\npage two" in client.calls[1][1]["content"]


def test_answer_agent_exposes_retrieval_abstracts(monkeypatch) -> None:
    """Scholar search observations and QA artifacts should keep abstracts."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_scholar</tool_name>
              <query>calibration language models</query>
              <rationale>Need prior work.</rationale>
            </tool_call>
            """,
            """
            <qa_result>
              <question>Is this novel?</question>
              <answer>The retrieved work is relevant.</answer>
              <evidence><item source="retrieval">Prior work found.</item></evidence>
              <retrieved_papers>
                <paper>
                  <title>Calibration for Language Models</title>
                  <year>2023</year>
                  <url>https://example.test/paper</url>
                  <relevance>Relevant prior work.</relevance>
                </paper>
              </retrieved_papers>
              <review_impact>
                <dimension>Contribution</dimension>
                <polarity>weakness</polarity>
                <impact_level>C2</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    retrieved = [
        {
            "title": "Calibration for Language Models",
            "abstract": "This paper studies calibration behavior in language models.",
            "year": 2023,
            "url": "https://example.test/paper",
            "citation_count": 7,
        }
    ]
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)
    monkeypatch.setattr(
        "reviewer.agents.answer.agent.RetrievalTool.search",
        lambda self, query, paper_metadata: retrieved,
    )

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Is this novel?",
        "Contribution",
        {"text": "Intro", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "Abstract: This paper studies calibration behavior" in client.calls[1][1]["content"]
    assert "URL:" not in client.calls[1][1]["content"]
    assert result.retrieved_papers[0]["abstract"] == retrieved[0]["abstract"]
    observation_event = next(
        event for event in result.trace_events if event["event"] == "tool_observation"
    )
    assert observation_event["retrieved_papers"][0]["abstract"] == retrieved[0]["abstract"]


def test_answer_agent_handles_multiple_xml_documents(monkeypatch) -> None:
    """If the model emits tool_call and qa_result together, AnswerAgent should run the tool first."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The answer is already included.</answer>
              <evidence><item source="paper">Evidence.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Soundness</dimension>
                <polarity>weakness</polarity>
                <impact_level>C2</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The answer follows the actual tool observation.</answer>
              <evidence><item source="paper">Evidence.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Soundness</dimension>
                <polarity>weakness</polarity>
                <impact_level>C2</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The answer follows the actual tool observation."
    assert len(client.calls) == 2
    assert "search_file('baseline')" in client.calls[1][1]["content"]
    assert any(event["event"] == "mixed_output_tool_call_prioritized" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_after_unparseable_xml(monkeypatch) -> None:
    """Malformed XML should be retried without adding feedback observations."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_file</tool_name>
            """,
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The retry returned a valid answer.</answer>
              <evidence><item source="paper">Evidence.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Soundness</dimension>
                <polarity>weakness</polarity>
                <impact_level>C2</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The retry returned a valid answer."
    assert "Previous model output could not be parsed" not in client.calls[1][1]["content"]
    assert "No observations yet." in client.calls[1][1]["content"]


def test_dimension_agent_asks_question_then_writes_review(monkeypatch) -> None:
    """A dimension agent should call AnswerAgent for questions and then write a review."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Are baselines sufficient?</question>
              <rationale>Need evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <score>2</score>
              <strengths><item>Interesting task.</item></strengths>
              <weaknesses><item>Limited novelty evidence.</item></weaknesses>
              <evidence_summary>One QA result.</evidence_summary>
              <rationale>Mixed contribution.</rationale>
            </dimension_review>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    monkeypatch.setattr(
        "reviewer.agents.dimension_base.AnswerAgent.run",
        lambda self, question, dimension, paper, paper_summary: QAResult(
            question=question,
            answer="One baseline is mentioned.",
            evidence=["paper: baseline line"],
            review_impact=ReviewImpact(
                dimension=dimension,
                polarity="weakness",
                impact_level="C2",
                confidence="medium",
            ),
        ),
    )

    review_xml = ContributionAgent(
        {"agents": {"contribution": {"max_qa_turns": 2, "require_balanced_qa": False}}}
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "<dimension>Contribution</dimension>" in review_xml
    assert len(client.calls) == 2


def test_dimension_agent_enforces_min_qa_turns(monkeypatch) -> None:
    """A dimension agent should not write a review before the configured minimum Q&A count."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>Enough evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Is the contribution novel?</question>
              <rationale>Need novelty evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <score>2</score>
              <strengths><item>Useful task.</item></strengths>
              <weaknesses><item>Novelty is unclear.</item></weaknesses>
              <evidence_summary>One QA result.</evidence_summary>
              <rationale>Enough evidence.</rationale>
            </dimension_review>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Is the impact broad?</question>
              <rationale>Need impact evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <score>2</score>
              <strengths><item>Useful task.</item></strengths>
              <weaknesses><item>Novelty and impact are limited.</item></weaknesses>
              <evidence_summary>Two QA results.</evidence_summary>
              <rationale>Minimum evidence met.</rationale>
            </dimension_review>
            """,
        ]
    )
    asked_questions = []
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)

    def fake_answer(self, question, dimension, paper, paper_summary):
        asked_questions.append(question)
        return QAResult(
            question=question,
            answer="Evidence collected.",
            evidence=["paper: evidence"],
            review_impact=ReviewImpact(
                dimension=dimension,
                polarity="weakness",
                impact_level="C2",
                confidence="medium",
            ),
        )

    monkeypatch.setattr("reviewer.agents.dimension_base.AnswerAgent.run", fake_answer)

    review_xml = ContributionAgent(
        {
            "agents": {
                "contribution": {
                    "min_qa_turns": 2,
                    "max_qa_turns": 4,
                    "require_balanced_qa": False,
                }
            }
        }
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "<dimension>Contribution</dimension>" in review_xml
    assert asked_questions == ["Is the contribution novel?", "Is the impact broad?"]
    assert "requires at least 2" in client.calls[1][1]["content"]
    assert "requires at least 2" in client.calls[3][1]["content"]


def test_dimension_agent_prompt_includes_configured_qa_limits(monkeypatch) -> None:
    """Dimension agent prompt should state configured minimum and maximum Q&A counts."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Question one?</question>
              <rationale>Need evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Question two?</question>
              <rationale>Need evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>Question three?</question>
              <rationale>Need evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <score>2</score>
              <strengths><item>Useful task.</item></strengths>
              <weaknesses><item>Limited novelty evidence.</item></weaknesses>
              <evidence_summary>Prompt only test.</evidence_summary>
              <rationale>Done.</rationale>
            </dimension_review>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    monkeypatch.setattr(
        "reviewer.agents.dimension_base.AnswerAgent.run",
        lambda self, question, dimension, paper, paper_summary: QAResult(
            question=question,
            answer="Evidence collected.",
            evidence=["paper: evidence"],
            review_impact=ReviewImpact(
                dimension=dimension,
                polarity="neutral",
                impact_level="C1",
                confidence="medium",
            ),
        ),
    )

    ContributionAgent(
        {
            "agents": {
                "contribution": {
                    "min_qa_turns": 3,
                    "max_qa_turns": 10,
                    "require_balanced_qa": False,
                }
            }
        }
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    system_prompt = client.calls[0][0]["content"]
    assert "at least 3 Q&A" in system_prompt
    assert "up to 10 question" in system_prompt
    assert "Do not return `write_review` or `<dimension_review>`" in system_prompt


def test_dimension_agent_enforces_strength_and_weakness_qa(monkeypatch) -> None:
    """A dimension agent should collect both strength and weakness Q&A before review."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>Ready.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>What is the strongest contribution?</question>
              <rationale>Need strength evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>Ready.</rationale>
            </dimension_action>
            """,
            """
            <dimension_action>
              <action>ask_question</action>
              <question>What is the main contribution weakness?</question>
              <rationale>Need weakness evidence.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <score>3</score>
              <strengths><item>Strong positive contribution.</item></strengths>
              <weaknesses><item>Some limitation.</item></weaknesses>
              <evidence_summary>Balanced evidence.</evidence_summary>
              <rationale>Balanced evidence met.</rationale>
            </dimension_review>
            """,
        ]
    )
    asked_questions = []
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)

    def fake_answer(self, question, dimension, paper, paper_summary):
        asked_questions.append(question)
        polarity = "strength" if "strongest" in question else "weakness"
        return QAResult(
            question=question,
            answer="Evidence collected.",
            evidence=["paper: evidence"],
            review_impact=ReviewImpact(
                dimension=dimension,
                polarity=polarity,
                impact_level="C2",
                confidence="medium",
            ),
        )

    monkeypatch.setattr("reviewer.agents.dimension_base.AnswerAgent.run", fake_answer)

    review_xml = ContributionAgent(
        {"agents": {"contribution": {"min_qa_turns": 0, "max_qa_turns": 4, "require_balanced_qa": True}}}
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "<dimension>Contribution</dimension>" in review_xml
    assert asked_questions == ["What is the strongest contribution?", "What is the main contribution weakness?"]
    assert "ask a question that can identify a strength" in client.calls[1][1]["content"]
    assert "ask a question that can identify a weakness" in client.calls[3][1]["content"]


def test_presentation_agent_uses_vlm_not_pdf_text(monkeypatch, tmp_path) -> None:
    """PresentationAgent should ground presentation in VLM page observations."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>PDF evidence is enough.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Presentation</dimension>
              <score>3</score>
              <strengths><item>Readable structure.</item></strengths>
              <weaknesses><item>Some figure references need detail.</item></weaknesses>
              <evidence_summary>PDF pages were inspected.</evidence_summary>
              <rationale>Presentation is mostly clear.</rationale>
            </dimension_review>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    monkeypatch.setattr(
        "reviewer.agents.presentation.agent.render_pdf_pages",
        lambda source_path, output_dir, max_pages, dpi: ["page_1.png"],
    )
    monkeypatch.setattr(
        "reviewer.agents.presentation.agent.VLMTool.inspect_pages",
        lambda self, page_images, questions: "VLM: Figure 1 is visible and captioned.",
    )
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"fake")

    PresentationAgent({"agents": {"presentation": {"use_vlm": True, "require_balanced_qa": False}}}).run(
        {
            "id": "paper",
            "text": "paper",
            "pdf_pages": ["Figure 1 is visible and captioned."],
            "metadata": {"title": "Paper", "source_path": str(pdf_path)},
        },
        SUMMARY_XML,
    )

    assert "Inspect the PDF pages for presentation evidence" in client.calls[1][1]["content"]
    assert "VLM: Figure 1 is visible and captioned." in client.calls[1][1]["content"]
    assert "Extracted PDF text" not in client.calls[1][1]["content"]


def test_presentation_agent_injects_vlm_observation(monkeypatch, tmp_path) -> None:
    """PresentationAgent should add VLM page observations when enabled."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>PDF and VLM evidence is enough.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Presentation</dimension>
              <score>3</score>
              <strengths><item>Readable figures.</item></strengths>
              <weaknesses></weaknesses>
              <evidence_summary>VLM inspected pages.</evidence_summary>
              <rationale>Presentation is clear.</rationale>
            </dimension_review>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    monkeypatch.setattr(
        "reviewer.agents.presentation.agent.render_pdf_pages",
        lambda source_path, output_dir, max_pages, dpi: ["page_1.png"],
    )
    monkeypatch.setattr(
        "reviewer.agents.presentation.agent.VLMTool.inspect_pages",
        lambda self, page_images, questions: "VLM: table text is legible.",
    )
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"fake")

    PresentationAgent(
        {
            "agents": {"presentation": {"use_vlm": True, "require_balanced_qa": False}},
            "paper": {"presentation_pdf_pages": 1},
        }
    ).run(
        {
            "id": "paper",
            "text": "paper",
            "pdf_pages": ["Figure 1 is visible."],
            "metadata": {"title": "Paper", "source_path": str(pdf_path)},
        },
        SUMMARY_XML,
    )

    assert "VLM page observations" in client.calls[1][1]["content"]
    assert "VLM: table text is legible." in client.calls[1][1]["content"]


def test_presentation_agent_requires_pdf_by_default(monkeypatch) -> None:
    """PresentationAgent should fail loudly when PDF evidence is unavailable."""
    client = FakeClient([])
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)

    try:
        PresentationAgent({}).run(
            {"text": "paper", "metadata": {"title": "Paper"}},
            SUMMARY_XML,
        )
    except ValueError as exc:
        assert "requires PDF evidence" in str(exc)
    else:
        raise AssertionError("PresentationAgent should require PDF evidence.")


def test_final_review_agent_returns_final_review_xml(monkeypatch) -> None:
    """FinalReviewAgent should validate final review XML."""
    client = FakeClient(
        [
            """
            <final_review>
              <final_score>6</final_score>
              <summary>Mixed paper.</summary>
              <strengths><item>Useful problem.</item></strengths>
              <weaknesses><item>Weak evidence.</item></weaknesses>
              <requested_changes><item>Add baselines.</item></requested_changes>
              <recommendation>Reject</recommendation>
              <confidence_score>4</confidence_score>
            </final_review>
            """
        ]
    )
    monkeypatch.setattr("reviewer.agents.final.agent.build_llm", lambda config, model_key: client)

    output = FinalReviewAgent({}).run(
        SUMMARY_XML,
        {"Contribution": "<dimension_review><dimension>Contribution</dimension></dimension_review>"},
    )

    assert "<recommendation>Reject</recommendation>" in output
    assert "<confidence_score>4</confidence_score>" in output
