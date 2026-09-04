from app.main import app


def test_openapi_contains_required_operations() -> None:
    schema = app.openapi()
    required = {
        "/api/health", "/api/auth/login", "/api/auth/logout", "/api/auth/me",
        "/api/users", "/api/contents", "/api/contents/{content_id}/submit",
        "/api/contents/{content_id}/publish", "/api/contents/{content_id}/republish",
        "/api/contents/{content_id}/preview", "/api/contents/{content_id}/preview/file",
        "/api/contents/{content_id}/preview/files/{file_path}",
        "/api/reviews", "/api/reviews/{content_id}/approve",
        "/api/reviews/{content_id}/reject", "/api/publish-targets", "/api/publish-targets/{target_id}/test", "/api/publish-records",
        "/api/search", "/api/logs/operations", "/api/dashboard",
    }
    assert required.issubset(schema["paths"].keys())
    assert len(schema["paths"]) == 28
