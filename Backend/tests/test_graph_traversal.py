from app.core.graph.builder import build_graph
from app.core.graph.traversal import CapabilityGraph
from app.core.ir.normalizer import normalize
from app.core.parser.adapters import generic_adapter
from app.core.parser.yaml_loader import load_yaml_text

from .conftest import fixture_text


def _cg(name: str) -> CapabilityGraph:
    ir = normalize(generic_adapter.load(load_yaml_text(fixture_text(name)), "a"))
    return CapabilityGraph(build_graph(ir))


def test_selectors_identify_risky_nodes():
    cg = _cg("hiresmart_generic.yaml")
    assert cg.untrusted_inputs() == ["input_web_form"]
    assert set(cg.sensitive_assets()) == {"asset_cv_attachments", "asset_ats_database"}
    assert cg.external_outputs() == ["output_email_candidate"]


def test_paths_from_untrusted_input_to_external_output():
    cg = _cg("hiresmart_generic.yaml")
    paths = cg.find_paths_to_external_output()
    assert paths, "expected at least one untrusted-input -> external-output path"
    # The exfiltration path must route through the sensitive CV asset.
    assert any("asset_cv_attachments" in p for p in paths)


def test_capabilities_on_path():
    cg = _cg("hiresmart_generic.yaml")
    path = next(p for p in cg.find_paths_to_external_output() if "asset_cv_attachments" in p)
    caps = cg.capabilities_on_path(path)
    assert "read" in caps and "send" in caps


def test_reachable_nodes():
    cg = _cg("hiresmart_generic.yaml")
    reachable = cg.get_reachable_nodes("input_web_form")
    assert "output_email_candidate" in reachable
