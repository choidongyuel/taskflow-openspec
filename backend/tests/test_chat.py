from tests.conftest import auth_headers, signup_and_login


def test_send_message_success(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.post(
        f"/teams/{team_id}/messages", json={"content": "안녕하세요"}, headers=team_owner_with_team["headers"]
    )
    assert resp.status_code == 201
    assert resp.json()["content"] == "안녕하세요"


def test_send_message_too_long(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    long_content = "가" * 1001
    resp = client.post(
        f"/teams/{team_id}/messages", json={"content": long_content}, headers=team_owner_with_team["headers"]
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "TOO_LONG"
    assert body["error"]["meta"]["limit"] == 1000


def test_send_message_non_member_forbidden(client, team_owner_with_team, signed_up_user):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.post(
        f"/teams/{team_id}/messages",
        json={"content": "hi"},
        headers=auth_headers(signed_up_user["token"]),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_list_messages_initial(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    client.post(f"/teams/{team_id}/messages", json={"content": "msg1"}, headers=headers)
    client.post(f"/teams/{team_id}/messages", json={"content": "msg2"}, headers=headers)

    resp = client.get(f"/teams/{team_id}/messages", headers=headers)
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2


def test_list_messages_since_incremental(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    client.post(f"/teams/{team_id}/messages", json={"content": "msg1"}, headers=headers)

    first_resp = client.get(f"/teams/{team_id}/messages", headers=headers)
    last_created_at = first_resp.json()[-1]["created_at"]

    resp = client.get(f"/teams/{team_id}/messages?since={last_created_at}", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_delete_message_by_author(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    msg = client.post(f"/teams/{team_id}/messages", json={"content": "delete me"}, headers=headers).json()
    resp = client.delete(f"/messages/{msg['id']}", headers=headers)
    assert resp.status_code == 200


def test_delete_message_by_others_forbidden_even_owner(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    invite_code = team_owner_with_team["team"]["invite_code"]

    member = signup_and_login(client, email="chat-member@example.com")
    member_headers = auth_headers(member["token"])
    client.post("/teams/join", json={"invite_code": invite_code}, headers=member_headers)

    msg = client.post(
        f"/teams/{team_id}/messages", json={"content": "member's message"}, headers=member_headers
    ).json()

    resp = client.delete(f"/messages/{msg['id']}", headers=team_owner_with_team["headers"])
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "NOT_OWNER"
