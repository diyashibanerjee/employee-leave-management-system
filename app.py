from flask import Flask, render_template, request, redirect, session, url_for
import pyodbc

app = Flask(__name__)
app.secret_key = 'diyashi'

# Connect to SQL Server
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DIYASHI\\SQLEXPRESS;'
    'DATABASE=leaverequest;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        cursor.execute("SELECT id, role FROM Users WHERE username=? AND password=?", (user, pwd))
        result = cursor.fetchone()
        if result:
            session['user'] = user
            session['role'] = result[1]
            return redirect(url_for('admindashboard') if session['role']=='admin' else url_for('employeedashboard'))
        else:
            return render_template('index.html', error="Invalid credentials")
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        role = request.form['role']
        cursor.execute("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)", (user, pwd, role))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/employeedashboard', methods=['GET','POST'])
def employeedashboard():
    if 'user' not in session or session['role']!='employee':
        return redirect(url_for('login'))
    if request.method=='POST':
        f = request.form['from']
        t = request.form['to']
        reason = request.form['reason']
        lt = request.form['leaveType']
        cursor.execute("INSERT INTO LeaveRequests (username, from_date, to_date, reason, leave_type) VALUES (?, ?, ?, ?, ?)",
                       (session['user'], f, t, reason, lt))
        conn.commit()
    # show history
    cursor.execute("SELECT * FROM LeaveRequests WHERE username=?", (session['user'],))
    leaves = cursor.fetchall()
    return render_template('employeedashboard.html', username=session['user'], leaves=leaves)

@app.route('/admindashboard')
def admindashboard():
    if 'user' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    cursor.execute("SELECT * FROM LeaveRequests WHERE status='Pending'")
    pending = cursor.fetchall()
    return render_template('admindashboard.html', pending=pending)

@app.route('/approve/<int:id>')
def approve(id):
    cursor.execute("UPDATE LeaveRequests SET status='Approved' WHERE id=?", (id,))
    conn.commit()
    return redirect(url_for('admindashboard'))

@app.route('/reject/<int:id>')
def reject(id):
    cursor.execute("UPDATE LeaveRequests SET status='Rejected' WHERE id=?", (id,))
    conn.commit()
    return redirect(url_for('admindashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
