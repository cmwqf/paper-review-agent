"""Purpose: Tests for XML parsing and validation helpers."""

from reviewer.schemas.xml import root_tag
from reviewer.schemas.final_review import parse_final_review_xml
from reviewer.schemas.review import parse_dimension_review_xml
from reviewer.schemas.summary import parse_summary_xml, render_summary_for_agent
from reviewer.tools.xml_validator import validate_xml_root


def test_root_tag_reads_valid_xml() -> None:
    """Ensure basic XML parsing works."""
    assert root_tag("<paper_summary></paper_summary>") == "paper_summary"


def test_validate_xml_root_extracts_wrapped_xml() -> None:
    """Model text around XML should be stripped when the root tag is present."""
    xml = validate_xml_root("```xml\n<paper_summary></paper_summary>\n```", "paper_summary")
    assert xml == "<paper_summary></paper_summary>"


def test_validate_xml_root_extracts_first_matching_xml_document() -> None:
    """Multiple XML documents should not make the first target invalid."""
    xml = validate_xml_root(
        """
        <tool_call>
          <tool_name>search_file</tool_name>
        </tool_call>
        <tool_call>
          <tool_name>search_scholar</tool_name>
        </tool_call>
        """,
        "tool_call",
    )

    assert xml.strip() == "<tool_call>\n          <tool_name>search_file</tool_name>\n        </tool_call>"


def test_parse_summary_xml_to_paper_map() -> None:
    """Summary XML should parse into JSON-friendly paper map schema."""
    summary = parse_summary_xml(
        """
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
              <title>Introduction</title>
              <summary>Introduces the problem.</summary>
              <key_items>
                <item>
                  <type>problem</type>
                  <text>Problem statement.</text>
                  <location_hint>Section 1</location_hint>
                </item>
              </key_items>
            </section>
          </paper_map>
          <global_index>
            <claims><item section_ref="s1">Claim text.</item></claims>
            <baselines><item section_ref="s4">Baseline A.</item></baselines>
          </global_index>
        </paper_summary>
        """
    )

    assert summary.metadata.title == "Paper"
    assert summary.paper_map[0].section_id == "s1"
    assert summary.paper_map[0].key_items[0].type == "problem"
    assert summary.paper_map[0].key_items[0].location_hint == "Section 1"
    assert summary.global_index.claims[0].section_ref == "s1"
    assert summary.global_index.baselines[0].text == "Baseline A."


def test_render_summary_for_agent_includes_refs_and_location_hints() -> None:
    """Rendered summary should be compact and model-readable."""
    summary = parse_summary_xml(
        """
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
              <summary>Reports baselines and ablations.</summary>
              <key_items>
                <item>
                  <type>baseline</type>
                  <text>Baseline A is compared.</text>
                  <location_hint>Table 1</location_hint>
                </item>
              </key_items>
            </section>
          </paper_map>
          <global_index>
            <baselines><item section_ref="s1">Baseline A.</item></baselines>
          </global_index>
        </paper_summary>
        """
    )

    rendered = render_summary_for_agent(summary)
    assert "PAPER MAP" in rendered
    assert "[s1] Experiments" in rendered
    assert "baseline (Table 1): Baseline A is compared." in rendered
    assert "- [s1] Baseline A." in rendered


def test_parse_final_review_xml_uses_iclr_confidence_score() -> None:
    """Final review XML should parse the ICLR confidence score."""
    review = parse_final_review_xml(
        """
        <final_review>
          <final_score>6</final_score>
          <summary>Mixed paper.</summary>
          <strengths><item>Useful problem.</item></strengths>
          <weaknesses><item>Needs stronger baselines.</item></weaknesses>
          <requested_changes><item>Add comparisons.</item></requested_changes>
          <administrative_decision>desk_reject_risk</administrative_decision>
          <administrative_reasons>
            <item>Possible anonymity issue in the PDF.</item>
          </administrative_reasons>
          <recommendation>Reject</recommendation>
          <confidence_score>4</confidence_score>
        </final_review>
        """
    )

    assert review.final_score == 6
    assert review.confidence_score == 4
    assert review.recommendation == "Reject"
    assert review.administrative_decision == "desk_reject_risk"
    assert review.administrative_reasons == ["Possible anonymity issue in the PDF."]


def test_parse_final_review_xml_defaults_administrative_decision() -> None:
    """Older final review XML should default to no administrative issue."""
    review = parse_final_review_xml(
        """
        <final_review>
          <final_score>5</final_score>
          <summary>Mixed paper.</summary>
          <strengths></strengths>
          <weaknesses></weaknesses>
          <requested_changes></requested_changes>
          <recommendation>Reject</recommendation>
          <confidence_score>3</confidence_score>
        </final_review>
        """
    )

    assert review.administrative_decision == "clear"
    assert review.administrative_reasons == []


def test_parse_dimension_review_xml_reads_key_points() -> None:
    """Dimension review XML should preserve prioritized key points."""
    review = parse_dimension_review_xml(
        """
        <dimension_review>
          <dimension>Soundness</dimension>
          <score>2</score>
          <key_points>
            <item importance="C1" polarity="weakness" confidence="high" evidence_status="confirmed">Main claim lacks ablation evidence.</item>
          </key_points>
          <strengths><item>Clear setup.</item></strengths>
          <weaknesses><item>Missing ablations.</item></weaknesses>
          <evidence_summary>Table 1 lacks the ablation.</evidence_summary>
          <rationale>C1 weakness determines the score.</rationale>
        </dimension_review>
        """
    )

    assert review.key_points[0].importance == "C1"
    assert review.key_points[0].polarity == "weakness"
    assert review.key_points[0].confidence == "high"
    assert review.key_points[0].evidence_status == "confirmed"
    assert review.key_points[0].text == "Main claim lacks ablation evidence."
