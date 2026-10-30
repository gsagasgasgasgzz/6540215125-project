import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path / "test.db")
    app.config["TESTING"]=True
    return app.test_client()

def test_activity_list(client):
    res=client.get("/api/activities")
    assert res.status_code==200
    assert len(res.get_json())==4

def test_activity_detail(client):
    res=client.get("/api/activities/1")
    assert res.status_code==200
    assert res.get_json()["title"]=="อบรมพัฒนาเว็บไซต์"

def test_register_and_duplicate(client):
    first=client.post("/api/registrations",json={"student_id":1,"activity_id":1})
    assert first.status_code==201
    second=client.post("/api/registrations",json={"student_id":1,"activity_id":1})
    assert second.status_code==409
    mine=client.get("/api/my-activities")
    assert len(mine.get_json())==1

def test_invalid_activity(client):
    assert client.post("/api/registrations",json={"student_id":1,"activity_id":999}).status_code==404
