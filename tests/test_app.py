import pytest

import app as app_module


@pytest.fixture
def client():
    """Provide an isolated Flask test client and task store."""
    original_tasks = app_module.tasks
    original_next_id = app_module.next_id
    app_module.tasks = [
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ]
    app_module.next_id = 3
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.tasks = original_tasks
    app_module.next_id = original_next_id


def test_index(client):
    """Return the task tracker page."""
    response = client.get('/')

    assert response.status_code == 200
    assert b'Task Tracker' in response.data


def test_get_tasks(client):
    """Return existing tasks with default priorities."""
    response = client.get('/api/tasks')

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "id": 1,
            "title": "Project-1 Report",
            "priority": "Medium"
        },
        {
            "id": 2,
            "title": "Project-2 MMFs",
            "priority": "Medium"
        }
    ]


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_supported_priorities(client, priority):
    """Create tasks for every supported priority."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()["priority"] == priority


@pytest.mark.parametrize('priority', [None, ""])
def test_add_task_missing_priority_defaults_to_medium(client, priority):
    """Default omitted or empty priorities to Medium."""
    payload = {"title": "Default priority task"}
    if priority is not None:
        payload["priority"] = priority

    response = client.post('/api/tasks', json=payload)

    assert response.status_code == 201
    assert response.get_json()["priority"] == "Medium"


@pytest.mark.parametrize('priority', ['Urgent', [], {}])
def test_add_task_rejects_invalid_priority(client, priority):
    """Reject unsupported and unhashable priority values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": priority}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "Priority must be Low, Medium, or High"
    )


def test_get_tasks_defaults_legacy_priority(client):
    """Expose Medium for legacy tasks without stored priorities."""
    app_module.tasks.append({"id": 3, "title": "Legacy task"})

    response = client.get('/api/tasks')

    assert response.status_code == 200
    assert response.get_json()[-1] == {
        "id": 3,
        "title": "Legacy task",
        "priority": "Medium"
    }


def test_add_task_success(client):
    """Create a task and return its stored priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "New task", "priority": "High"}
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "id": 3,
        "title": "New task",
        "priority": "High"
    }


def test_add_task_missing_title(client):
    """Reject a task without a title."""
    response = client.post('/api/tasks', json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Title is required"}


def test_delete_task(client):
    """Delete a task by identifier."""
    response = client.delete('/api/tasks/1')

    assert response.status_code == 200
    assert response.get_json() == {"result": "success"}
    assert client.get('/api/tasks').get_json()[0]["id"] == 2
