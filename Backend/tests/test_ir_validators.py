import pytest

from app.core.ir.models import AnalysisIR, Edge, IRValidationError, Node, NodeType
from app.core.ir.validators import validate_ir


def _ir(nodes, edges):
    return AnalysisIR(analysis_id="a", nodes=nodes, edges=edges)


def test_empty_ir_rejected():
    with pytest.raises(IRValidationError) as exc:
        validate_ir(_ir([], []))
    assert exc.value.code == "EMPTY_IR"


def test_duplicate_node_id_rejected():
    nodes = [
        Node(id="n1", type=NodeType.AGENT, name="A"),
        Node(id="n1", type=NodeType.INPUT, name="B"),
    ]
    with pytest.raises(IRValidationError) as exc:
        validate_ir(_ir(nodes, []))
    assert exc.value.code == "DUPLICATE_NODE_ID"


def test_dangling_edge_rejected():
    nodes = [Node(id="n1", type=NodeType.AGENT, name="A")]
    edges = [Edge(id="e1", source="n1", target="ghost", capability="read")]
    with pytest.raises(IRValidationError) as exc:
        validate_ir(_ir(nodes, edges))
    assert exc.value.code == "INVALID_IR"
    assert "ghost" in exc.value.message


def test_unknown_capability_rejected():
    nodes = [
        Node(id="n1", type=NodeType.AGENT, name="A"),
        Node(id="n2", type=NodeType.OUTPUT, name="B"),
    ]
    edges = [Edge(id="e1", source="n1", target="n2", capability="teleport")]
    with pytest.raises(IRValidationError) as exc:
        validate_ir(_ir(nodes, edges))
    assert exc.value.code == "UNKNOWN_CAPABILITY"
