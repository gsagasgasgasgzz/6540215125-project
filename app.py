
import os, re, sqlite3, secrets, argparse, getpass, sys, uuid
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, g, send_from_directory, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, UnidentifiedImageError

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get("DATABASE_PATH",os.path.join(BASE,"portal.sqlite3"))
UPLOAD_DIR=os.path.join(BASE,"uploads")
app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE")=="1",MAX_CONTENT_LENGTH=5*1024*1024)
ADMIN_ID="6540215125"
STATUSES=("planning","in_progress","completed","archived")

def conn():
    if "db" not in g:
        g.db=sqlite3.connect(DB)
        g.db.row_factory=sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db
@app.teardown_appcontext
def close(e):
    db=g.pop("db",None)
    if db: db.close()

def init_db():
    with app.app_context():
        db=conn()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          student_id TEXT PRIMARY KEY, name TEXT NOT NULL,
          password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student'
          CHECK(role IN ('student','teacher','admin')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 150),
          description TEXT NOT NULL DEFAULT '', academic_year INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'planning' CHECK(status IN ('planning','in_progress','completed','archived')),
          advisor_id TEXT REFERENCES users(student_id) ON DELETE SET NULL,
          created_by TEXT NOT NULL REFERENCES users(student_id),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS project_members (
          project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
          PRIMARY KEY(project_id,student_id)
        );
        CREATE TABLE IF NOT EXISTS progress (
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          note TEXT NOT NULL, percent INTEGER NOT NULL CHECK(percent BETWEEN 0 AND 100),
          created_by TEXT NOT NULL REFERENCES users(student_id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, project_title TEXT NOT NULL,
          action TEXT NOT NULL, actor_id TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cols={r[1] for r in db.execute("PRAGMA table_info(users)")}
        if "avatar" not in cols:db.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          sender_id TEXT NOT NULL REFERENCES users(student_id),
          recipient_id TEXT NOT NULL REFERENCES users(student_id),
          project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
          body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
          is_read INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        db.executescript("""
        CREATE TABLE IF NOT EXISTS announcements (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '',
          image TEXT, kind TEXT NOT NULL DEFAULT 'news',
          created_by TEXT NOT NULL REFERENCES users(student_id),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS project_posts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          body TEXT NOT NULL DEFAULT '', image TEXT,
          author_id TEXT NOT NULL REFERENCES users(student_id),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CHECK(length(body)>0 OR image IS NOT NULL)
        );
        CREATE TABLE IF NOT EXISTS post_comments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL REFERENCES project_posts(id) ON DELETE CASCADE,
          author_id TEXT NOT NULL REFERENCES users(student_id), body TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        db.commit()

def user():
    sid=session.get("sid")
    return conn().execute("SELECT student_id,name,role,avatar FROM users WHERE student_id=?",(sid,)).fetchone() if sid else None
def login_required(fn):
    @wraps(fn)
    def inner(*a,**k):
        if not user(): return jsonify(error="กรุณาเข้าสู่ระบบ"),401
        return fn(*a,**k)
    return inner
def csrf_required(fn):
    @wraps(fn)
    def inner(*a,**k):
        if request.headers.get("X-CSRF-Token") != session.get("csrf") or not session.get("csrf"):
            return jsonify(error="CSRF token ไม่ถูกต้อง"),403
        return fn(*a,**k)
    return inner
def payload():
    d=request.get_json(silent=True)
    return d if isinstance(d,dict) else {}
def log(db,pid,title,action,details=""):
    db.execute("INSERT INTO audit_log(project_id,project_title,action,actor_id,details) VALUES(?,?,?,?,?)",
               (pid,title,action,user()["student_id"],details))
def is_project_student(project):
    u=user()
    if not u or u["role"]!="student": return False
    sid=u["student_id"]
    return project["created_by"]==sid or bool(conn().execute(
        "SELECT 1 FROM project_members WHERE project_id=? AND student_id=?",(project["id"],sid)).fetchone())
def can_edit(project):
    u=user()
    return bool(u and (u["role"]=="admin" or (u["role"]=="teacher" and project["advisor_id"]==u["student_id"]) or is_project_student(project)))
def can_manage(project):
    u=user()
    return bool(u and (u["role"]=="admin" or (u["role"]=="teacher" and project["advisor_id"]==u["student_id"])))
def can_create():
    u=user()
    return u and u["role"] in ("student","teacher","admin")
def project_json(p):
    d=dict(p)
    d["members"]=[dict(x) for x in conn().execute(
        "SELECT u.student_id,u.name FROM project_members pm JOIN users u ON pm.student_id=u.student_id WHERE pm.project_id=?",(p["id"],))]
    return d

@app.get("/")
def index():
    return render_template("index.html")
@app.get("/admin")
def admin_page():
    if not user(): return render_template("admin.html")
    if user()["role"]!="admin": return "ไม่มีสิทธิ์เข้าถึงหลังบ้าน",403
    return render_template("admin.html")

@app.get("/api/me")
def me():
    u=user()
    return jsonify(user=dict(u) if u else None,csrf=session.get("csrf") if u else None)
@app.put("/api/profile")
@login_required
@csrf_required
def update_profile():
    d=payload();name=str(d.get("name","")).strip()
    if not 2<=len(name)<=100:return jsonify(error="ชื่อต้องมี 2–100 ตัวอักษร"),400
    db=conn();db.execute("UPDATE users SET name=? WHERE student_id=?",(name,user()["student_id"]));db.commit()
    return jsonify(message="แก้ไขโปรไฟล์สำเร็จ",user=dict(user()))

@app.post("/api/profile/avatar")
@login_required
@csrf_required
def upload_avatar():
    upload=request.files.get("avatar")
    if not upload:return jsonify(error="กรุณาเลือกรูปภาพ"),400
    import io
    data=upload.read(2*1024*1024+1)
    if len(data)>2*1024*1024:return jsonify(error="ไฟล์ต้องไม่เกิน 2 MB"),400
    try:
        img=Image.open(io.BytesIO(data));img.verify()
        img=Image.open(io.BytesIO(data))
        if img.format not in ("JPEG","PNG","WEBP") or img.width*img.height>12000000:
            return jsonify(error="รองรับ JPG, PNG, WEBP และรูปไม่เกิน 12 ล้านพิกเซล"),400
        img=img.convert("RGB");img.thumbnail((512,512))
        os.makedirs(UPLOAD_DIR,exist_ok=True)
        filename=uuid.uuid4().hex+".jpg"
        img.save(os.path.join(UPLOAD_DIR,filename),format="JPEG",quality=85)
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError):
        return jsonify(error="ไฟล์รูปภาพไม่ถูกต้อง"),400
    db=conn();old=user()["avatar"]
    db.execute("UPDATE users SET avatar=? WHERE student_id=?",(filename,user()["student_id"]));db.commit()
    if old and old!=filename:
        try:os.remove(os.path.join(UPLOAD_DIR,old))
        except OSError:pass
    return jsonify(message="อัปโหลดรูปสำเร็จ",user=dict(user()))

@app.get("/avatars/<filename>")
@login_required
def avatar_file(filename):
    if not re.fullmatch(r"[0-9a-f]{32}\.jpg",filename):return jsonify(error="ไม่พบรูป"),404
    return send_from_directory(UPLOAD_DIR,filename)

@app.put("/api/users/<sid>/profile")
@login_required
@csrf_required
def admin_edit_user(sid):
    if user()["role"]!="admin":return jsonify(error="เฉพาะผู้ดูแลระบบ"),403
    name=str(payload().get("name","")).strip()
    if not 2<=len(name)<=100:return jsonify(error="ชื่อต้องมี 2–100 ตัวอักษร"),400
    db=conn();cur=db.execute("UPDATE users SET name=? WHERE student_id=?",(name,sid))
    if not cur.rowcount:return jsonify(error="ไม่พบผู้ใช้"),404
    db.commit();return jsonify(message="แก้ไขชื่อผู้ใช้สำเร็จ")

@app.post("/api/register")
def register():
    d=payload();sid=str(d.get("student_id","")).strip();name=str(d.get("name","")).strip();pw=str(d.get("password",""))
    if not re.fullmatch(r"\d{10}",sid) or sid==ADMIN_ID:
        return jsonify(error="รหัสนักศึกษาต้องเป็นตัวเลข 10 หลัก และไม่ใช่รหัสผู้ดูแล"),400
    if not 2<=len(name)<=100 or len(pw)<8 or len(pw)>128:
        return jsonify(error="ชื่อ 2–100 ตัวอักษร และรหัสผ่าน 8–128 ตัวอักษร"),400
    try:
        db=conn()
        db.execute("INSERT INTO users(student_id,name,password_hash) VALUES(?,?,?)",(sid,name,generate_password_hash(pw)))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="รหัสนักศึกษานี้ถูกใช้งานแล้ว"),409
    return jsonify(message="สมัครสมาชิกสำเร็จ"),201
@app.post("/api/login")
def login():
    d=payload();sid=str(d.get("student_id","")).strip()
    row=conn().execute("SELECT * FROM users WHERE student_id=?",(sid,)).fetchone()
    if not row or not check_password_hash(row["password_hash"],str(d.get("password",""))):
        return jsonify(error="รหัสผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"),401
    session.clear();session["sid"]=sid;session["csrf"]=secrets.token_urlsafe(32)
    return jsonify(user=dict(user()),csrf=session["csrf"])
@app.post("/api/logout")
@login_required
@csrf_required
def logout():
    session.clear();return jsonify(message="ออกจากระบบแล้ว")
@app.get("/api/users")
@login_required
def users():
    return jsonify(data=[dict(x) for x in conn().execute("SELECT student_id,name,role,avatar FROM users ORDER BY name")])
@app.put("/api/users/<sid>/role")
@login_required
@csrf_required
def set_role(sid):
    if user()["role"]!="admin": return jsonify(error="เฉพาะผู้ดูแลระบบ"),403
    if sid==ADMIN_ID:return jsonify(error="ไม่สามารถเปลี่ยนสิทธิ์ผู้ดูแลหลัก"),400
    role=payload().get("role")
    if role not in ("student","teacher"):return jsonify(error="สิทธิ์ไม่ถูกต้อง"),400
    db=conn()
    old=db.execute("SELECT role FROM users WHERE student_id=?",(sid,)).fetchone()
    if not old:return jsonify(error="ไม่พบผู้ใช้"),404
    if old["role"]=="teacher" and role=="student":
        linked=db.execute("SELECT 1 FROM projects WHERE advisor_id=? LIMIT 1",(sid,)).fetchone()
        if linked:return jsonify(error="ย้ายโครงงานไปยังอาจารย์คนอื่นก่อนลดสิทธิ์"),409
    db.execute("UPDATE users SET role=? WHERE student_id=?",(role,sid));db.commit()
    return jsonify(message="ปรับสิทธิ์สำเร็จ")
@app.get("/api/advisors")
@login_required
def advisors():
    return jsonify(data=[dict(x) for x in conn().execute("SELECT student_id,name,avatar FROM users WHERE role='teacher' ORDER BY name")])
@app.get("/api/projects")
@login_required
def projects():
    q=request.args.get("q","").strip()
    status=request.args.get("status","").strip()
    sql="""SELECT p.*,u.name AS advisor_name,c.name AS creator_name FROM projects p
           LEFT JOIN users u ON p.advisor_id=u.student_id
           LEFT JOIN users c ON p.created_by=c.student_id WHERE 1=1"""
    args=[]
    if q:sql+=" AND (p.title LIKE ? OR p.description LIKE ?)";args.extend(["%"+q+"%"]*2)
    if status in STATUSES:sql+=" AND p.status=?";args.append(status)
    sql+=" ORDER BY p.created_at DESC,p.id DESC"
    return jsonify(data=[project_json(x) for x in conn().execute(sql,args)])
@app.get("/api/projects/<int:pid>")
@login_required
def get_project(pid):
    p=conn().execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    return (jsonify(data=project_json(p)),200) if p else (jsonify(error="ไม่พบโครงงาน"),404)
def validate_project(d,creating=False):
    title=str(d.get("title","")).strip()
    desc=str(d.get("description","")).strip()
    if not 1<=len(title)<=150:return "ชื่อโครงงานต้องมี 1–150 ตัวอักษร"
    if len(desc)>3000:return "รายละเอียดต้องไม่เกิน 3000 ตัวอักษร"
    try:year=int(d.get("academic_year"))
    except (TypeError,ValueError):return "ปีการศึกษาต้องเป็นตัวเลข"
    if not 2500<=year<=2700:return "ปีการศึกษาไม่ถูกต้อง"
    if d.get("status") not in STATUSES:return "สถานะไม่ถูกต้อง"
    advisor=d.get("advisor_id")
    if advisor:
        row=conn().execute("SELECT role FROM users WHERE student_id=?",(advisor,)).fetchone()
        if not row or row["role"]!="teacher":return "ต้องเลือกอาจารย์ที่มีสิทธิ์ teacher"
    return None
@app.post("/api/projects")
@login_required
@csrf_required
def create_project():
    if not can_create():return jsonify(error="ไม่มีสิทธิ์สร้างโครงงาน"),403
    d=payload();err=validate_project(d,True)
    if err:return jsonify(error=err),400
    if user()["role"]=="teacher" and d.get("advisor_id")!=user()["student_id"]:
        return jsonify(error="อาจารย์สร้างโครงงานได้เฉพาะที่ตนเป็นที่ปรึกษา"),403
    if user()["role"]=="student" and d.get("advisor_id"):
        return jsonify(error="นักศึกษาสร้างโครงงานโดยยังไม่กำหนดที่ปรึกษา ให้ Admin กำหนดภายหลัง"),403
    db=conn()
    cur=db.execute("""INSERT INTO projects(title,description,academic_year,status,advisor_id,created_by)
      VALUES(?,?,?,?,?,?)""",(d["title"].strip(),str(d.get("description","")).strip(),int(d["academic_year"]),d.get("status"),d.get("advisor_id") or None,user()["student_id"]))
    log(db,cur.lastrowid,d["title"].strip(),"created");db.commit()
    return jsonify(message="เพิ่มโครงงานสำเร็จ",project_id=cur.lastrowid),201
@app.put("/api/projects/<int:pid>")
@login_required
@csrf_required
def update_project(pid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_edit(p):return jsonify(error="ไม่มีสิทธิ์แก้ไข"),403
    d=payload();err=validate_project(d)
    if err:return jsonify(error=err),400
    if user()["role"]=="teacher" and d.get("advisor_id")!=user()["student_id"]:
        return jsonify(error="อาจารย์ไม่สามารถโอนที่ปรึกษาเองได้"),403
    if user()["role"]=="student":
        if d.get("advisor_id") != p["advisor_id"] or d.get("status") != p["status"]:
            return jsonify(error="นักศึกษาแก้ไขได้เฉพาะชื่อ รายละเอียด และปีการศึกษา"),403
    db.execute("""UPDATE projects SET title=?,description=?,academic_year=?,status=?,advisor_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
               (d["title"].strip(),str(d.get("description","")).strip(),int(d["academic_year"]),d["status"],d.get("advisor_id") or None,pid))
    log(db,pid,d["title"].strip(),"updated");db.commit()
    return jsonify(message="แก้ไขโครงงานสำเร็จ")
@app.delete("/api/projects/<int:pid>")
@login_required
@csrf_required
def delete_project(pid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_manage(p):return jsonify(error="เฉพาะ Admin หรืออาจารย์ที่รับผิดชอบเท่านั้นที่ลบได้"),403
    log(db,pid,p["title"],"deleted")
    db.execute("DELETE FROM projects WHERE id=?",(pid,));db.commit()
    return jsonify(message="ลบโครงงานสำเร็จ")
@app.get("/api/projects/<int:pid>/members")
@login_required
def members(pid):
    if not conn().execute("SELECT 1 FROM projects WHERE id=?",(pid,)).fetchone():return jsonify(error="ไม่พบโครงงาน"),404
    return jsonify(data=[dict(x) for x in conn().execute("SELECT u.student_id,u.name FROM project_members pm JOIN users u ON pm.student_id=u.student_id WHERE pm.project_id=?",(pid,))])
@app.post("/api/projects/<int:pid>/members")
@login_required
@csrf_required
def add_member(pid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_manage(p):return jsonify(error="ไม่มีสิทธิ์"),403
    sid=str(payload().get("student_id",""))
    target=db.execute("SELECT role FROM users WHERE student_id=?",(sid,)).fetchone()
    if not target or target["role"]!="student":return jsonify(error="ไม่พบนักศึกษาที่เลือก"),400
    try:db.execute("INSERT INTO project_members VALUES(?,?)",(pid,sid))
    except sqlite3.IntegrityError:return jsonify(error="นักศึกษาเป็นสมาชิกอยู่แล้ว"),409
    log(db,pid,p["title"],"member_added",sid);db.commit()
    return jsonify(message="เพิ่มสมาชิกสำเร็จ"),201
@app.delete("/api/projects/<int:pid>/members/<sid>")
@login_required
@csrf_required
def remove_member(pid,sid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_manage(p):return jsonify(error="ไม่มีสิทธิ์"),403
    cur=db.execute("DELETE FROM project_members WHERE project_id=? AND student_id=?",(pid,sid))
    if not cur.rowcount:return jsonify(error="ไม่พบสมาชิก"),404
    log(db,pid,p["title"],"member_removed",sid);db.commit()
    return jsonify(message="ลบสมาชิกสำเร็จ")
@app.post("/api/projects/<int:pid>/claim-advisor")
@login_required
@csrf_required
def claim_advisor(pid):
    if user()["role"]!="teacher":
        return jsonify(error="เฉพาะอาจารย์เท่านั้นที่รับเป็นที่ปรึกษาได้"),403
    db=conn()
    # Atomic conditional update prevents two teachers from claiming the same project.
    cur=db.execute("UPDATE projects SET advisor_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND advisor_id IS NULL",
                   (user()["student_id"],pid))
    if not cur.rowcount:
        if not db.execute("SELECT 1 FROM projects WHERE id=?",(pid,)).fetchone():
            return jsonify(error="ไม่พบโครงงาน"),404
        return jsonify(error="โครงงานนี้มีอาจารย์ที่ปรึกษาแล้ว"),409
    p=db.execute("SELECT title FROM projects WHERE id=?",(pid,)).fetchone()
    log(db,pid,p["title"],"advisor_claimed","อาจารย์รับเป็นที่ปรึกษา")
    db.commit()
    return jsonify(message="รับเป็นอาจารย์ที่ปรึกษาสำเร็จ")

@app.put("/api/projects/<int:pid>/progress/<int:progress_id>")
@login_required
@csrf_required
def edit_progress(pid,progress_id):
    db=conn()
    p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    row=db.execute("SELECT * FROM progress WHERE id=? AND project_id=?",(progress_id,pid)).fetchone()
    if not row:return jsonify(error="ไม่พบบันทึกความก้าวหน้า"),404
    u=user()
    # Students may revise only their own entries; supervising teachers and admins may revise any.
    if not (can_manage(p) or (is_project_student(p) and row["created_by"]==u["student_id"])):
        return jsonify(error="ไม่มีสิทธิ์แก้ไขบันทึกนี้"),403
    d=payload();note=str(d.get("note","")).strip()
    try:percent=int(d.get("percent"))
    except (ValueError,TypeError):return jsonify(error="เปอร์เซ็นต์ไม่ถูกต้อง"),400
    if not 1<=len(note)<=500 or not 0<=percent<=100:
        return jsonify(error="ข้อความ 1–500 ตัวอักษร และเปอร์เซ็นต์ 0–100"),400
    db.execute("UPDATE progress SET note=?,percent=? WHERE id=? AND project_id=?",
               (note,percent,progress_id,pid))
    log(db,pid,p["title"],"progress_updated",f"บันทึก #{progress_id}: {percent}%")
    db.commit()
    return jsonify(message="แก้ไขความก้าวหน้าสำเร็จ")

@app.get("/api/projects/<int:pid>/progress")
@login_required
def get_progress(pid):
    return jsonify(data=[dict(x) for x in conn().execute("SELECT * FROM progress WHERE project_id=? ORDER BY id DESC",(pid,))])
@app.post("/api/projects/<int:pid>/progress")
@login_required
@csrf_required
def add_progress(pid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_edit(p):return jsonify(error="ไม่มีสิทธิ์"),403
    d=payload();note=str(d.get("note","")).strip()
    try:percent=int(d.get("percent"))
    except (TypeError,ValueError):return jsonify(error="เปอร์เซ็นต์ไม่ถูกต้อง"),400
    if not 1<=len(note)<=500 or not 0<=percent<=100:return jsonify(error="ข้อความ 1–500 ตัวอักษร และเปอร์เซ็นต์ 0–100"),400
    db.execute("INSERT INTO progress(project_id,note,percent,created_by) VALUES(?,?,?,?)",(pid,note,percent,user()["student_id"]))
    log(db,pid,p["title"],"progress_added",str(percent)+"%");db.commit()
    return jsonify(message="บันทึกความก้าวหน้าสำเร็จ"),201
@app.get("/api/chat/contacts")
@login_required
def chat_contacts():
    u=user();sid=u["student_id"];db=conn()
    contacts={}
    for x in db.execute("SELECT student_id,name,role,avatar FROM users WHERE role='admin' AND student_id!=?",(sid,)):
        contacts[x["student_id"]]=dict(x)
    if u["role"]=="student":
        sql="""SELECT DISTINCT u.student_id,u.name,u.role,u.avatar FROM users u
          JOIN projects p ON p.advisor_id=u.student_id
          LEFT JOIN project_members pm ON pm.project_id=p.id
          WHERE (p.created_by=? OR pm.student_id=?) AND u.role='teacher'"""
        for x in db.execute(sql,(sid,sid)):contacts[x["student_id"]]=dict(x)
    elif u["role"]=="teacher":
        sql="""SELECT DISTINCT u.student_id,u.name,u.role,u.avatar FROM users u
          JOIN projects p ON p.advisor_id=?
          LEFT JOIN project_members pm ON pm.project_id=p.id
          WHERE u.student_id=p.created_by OR u.student_id=pm.student_id"""
        for x in db.execute(sql,(sid,)):contacts[x["student_id"]]=dict(x)
    else:
        for x in db.execute("SELECT student_id,name,role,avatar FROM users WHERE student_id!=?",(sid,)):
            contacts[x["student_id"]]=dict(x)
    return jsonify(data=list(contacts.values()))

def chat_allowed(other_id):
    u=user();sid=u["student_id"];db=conn()
    other=db.execute("SELECT role FROM users WHERE student_id=?",(other_id,)).fetchone()
    if not other or other_id==sid:return False
    if u["role"]=="admin" or other["role"]=="admin":return True
    if {u["role"],other["role"]}!={"student","teacher"}:return False
    teacher=sid if u["role"]=="teacher" else other_id
    student=other_id if u["role"]=="teacher" else sid
    return bool(db.execute("""SELECT 1 FROM projects p LEFT JOIN project_members pm ON pm.project_id=p.id
      WHERE p.advisor_id=? AND (p.created_by=? OR pm.student_id=?) LIMIT 1""",(teacher,student,student)).fetchone())

@app.get("/api/chat/<other_id>")
@login_required
def chat_thread(other_id):
    if not chat_allowed(other_id):return jsonify(error="ไม่มีสิทธิ์สนทนากับบัญชีนี้"),403
    sid=user()["student_id"]
    rows=conn().execute("""SELECT id,sender_id,recipient_id,body,created_at,is_read FROM messages
       WHERE (sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?) ORDER BY id DESC LIMIT 100""",
       (sid,other_id,other_id,sid)).fetchall()
    return jsonify(data=[dict(x) for x in reversed(rows)])
@app.post("/api/chat/<other_id>")
@login_required
@csrf_required
def send_message(other_id):
    if not chat_allowed(other_id):return jsonify(error="ไม่มีสิทธิ์สนทนากับบัญชีนี้"),403
    body=str(payload().get("body","")).strip()
    if not 1<=len(body)<=2000:return jsonify(error="ข้อความต้องมี 1–2000 ตัวอักษร"),400
    db=conn();db.execute("INSERT INTO messages(sender_id,recipient_id,body) VALUES(?,?,?)",(user()["student_id"],other_id,body));db.commit()
    return jsonify(message="ส่งข้อความสำเร็จ"),201


# Announcements, project board and image uploads
IMAGE_DIR=os.path.join(UPLOAD_DIR,"board")
def save_image(field="image"):
    file=request.files.get(field)
    if not file or not file.filename:return None
    if file.mimetype not in ("image/jpeg","image/png","image/webp"):
        raise ValueError("รองรับเฉพาะ JPG, PNG และ WEBP")
    try:
        file.stream.seek(0)
        img=Image.open(file.stream)
        img.verify()
        file.stream.seek(0)
        img=Image.open(file.stream)
        if img.width*img.height>16000000:raise ValueError("รูปมีความละเอียดสูงเกินไป")
        img.thumbnail((1800,1200))
        img=img.convert("RGB")
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError):
        raise ValueError("ไฟล์รูปภาพไม่ถูกต้อง")
    os.makedirs(IMAGE_DIR,exist_ok=True)
    filename=uuid.uuid4().hex+".jpg"
    img.save(os.path.join(IMAGE_DIR,filename),"JPEG",quality=84,optimize=True)
    return filename

@app.get("/media/<filename>")
@login_required
def board_media(filename):
    return send_from_directory(IMAGE_DIR,filename)

@app.get("/api/announcements")
@login_required
def get_announcements():
    return jsonify(data=[dict(r) for r in conn().execute("SELECT a.*,u.name AS author_name FROM announcements a JOIN users u ON u.student_id=a.created_by ORDER BY a.id DESC LIMIT 50")])

@app.post("/api/announcements")
@login_required
@csrf_required
def create_announcement():
    if user()["role"]!="admin":return jsonify(error="เฉพาะผู้ดูแลระบบ"),403
    title=str(request.form.get("title","")).strip()
    body=str(request.form.get("body","")).strip()
    kind=str(request.form.get("kind","news"))
    if not 1<=len(title)<=140 or len(body)>3000 or kind not in ("news","maintenance"):
        return jsonify(error="กรุณากรอกชื่อประกาศให้ถูกต้อง"),400
    try:image=save_image()
    except ValueError as e:return jsonify(error=str(e)),400
    db=conn();db.execute("INSERT INTO announcements(title,body,image,kind,created_by) VALUES(?,?,?,?,?)",(title,body,image,kind,user()["student_id"]));db.commit()
    return jsonify(message="เผยแพร่ประกาศแล้ว"),201

@app.delete("/api/announcements/<int:aid>")
@login_required
@csrf_required
def delete_announcement(aid):
    if user()["role"]!="admin":return jsonify(error="เฉพาะผู้ดูแลระบบ"),403
    db=conn();cur=db.execute("DELETE FROM announcements WHERE id=?",(aid,));db.commit()
    return jsonify(message="ลบประกาศแล้ว") if cur.rowcount else (jsonify(error="ไม่พบประกาศ"),404)

@app.get("/api/projects/<int:pid>/posts")
@login_required
def get_posts(pid):
    db=conn()
    if not db.execute("SELECT 1 FROM projects WHERE id=?",(pid,)).fetchone():return jsonify(error="ไม่พบโครงงาน"),404
    posts=[dict(r) for r in db.execute("SELECT p.*,u.name AS author_name FROM project_posts p JOIN users u ON u.student_id=p.author_id WHERE project_id=? ORDER BY p.id DESC",(pid,))]
    for p in posts:
        p["comments"]=[dict(r) for r in db.execute("SELECT c.*,u.name AS author_name FROM post_comments c JOIN users u ON u.student_id=c.author_id WHERE post_id=? ORDER BY c.id",(p["id"],))]
    return jsonify(data=posts)

@app.post("/api/projects/<int:pid>/posts")
@login_required
@csrf_required
def add_post(pid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    if not p:return jsonify(error="ไม่พบโครงงาน"),404
    if not can_edit(p):return jsonify(error="ไม่มีสิทธิ์อัปเดตโครงงานนี้"),403
    body=str(request.form.get("body","")).strip()
    if len(body)>3000:return jsonify(error="ข้อความยาวเกิน 3000 ตัวอักษร"),400
    try:image=save_image()
    except ValueError as e:return jsonify(error=str(e)),400
    if not body and not image:return jsonify(error="กรุณาใส่ข้อความหรือรูปภาพ"),400
    db.execute("INSERT INTO project_posts(project_id,body,image,author_id) VALUES(?,?,?,?)",(pid,body,image,user()["student_id"]))
    log(db,pid,p["title"],"post_added");db.commit()
    return jsonify(message="เผยแพร่อัปเดตแล้ว"),201

@app.delete("/api/projects/<int:pid>/posts/<int:post_id>")
@login_required
@csrf_required
def delete_post(pid,post_id):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    post=db.execute("SELECT * FROM project_posts WHERE id=? AND project_id=?",(post_id,pid)).fetchone()
    if not p or not post:return jsonify(error="ไม่พบโพสต์"),404
    if not (can_manage(p) or (can_edit(p) and post["author_id"]==user()["student_id"])):
        return jsonify(error="ไม่มีสิทธิ์ลบโพสต์"),403
    db.execute("DELETE FROM project_posts WHERE id=?",(post_id,));log(db,pid,p["title"],"post_deleted");db.commit()
    return jsonify(message="ลบโพสต์แล้ว")

@app.post("/api/projects/<int:pid>/posts/<int:post_id>/comments")
@login_required
@csrf_required
def add_comment(pid,post_id):
    db=conn()
    if not db.execute("SELECT 1 FROM project_posts WHERE id=? AND project_id=?",(post_id,pid)).fetchone():return jsonify(error="ไม่พบโพสต์"),404
    body=str(payload().get("body","")).strip()
    if not 1<=len(body)<=1000:return jsonify(error="ความคิดเห็นต้องมี 1–1000 ตัวอักษร"),400
    db.execute("INSERT INTO post_comments(post_id,author_id,body) VALUES(?,?,?)",(post_id,user()["student_id"],body));db.commit()
    return jsonify(message="แสดงความคิดเห็นแล้ว"),201

@app.delete("/api/projects/<int:pid>/posts/<int:post_id>/comments/<int:cid>")
@login_required
@csrf_required
def delete_comment(pid,post_id,cid):
    db=conn();p=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    row=db.execute("SELECT * FROM post_comments WHERE id=? AND post_id=?",(cid,post_id)).fetchone()
    if not p or not row or not db.execute("SELECT 1 FROM project_posts WHERE id=? AND project_id=?",(post_id,pid)).fetchone():return jsonify(error="ไม่พบความคิดเห็น"),404
    if not (can_manage(p) or row["author_id"]==user()["student_id"]):return jsonify(error="ไม่มีสิทธิ์ลบความคิดเห็น"),403
    db.execute("DELETE FROM post_comments WHERE id=?",(cid,));db.commit()
    return jsonify(message="ลบความคิดเห็นแล้ว")

@app.get("/api/history")
@login_required
def history():
    return jsonify(data=[dict(x) for x in conn().execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100")])
@app.get("/api/stats")
@login_required
def stats():
    rows=conn().execute("SELECT status,COUNT(*) n FROM projects GROUP BY status").fetchall()
    years=conn().execute("SELECT academic_year,COUNT(*) n FROM projects GROUP BY academic_year ORDER BY academic_year").fetchall()
    return jsonify(status={r["status"]:r["n"] for r in rows},years=[dict(x) for x in years])
@app.get("/health")
def health():return jsonify(ok=True)

def admin_password_prompt():
    print("หมายเหตุ: ระหว่างพิมพ์รหัสผ่านจะไม่แสดงตัวอักษรหรือเครื่องหมาย * (เป็นปกติ)")
    if not sys.stdin.isatty():
        raise SystemExit("โปรดรันใน Terminal แบบโต้ตอบ เช่น VS Code Terminal / PowerShell")
    pw=getpass.getpass("ตั้งรหัสผ่าน Admin (อย่างน้อย 8 ตัวอักษร): ")
    if len(pw)<8:raise SystemExit("รหัสผ่านสั้นเกินไป")
    confirm=getpass.getpass("ยืนยันรหัสผ่านอีกครั้ง: ")
    if pw!=confirm:raise SystemExit("รหัสผ่านสองครั้งไม่ตรงกัน")
    return pw

def bootstrap_admin(reset=False):
    init_db()
    with app.app_context():
        db=conn()
        exists=db.execute("SELECT 1 FROM users WHERE student_id=?",(ADMIN_ID,)).fetchone()
        if exists and not reset:
            print("มีบัญชี Admin อยู่แล้ว หากจำรหัสผ่านไม่ได้ใช้: python app.py reset-admin-password")
            return
        if reset and not exists:
            print("ยังไม่มีบัญชี Admin ใช้: python app.py init-admin");return
        pw=admin_password_prompt()
        if exists:
            db.execute("UPDATE users SET password_hash=?,role='admin' WHERE student_id=?",(generate_password_hash(pw),ADMIN_ID))
            print("เปลี่ยนรหัสผ่าน Admin สำเร็จ")
        else:
            db.execute("INSERT INTO users(student_id,name,password_hash,role) VALUES(?,?,?,'admin')",
                       (ADMIN_ID,"ผู้ดูแลระบบ",generate_password_hash(pw)))
            print("สร้าง Admin สำเร็จ")
        db.commit()
        print("รหัสผู้ใช้ Admin:",ADMIN_ID)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",nargs="?",default="run",choices=["run","init-db","init-admin","reset-admin-password"])
    args=parser.parse_args()
    if args.command=="init-db":init_db();print("Database initialized")
    elif args.command=="init-admin":bootstrap_admin()
    elif args.command=="reset-admin-password":bootstrap_admin(reset=True)
    else:
        init_db()
        app.run(host="127.0.0.1",port=int(os.environ.get("PORT",5000)),debug=False)
