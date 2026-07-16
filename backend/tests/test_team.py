from tests.conftest import auth_headers, signup_and_login


def test_create_team_success(client, signed_up_user):
    headers = auth_headers(signed_up_user["token"])
    resp = client.post("/teams", json={"name": "Frontiers"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Frontiers"
    assert body["owner_id"] == signed_up_user["user"]["id"]
    assert "-" in body["invite_code"]


def test_create_team_already_in_team(client, team_owner_with_team):
    resp = client.post("/teams", json={"name": "Second"}, headers=team_owner_with_team["headers"])
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ALREADY_IN_TEAM"


def test_join_team_success(client, team_owner_with_team):
    joiner = signup_and_login(client, email="joiner@example.com")
    resp = client.post(
        "/teams/join",
        json={"invite_code": team_owner_with_team["team"]["invite_code"]},
        headers=auth_headers(joiner["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == team_owner_with_team["team"]["id"]


def test_join_team_invalid_format(client, signed_up_user):
    resp = client.post(
        "/teams/join", json={"invite_code": "bad-code"}, headers=auth_headers(signed_up_user["token"])
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_join_team_not_found(client, signed_up_user):
    resp = client.post(
        "/teams/join", json={"invite_code": "ZZZZ-9999"}, headers=auth_headers(signed_up_user["token"])
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_join_team_already_in_team(client, team_owner_with_team):
    other_owner = signup_and_login(client, email="other-owner@example.com")
    headers = auth_headers(other_owner["token"])
    client.post("/teams", json={"name": "Other"}, headers=headers)
    resp = client.post(
        "/teams/join",
        json={"invite_code": team_owner_with_team["team"]["invite_code"]},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ALREADY_IN_TEAM"


def test_get_team_success(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.get(f"/teams/{team_id}", headers=team_owner_with_team["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == team_id


def test_get_team_non_member_forbidden(client, team_owner_with_team, signed_up_user):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.get(f"/teams/{team_id}", headers=auth_headers(signed_up_user["token"]))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_list_members_success(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.get(f"/teams/{team_id}/members", headers=team_owner_with_team["headers"])
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["is_owner"] is True
