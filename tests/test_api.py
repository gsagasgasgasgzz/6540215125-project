import pytest
from app import create_app
@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path/'test.db');app.config['TESTING']=True
    return app.test_client()
def test_home_and_health(client):
    assert client.get('/').status_code==200
    assert client.get('/api/health').json['database']=='connected'
def test_crud(client):
    r=client.get('/api/projects');assert r.status_code==200 and r.json['count']==3
    d={'title':'โครงงานทดสอบ','description':'รายละเอียด','advisor_id':1,'status':'planning','academic_year':2569}
    r=client.post('/api/projects',json=d);assert r.status_code==201
    pid=r.json['data']['project_id'];assert client.get(f'/api/projects/{pid}').status_code==200
    d['title']='แก้ไขแล้ว';assert client.put(f'/api/projects/{pid}',json=d).json['data']['title']=='แก้ไขแล้ว'
    assert client.delete(f'/api/projects/{pid}').status_code==200
    assert client.get(f'/api/projects/{pid}').status_code==404
def test_validation(client):
    assert client.post('/api/projects',json={'title':'','advisor_id':1}).status_code==400
    assert client.post('/api/projects',json={'title':'x','advisor_id':999}).status_code==404
    assert client.post('/api/projects',json={'title':'x','advisor_id':True}).status_code==400
def test_related_api(client):
    assert client.get('/api/advisors').status_code==200
    assert client.get('/api/students').status_code==200
    assert client.get('/api/projects/1/members').status_code==200
    assert client.post('/api/projects/1/members',json={'student_id':2,'role':'Developer'}).status_code==201
    assert client.post('/api/projects/1/members',json={'student_id':2}).status_code==409
    assert client.get('/api/projects/1/progress').status_code==200
    assert client.post('/api/projects/1/progress',json={'title':'Sprint 2','progress_percent':80}).status_code==201
    assert client.post('/api/projects/1/progress',json={'title':'Bad','progress_percent':120}).status_code==400
