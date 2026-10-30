import os, sqlite3
from pathlib import Path
from flask import Flask, jsonify, render_template, request

SCHEMA='''
CREATE TABLE IF NOT EXISTS advisors (advisor_id INTEGER PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL, email TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS students (student_id INTEGER PRIMARY KEY, student_code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, email TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS projects (project_id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', advisor_id INTEGER NOT NULL REFERENCES advisors(advisor_id), status TEXT NOT NULL DEFAULT 'planning' CHECK(status IN ('planning','in_progress','completed')), academic_year INTEGER NOT NULL DEFAULT 2569, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS project_members (member_id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE, student_id INTEGER NOT NULL REFERENCES students(student_id), role TEXT NOT NULL DEFAULT 'member', UNIQUE(project_id,student_id));
CREATE TABLE IF NOT EXISTS progress (progress_id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE, title TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', progress_percent INTEGER NOT NULL CHECK(progress_percent BETWEEN 0 AND 100), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
'''
def connect(path):
    c=sqlite3.connect(path);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c

def create_app(db_path=None):
    app=Flask(__name__)
    app.config['DB_PATH']=str(db_path or os.environ.get('DATABASE_PATH') or Path(__file__).with_name('portal.db'))
    with connect(app.config['DB_PATH']) as c:
        c.executescript(SCHEMA)
        if not c.execute('SELECT 1 FROM advisors').fetchone():
            c.executemany('INSERT INTO advisors(name,department,email) VALUES(?,?,?)',[('อาจารย์ที่ปรึกษา ก.','วิทยาการคอมพิวเตอร์','advisor1@example.edu'),('อาจารย์ที่ปรึกษา ข.','เทคโนโลยีสารสนเทศ','advisor2@example.edu')])
        if not c.execute('SELECT 1 FROM students').fetchone():
            c.executemany('INSERT INTO students(student_code,name,email) VALUES(?,?,?)',[('66010001','นักศึกษาตัวอย่าง 1','student1@example.edu'),('66010002','นักศึกษาตัวอย่าง 2','student2@example.edu')])
        if not c.execute('SELECT 1 FROM projects').fetchone():
            c.executemany('INSERT INTO projects(title,description,advisor_id,status,academic_year) VALUES(?,?,?,?,?)',[('ระบบจัดการกิจกรรมนักศึกษา','ระบบจัดการกิจกรรมและการลงทะเบียนออนไลน์',1,'in_progress',2569),('ระบบจองห้องประชุมออนไลน์','จัดการตารางห้องประชุมและการจอง',2,'planning',2569),('ระบบติดตามโครงงานนักศึกษา','ติดตามความก้าวหน้าและบันทึกผลการดำเนินงาน',1,'completed',2568)])
            c.execute('INSERT INTO project_members(project_id,student_id,role) VALUES(1,1,?)',('หัวหน้าโครงงาน',))
            c.execute('INSERT INTO progress(project_id,title,detail,progress_percent) VALUES(1,?,?,?)',('ออกแบบฐานข้อมูล','สร้างตารางและเชื่อมต่อ API',60))
    def err(message,status):return jsonify(success=False,error=message),status
    def one(c,id):
        row=c.execute('SELECT p.*,a.name advisor_name,a.department advisor_department FROM projects p JOIN advisors a ON p.advisor_id=a.advisor_id WHERE p.project_id=?',(id,)).fetchone()
        return dict(row) if row else None
    def check(d):
        if not isinstance(d,dict):return 'กรุณาส่ง JSON Object'
        if not isinstance(d.get('title'),str) or not 1<=len(d['title'].strip())<=150:return 'ชื่อโครงงานต้องมี 1–150 ตัวอักษร'
        if not isinstance(d.get('description',''),str) or len(d.get('description',''))>2000:return 'รายละเอียดไม่ถูกต้อง'
        if type(d.get('advisor_id')) is not int:return 'กรุณาเลือกอาจารย์ที่ปรึกษา'
        if d.get('status','planning') not in ('planning','in_progress','completed'):return 'สถานะไม่ถูกต้อง'
        if type(d.get('academic_year',2569)) is not int or not 2500<=d.get('academic_year',2569)<=2700:return 'ปีการศึกษาไม่ถูกต้อง'
    @app.get('/')
    def home():return render_template('index.html')
    @app.get('/api/health')
    def health():
        with connect(app.config['DB_PATH']) as c:c.execute('SELECT 1')
        return jsonify(success=True,database='connected')
    @app.get('/api/projects')
    def listing():
        with connect(app.config['DB_PATH']) as c:
            data=[dict(x) for x in c.execute('SELECT p.*,a.name advisor_name,a.department advisor_department FROM projects p JOIN advisors a ON p.advisor_id=a.advisor_id ORDER BY p.project_id DESC')]
        return jsonify(success=True,count=len(data),data=data)
    @app.get('/api/projects/<int:id>')
    def detail(id):
        with connect(app.config['DB_PATH']) as c:p=one(c,id)
        return jsonify(success=True,data=p) if p else err('ไม่พบโครงงาน',404)
    @app.post('/api/projects')
    def create():
        d=request.get_json(silent=True);e=check(d)
        if e:return err(e,400)
        with connect(app.config['DB_PATH']) as c:
            if not c.execute('SELECT 1 FROM advisors WHERE advisor_id=?',(d['advisor_id'],)).fetchone():return err('ไม่พบอาจารย์ที่ปรึกษา',404)
            cur=c.execute('INSERT INTO projects(title,description,advisor_id,status,academic_year) VALUES(?,?,?,?,?)',(d['title'].strip(),d.get('description',''),d['advisor_id'],d.get('status','planning'),d.get('academic_year',2569)))
            p=one(c,cur.lastrowid)
        return jsonify(success=True,data=p),201
    @app.put('/api/projects/<int:id>')
    def update(id):
        d=request.get_json(silent=True);e=check(d)
        if e:return err(e,400)
        with connect(app.config['DB_PATH']) as c:
            if not one(c,id):return err('ไม่พบโครงงาน',404)
            if not c.execute('SELECT 1 FROM advisors WHERE advisor_id=?',(d['advisor_id'],)).fetchone():return err('ไม่พบอาจารย์ที่ปรึกษา',404)
            c.execute('UPDATE projects SET title=?,description=?,advisor_id=?,status=?,academic_year=? WHERE project_id=?',(d['title'].strip(),d.get('description',''),d['advisor_id'],d.get('status','planning'),d.get('academic_year',2569),id))
            p=one(c,id)
        return jsonify(success=True,data=p)
    @app.delete('/api/projects/<int:id>')
    def remove(id):
        with connect(app.config['DB_PATH']) as c:
            if not c.execute('DELETE FROM projects WHERE project_id=?',(id,)).rowcount:return err('ไม่พบโครงงาน',404)
        return jsonify(success=True,message='ลบโครงงานสำเร็จ')
    @app.get('/api/advisors')
    def advisors():
        with connect(app.config['DB_PATH']) as c:data=[dict(x) for x in c.execute('SELECT * FROM advisors')]
        return jsonify(success=True,data=data)
    @app.get('/api/students')
    def students():
        with connect(app.config['DB_PATH']) as c:data=[dict(x) for x in c.execute('SELECT * FROM students')]
        return jsonify(success=True,data=data)
    @app.get('/api/projects/<int:id>/members')
    def members(id):
        with connect(app.config['DB_PATH']) as c:
            if not one(c,id):return err('ไม่พบโครงงาน',404)
            data=[dict(x) for x in c.execute('SELECT m.*,s.name,s.student_code FROM project_members m JOIN students s ON m.student_id=s.student_id WHERE m.project_id=?',(id,))]
        return jsonify(success=True,data=data)
    @app.post('/api/projects/<int:id>/members')
    def add_member(id):
        d=request.get_json(silent=True)
        if not isinstance(d,dict) or type(d.get('student_id')) is not int:return err('student_id ไม่ถูกต้อง',400)
        role=d.get('role','member')
        if not isinstance(role,str) or not 1<=len(role.strip())<=80:return err('role ไม่ถูกต้อง',400)
        with connect(app.config['DB_PATH']) as c:
            if not one(c,id):return err('ไม่พบโครงงาน',404)
            if not c.execute('SELECT 1 FROM students WHERE student_id=?',(d['student_id'],)).fetchone():return err('ไม่พบนักศึกษา',404)
            try:cur=c.execute('INSERT INTO project_members(project_id,student_id,role) VALUES(?,?,?)',(id,d['student_id'],role.strip()))
            except sqlite3.IntegrityError:return err('นักศึกษาเป็นสมาชิกอยู่แล้ว',409)
            mid=cur.lastrowid
        return jsonify(success=True,member_id=mid),201
    @app.get('/api/projects/<int:id>/progress')
    def progress(id):
        with connect(app.config['DB_PATH']) as c:
            if not one(c,id):return err('ไม่พบโครงงาน',404)
            data=[dict(x) for x in c.execute('SELECT * FROM progress WHERE project_id=? ORDER BY progress_id DESC',(id,))]
        return jsonify(success=True,data=data)
    @app.post('/api/projects/<int:id>/progress')
    def add_progress(id):
        d=request.get_json(silent=True)
        if not isinstance(d,dict) or not isinstance(d.get('title'),str) or not 1<=len(d['title'].strip())<=150:return err('title ไม่ถูกต้อง',400)
        if type(d.get('progress_percent')) is not int or not 0<=d['progress_percent']<=100:return err('progress_percent ต้องอยู่ระหว่าง 0–100',400)
        if not isinstance(d.get('detail',''),str):return err('detail ไม่ถูกต้อง',400)
        with connect(app.config['DB_PATH']) as c:
            if not one(c,id):return err('ไม่พบโครงงาน',404)
            cur=c.execute('INSERT INTO progress(project_id,title,detail,progress_percent) VALUES(?,?,?,?)',(id,d['title'].strip(),d.get('detail',''),d['progress_percent']))
            pid=cur.lastrowid
        return jsonify(success=True,progress_id=pid),201
    return app
if __name__=='__main__':create_app().run(port=int(os.environ.get('PORT',5000)),debug=os.environ.get('FLASK_DEBUG')=='1')
