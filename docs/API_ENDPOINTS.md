# REST API Endpoint List

Base URL: `http://127.0.0.1:5000`

| Function | Method | Endpoint | Success |
|---|---|---|---|
| ดูโครงงานทั้งหมด | GET | `/api/projects` | 200 |
| ดูโครงงานรายรายการ | GET | `/api/projects/{id}` | 200 |
| เพิ่มโครงงาน | POST | `/api/projects` | 201 |
| แก้ไขโครงงาน | PUT | `/api/projects/{id}` | 200 |
| ลบโครงงาน | DELETE | `/api/projects/{id}` | 200 |
| ดูนักศึกษา | GET | `/api/students` | 200 |
| ดูอาจารย์ | GET | `/api/advisors` | 200 |
| ดูสมาชิกโครงงาน | GET | `/api/projects/{id}/members` | 200 |
| เพิ่มสมาชิกโครงงาน | POST | `/api/projects/{id}/members` | 201 |
| ดูความก้าวหน้า | GET | `/api/projects/{id}/progress` | 200 |
| เพิ่มความก้าวหน้า | POST | `/api/projects/{id}/progress` | 201 |
| ตรวจสอบการเชื่อมต่อ | GET | `/api/health` | 200 |

## POST /api/projects — Request JSON
```json
{"title":"ระบบจัดการกิจกรรมนักศึกษา","description":"ระบบจัดการกิจกรรมและการลงทะเบียนออนไลน์","advisor_id":1,"status":"in_progress","academic_year":2569}
```

## GET /api/projects — Example Response JSON
```json
{"success":true,"count":1,"data":[{"project_id":1,"title":"ระบบจัดการกิจกรรมนักศึกษา","description":"ระบบจัดการกิจกรรมและการลงทะเบียนออนไลน์","advisor_id":1,"advisor_name":"อาจารย์ที่ปรึกษา ก.","advisor_department":"วิทยาการคอมพิวเตอร์","status":"in_progress","academic_year":2569,"created_at":"2026-10-30 12:00:00"}]}
```
> Response ข้างต้นเป็นตัวอย่างรูปแบบ; จำนวนและเวลาจริงขึ้นอยู่กับข้อมูลในระบบ

## Error Response
```json
{"success":false,"error":"ไม่พบโครงงาน"}
```
- 400 Invalid JSON / Validation Error
- 404 Missing Project / Advisor / Student
- 409 Duplicate Member

## POST /api/projects/1/members
```json
{"student_id":2,"role":"Developer"}
```

## POST /api/projects/1/progress
```json
{"title":"Sprint 2","detail":"เชื่อมต่อ API","progress_percent":80}
```
