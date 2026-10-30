# Database Schema — ระบบจัดการโครงงานนักศึกษา

## 1. Student (`students`)
| Field | Data Type | Key |
|---|---|---|
| student_id | INTEGER | PK |
| student_code | TEXT | UNIQUE, NOT NULL |
| name | TEXT | NOT NULL |
| email | TEXT | UNIQUE |

## 2. Advisor (`advisors`)
| Field | Data Type | Key |
|---|---|---|
| advisor_id | INTEGER | PK |
| name | TEXT | NOT NULL |
| department | TEXT | NOT NULL |
| email | TEXT | UNIQUE |

## 3. Project (`projects`)
| Field | Data Type | Key |
|---|---|---|
| project_id | INTEGER | PK |
| title | TEXT | NOT NULL |
| description | TEXT | |
| advisor_id | INTEGER | FK → advisors.advisor_id |
| status | TEXT | CHECK planning/in_progress/completed |
| academic_year | INTEGER | |
| created_at | TEXT | |

## 4. ProjectMember (`project_members`)
| Field | Data Type | Key |
|---|---|---|
| member_id | INTEGER | PK |
| project_id | INTEGER | FK → projects.project_id |
| student_id | INTEGER | FK → students.student_id |
| role | TEXT | |

Unique constraint: `(project_id, student_id)`

## 5. Progress (`progress`)
| Field | Data Type | Key |
|---|---|---|
| progress_id | INTEGER | PK |
| project_id | INTEGER | FK → projects.project_id |
| title | TEXT | NOT NULL |
| detail | TEXT | |
| progress_percent | INTEGER | CHECK 0–100 |
| created_at | TEXT | |

## Relationships
- Advisor (1) → (N) Project
- Student (1) → (N) ProjectMember
- Project (1) → (N) ProjectMember
- Project (1) → (N) Progress
- Student (M) ↔ (N) Project ผ่าน ProjectMember

ER Diagram: `ER_DIAGRAM.svg`. Actual SQL schema: `app.py`.
