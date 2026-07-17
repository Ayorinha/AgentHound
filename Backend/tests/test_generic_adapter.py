import pytest

from app.core.ir.models import IRValidationError, NodeType
from app.core.ir.normalizer import normalize
from app.core.parser.adapters import generic_adapter
from app.core.parser.yaml_loader import load_yaml_text

from .conftest import fixture_text


def _load(name: str):
    data = load_yaml_text(fixture_text(name))
    ir = generic_adapter.load(data, "test-analysis")
    return normalize(ir)


def test_generic_adapter_builds_ir():
    ir = _load("hiresmart_generic.yaml")
    assert ir.metadata.name == "HireSmart Copilot"
    assert len(ir.nodes) == 7
    assert len(ir.edges) == 6
    inputs = ir.nodes_of_type(NodeType.INPUT)
    assert inputs[0].properties["trust_level"] == "untrusted"


def test_normalizer_fills_safe_defaults():
    ir = _load("hiresmart_generic.yaml")
    communicator = ir.node_map()["agent_candidate_communicator"]
    # autonomy_level not declared for this agent -> safe default full_auto
    assert communicator.properties["autonomy_level"] == "full_auto"
    output = ir.node_map()["output_email_candidate"]
    assert output.properties["approval_gate_present"] is False


def test_normalizer_canonicalizes_enum_casing():
    data = {
        "nodes": [
            {"id": "in1", "type": "input", "name": "Form", "properties": {"trust_level": "Untrusted"}},
            {"id": "as1", "type": "data_asset", "name": "DB", "properties": {"sensitivity": " High "}},
            {"id": "out1", "type": "output", "name": "Email", "properties": {"boundary": "EXTERNAL"}},
        ]
    }
    ir = normalize(generic_adapter.load(data, "a"))
    props = ir.node_map()
    assert props["in1"].properties["trust_level"] == "untrusted"
    assert props["as1"].properties["sensitivity"] == "high"
    assert props["out1"].properties["boundary"] == "external"


def test_normalizer_coerces_boolean_properties():
    # Any property whose catalog default is a boolean must be coerced, so a
    # quoted YAML "false"/"true" becomes a real bool rather than a truthy string.
    data = {
        "nodes": [
            {
                "id": "t1",
                "type": "tool",
                "name": "T",
                "properties": {"requires_approval": "true", "sandbox_enabled": "false"},
            },
            {"id": "o1", "type": "output", "name": "O", "properties": {"approval_gate_present": "false"}},
        ]
    }
    ir = normalize(generic_adapter.load(data, "a"))
    props = ir.node_map()
    assert props["t1"].properties["requires_approval"] is True
    assert props["t1"].properties["sandbox_enabled"] is False
    assert props["o1"].properties["approval_gate_present"] is False


def test_missing_nodes_rejected():
    with pytest.raises(IRValidationError):
        generic_adapter.load({"metadata": {"name": "x"}}, "a")


def test_invalid_node_type_rejected():
    data = {"nodes": [{"id": "n1", "type": "wizard", "name": "N"}]}
    with pytest.raises(IRValidationError):
        generic_adapter.load(data, "a")


def test_nodes_as_mapping_rejected_clearly():
    # A mapping instead of a list must fail with a clear list-type error.
    data = {"nodes": {"n1": {"type": "agent", "name": "N"}}}
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load(data, "a")
    assert exc.value.code == "INVALID_INPUT"
    assert "list" in exc.value.message


def test_empty_mapping_nodes_rejected_as_type_error():
    # An empty mapping is falsy but not a list; it must be an INVALID_INPUT type
    # error, not EMPTY_IR (which is reserved for a missing key or an empty list).
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load({"nodes": {}}, "a")
    assert exc.value.code == "INVALID_INPUT"
    assert "list" in exc.value.message


def test_empty_list_nodes_rejected_as_empty_ir():
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load({"nodes": []}, "a")
    assert exc.value.code == "EMPTY_IR"


def test_non_mapping_properties_rejected():
    data = {"nodes": [{"id": "n1", "type": "agent", "name": "N", "properties": ["oops"]}]}
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load(data, "a")
    assert exc.value.code == "INVALID_INPUT"


def test_non_mapping_metadata_rejected():
    data = {"metadata": "just a string", "nodes": [{"id": "n1", "type": "agent", "name": "N"}]}
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load(data, "a")
    assert exc.value.code == "INVALID_INPUT"


def test_non_list_controls_rejected():
    data = {"controls": {"c1": {}}, "nodes": [{"id": "n1", "type": "agent", "name": "N"}]}
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load(data, "a")
    assert exc.value.code == "INVALID_INPUT"


def test_falsy_non_list_edges_rejected():
    # An empty mapping is falsy but not a list; it must be rejected, not
    # silently treated as "no edges".
    data = {"edges": {}, "nodes": [{"id": "n1", "type": "agent", "name": "N"}]}
    with pytest.raises(IRValidationError) as exc:
        generic_adapter.load(data, "a")
    assert exc.value.code == "INVALID_INPUT"
