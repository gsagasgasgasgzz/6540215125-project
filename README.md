Student Activity Management System
ระบบจัดการงานและกิจกรรมของนักศึกษา
Project Description
เว็บแอปพลิเคชันสำหรับให้นักศึกษาค้นหา ดูรายละเอียด และลงทะเบียนเข้าร่วมกิจกรรมภายในมหาวิทยาลัย พร้อมตรวจสอบกิจกรรมที่ตนเองลงทะเบียนไว้ พัฒนาขึ้นเป็นต้นแบบสำหรับ Sprint 1 ในรายวิชาการประยุกต์ใช้เทคโนโลยีเว็บและแพลตฟอร์ม
Objectives
1. รวบรวมรายการกิจกรรมของนักศึกษาไว้ในระบบเดียว
2. ช่วยให้นักศึกษาดูรายละเอียดและลงทะเบียนกิจกรรมได้สะดวก
3. ฝึกพัฒนา Web Application ที่เชื่อมต่อ Frontend, API และ Database
Target Users
- นักศึกษาที่ต้องการค้นหาและลงทะเบียนกิจกรรม
- ผู้ดูแลกิจกรรมของมหาวิทยาลัย (กลุ่มผู้ใช้เป้าหมายสำหรับการพัฒนาต่อไป)
Main Features
- Activity List: แสดงรายการกิจกรรมจากฐานข้อมูล
- Search Activities: ค้นหากิจกรรมตามชื่อ
- Activity Details: ดูวันที่ สถานที่ รายละเอียด และจำนวนที่นั่ง
- Activity Registration: ลงทะเบียนกิจกรรมด้วยบัญชีตัวอย่าง
- Duplicate Registration Check: ป้องกันการลงทะเบียนกิจกรรมเดิมซ้ำ
- My Activities: ดูรายการกิจกรรมที่ลงทะเบียนแล้ว
Technology
- Backend: Python, Flask
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- API: REST-style HTTP endpoints
- Version Control: Git และ GitHub
Project Structure
student-activity-sprint1/
├── app.py
├── requirements.txt
├── README.md
├── TASK_BOARD.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
└── tests/
    └── test_app.py
Installation and Run
ต้องมี Python 3.10 หรือใหม่กว่า
git clone https://github.com/YOUR-USERNAME/student-activity-management.git
cd student-activity-management
python -m venv .venv
เปิด Virtual Environment:

Windows
.venv\Scripts\activate
macOS / Linux
source .venv/bin/activate
ติดตั้งและเริ่มระบบ:
pip install -r requirements.txt
python app.py
เปิดเว็บที่ http://127.0.0.1:5000
เปลี่ยน YOUR-USERNAME เป็นชื่อผู้ใช้ GitHub จริง และอัปโหลดโค้ดโปรเจกต์ก่อนใช้งานคำสั่ง git clone

Database
ใช้ฐานข้อมูล SQLite ที่สร้างอัตโนมัติเมื่อเปิดแอปครั้งแรก โดยมีตารางหลัก:
- students — ข้อมูลนักศึกษา
- activities — ข้อมูลกิจกรรม
- registrations — ข้อมูลการลงทะเบียน
ระบบเตรียมข้อมูลกิจกรรมตัวอย่าง 4 รายการ และบัญชีนักศึกษาตัวอย่างสำหรับสาธิต
API Endpoints
Method	Endpoint	Description
GET	/api/activities	ดูกิจกรรมทั้งหมด
GET	/api/activities/<id>	ดูรายละเอียดกิจกรรม
POST	/api/registrations	ลงทะเบียนกิจกรรม
GET	/api/my-activities	ดูกิจกรรมของนักศึกษาตัวอย่าง


ตัวอย่าง JSON สำหรับลงทะเบียน:
{
  "student_id": 1,
  "activity_id": 1
}
Testing
หลังติดตั้ง dependencies ให้ทดสอบด้วย:
pytest -q
Test Cases ที่ควรตรวจสอบด้วยตนเอง:
1. เปิดหน้ารายการกิจกรรม
2. ค้นหากิจกรรม
3. ดูรายละเอียดกิจกรรม
4. ลงทะเบียนกิจกรรม
5. ลงทะเบียนกิจกรรมเดิมซ้ำ
6. ดูกิจกรรมที่ลงทะเบียนในหน้า My Activities
Project Status
Sprint 1 — Prototype

เตรียมโค้ดต้นแบบสำหรับ Activity List, Activity Details, Registration และ My Activities แล้ว โดยต้องทดสอบการทำงานจริงบนเครื่องของทีมและบันทึกผล Test Case ก่อนส่งงาน
Team
Member	Responsibility
สมาชิก 1: [ชื่อ]	Frontend / UI
สมาชิก 2: [ชื่อ]	Backend / API
สมาชิก 3: [ชื่อ]	Database
สมาชิก 4: [ชื่อ]	Testing / Documentation


GitHub Workflow
Plan → Create Branch → Develop → Test → Commit → Push → Pull Request → Review → Merge

ตัวอย่าง Branch:
- feature-activity-ui
- feature-activity-api
- feature-database
- feature-testing-docs
Notes
โปรเจกต์นี้เป็นต้นแบบสำหรับการเรียน โดยใช้บัญชีผู้ใช้ตัวอย่าง ยังไม่มีระบบ Login และการกำหนดสิทธิ์ใช้งานจริง ไม่ควรนำขึ้นใช้งานสาธารณะโดยไม่เพิ่มมาตรการความปลอดภัย

Repository URL: [คลิ้ก](https://github.com/gsagasgasgasgzz/6540215125-project)
