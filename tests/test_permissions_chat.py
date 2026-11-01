import os,tempfile,unittest
import app as mod
class PermissionsChatTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();mod.DB=os.path.join(self.tmp.name,'test.sqlite3');mod.app.config['TESTING']=True;mod.init_db();self.c=mod.app.test_client()
  with mod.app.app_context():
   db=mod.conn()
   for sid,role in [('6540215125','admin'),('1111111111','student'),('2222222222','student'),('3333333333','teacher')]:
    db.execute('INSERT INTO users(student_id,name,password_hash,role) VALUES(?,?,?,?)',(sid,sid,mod.generate_password_hash('testpassword'),role))
   db.commit()
 def tearDown(self):self.tmp.cleanup()
 def login(self,sid):
  r=self.c.post('/api/login',json={'student_id':sid,'password':'testpassword'});self.assertEqual(r.status_code,200);return {'X-CSRF-Token':r.json['csrf']}
 def test_student_owns_project_and_teacher_can_manage(self):
  h=self.login('1111111111');d={'title':'My project','description':'Original','academic_year':2569,'status':'planning','advisor_id':None}
  r=self.c.post('/api/projects',json=d,headers=h);self.assertEqual(r.status_code,201);pid=r.json['project_id']
  self.assertEqual(self.c.put(f'/api/projects/{pid}',json={**d,'description':'Edited'},headers=h).status_code,200)
  self.assertEqual(self.c.post(f'/api/projects/{pid}/progress',json={'note':'Updated','percent':25},headers=h).status_code,201)
  self.assertEqual(self.c.delete(f'/api/projects/{pid}',headers=h).status_code,403)
  self.assertEqual(self.c.put(f'/api/projects/{pid}',json={**d,'status':'completed'},headers=h).status_code,403)
  h=self.login('2222222222');self.assertEqual(self.c.put(f'/api/projects/{pid}',json=d,headers=h).status_code,403)
  h=self.login('6540215125');self.assertEqual(self.c.put(f'/api/projects/{pid}',json={**d,'advisor_id':'3333333333'},headers=h).status_code,200)
  h=self.login('3333333333');self.assertEqual(self.c.put(f'/api/projects/{pid}',json={**d,'advisor_id':'3333333333','status':'completed'},headers=h).status_code,200)
  self.assertEqual(self.c.delete(f'/api/projects/{pid}',headers=h).status_code,200)
 def test_chat_permissions(self):
  h=self.login('1111111111')
  self.assertEqual(self.c.post('/api/chat/6540215125',json={'body':'สวัสดี'},headers=h).status_code,201)
  self.assertEqual(self.c.post('/api/chat/3333333333',json={'body':'test'},headers=h).status_code,403)
  self.assertEqual(self.c.post('/api/chat/6540215125',json={'body':' '},headers=h).status_code,400)
  h=self.login('6540215125');self.assertEqual(len(self.c.get('/api/chat/1111111111').json['data']),1)
if __name__=='__main__':unittest.main()
