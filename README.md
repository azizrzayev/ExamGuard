# ExamGuard - AI Powered Exam System

ExamGuard PDF materiallardan və əl ilə daxil edilən məlumatlardan avtomatik imtahan sualları çıxaran və proctoring (distant nəzarət) imkanı sunan Django tətbiqidir.

## 🚀 Features
- 📄 PDF-dən avtomatik sual çıxarma
- ✍️ Əl ilə sual idarəetməsi (Manual Question Ingestion)
- 🛡️ Anti-cheat imtahan rejimi (Proctoring)
- 📊 Dashboard (Teacher / Student)
- 🔒 Rol əsaslı Django Auth sistemi

## 🛠️ Tech Stack
- **Backend:** Django, Python
- **Frontend:** HTML5, CSS3, JavaScript, Responsive UI
- **DB:** SQLite
- **AI:** Google Gemini API

## ⚙️ Quraşdırma
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
