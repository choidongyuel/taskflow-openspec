from tests.conftest import auth_headers, signup_and_login


def _create_task(client, team_id, headers, title="Sample task", assignee_id=None):
    payload = {"title": title}
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id
    resp = client.post(f"/teams/{team_id}/tasks", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_task_success(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"], title="DB 마이그레이션")
    assert task["title"] == "DB 마이그레이션"
    assert task["status"] == "TODO"
    assert task["creator_id"] == team_owner_with_team["user"]["user"]["id"]


def test_create_task_non_member_forbidden(client, team_owner_with_team, signed_up_user):
    team_id = team_owner_with_team["team"]["id"]
    resp = client.post(
        f"/teams/{team_id}/tasks", json={"title": "x"}, headers=auth_headers(signed_up_user["token"])
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_list_tasks_all(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    _create_task(client, team_id, headers, title="Task 1")
    _create_task(client, team_id, headers, title="Task 2")
    resp = client.get(f"/teams/{team_id}/tasks", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_tasks_filter_me(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    owner_id = team_owner_with_team["user"]["user"]["id"]
    _create_task(client, team_id, headers, title="Mine", assignee_id=owner_id)
    _create_task(client, team_id, headers, title="Unassigned")
    resp = client.get(f"/teams/{team_id}/tasks?filter=me", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Mine"


def test_list_tasks_filter_unassigned(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    headers = team_owner_with_team["headers"]
    owner_id = team_owner_with_team["user"]["user"]["id"]
    _create_task(client, team_id, headers, title="Mine", assignee_id=owner_id)
    _create_task(client, team_id, headers, title="Unassigned")
    resp = client.get(f"/teams/{team_id}/tasks?filter=unassigned", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Unassigned"


def test_get_task_single(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"])
    resp = client.get(f"/tasks/{task['id']}", headers=team_owner_with_team["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == task["id"]


def test_update_task_title(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"])
    resp = client.put(
        f"/tasks/{task['id']}",
        json={"title": "수정된 제목", "assignee_id": None},
        headers=team_owner_with_team["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "수정된 제목"


def test_update_task_status_success(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"])
    resp = client.patch(
        f"/tasks/{task['id']}/status", json={"status": "DOING"}, headers=team_owner_with_team["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DOING"


def test_update_task_status_invalid_value(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"])
    resp = client.patch(
        f"/tasks/{task['id']}/status", json={"status": "ARCHIVED"}, headers=team_owner_with_team["headers"]
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_delete_task_by_creator(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    task = _create_task(client, team_id, team_owner_with_team["headers"])
    resp = client.delete(f"/tasks/{task['id']}", headers=team_owner_with_team["headers"])
    assert resp.status_code == 200


def test_delete_task_by_owner_overriding_others(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    invite_code = team_owner_with_team["team"]["invite_code"]
    member = signup_and_login(client, email="member@example.com")
    member_headers = auth_headers(member["token"])
    client.post("/teams/join", json={"invite_code": invite_code}, headers=member_headers)

    task = _create_task(client, team_id, member_headers, title="Member task")
    resp = client.delete(f"/tasks/{task['id']}", headers=team_owner_with_team["headers"])
    assert resp.status_code == 200


def test_delete_task_forbidden_for_other_member(client, team_owner_with_team):
    team_id = team_owner_with_team["team"]["id"]
    invite_code = team_owner_with_team["team"]["invite_code"]

    member_a = signup_and_login(client, email="member-a@example.com")
    member_a_headers = auth_headers(member_a["token"])
    client.post("/teams/join", json={"invite_code": invite_code}, headers=member_a_headers)

    member_b = signup_and_login(client, email="member-b@example.com")
    member_b_headers = auth_headers(member_b["token"])
    client.post("/teams/join", json={"invite_code": invite_code}, headers=member_b_headers)

    task = _create_task(client, team_id, member_a_headers, title="A's task")
    resp = client.delete(f"/tasks/{task['id']}", headers=member_b_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
