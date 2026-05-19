from flask import Flask, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_PATH = 'clinic.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service TEXT,
            paid REAL,
            remaining REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>عيادة د. أحمد عامر</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: sans-serif; padding-top: 20px; }
        .card { border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }
        .patient-row:hover { background-color: #f1f3f5; }
    </style>
</head>
<body class="container">
    <h3 class="text-center mb-4 text-primary fw-bold">نظام إدارة العيادة</h3>
    
    <div class="card p-3 mb-4">
        <form action="/add" method="POST" class="row g-2">
            <div class="col-md-3 col-12"><input type="text" name="name" class="form-control" placeholder="اسم المريض" required></div>
            <div class="col-md-3 col-12"><input type="text" name="service" class="form-control" placeholder="الخدمة"></div>
            <div class="col-md-2 col-6"><input type="number" name="paid" class="form-control" placeholder="المدفوع"></div>
            <div class="col-md-2 col-6"><input type="number" name="remaining" class="form-control" placeholder="المتبقي"></div>
            <div class="col-md-2 col-12"><button type="submit" class="btn btn-success w-100">حفظ</button></div>
        </form>
    </div>

    <form action="/" method="GET" class="d-flex mb-3">
        <input type="text" name="search" class="form-control me-2" placeholder="ابحث باسم المريض..." value="~SEARCH~">
        <button type="submit" class="btn btn-primary">بحث</button>
    </form>

    <div class="card p-2">
        <div class="table-responsive">
            <table class="table align-middle">
                <thead class="table-dark">
                    <tr><th>الاسم</th><th>الخدمة</th><th>المدفوع</th><th>المتبقي</th><th>تعديل</th></tr>
                </thead>
                <tbody>~ROWS~</tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تعديل المريض</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container py-4">
    <div class="card p-4 font-sans shadow-sm mx-auto" style="max-width: 500px;">
        <h4 class="text-center text-primary mb-4">تعديل بيانات المريض</h4>
        <form method="POST">
            <div class="mb-3"><label class="form-label">الاسم</label><input type="text" name="name" class="form-control" value="{name}" required></div>
            <div class="mb-3"><label class="form-label">الخدمة</label><input type="text" name="service" class="form-control" value="{service}"></div>
            <div class="mb-3"><label class="form-label text-success">المدفوع</label><input type="number" name="paid" class="form-control" value="{paid}"></div>
            <div class="mb-3"><label class="form-label text-danger">المتبقي</label><input type="number" name="remaining" class="form-control" value="{remaining}"></div>
            <button type="submit" class="btn btn-success w-100 mb-2">حفظ التعديلات</button>
            <a href="/" class="btn btn-secondary w-100">إلغاء</a>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT * FROM patients WHERE name LIKE ?", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM patients ORDER BY id DESC")
    patients = cursor.fetchall()
    conn.close()
    
    rows = ""
    for p in patients:
        rows += f"<tr class='patient-row'><td><b>{p[1]}</b></td><td>{p[2] or ''}</td><td class='text-success'>{p[3] or 0}</td><td class='text-danger'>{p[4] or 0}</td><td><a href='/edit/{p[0]}' class='btn btn-sm btn-outline-primary'>تعديل</a></td></tr>"
    if not rows:
        rows = "<tr><td colspan='5' class='text-center text-muted'>لا يوجد مرضى.</td></tr>"
    return HTML_TEMPLATE.replace('~ROWS~', rows).replace('~SEARCH~', search_query)

@app.route('/add', methods=['POST'])
def add_patient():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO patients (name, service, paid, remaining) VALUES (?, ?, ?, ?)',
                   (request.form['name'], request.form['service'], request.form['paid'] or 0, request.form['remaining'] or 0))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute('UPDATE patients SET name=?, service=?, paid=?, remaining=? WHERE id=?',
                       (request.form['name'], request.form['service'], request.form['paid'] or 0, request.form['remaining'] or 0, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    cursor.execute("SELECT * FROM patients WHERE id=?", (id,))
    p = cursor.fetchone()
    conn.close()
    return EDIT_TEMPLATE.format(name=p[1], service=p[2] or '', paid=p[3] or 0, remaining=p[4] or 0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
