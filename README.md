# Student Project Portal — ธีมดำส้ม

ระบบจัดการข้อมูลโครงงานนักศึกษา Flask + SQLite พร้อม Register/Login, Admin, Teacher permission, CRUD, สมาชิก, Progress, Dashboard, Audit history และ UI popup/toast

## ติดตั้ง
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python app.py init-db
python app.py init-admin
python app.py
```
เข้าเว็บ http://127.0.0.1:5000

**Admin:** รหัสผู้ใช้ `6540215125` รหัสผ่านจะถูกถามตอนรัน `init-admin` (ไม่ได้ตั้งรหัสผ่านเริ่มต้นไว้)

## สิทธิ์
- Student: สมัครสมาชิกด้วยรหัส 10 หลัก เข้าระบบ ดูโครงงานและประวัติ
- Teacher: ต้องให้ Admin เปลี่ยนสิทธิ์จากหน้า "จัดการสิทธิ์ผู้ใช้" จึงจะสร้างโครงงานที่ตนเป็นที่ปรึกษา และแก้ไข/ลบโครงงานของตนได้
- Admin: แก้ไข/ลบทุกโครงงาน ตั้งที่ปรึกษาจากบัญชี Teacher และปรับสิทธิ์ผู้ใช้
- รหัส `6540215125` สงวนไว้สำหรับ Admin เท่านั้น สมัครผ่านหน้าเว็บไม่ได้

## API
`POST /api/register`, `POST /api/login`, `POST /api/logout`, `GET /api/me`, `GET /api/users`, `PUT /api/users/{id}/role`, `GET /api/advisors`, `GET/POST /api/projects`, `GET/PUT/DELETE /api/projects/{id}`, `GET/POST /api/projects/{id}/members`, `DELETE /api/projects/{id}/members/{student_id}`, `GET/POST /api/projects/{id}/progress`, `GET /api/stats`, `GET /api/history`, `GET /health`.

API เขียนข้อมูลต้องเข้าสู่ระบบและส่ง Header `X-CSRF-Token` ซึ่งได้จาก `/api/me` หลังล็อกอิน พร้อม session cookie. ตัวอย่าง JSON เพิ่มโครงงาน:
```json
{"title":"ระบบจองห้อง","description":"ตัวอย่าง","academic_year":2569,"status":"planning","advisor_id":"รหัสบัญชีอาจารย์"}
```
หากยังไม่มี Teacher ให้ Admin สร้างโครงงานโดย `advisor_id: null` ได้

## ความปลอดภัย / ก่อนเผยแพร่จริง
ใช้ password hash, SQL parameterized queries, role checks, CSRF token, จำกัดขนาด request, session cookie HTTPOnly. หาก deploy ออนไลน์ ต้องตั้ง `SECRET_KEY` เป็นค่าสุ่มถาวรใน environment, เปิด HTTPS และ `COOKIE_SECURE=1`, เพิ่ม rate limiting, backup ฐานข้อมูล, logging และทดสอบด้านความปลอดภัยก่อนใช้งานจริง. อย่า commit `portal.sqlite3`, `.env` หรือรหัสผ่านขึ้น GitHub. โปรเจกต์นี้เป็นต้นแบบสำหรับสาธิตในเครื่อง ไม่ใช่ระบบ production สำเร็จรูป

## การทดสอบ
`python -m unittest discover -s tests -v`

## นำเสนอความก้าวหน้า
ถ่ายภาพหน้า Register/Login, หน้า Dashboard, กราฟ, หน้าเพิ่ม/แก้ไข/ลบ, การเปลี่ยนสิทธิ์ Teacher, ประวัติ, ผล API Test, GitHub commits และบันทึกปัญหาที่พบจริง

## อัปเดต UI และโปรไฟล์ (เวอร์ชัน 2)
- ส่วนหัวแบบ University Portal, เมนูผู้ใช้แบบ Dropdown, ดูและแก้ไขชื่อบัญชีตนเอง
- อัปโหลดรูปโปรไฟล์ JPG/PNG/WEBP ขนาดไม่เกิน 2 MB; ระบบตรวจสอบและแปลงเป็น JPEG ก่อนบันทึก
- Admin แก้ชื่อบัญชีที่ลงทะเบียนแล้วจากหน้าจัดการผู้ใช้ได้
- เพิ่ม API: `PUT /api/profile`, `POST /api/profile/avatar` (multipart form-data), `PUT /api/users/{id}/profile` (Admin)
- บัญชีที่มีอยู่เดิมจะถูกเพิ่มคอลัมน์ avatar อัตโนมัติเมื่อเริ่มโปรแกรม (ไม่ต้องลบฐานข้อมูลเดิม)

### ตั้งรหัสผ่าน Admin
คำสั่ง `python app.py init-admin` จะถามรหัสผ่าน **โดยไม่แสดงตัวอักษรแม้แต่ดอกจัน** ให้พิมพ์รหัสผ่านแล้วกด Enter จากนั้นพิมพ์ยืนยันอีกครั้ง
ถ้ามี Admin อยู่แล้วและต้องการเปลี่ยนรหัสผ่าน ใช้ `python app.py reset-admin-password` ใน VS Code Terminal หรือ PowerShell
อย่าใส่รหัสผ่านในคำสั่ง Terminal หรือใน GitHub

### การตรวจสอบและข้อจำกัด
มีการตรวจสอบไวยากรณ์ Python และ JavaScript แต่สภาพแวดล้อมที่สร้างไฟล์ไม่มี Flask/Pillow และไม่สามารถดาวน์โหลดแพ็กเกจ จึงยังไม่ได้ทดสอบเว็บจริงด้วย automated tests. หลังติดตั้งบนเครื่องให้รัน `python -m unittest discover -s tests -v` และทดสอบการสมัคร/ล็อกอิน/อัปโหลดรูป/สิทธิ์ก่อนนำไปใช้จริง


## ธีมมหาวิทยาลัย น้ำเงิน–ครีม–ทอง
เวอร์ชันนี้ปรับหน้าตาเป็นโทนทางการ โดยเพิ่ม `static/university-theme.css` และโหลดหลัง `style.css` เพื่อคงการทำงานของระบบเดิมไว้ แก้ค่าสีหลักได้ที่ตัวแปร CSS `:root` ในไฟล์ธีม หากเปิดแล้วไม่เปลี่ยนสีให้กด Ctrl+F5 เพื่อล้างแคชหน้าเว็บ


## เวอร์ชัน 3: Student / Teacher / Admin + Messaging
- หน้า `/` คือส่วนใช้งานสำหรับนักศึกษาและอาจารย์; หน้า `/admin` เป็นหลังบ้านแยกเฉพาะ Admin
- นักศึกษาสร้างโครงงานของตนได้โดยไม่กำหนดอาจารย์ก่อน, แก้ไขชื่อ รายละเอียด ปีการศึกษาได้เฉพาะโครงงานที่ตนสร้างหรือเป็นสมาชิก และเพิ่มบันทึกความก้าวหน้าได้
- อาจารย์จัดการโครงงานที่ตนเป็นที่ปรึกษาได้ (รวมสถานะ สมาชิก ความก้าวหน้า และการลบ)
- Admin จัดการทุกโครงงาน กำหนดสิทธิ์ Teacher และเลือกที่ปรึกษาจากบัญชี Teacher
- เมนู “ติดต่ออาจารย์ / ผู้ดูแล” เป็นข้อความส่วนตัวที่เก็บในฐานข้อมูล: นักศึกษาติดต่อ Admin หรืออาจารย์ประจำโครงงาน, อาจารย์ติดต่อ Admin หรือนักศึกษาในโครงงานที่ดูแล, Admin ติดต่อทุกบัญชี
- ข้อความจะอัปเดตเมื่อเลือกบทสนทนาใหม่ **ไม่ใช่ real-time chat**, ยังไม่มีการแนบไฟล์ การแจ้งเตือนข้อความใหม่ หรือการลบข้อความ
- `python app.py` จะสร้างตาราง messages ให้เอง โดยไม่ต้องลบฐานข้อมูลเดิม
- อย่าลบไฟล์ `portal.sqlite3` หากต้องการรักษาข้อมูลเดิม และสำรองก่อนอัปเดต
- ระบบนี้ยังเป็น local prototype; ก่อนเผยแพร่สาธารณะควรเพิ่ม rate limiting, HTTPS, การกู้คืนบัญชี, การสำรองข้อมูล และตรวจสอบความปลอดภัยเพิ่มเติม

## v5 — Campus Dashboard
- เปลี่ยนหน้าเว็บเป็น Layout แบบ University Portal มี Sidebar สีน้ำเงิน, เมนู Dashboard, โครงงาน, ประวัติ, ข้อความ, สถิติ และปุ่มเข้าหลังบ้านสำหรับ Admin
- อาจารย์สามารถกด **รับเป็นที่ปรึกษา** บนโครงงานที่ `advisor_id` เป็น NULL ได้ (`POST /api/projects/<id>/claim-advisor`) ใช้ conditional UPDATE ป้องกันการรับซ้ำพร้อมกัน
- แก้ไขบันทึกความก้าวหน้าเดิมได้ (`PUT /api/projects/<id>/progress/<progress_id>`) นักศึกษาแก้ได้เฉพาะบันทึกที่ตนเองเขียนในโครงงานของตน ส่วนอาจารย์ที่ปรึกษาและ Admin แก้ได้ทุกบันทึกในโครงงานที่มีสิทธิ์
- การแก้ไขความก้าวหน้าและการรับเป็นที่ปรึกษาถูกบันทึกใน audit_log
- ไม่จำเป็นต้องลบฐานข้อมูลเดิม เพราะฟังก์ชันใหม่ใช้ตารางที่มีอยู่แล้ว
- ธีมอิงโครงสร้าง Dashboard จากภาพตัวอย่างของผู้ใช้ แต่ไม่ใช้ภาพ โลโก้ หรือเครื่องหมายการค้าของมหาวิทยาลัยในภาพ

**ตรวจสอบแล้ว:** Python syntax และ JavaScript syntax. **ยังไม่ได้รัน Flask integration tests** ในสภาพแวดล้อมสร้างไฟล์นี้ เพราะไม่มี Flask ติดตั้ง

## v6 — University Portal แยกหน้า / กระดานโครงงาน

- Dashboard แยกจากหน้ารายการโครงงาน, ประกาศ, ประวัติ; ใช้เมนูด้านซ้ายสลับหน้าโดยไม่ต้องรีโหลด
- Dashboard แสดงตัวอย่างประกาศ 3 ช่อง: ถ้ายังไม่มีข่าวจริงจะแสดงภาพ placeholder ที่รอ Admin อัปโหลด
- Admin สร้างประกาศพร้อมภาพ (JPG/PNG/WEBP), เลือกข่าวทั่วไปหรือแจ้งปรับปรุงระบบ และลบประกาศได้ที่ `/admin`
- ผู้ใช้ที่เข้าสู่ระบบจะเห็นประกาศและแถบแจ้งปรับปรุงระบบล่าสุดบน Dashboard
- หน้าโครงงานเป็นกระดานโพสต์ อัปโหลดรูปภาพ เขียนความคิดเห็น และลบโพสต์/ความคิดเห็นตามสิทธิ์
- นักศึกษา/อาจารย์ที่ดูแลโครงงานโพสต์ได้; ผู้ใช้ที่ล็อกอินสามารถแสดงความคิดเห็น; ผู้เขียนโพสต์หรือผู้ดูแลโครงงานลบโพสต์ได้
- Chat API ยังบังคับ login และตรวจสอบคู่สนทนาตามสิทธิ์; ไม่แสดงแชทก่อนเข้าสู่ระบบ
- แก้ Popup ความก้าวหน้าซ้อนหลังหน้าต่างรายละเอียดโดยกำหนด z-index ของ modal ให้ถูกลำดับ
- รูปภาพที่อัปโหลดถูกแปลงเป็น JPG และเก็บใน `uploads/board/` ไม่ใช่ base64 ใน SQLite
- แนะนำให้สำรองทั้ง `portal.sqlite3` **และ** โฟลเดอร์ `uploads/` ก่อนอัปเกรด

### API ใหม่
- `GET/POST /api/announcements`, `DELETE /api/announcements/<id>`
- `GET/POST /api/projects/<id>/posts`, `DELETE /api/projects/<id>/posts/<post_id>`
- `POST /api/projects/<id>/posts/<post_id>/comments`, `DELETE /api/projects/<id>/posts/<post_id>/comments/<comment_id>`
- `GET /media/<filename>` ต้องล็อกอิน

### ข้อจำกัด
ยังเป็นต้นแบบสาธิตในเครื่อง: การแจ้งเตือนยังเป็นแถบประกาศที่โหลดเมื่อเข้าระบบ/รีเฟรช ไม่ใช่ push notification; แชทไม่ใช่ realtime; ยังไม่ได้รันทดสอบ Flask แบบครบวงจรในสภาพแวดล้อมสร้างไฟล์นี้
