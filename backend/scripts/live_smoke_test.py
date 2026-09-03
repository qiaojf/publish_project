"""Run a full acceptance flow against the running local FastAPI service."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS  {message}")


class Api:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        expected: int = 200,
        **kwargs: Any,
    ) -> httpx.Response:
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.client.request(method, path, headers=headers, **kwargs)
        check(
            response.status_code == expected,
            f"{method} {path} -> {expected} (actual {response.status_code})",
        )
        return response

    def data(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.request(method, path, **kwargs)
        payload = response.json()
        check(payload.get("success") is True, f"{method} {path} uses the API envelope")
        return payload["data"]

    def login(self, username: str, password: str) -> str:
        result = self.data("POST", "/api/auth/login", json={"username": username, "password": password})
        check(result["user"]["username"] == username, f"login as {username}")
        return result["token"]


def create_ppt(api: Api, token: str, target_id: int, title: str) -> dict[str, Any]:
    return api.data(
        "POST",
        "/api/contents",
        token=token,
        expected=201,
        data={
            "title": title,
            "description": "本地全链路验收内容",
            "category": "培训材料",
            "content_type": "ppt",
            "publish_target_id": str(target_id),
        },
        files={
            "file": (
                "acceptance.pptx",
                b"local integration acceptance artifact",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = Api(args.base_url)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    health = api.data("GET", "/api/health")
    check(health["status"] == "ok", "FastAPI can reach PostgreSQL")
    swagger = api.request("GET", "/docs")
    check("swagger-ui" in swagger.text.lower(), "Swagger UI is available")
    openapi = api.request("GET", "/openapi.json").json()
    check(len(openapi.get("paths", {})) >= 25, "OpenAPI exposes the complete API surface")
    admin = api.login("admin", "admin123")
    employee = api.login("employee", "employee123")

    username = f"accept_{suffix}"
    user = api.data(
        "POST",
        "/api/users",
        token=admin,
        expected=201,
        json={
            "username": username,
            "name": "联调验收用户",
            "password": "accept123",
            "role": "employee",
            "status": "active",
        },
    )
    disabled = api.data("PATCH", f"/api/users/{user['id']}/status", token=admin, json={"status": "disabled"})
    check(disabled["status"] == "disabled", "admin can manage user status")
    deleted = api.data("DELETE", f"/api/users/{user['id']}", token=admin)
    check(deleted["deleted"] is True, "admin can delete an unused user")

    for forbidden_path in ("/api/users", "/api/reviews", "/api/logs/operations", "/api/publish-records"):
        api.request("GET", forbidden_path, token=employee, expected=403)

    employee_targets = api.data("GET", "/api/publish-targets", token=employee)
    check(employee_targets and all("publish_root" not in item and "base_url" not in item for item in employee_targets), "employee target payload is redacted")
    ppt_target = next(item for item in employee_targets if "ppt" in item["content_types"])

    title = f"联调发布闭环 {suffix}"
    content = create_ppt(api, employee, ppt_target["id"], title)
    content_id = content["id"]
    check(content["review_status"] == "draft" and content["publish_status"] == "unpublished", "content begins as an unpublished draft")
    submitted = api.data("POST", f"/api/contents/{content_id}/submit", token=employee)
    check(submitted["review_status"] == "pending", "employee submits a review")
    api.request(
        "PUT",
        f"/api/contents/{content_id}",
        token=employee,
        expected=409,
        data={"title": title, "content_type": "ppt", "publish_target_id": str(ppt_target["id"])},
    )
    hidden = api.data("GET", "/api/search", token=employee, params={"keyword": title})
    check(hidden["total"] == 0, "unpublished content is absent from search")

    detail = api.data("GET", f"/api/reviews/{content_id}", token=admin)
    check(detail["publish_target"].get("publish_root"), "admin review detail contains the physical publish path")
    check(detail["history"][0]["action"] == "submit", "review history uses the documented submit action")
    rejected = api.data(
        "POST",
        f"/api/reviews/{content_id}/reject",
        token=admin,
        json={"comment": "请补充联调验收说明"},
    )
    check(rejected["review_status"] == "rejected", "admin rejects content with a reason")
    changed = api.data(
        "PUT",
        f"/api/contents/{content_id}",
        token=employee,
        data={
            "title": f"{title} 已修改",
            "description": "已补充联调验收说明",
            "category": "培训材料",
            "content_type": "ppt",
            "publish_target_id": str(ppt_target["id"]),
        },
    )
    check(changed["title"].endswith("已修改"), "employee edits rejected content")
    api.data("POST", f"/api/contents/{content_id}/submit", token=employee)
    published = api.data(
        "POST",
        f"/api/reviews/{content_id}/approve",
        token=admin,
        json={"comment": "联调验收通过"},
    )
    check(published["review_status"] == "approved" and published["publish_status"] == "published", "approval triggers a successful publish")
    artifact = api.request("GET", published["view_url"], expected=200)
    check("files/source.pptx" in artifact.text, "published URL serves the generated artifact index")
    found = api.data("GET", "/api/search", token=employee, params={"keyword": title})
    check(found["total"] == 1 and found["items"][0]["view_url"] == published["view_url"], "published content is searchable with its backend URL")

    admin_targets = api.data("GET", "/api/publish-targets", token=admin)
    recovery_name = "E2E 发布失败恢复目标"
    recovery = next((item for item in admin_targets if item["name"] == recovery_name), None)
    blocker = (PROJECT_ROOT / "local-data" / "publish-root-blocker").resolve()
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("This file intentionally blocks directory creation during E2E.", encoding="utf-8")
    target_payload = {
        "name": recovery_name,
        "content_types": ["ppt"],
        "publish_root": str(blocker),
        "base_url": f"{args.base_url.rstrip('/')}/local-published/failure-recovery/",
        "enabled": True,
    }
    if recovery:
        recovery = api.data("PUT", f"/api/publish-targets/{recovery['id']}", token=admin, json=target_payload)
    else:
        recovery = api.data("POST", "/api/publish-targets", token=admin, expected=201, json=target_payload)

    failed_content = create_ppt(api, employee, recovery["id"], f"联调失败重发 {suffix}")
    api.data("POST", f"/api/contents/{failed_content['id']}/submit", token=employee)
    failed = api.data(
        "POST",
        f"/api/reviews/{failed_content['id']}/approve",
        token=admin,
        json={"comment": "触发失败路径"},
    )
    check(failed["review_status"] == "approved" and failed["publish_status"] == "failed", "publish failure preserves approved review state")

    valid_root = (PROJECT_ROOT / "local-data" / "published" / "failure-recovery").resolve()
    target_payload["publish_root"] = str(valid_root)
    api.data("PUT", f"/api/publish-targets/{recovery['id']}", token=admin, json=target_payload)
    retried = api.data("POST", f"/api/contents/{failed_content['id']}/republish", token=admin)
    check(retried["publish_status"] == "published", "failed content can be republished without a second review")

    records = api.data(
        "GET",
        "/api/publish-records",
        token=admin,
        params={"content_id": failed_content["id"], "page_size": 20},
    )
    statuses = [item["status"] for item in reversed(records["items"])]
    check(statuses[-2:] == ["failed", "success"], "publish history retains failed and successful attempts")
    operations = api.data("GET", "/api/logs/operations", token=admin, params={"page_size": 100})
    actions = {item["action"] for item in operations["items"]}
    check({"submit_content", "reject_content", "approve_content", "republish_content"}.issubset(actions), "operation log covers the business workflow")

    print("\nLIVE INTEGRATION ACCEPTANCE: PASS")
    print(f"Published content: {published['view_url']}")
    print(f"Republished content: {retried['view_url']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, httpx.HTTPError, StopIteration) as exc:
        print(f"\nLIVE INTEGRATION ACCEPTANCE: FAIL\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
