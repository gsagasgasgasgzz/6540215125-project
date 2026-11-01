import unittest,tempfile,os
from pathlib import Path
import app as mod
class PortalTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  mod.DB=os.path.join(self.tmp.name,"test.sqlite3")
  mod.app.config["TESTING"]=True
  mod.init_db()
  self.c=mod.app.test_client()
  with mod.app.app_context():
   db=mod.conn()
   db.execute("INSERT INTO users(student_id,name,password_hash,role) VALUES(?,?,?,?)",(mod.ADMIN_ID,"Admin",mod.generate_password_hash("adminpass123"),"admin"))
   db.commit()
 def tearDown(self):self.tmp.cleanup()
 def login(self,sid=mod.ADMIN_ID,pw="adminpass123"):
  r=self.c.post("/api/login",json={"student_id":sid,"password":pw})
  self.assertEqual(r.status_code,200)
  return r.json["csrf"]
 def test_register_and_permissions(self):
  r=self.c.post("/api/register",json={"student_id":"1234567890","name":"Student A","password":"mypassword123"})
  self.assertEqual(r.status_code,201)
  token=self.login("1234567890","mypassword123")
  r=self.c.post("/api/projects",json={"title":"Test"},headers={"X-CSRF-Token":token})
  self.assertEqual(r.status_code,400)
 def test_crud_and_validation(self):
  token=self.login()
  h={"X-CSRF-Token":token}
  data={"title":"Test project","description":"Hello","academic_year":2569,"status":"planning","advisor_id":None}
  self.assertEqual(self.c.post("/api/projects",json={**data,"title":""},headers=h).status_code,400)
  self.assertEqual(self.c.post("/api/projects",json=data).status_code,403)
  r=self.c.post("/api/projects",json=data,headers=h)
  self.assertEqual(r.status_code,201);pid=r.json["project_id"]
  self.assertEqual(self.c.get("/api/projects").status_code,200)
  self.assertEqual(self.c.get(f"/api/projects/{pid}").status_code,200)
  self.assertEqual(self.c.put(f"/api/projects/{pid}",json={**data,"title":"Updated"},headers=h).status_code,200)
  self.assertEqual(self.c.delete(f"/api/projects/{pid}",headers=h).status_code,200)
  self.assertEqual(self.c.get(f"/api/projects/{pid}").status_code,404)
  self.assertTrue(any(x["action"]=="deleted" for x in self.c.get("/api/history").json["data"]))
if __name__=="__main__":unittest.main()
