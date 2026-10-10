from app.ai_services import _chunks, _cosine, gemini_config


def test_policy_chunks_keep_section_numbers():
    chunks = _chunks("Heading\n\nClause one.\n\nClause two.")
    assert [c["section"] for c in chunks] == [1, 2, 3]
    assert chunks[1]["text"] == "Clause one."


def test_cosine_similarity():
    assert abs(_cosine([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9
    assert abs(_cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9
    assert _cosine([], [1.0]) == 0.0


def test_gemini_config_has_safe_defaults(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_EMBEDDING_MODEL", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    config = gemini_config()
    assert config["api_key"] == ""
    assert config["model"] == "gemini-3.8-flash"
    assert config["embedding_model"] == "gemini-embedding-001"
