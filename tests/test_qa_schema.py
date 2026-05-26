"""Purpose: Tests for Q&A result schema and review-impact constraints."""

from reviewer.schemas.qa import QAResult, ReviewImpact, parse_qa_result_xml


def test_qa_result_accepts_simplified_review_impact() -> None:
    """QAResult should carry the simplified discrete impact labels."""
    result = QAResult(
        question="Are baselines sufficient?",
        answer="No. The answer explains why the issue matters.",
        review_impact=ReviewImpact(
            dimension="Soundness",
            polarity="weakness",
            impact_level="C2",
            confidence="high",
        ),
    )

    assert result.review_impact.impact_level == "C2"


def test_parse_qa_result_keeps_retrieved_abstract() -> None:
    """Parsed retrieved papers should include abstracts when the model emits them."""
    result = parse_qa_result_xml(
        """
        <qa_result>
          <question>Is this novel?</question>
          <answer>Partially.</answer>
          <evidence></evidence>
          <retrieved_papers>
            <paper>
              <title>Prior Work</title>
              <abstract>Prior abstract.</abstract>
              <year>2023</year>
              <url>https://example.test/prior</url>
              <relevance>Relevant.</relevance>
            </paper>
          </retrieved_papers>
          <review_impact>
            <dimension>Contribution</dimension>
            <polarity>weakness</polarity>
            <impact_level>C2</impact_level>
            <confidence>medium</confidence>
          </review_impact>
        </qa_result>
        """
    )

    assert result.retrieved_papers[0]["abstract"] == "Prior abstract."


def test_parse_qa_result_defaults_missing_impact_to_lowest_level() -> None:
    """Missing impact_level should not default to the highest-priority label."""
    result = parse_qa_result_xml(
        """
        <qa_result>
          <question>Is this important?</question>
          <answer>Unclear.</answer>
          <evidence></evidence>
          <retrieved_papers></retrieved_papers>
          <review_impact>
            <dimension>Contribution</dimension>
            <polarity>weakness</polarity>
            <confidence>low</confidence>
          </review_impact>
        </qa_result>
        """
    )

    assert result.review_impact.impact_level == "C3"
