import sys
from pathlib import Path

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = BACKEND_ROOT / "tests" / "fixtures"
API = "http://127.0.0.1:8000/api"


def check(response: httpx.Response, expected: int = 200) -> dict:
    if response.status_code != expected:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
    return response.json()


def main() -> None:
    with httpx.Client(timeout=30) as client:
        login = check(client.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"}))
        headers = {"Authorization": f"Bearer {login['data']['token']}"}
        targets = check(client.get(f"{API}/publish-targets", headers=headers))["data"]
        file_target = next(item for item in targets if item["enabled"] and item["target_type"] == "local" and "file" in item["content_types"])
        ppt_target = next(item for item in targets if item["enabled"] and item["target_type"] == "local" and "ppt" in item["content_types"])

        readme = FIXTURES / "multi-file-readme.txt"
        data_file = FIXTURES / "multi-file-data.csv"
        with readme.open("rb") as first, data_file.open("rb") as second:
            created = check(client.post(
                f"{API}/contents",
                data={
                    "title": "Local 多文件真实联调", "description": "多文件目录发布验证",
                    "category": "测试", "content_type": "file", "publish_target_id": str(file_target["id"]),
                    "file_paths": ["资料/readme.txt", "资料/data.csv"],
                },
                files=[("files", (readme.name, first, "text/plain")), ("files", (data_file.name, second, "text/csv"))],
                headers=headers,
            ), 201)["data"]
        preview = check(client.get(f"{API}/contents/{created['id']}/preview", headers=headers))["data"]
        if preview["preview_type"] != "files" or len(preview["files"]) != 2 or preview.get("content"):
            raise RuntimeError("Multi-file preview contract failed")
        published = check(client.post(f"{API}/contents/{created['id']}/publish", headers=headers))["data"]
        page = client.get(published["view_url"])
        if page.status_code != 200 or "资料/readme.txt" not in page.text or "资料/data.csv" not in page.text:
            raise RuntimeError("Local multi-file published page failed")

        ppt = FIXTURES / "preview-check.pptx"
        with ppt.open("rb") as source:
            ppt_created = check(client.post(
                f"{API}/contents",
                data={"title": "PPT 文件预览真实联调", "category": "测试", "content_type": "ppt", "publish_target_id": str(ppt_target["id"])},
                files={"files": (ppt.name, source, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                headers=headers,
            ), 201)["data"]
        ppt_preview = check(client.get(f"{API}/contents/{ppt_created['id']}/preview", headers=headers))["data"]
        if ppt_preview["preview_type"] != "file" or ppt_preview["file_name"] != ppt.name:
            raise RuntimeError("PPT file preview contract failed")
        connection = check(client.post(f"{API}/publish-targets/{file_target['id']}/test", headers=headers))["data"]
        if connection != {"connected": True}:
            raise RuntimeError("Local target connection test failed")

        print(f"MULTI_CONTENT_ID={created['id']}")
        print(f"MULTI_PREVIEW_FILES={len(preview['files'])}")
        print(f"MULTI_VIEW_URL={published['view_url']}")
        print(f"PPT_CONTENT_ID={ppt_created['id']}")
        print(f"PPT_PREVIEW={ppt_preview['preview_type']}:{ppt_preview['file_name']}")
        print("LOCAL_TARGET_CONNECTION=true")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LIVE_SMOKE_FAILED={exc}", file=sys.stderr)
        raise
