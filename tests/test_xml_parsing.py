"""Purpose: Tests for XML parsing and validation helpers."""

from reviewer.schemas.xml import root_tag
from reviewer.schemas.summary import parse_summary_xml
from reviewer.tools.xml_validator import validate_xml_root


def test_root_tag_reads_valid_xml() -> None:
    """Ensure basic XML parsing works."""
    assert root_tag("<paper_summary></paper_summary>") == "paper_summary"


def test_validate_xml_root_extracts_wrapped_xml() -> None:
    """Model text around XML should be stripped when the root tag is present."""
    xml = validate_xml_root("```xml\n<paper_summary></paper_summary>\n```", "paper_summary")
    assert xml == "<paper_summary></paper_summary>"


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
                <item><type>problem</type><text>Problem statement.</text></item>
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
    assert summary.global_index.claims[0].section_ref == "s1"
    assert summary.global_index.baselines[0].text == "Baseline A."
