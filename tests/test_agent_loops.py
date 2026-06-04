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
    assert "Active review rubric profile: ICLR" in client.calls[0][0]["content"]


def test_answer_agent_sees_prior_qa_for_impact_calibration(monkeypatch) -> None:
    """Prior Q&A should be visible when the AnswerAgent assigns impact level."""
    client = FakeClient(
        [
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The answer compares against prior QA.</answer>
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
    prior = [
        QAResult(
            question="Is the main claim supported?",
            answer="The main claim has a decisive flaw.",
            evidence=["paper: detailed evidence should not be rendered here"],
            review_impact=ReviewImpact(
                dimension="Soundness",
                polarity="weakness",
                impact_level="C1",
                confidence="high",
            ),
        )
    ]
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    AnswerAgent({"qa": {"max_answer_steps": 1}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
        prior_qa_results=prior,
    )

    prompt = client.calls[0][1]["content"]
    assert "Prior Q&A in this dimension for impact calibration" in prompt
    assert "Q1: Is the main claim supported?" in prompt
    assert "Answer: The main claim has a decisive flaw." in prompt
    assert "Prior impact: weakness, C1, confidence=high" in prompt
    assert "detailed evidence should not be rendered here" not in prompt


def test_answer_agent_retries_forced_answer_xml_parse_errors(monkeypatch) -> None:
    """Forced final answers should retry when the model emits invalid XML."""
    client = FakeClient(
        [
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The paper compares A & B without escaping the ampersand.</answer>
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
              <answer>The paper compares A &amp; B after retry.</answer>
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

    result = AnswerAgent(
        {
            "qa": {"max_answer_steps": 0},
            "xml": {"max_generation_attempts": 2},
        }
    ).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The paper compares A & B after retry."
    assert len(client.calls) == 2
    assert "Parser error: ParseError" in client.calls[1][-1]["content"]
    assert any(
        event.get("forced_answer") and event.get("attempt") == 2
        for event in result.trace_events
    )


def test_answer_agent_can_inspect_visual_before_answering(monkeypatch, tmp_path) -> None:
    """AnswerAgent should expose inspect_visual as the unified visual tool."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>inspect_visual</tool_name>
              <target>Figure 2</target>
              <focus>Check labels and caption readability.</focus>
              <rationale>Need focused visual evidence.</rationale>
            </tool_call>
            """,
            """
            <qa_result>
              <question>Are figures readable?</question>
              <answer>The visual inspection reports readable labels.</answer>
              <evidence><item source="pdf_image">Page 4 visual evidence.</item></evidence>
              <retrieved_papers></retrieved_papers>
              <review_impact>
                <dimension>Presentation</dimension>
                <polarity>strength</polarity>
                <impact_level>C1</impact_level>
                <confidence>medium</confidence>
              </review_impact>
            </qa_result>
            """,
        ]
    )
    calls = []
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    def fake_inspect(self, paper, target="", focus=""):
        calls.append((paper, target, focus))
        return "Figure 2 labels are readable."

    monkeypatch.setattr("reviewer.agents.answer.agent.VisualInspectionTool.inspect", fake_inspect)

    result = AnswerAgent({"qa": {"max_answer_steps": 3}}).run(
        "Are figures readable?",
        "Presentation",
        {"metadata": {"title": "Paper", "source_path": str(tmp_path / "paper.pdf")}},
        SUMMARY_XML,
    )

    assert result.review_impact.dimension == "Presentation"
    assert calls[0][1:] == ("Figure 2", "Check labels and caption readability.")
    assert "inspect_visual(target='Figure 2'" in client.calls[1][1]["content"]
    assert "Figure 2 labels are readable." in client.calls[1][1]["content"]


def test_answer_agent_shows_visual_asset_index(monkeypatch, tmp_path) -> None:
    """AnswerAgent should expose compact figure labels/pages for inspect_visual."""
    client = FakeClient(
        [
            """
            <qa_result>
              <question>Are figures readable?</question>
              <answer>The visual index is visible.</answer>
              <evidence><item source="paper">Figure index.</item></evidence>
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
    figure_path = tmp_path / "_page_4_Figure_2.jpeg"
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    AnswerAgent({"qa": {"max_answer_steps": 1}}).run(
        "Are figures readable?",
        "Presentation",
        {
            "metadata": {"title": "Paper"},
            "figures": [
                {
                    "label": "Figure 2",
                    "pdf_page": 5,
                    "path": str(figure_path),
                }
            ],
        },
        SUMMARY_XML,
    )

    prompt = client.calls[0][1]["content"]
    assert "Available visual assets for inspect_visual" in prompt
    assert "- Figure 2, PDF page 5" in prompt
    assert str(figure_path) not in prompt


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


def test_answer_agent_retries_after_mixed_tool_and_answer(monkeypatch) -> None:
    """If the model emits tool_call and qa_result together, AnswerAgent should retry."""
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
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
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
    assert len(client.calls) == 3
    assert "Previous output format error" in client.calls[1][1]["content"]
    assert "both <tool_call> and <qa_result>" in client.calls[1][1]["content"]
    assert "search_file('baseline')" in client.calls[2][1]["content"]
    assert any(event["event"] == "output_contract_violation" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_multiple_tool_calls_without_spending_tool_step(monkeypatch) -> None:
    """Multiple tool calls should be retried as a format error without spending a tool step."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
            <tool_call>
              <tool_name>read_file</tool_name>
              <start_line>1</start_line>
              <num_lines>2</num_lines>
              <rationale>Read the located evidence.</rationale>
            </tool_call>
            """,
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
              <answer>The forced answer follows the retried tool observation.</answer>
              <evidence><item source="paper">Evidence from search.</item></evidence>
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

    result = AnswerAgent({"qa": {"max_answer_steps": 1}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The forced answer follows the retried tool observation."
    assert "Previous output format error" in client.calls[1][1]["content"]
    assert "multiple <tool_call>" in client.calls[1][1]["content"]
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_falls_back_to_first_tool_call_after_format_retry_limit(
    monkeypatch,
) -> None:
    """After configured format retries, repeated multi-tool output should use the first call."""
    multi_tool_output = """
        <tool_call>
          <tool_name>search_file</tool_name>
          <keyword>baseline</keyword>
          <rationale>Need paper evidence.</rationale>
        </tool_call>
        <tool_call>
          <tool_name>read_file</tool_name>
          <start_line>1</start_line>
          <num_lines>2</num_lines>
          <rationale>Read the located evidence.</rationale>
        </tool_call>
        """
    client = FakeClient(
        [
            multi_tool_output,
            multi_tool_output,
            multi_tool_output,
            multi_tool_output,
            """
            <qa_result>
              <question>Are baselines sufficient?</question>
              <answer>The forced answer follows the fallback tool observation.</answer>
              <evidence><item source="paper">Evidence from fallback search.</item></evidence>
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

    result = AnswerAgent({"qa": {"max_answer_steps": 1, "max_format_retries": 3}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The forced answer follows the fallback tool observation."
    assert len(client.calls) == 5
    assert any(event["event"] == "output_contract_fallback" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_after_tool_call_and_qa_result(monkeypatch) -> None:
    """Mixed action and answer documents should still be rejected as ambiguous."""
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
              <answer>Premature answer.</answer>
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
              <answer>The retry returned one document.</answer>
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

    assert result.answer == "The retry returned one document."
    assert "both <tool_call> and <qa_result>" in client.calls[1][1]["content"]
    assert not any(event["event"] == "tool_observation" for event in result.trace_events)


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
        lambda self, question, dimension, paper, paper_summary, **kwargs: QAResult(
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

    def fake_answer(self, question, dimension, paper, paper_summary, **kwargs):
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
        lambda self, question, dimension, paper, paper_summary, **kwargs: QAResult(
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
    assert "Active review rubric profile: ICLR" in system_prompt


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

    def fake_answer(self, question, dimension, paper, paper_summary, **kwargs):
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


def test_presentation_agent_does_not_preload_visual_evidence(monkeypatch, tmp_path) -> None:
    """PresentationAgent should let AnswerAgent request visual evidence on demand."""
    client = FakeClient(
        [
            """
            <dimension_action>
              <action>write_review</action>
              <question></question>
              <rationale>No initial evidence was required.</rationale>
            </dimension_action>
            """,
            """
            <dimension_review>
              <dimension>Presentation</dimension>
              <score>3</score>
              <strengths><item>Readable structure.</item></strengths>
              <weaknesses></weaknesses>
              <evidence_summary>Review used available evidence.</evidence_summary>
              <rationale>Presentation is clear enough.</rationale>
            </dimension_review>
            """,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"fake")

    PresentationAgent({"agents": {"presentation": {"use_vlm": True, "require_balanced_qa": False}}}).run(
        {
            "id": "paper",
            "text": "paper",
            "metadata": {"title": "Paper", "source_path": str(pdf_path)},
        },
        SUMMARY_XML,
    )

    assert "VLM page observations" not in client.calls[1][1]["content"]
    assert "Inspect the PDF pages for presentation evidence" not in client.calls[1][1]["content"]


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
              <administrative_decision>clear</administrative_decision>
              <administrative_reasons></administrative_reasons>
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
    assert "<administrative_decision>clear</administrative_decision>" in output
    assert "<confidence_score>4</confidence_score>" in output
    assert "Active review rubric profile: ICLR" in client.calls[0][0]["content"]
