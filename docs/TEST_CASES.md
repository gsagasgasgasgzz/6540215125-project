# API Testing

| Test | Method | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| GET /api/projects | GET | 200 + JSON data | รอทดสอบด้วย Postman | Not Run |
| POST /api/projects | POST | 201 + เพิ่มข้อมูล | รอทดสอบด้วย Postman | Not Run |
| PUT /api/projects/{id} | PUT | 200 + แก้ไขข้อมูล | รอทดสอบด้วย Postman | Not Run |
| DELETE /api/projects/{id} | DELETE | 200 + ลบข้อมูล | รอทดสอบด้วย Postman | Not Run |
| POST invalid title | POST | 400 + error | รอทดสอบด้วย Postman | Not Run |
| GET /api/projects/999 | GET | 404 + error | รอทดสอบด้วย Postman | Not Run |

Use Postman/cURL, record actual results and capture genuine screenshots.

Automated test: `python -m pytest -q`.
