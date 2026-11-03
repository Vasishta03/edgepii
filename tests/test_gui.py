from pathlib import Path

import pytest

from edgepii.gui import MODEL_SPECS, WEB_ROOT, current_rss_mib, public_model_specs, validate_request


def test_gui_request_validation():
    result = validate_request({
        "model": "distilbert",
        "context": "My name is Alice.",
        "question": "Who am I?",
        "policy": "context-aware",
        "threshold": 0.8,
    })
    assert result["context"] == "My name is Alice."
    assert result["threshold"] == 0.8


@pytest.mark.parametrize("payload", [
    {},
    {"model": "unknown", "context": "text"},
    {"model": "minilm", "context": "text", "policy": "context-aware", "question": ""},
    {"model": "bert", "context": "text", "threshold": 2},
])
def test_gui_rejects_invalid_requests(payload):
    with pytest.raises(ValueError):
        validate_request(payload)


def test_gui_assets_and_public_specs():
    assert set(public_model_specs()) == set(MODEL_SPECS)
    assert "detector" not in public_model_specs()["minilm"]
    for name in ("index.html", "styles.css", "app.js", "favicon.svg"):
        path = WEB_ROOT / name
        assert path.is_file()
        assert "\u2014" not in path.read_text()
    assert "[hidden] { display: none !important; }" in (WEB_ROOT / "styles.css").read_text()
    html = (WEB_ROOT / "index.html").read_text()
    script = (WEB_ROOT / "app.js").read_text()
    assert "RAM now" in html
    assert "<footer" not in html
    assert "Customer name: Anita Sharma. City: Bengaluru." in script
    assert "Phone number: 9876543210." not in script


def test_current_rss_is_positive():
    assert current_rss_mib() > 0
