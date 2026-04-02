"""Action Panel 엔드포인트 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# 인증 없이 401 반환
# ---------------------------------------------------------------------------

def test_action_panel_no_auth(client: TestClient):
    """인증 토큰 없으면 401 반환"""
    resp = client.post(
        "/api/v1/action-panel",
        json={"view": "sd-matrix", "context": {"userCategory": "INHOUSE_HR", "userPlan": "PRO"}},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# sd-matrix view, HEADHUNTER, RED signal → insight 반환
# ---------------------------------------------------------------------------

def test_action_panel_sd_matrix_headhunter_red(authed_client: TestClient, mock_user):
    """sd-matrix + HEADHUNTER + RED sdRatio → insight 포함 응답"""
    # mock_user는 STARTER 플랜이므로 sd-matrix는 접근 가능
    mock_user["plan"] = "PRO"
    resp = authed_client.post(
        "/api/v1/action-panel",
        json={
            "view": "sd-matrix",
            "context": {
                "userCategory": "HEADHUNTER",
                "userPlan": "PRO",
                "currentData": {"sdRatio": 0.3},
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert isinstance(data["insight"], str)
    assert len(data["insight"]) > 0
    # RED 시그널 HEADHUNTER 인사이트 포함 여부
    assert "수임료" in data["insight"] or "공급" in data["insight"]
    assert isinstance(data["actions"], list)
    assert isinstance(data["relatedViews"], list)
    assert data["isAiGenerated"] is False


# ---------------------------------------------------------------------------
# STARTER 플랜이 PRO 전용 뷰 요청 → locked=True, 빈 actions
# ---------------------------------------------------------------------------

def test_action_panel_starter_locked_view(authed_client: TestClient):
    """STARTER 플랜이 PRO 전용 뷰 요청 → locked=True 응답"""
    resp = authed_client.post(
        "/api/v1/action-panel",
        json={
            "view": "timeline",
            "context": {
                "userCategory": "INHOUSE_HR",
                "userPlan": "STARTER",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["locked"] is True
    assert data["actions"] == []


# ---------------------------------------------------------------------------
# 잘못된 view → graceful 기본 응답 반환 (에러 아님)
# ---------------------------------------------------------------------------

def test_action_panel_unknown_view_graceful(authed_client: TestClient, mock_user):
    """알 수 없는 view → 에러 없이 기본 응답 반환"""
    mock_user["plan"] = "PRO"
    resp = authed_client.post(
        "/api/v1/action-panel",
        json={
            "view": "unknown-view-xyz",
            "context": {
                "userCategory": "INHOUSE_HR",
                "userPlan": "PRO",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data["insight"], str)
    assert isinstance(data["actions"], list)
    assert isinstance(data["relatedViews"], list)


# ---------------------------------------------------------------------------
# 응답 구조 검증: insight, actions, relatedViews 필드 존재
# ---------------------------------------------------------------------------

def test_action_panel_response_structure(authed_client: TestClient, mock_user):
    """응답 구조에 필수 필드가 모두 존재하는지 검증"""
    mock_user["plan"] = "PRO"
    resp = authed_client.post(
        "/api/v1/action-panel",
        json={
            "view": "top-companies",
            "context": {
                "userCategory": "JOB_SEEKER",
                "userPlan": "PRO",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "insight" in data
    assert "actions" in data
    assert "relatedViews" in data
    assert "isAiGenerated" in data
    assert "locked" in data
    # actions 요소 구조 검증
    if data["actions"]:
        action = data["actions"][0]
        assert "priority" in action
        assert "text" in action
        assert action["priority"] in ("HIGH", "MEDIUM", "LOW")
