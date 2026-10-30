from flask import Flask, render_template, jsonify, request
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "student_activities.db"

def connect(db_path=None):
    con = sqlite3.connect(str(db_path or DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db(db_path=None):
    with connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_code TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activities (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          category TEXT NOT NULL,
          activity_date TEXT NOT NULL,
          location TEXT NOT NULL,
          description TEXT NOT NULL,
          capacity INTEGER NOT NULL CHECK(capacity > 0)
        );
        CREATE TABLE IF NOT EXISTS registrations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id INTEGER NOT NULL,
          activity_id INTEGER NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(student_id, activity_id),
          FOREIGN KEY(student_id) REFERENCES students(id),
          FOREIGN KEY(activity_id) REFERENCES activities(id)
        );
        """)
        if con.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            con.execute("INSERT INTO students(student_code,name) VALUES (?,?)",
                        ("65000001", "นักศึกษาตัวอย่าง"))
        if con.execute("SELECT COUNT(*) FROM activities").fetchone()[0] == 0:
            con.executemany("""INSERT INTO activities
              (title,category,activity_date,location,description,capacity)
              VALUES (?,?,?,?,?,?)""", [
              ("อบรมพัฒนาเว็บไซต์", "วิชาการ", "2026-11-12", "ห้องปฏิบัติการคอมพิวเตอร์",
               "เรียนรู้พื้นฐานการพัฒนาเว็บและการออกแบบส่วนติดต่อผู้ใช้", 30),
              ("จิตอาสาพัฒนาชุมชน", "จิตอาสา", "2026-11-18", "ศูนย์กิจกรรมนักศึกษา",
               "ร่วมกิจกรรมเพื่อสังคมและพัฒนาพื้นที่ส่วนรวม", 40),
              ("แข่งขันออกแบบ UI", "แข่งขัน", "2026-11-25", "อาคารนวัตกรรม",
               "ฝึกคิดและนำเสนอต้นแบบหน้าจอสำหรับผู้ใช้งานจริง", 20),
              ("เสวนาเตรียมความพร้อมอาชีพ", "แนะแนว", "2026-12-02", "หอประชุม",
               "พูดคุยเรื่องทักษะการทำงานและการเตรียมแฟ้มผลงาน", 80),
            ])

def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = str(db_path or DB_PATH)
    init_db(app.config["DATABASE"])

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/activities")
    def activities():
        with connect(app.config["DATABASE"]) as con:
            rows = con.execute("""
              SELECT a.*, COUNT(r.id) AS registered
              FROM activities a LEFT JOIN registrations r ON r.activity_id=a.id
              GROUP BY a.id ORDER BY a.activity_date, a.id
            """).fetchall()
            return jsonify([dict(r) for r in rows])

    @app.get("/api/activities/<int:activity_id>")
    def activity_detail(activity_id):
        with connect(app.config["DATABASE"]) as con:
            row = con.execute("""
              SELECT a.*, COUNT(r.id) AS registered
              FROM activities a LEFT JOIN registrations r ON r.activity_id=a.id
              WHERE a.id=? GROUP BY a.id
            """, (activity_id,)).fetchone()
            return (jsonify(dict(row)), 200) if row else (jsonify(error="ไม่พบกิจกรรม"),404)

    @app.post("/api/registrations")
    def register():
        body = request.get_json(silent=True) or {}
        activity_id = body.get("activity_id")
        student_id = body.get("student_id", 1)
        if type(activity_id) is not int or type(student_id) is not int:
            return jsonify(error="ข้อมูลการลงทะเบียนไม่ถูกต้อง"),400
        with connect(app.config["DATABASE"]) as con:
            if not con.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone():
                return jsonify(error="ไม่พบนักศึกษา"),404
            activity = con.execute("SELECT capacity FROM activities WHERE id=?",
                                   (activity_id,)).fetchone()
            if not activity:
                return jsonify(error="ไม่พบกิจกรรม"),404
            if con.execute("SELECT 1 FROM registrations WHERE student_id=? AND activity_id=?",
                           (student_id, activity_id)).fetchone():
                return jsonify(error="ลงทะเบียนกิจกรรมนี้แล้ว"),409
            count = con.execute("SELECT COUNT(*) FROM registrations WHERE activity_id=?",
                                (activity_id,)).fetchone()[0]
            if count >= activity["capacity"]:
                return jsonify(error="กิจกรรมเต็มแล้ว"),409
            con.execute("INSERT INTO registrations(student_id,activity_id) VALUES (?,?)",
                        (student_id,activity_id))
        return jsonify(message="ลงทะเบียนสำเร็จ"),201

    @app.get("/api/my-activities")
    def my_activities():
        with connect(app.config["DATABASE"]) as con:
            rows=con.execute("""
              SELECT a.* FROM registrations r JOIN activities a ON a.id=r.activity_id
              WHERE r.student_id=1 ORDER BY a.activity_date
            """).fetchall()
            return jsonify([dict(r) for r in rows])
    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True, port=5000)
