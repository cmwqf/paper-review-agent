"""Purpose: Tests for Q&A, dimension, final, and workflow agent loops."""

from __future__ import annotations

from xml.sax.saxutils import escape

from reviewer.agents.answer.agent import AnswerAgent
from reviewer.agents.contribution.agent import ContributionAgent
from reviewer.agents.final.agent import FinalReviewAgent
from reviewer.agents.presentation.agent import PresentationAgent
from reviewer.agents.soundness.agent import SoundnessAgent
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

def end_answer_xml(
    *,
    question: str,
    answer: str,
    dimension: str = "Soundness",
    polarity: str = "weakness",
    impact_level: str = "C2",
    confidence: str = "medium",
    evidence: str = "Evidence.",
    evidence_source: str = "paper",
    retrieved_papers: str = "",
) -> str:
    """Build an end_answer tool call for AnswerAgent tests."""
    return f"""
    <tool_call>
      <tool_name>end_answer</tool_name>
      <question>{question}</question>
      <answer>{answer}</answer>
      <evidence><item source="{evidence_source}">{evidence}</item></evidence>
      <retrieved_papers>
        {retrieved_papers}
      </retrieved_papers>
      <review_impact>
        <dimension>{dimension}</dimension>
        <polarity>{polarity}</polarity>
        <impact_level>{impact_level}</impact_level>
        <confidence>{confidence}</confidence>
      </review_impact>
      <rationale>Enough evidence is available.</rationale>
    </tool_call>
    """


def dimension_tool_xml(
    *,
    tool_name: str,
    question: str | None = None,
    rationale: str = "Need evidence.",
) -> str:
    """Build a DimensionAgent question-stage tool call."""
    question_xml = f"\n      <question>{escape(question)}</question>" if question is not None else ""
    return f"""
    <tool_call>
      <tool_name>{tool_name}</tool_name>{question_xml}
      <rationale>{escape(rationale)}</rationale>
    </tool_call>
    """


def test_answer_agent_can_search_file_before_answering(monkeypatch) -> None:
    """AnswerAgent should execute tool actions before an end_answer tool call."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
            """,
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The paper mentions one baseline.",
                evidence="Line evidence from search.",
            ),
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
    assert len(client.calls) == 2
    assert "TOOL-CALL STAGE" in client.calls[0][0]["content"]
    assert "end_answer" in client.calls[0][0]["content"]
    assert "search_file" in client.calls[1][1]["content"]
    assert "For Soundness questions" in client.calls[0][0]["content"]
    assert "Active review rubric profile: ICLR" in client.calls[0][0]["content"]


def test_answer_agent_sees_prior_qa_for_impact_calibration(monkeypatch) -> None:
    """Prior Q&A should be visible when the AnswerAgent assigns impact level."""
    client = FakeClient(
        [
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The answer compares against prior QA.",
            ),
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
            <tool_call>
              <tool_name>end_answer</tool_name>
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
              <rationale>Enough evidence.</rationale>
            </tool_call>
            """,
            """
            <tool_call>
              <tool_name>end_answer</tool_name>
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
              <rationale>Enough evidence.</rationale>
            </tool_call>
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
            end_answer_xml(
                question="Are figures readable?",
                answer="The visual inspection reports readable labels.",
                dimension="Presentation",
                polarity="strength",
                impact_level="C1",
                evidence="Page 4 visual evidence.",
                evidence_source="visual",
            ),
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
            end_answer_xml(
                question="Are figures readable?",
                answer="The visual index is visible.",
                dimension="Presentation",
                polarity="strength",
                impact_level="C1",
                evidence="Figure index.",
            ),
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
            end_answer_xml(
                question="Is this novel?",
                answer="The retrieved work is relevant.",
                dimension="Contribution",
                evidence="Prior work found.",
                evidence_source="retrieval",
                retrieved_papers="""
                <paper>
                  <title>Calibration for Language Models</title>
                  <year>2023</year>
                  <url>https://example.test/paper</url>
                  <relevance>Relevant prior work.</relevance>
                </paper>
                """,
            ),
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


def test_answer_agent_can_run_python_before_answering(monkeypatch) -> None:
    """AnswerAgent should expose run_python for small evidence calculations."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>run_python</tool_name>
              <code><![CDATA[
baseline = 82.0
reported = [83.1, 84.0, 84.4]
print([round(value - baseline, 2) for value in reported])
              ]]></code>
              <rationale>Check the absolute improvements over baseline.</rationale>
            </tool_call>
            """,
            end_answer_xml(
                question="Are the reported gains consistent?",
                answer="The calculation shows gains of 1.1, 2.0, and 2.4 points.",
                polarity="strength",
                evidence="The numeric claim was checked with run_python.",
            ),
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 2}}).run(
        "Are the reported gains consistent?",
        "Soundness",
        {"text": "The baseline is 82.0 and reported results are 83.1, 84.0, 84.4."},
        SUMMARY_XML,
    )

    assert result.answer == "The calculation shows gains of 1.1, 2.0, and 2.4 points."
    assert "run_python" in client.calls[1][1]["content"]
    assert "[1.1, 2.0, 2.4]" in client.calls[1][1]["content"]
    assert any(
        event["event"] == "tool_call" and event["action"]["action"] == "run_python"
        for event in result.trace_events
    )


def test_answer_agent_retries_after_mixed_tool_and_answer(monkeypatch) -> None:
    """AnswerAgent should reject tool_call and qa_result mixed together."""
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
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The answer follows the actual tool observation.",
            ),
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
    assert "not valid <tool_call> stage XML" in client.calls[1][-1]["content"]
    assert "qa_result" in client.calls[1][-1]["content"]
    assert "search_file('baseline')" in client.calls[2][1]["content"]
    assert any(event["event"] == "stage_contract_violation" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_after_multiple_tool_calls(
    monkeypatch,
) -> None:
    """AnswerAgent should reject multiple tool_call documents and retry."""
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
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The answer follows the fallback tool observation.",
                evidence="Evidence from search.",
            ),
        ]
    )
    monkeypatch.setattr("reviewer.agents.answer.agent.build_llm", lambda config, model_key: client)

    result = AnswerAgent({"qa": {"max_answer_steps": 2}}).run(
        "Are baselines sufficient?",
        "Soundness",
        {"text": "Intro\nStrong baseline is used.", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert result.answer == "The answer follows the fallback tool observation."
    assert len(client.calls) == 3
    assert "Expected exactly one <tool_call>" in client.calls[1][-1]["content"]
    assert "search_file('baseline')" in client.calls[2][1]["content"]
    tool_calls = [
        event
        for event in result.trace_events
        if event["event"] == "tool_call" and event["action"]["action"] != "end_answer"
    ]
    assert len(tool_calls) == 1
    assert tool_calls[0]["action"]["action"] == "search_file"
    assert any(event["event"] == "stage_contract_violation" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_forced_answer_after_action_retry_when_budget_exhausted(monkeypatch) -> None:
    """After one valid tool step exhausts the budget, AnswerAgent forces end_answer."""
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
            """
            <tool_call>
              <tool_name>search_file</tool_name>
              <keyword>baseline</keyword>
              <rationale>Need paper evidence.</rationale>
            </tool_call>
            """,
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The forced answer follows the fallback tool observation.",
                evidence="Evidence from fallback search.",
            ),
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
    assert len(client.calls) == 3
    assert any(event["event"] == "stage_contract_violation" for event in result.trace_events)
    assert any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_after_tool_call_and_qa_result_before_answer(monkeypatch) -> None:
    """The single tool_call stage should reject action/answer XML and retry."""
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
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The retry returned one document.",
            ),
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
    assert "not valid <tool_call> stage XML" in client.calls[1][-1]["content"]
    assert "tool_call" in client.calls[1][-1]["content"]
    assert not any(event["event"] == "tool_observation" for event in result.trace_events)


def test_answer_agent_retries_after_unparseable_xml(monkeypatch) -> None:
    """Malformed XML should be retried without adding feedback observations."""
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>end_answer</tool_name>
            """,
            end_answer_xml(
                question="Are baselines sufficient?",
                answer="The retry returned a valid answer.",
            ),
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
    assert "not valid <tool_call> stage XML" in client.calls[1][-1]["content"]
    assert "No observations yet." in client.calls[1][1]["content"]


def test_dimension_agent_asks_question_then_writes_review(monkeypatch) -> None:
    """A dimension agent should call AnswerAgent for questions and then write a review."""
    client = FakeClient(
        [
            dimension_tool_xml(
                tool_name="ask_question",
                question="Are baselines sufficient?",
                rationale="Need evidence.",
            ),
            dimension_tool_xml(
                tool_name="end_questions",
                rationale="The Q&A trajectory is saturated.",
            ),
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <decisive_issues>
                <item qa_ids="CONTRIB-001" dimension_score_cap="2">Limited novelty evidence caps the contribution score.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>2</score>
              <key_points>
                <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Limited novelty evidence.</item>
              </key_points>
              <strengths><item>Interesting task.</item></strengths>
              <weaknesses><item>Limited novelty evidence.</item></weaknesses>
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
    assert len(client.calls) == 3


def test_dimension_agent_recovers_from_malformed_action_xml(monkeypatch) -> None:
    """A malformed question-stage tool call is reprompted, not allowed to crash the paper."""
    client = FakeClient(
        [
            # Turn 0: unescaped '<' makes the action XML not well-formed.
            """
            <tool_call>
              <tool_name>ask_question</tool_name>
              <question>Is x < y in all cases?</question>
              <rationale>Check the bound.</rationale>
            </tool_call>
            """,
            # Reprompt produces a valid action.
            dimension_tool_xml(
                tool_name="ask_question",
                question="Is x less than y in all cases?",
                rationale="Check the bound.",
            ),
            # Turn 1: end questions.
            dimension_tool_xml(
                tool_name="end_questions",
                rationale="The Q&A trajectory is saturated.",
            ),
            # Review writer produces the review.
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <decisive_issues>
                <item qa_ids="CONTRIB-001" dimension_score_cap="2">Limited novelty evidence caps the contribution score.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>2</score>
              <key_points>
                <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Limited novelty evidence.</item>
              </key_points>
              <strengths><item>Interesting task.</item></strengths>
              <weaknesses><item>Limited novelty evidence.</item></weaknesses>
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
    # malformed tool call + reprompt + end_questions + review = 4 model calls.
    assert len(client.calls) == 4


def test_dimension_agent_enforces_min_qa_turns(monkeypatch) -> None:
    """A dimension agent should not write a review before the configured minimum Q&A count."""
    client = FakeClient(
        [
            dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
            dimension_tool_xml(
                tool_name="ask_question",
                question="Is the contribution novel?",
                rationale="Need novelty evidence.",
            ),
            dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
            dimension_tool_xml(
                tool_name="ask_question",
                question="Is the impact broad?",
                rationale="Need impact evidence.",
            ),
            dimension_tool_xml(tool_name="end_questions", rationale="Minimum evidence met."),
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <decisive_issues>
                <item qa_ids="CONTRIB-001" dimension_score_cap="2">Novelty and impact limitations cap the contribution score.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>2</score>
              <key_points>
                <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Novelty and impact are limited.</item>
              </key_points>
              <strengths><item>Useful task.</item></strengths>
              <weaknesses><item>Novelty and impact are limited.</item></weaknesses>
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
            dimension_tool_xml(tool_name="ask_question", question="Question one?"),
            dimension_tool_xml(tool_name="ask_question", question="Question two?"),
            dimension_tool_xml(tool_name="ask_question", question="Question three?"),
            dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <decisive_issues>
                <item qa_ids="CONTRIB-001" dimension_score_cap="2">Limited novelty evidence caps the contribution score.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>2</score>
              <key_points>
                <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Limited novelty evidence.</item>
              </key_points>
              <strengths><item>Useful task.</item></strengths>
              <weaknesses><item>Limited novelty evidence.</item></weaknesses>
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
    assert "QUESTION TOOL-CALL STAGE" in system_prompt
    assert "<tool_name>ask_question</tool_name>" in system_prompt
    assert "<tool_name>end_questions</tool_name>" in system_prompt
    assert "For `end_questions`, include only `tool_name` and `rationale`" in system_prompt
    assert "Do not use `end_questions` or output `<dimension_review>`" in system_prompt
    assert "Active review rubric profile: ICLR" in system_prompt


def test_dimension_agent_rejects_direct_review_in_question_stage(monkeypatch) -> None:
    """The question stage should retry if the model emits a dimension_review directly."""
    review_xml = """
        <dimension_review>
          <dimension>Contribution</dimension>
          <decisive_issues>
            <item qa_ids="CONTRIB-001" dimension_score_cap="2">Limited novelty evidence caps the contribution score.</item>
          </decisive_issues>
          <dimension_judgment>
            <judgment_posture>limited_but_useful</judgment_posture>
            <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
          </dimension_judgment>
          <score>2</score>
          <key_points>
            <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Limited novelty evidence.</item>
          </key_points>
          <strengths><item>Useful task.</item></strengths>
          <weaknesses><item>Limited novelty evidence.</item></weaknesses>
          <rationale>Done.</rationale>
        </dimension_review>
        """
    client = FakeClient(
        [
            review_xml,
            dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
            review_xml,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)

    review_output = ContributionAgent(
        {"agents": {"contribution": {"max_qa_turns": 2, "require_balanced_qa": False}}}
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "<dimension>Contribution</dimension>" in review_output
    assert len(client.calls) == 3
    assert "not valid question-stage <tool_call> XML" in client.calls[1][-1]["content"]
    assert "Do not output <dimension_action> or <dimension_review>" in client.calls[1][-1]["content"]


def test_dimension_agent_rejects_end_questions_with_question(monkeypatch) -> None:
    """end_questions should not carry ask_question parameters."""
    review_xml = """
        <dimension_review>
          <dimension>Contribution</dimension>
          <decisive_issues>
            <item qa_ids="CONTRIB-001" dimension_score_cap="2">Limited novelty evidence caps the contribution score.</item>
          </decisive_issues>
          <dimension_judgment>
            <judgment_posture>limited_but_useful</judgment_posture>
            <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
          </dimension_judgment>
          <score>2</score>
          <key_points>
            <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Limited novelty evidence.</item>
          </key_points>
          <strengths><item>Useful task.</item></strengths>
          <weaknesses><item>Limited novelty evidence.</item></weaknesses>
          <rationale>Done.</rationale>
        </dimension_review>
        """
    client = FakeClient(
        [
            """
            <tool_call>
              <tool_name>end_questions</tool_name>
              <question>Should not be here.</question>
              <rationale>Enough evidence.</rationale>
            </tool_call>
            """,
            dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
            review_xml,
        ]
    )
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)

    review_output = ContributionAgent(
        {"agents": {"contribution": {"max_qa_turns": 2, "require_balanced_qa": False}}}
    ).run(
        {"text": "paper", "metadata": {"title": "Paper"}},
        SUMMARY_XML,
    )

    assert "<dimension>Contribution</dimension>" in review_output
    assert len(client.calls) == 3
    assert "end_questions must not include <question>" in client.calls[1][-1]["content"]
    assert "For end_questions include only <tool_name> and <rationale>" in client.calls[1][-1]["content"]


def test_dimension_review_writer_uses_dimension_specific_prompt(monkeypatch, tmp_path) -> None:
    """The final review writer should load Contribution/Soundness/Presentation-specific guidance."""
    outputs = []
    for dimension in ("Contribution", "Soundness", "Presentation"):
        outputs.extend(
            [
                dimension_tool_xml(tool_name="end_questions", rationale="Enough evidence."),
                f"""
                <dimension_review>
                  <dimension>{dimension}</dimension>
                  <decisive_issues>
                    <item qa_ids="{dimension.upper()}-001" dimension_score_cap="3">Dimension-specific evidence determines the score.</item>
                  </decisive_issues>
                  <dimension_judgment>
                    <judgment_posture>limited_but_useful</judgment_posture>
                    <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
                  </dimension_judgment>
                  <score>3</score>
                  <key_points>
                    <item importance="C2" polarity="strength" confidence="medium" evidence_status="confirmed">Supported dimension-specific strength.</item>
                  </key_points>
                  <strengths><item>Supported dimension-specific strength.</item></strengths>
                  <weaknesses></weaknesses>
                  <rationale>Dimension-specific prompt used.</rationale>
                </dimension_review>
                """,
            ]
        )
    client = FakeClient(outputs)
    monkeypatch.setattr("reviewer.agents.dimension_base.build_llm", lambda config, model_key: client)
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"fake")
    paper = {
        "id": "paper",
        "text": "paper",
        "metadata": {"title": "Paper", "source_path": str(pdf_path)},
    }

    ContributionAgent({"agents": {"contribution": {"require_balanced_qa": False}}}).run(paper, SUMMARY_XML)
    SoundnessAgent({"agents": {"soundness": {"require_balanced_qa": False}}}).run(paper, SUMMARY_XML)
    PresentationAgent({"agents": {"presentation": {"require_balanced_qa": False}}}).run(paper, SUMMARY_XML)

    writer_prompts = [client.calls[index][0]["content"] for index in (1, 3, 5)]
    assert "final Contribution dimension review" in writer_prompts[0]
    assert "novelty and originality" in writer_prompts[0]
    assert "final Soundness dimension review" in writer_prompts[1]
    assert "technical correctness" in writer_prompts[1]
    assert "final Presentation dimension review" in writer_prompts[2]
    assert "read, navigate, inspect, and verify" in writer_prompts[2]


def test_dimension_agent_enforces_strength_and_weakness_qa(monkeypatch) -> None:
    """A dimension agent should collect both strength and weakness Q&A before review."""
    client = FakeClient(
        [
            dimension_tool_xml(tool_name="end_questions", rationale="Ready."),
            dimension_tool_xml(
                tool_name="ask_question",
                question="What is the strongest contribution?",
                rationale="Need strength evidence.",
            ),
            dimension_tool_xml(tool_name="end_questions", rationale="Ready."),
            dimension_tool_xml(
                tool_name="ask_question",
                question="What is the main contribution weakness?",
                rationale="Need weakness evidence.",
            ),
            dimension_tool_xml(tool_name="end_questions", rationale="Ready."),
            """
            <dimension_review>
              <dimension>Contribution</dimension>
              <decisive_issues>
                <item qa_ids="CONTRIB-001" dimension_score_cap="3">Balanced evidence supports but caps the contribution score.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>3</score>
              <key_points>
                <item importance="C2" polarity="strength" confidence="medium" evidence_status="confirmed">Strong positive contribution.</item>
                <item importance="C2" polarity="weakness" confidence="medium" evidence_status="confirmed">Some limitation.</item>
              </key_points>
              <strengths><item>Strong positive contribution.</item></strengths>
              <weaknesses><item>Some limitation.</item></weaknesses>
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
            dimension_tool_xml(
                tool_name="end_questions",
                rationale="No initial evidence was required.",
            ),
            """
            <dimension_review>
              <dimension>Presentation</dimension>
              <decisive_issues>
                <item qa_ids="PRES-001" dimension_score_cap="3">Readable structure supports ordinary presentation quality.</item>
              </decisive_issues>
              <dimension_judgment>
                <judgment_posture>limited_but_useful</judgment_posture>
                <main_thesis>Evidence supports a limited dimension judgment.</main_thesis>
              </dimension_judgment>
              <score>3</score>
              <key_points>
                <item importance="C2" polarity="strength" confidence="medium" evidence_status="confirmed">Readable structure.</item>
              </key_points>
              <strengths><item>Readable structure.</item></strengths>
              <weaknesses></weaknesses>
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
