import os,tempfile,unittest
import app as mod

class PortalV6Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  mod.DB=os.path.join(self.temp.name,'test.sqlite3')
  mod.IMAGE_DIR=os.path.join(self.temp.name,'images')
  mod.app.config['TESTING']=True
  mod.init_db()
  with mod.app.app_context():
   db=mod.conn()
   for sid,name,role in [(mod.ADMIN_ID,'Admin','admin'),('1111111111','Student','student'),('2222222222','Teacher','teacher')]:
    db.execute('INSERT INTO users(student_id,name,password_hash,role) VALUES(?,?,?,?)',(sid,name,mod.generate_password_hash('pass12345'),role))
   db.commit()
  self.c=mod.app.test_client()
 def tearDown(self):self.temp.cleanup()
 def login(self,sid):
  r=self.c.post('/api/login',json={'student_id':sid,'password':'pass12345'})
  self.assertEqual(r.status_code,200)
  return {'X-CSRF-Token':r.json['csrf']}
 def test_announcements_and_permissions(self):
  self.assertEqual(self.c.get('/api/announcements').status_code,401)
  h=self.login('1111111111')
  self.assertEqual(self.c.post('/api/announcements',data={'title':'Hello'},headers=h).status_code,403)
  h=self.login(mod.ADMIN_ID)
  self.assertEqual(self.c.post('/api/announcements',data={'title':'Maintenance','kind':'maintenance','body':'Scheduled'},headers=h).status_code,201)
  self.assertEqual(len(self.c.get('/api/announcements').json['data']),1)
 def test_board_and_comments(self):
  h=self.login('1111111111')
  data={'title':'Student project','description':'test','academic_year':2569,'status':'planning','advisor_id':None}
  r=self.c.post('/api/projects',json=data,headers=h)
  self.assertEqual(r.status_code,201);pid=r.json['project_id']
  r=self.c.post(f'/api/projects/{pid}/posts',data={'body':'Progress today'},headers=h)
  self.assertEqual(r.status_code,201)
  post=self.c.get(f'/api/projects/{pid}/posts').json['data'][0]
  self.assertEqual(self.c.post(f'/api/projects/{pid}/posts/{post["id"]}/comments',json={'body':'Great'},headers=h).status_code,201)
  self.assertEqual(self.c.delete(f'/api/projects/{pid}/posts/{post["id"]}',headers=h).status_code,200)
  self.assertEqual(self.c.get(f'/api/projects/{pid}/posts').json['data'],[])
  h=self.login('2222222222')
  self.assertEqual(self.c.post(f'/api/projects/{pid}/claim-advisor',headers=h).status_code,200)
  self.assertEqual(self.c.post(f'/api/projects/{pid}/claim-advisor',headers=h).status_code,409)
if __name__=='__main__':unittest.main()
