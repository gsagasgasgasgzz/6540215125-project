# University Project Portal — ระบบจัดการโครงงานนักศึกษา

เว็บแอปสไตล์ระบบสารสนเทศมหาวิทยาลัย สำหรับบริหารข้อมูลโครงงานนักศึกษา ด้วย **Flask + SQLite + REST API**

## Features
- หน้า Dashboard พร้อมจำนวนโครงงานตามสถานะ
- ค้นหาและกรองโครงงานตามสถานะและปีการศึกษา
- เพิ่ม / ดูรายละเอียด / แก้ไข / ลบโครงงาน (CRUD)
- แสดงอาจารย์ที่ปรึกษา สมาชิก และความก้าวหน้าล่าสุด
- SQLite 5 ตาราง พร้อม PK/FK/Constraints
- REST API 12 Endpoints และ JSON Error Handling
- Responsive UI ธีมกรมท่า–ขาว–ทอง

## Installation
Requires Python 3.10+

```bash
python -m venv .venv
```

Activate virtual environment:
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

On first run, SQLite creates `portal.db` with demo projects, students, advisors, and progress data.

## API & Database Documentation
- `docs/DATABASE_SCHEMA.md` — fields, data types, PK/FK, relationships
- `docs/ER_DIAGRAM.svg` — ER Diagram
- `docs/API_ENDPOINTS.md` — endpoint list and JSON examples
- `docs/TEST_CASES.md` — API test-case worksheet

## Testing
```bash
python -m pytest -q
```

For screenshot evidence, run the web app and use Postman to test GET, POST, PUT, DELETE and invalid requests. Save real screenshots in `screenshots/`.

## Project Structure
```text
university-project-portal/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/index.html
├── static/style.css
├── static/app.js
├── docs/
│   ├── DATABASE_SCHEMA.md
│   ├── ER_DIAGRAM.svg
│   ├── API_ENDPOINTS.md
│   └── TEST_CASES.md
├── tests/test_api.py
└── screenshots/README.md
```

## Team
- [ชื่อสมาชิก 1] — Database
- [ชื่อสมาชิก 2] — Backend/API
- [ชื่อสมาชิก 3] — Frontend
- [ชื่อสมาชิก 4] — Testing/Documentation

## GitHub
Repository: [กรอกลิงก์ GitHub จริง]

## Important: Security / Deployment
This is a **working educational prototype**, not a production-ready university service. It has no authentication, authorization, CSRF protection, or rate limiting. **Do not expose the admin CRUD endpoints publicly** or use real student information until access control and security measures are added. Never commit `.env`, credentials, or the SQLite database.

To replace your previous repository, back up the old files, then commit the contents of this folder to the repository root. Existing Git commit history remains available.
