from app.core.config import Settings


def test_settings_have_safe_local_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./storage/edusphere.db"
    assert settings.llm_provider == "mock"
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.gemini_text_model == "gemini-3.8-flash"
    assert settings.gemini_json_model == "gemini-3.8-flash"


def test_google_vertex_environment_names_are_supported(monkeypatch):
    monkeypatch.setenv("GEMINI_USE_VERTEX", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "project-v")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "global")

    settings = Settings(_env_file=None)

    assert settings.gemini_use_vertex is True
    assert settings.vertex_project == "project-v"
    assert settings.vertex_location == "global"


def test_settings_load_backend_env_file_from_repository_root(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=gemini\nGEMINI_USE_VERTEX=false\n")

    settings = Settings(_env_file=env_file)

    assert settings.llm_provider == "gemini"
    assert settings.gemini_use_vertex is False


def test_example_env_can_be_copied_for_a_fresh_checkout():
    from app.core.config import BACKEND_DIR

    settings = Settings(_env_file=BACKEND_DIR / ".env.example")
    assert settings.llm_provider == "mock"
    assert "http://127.0.0.1:5173" in settings.cors_origins
