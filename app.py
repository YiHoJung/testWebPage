from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'test_secret_key'
DB_PATH = 'db.sqlite3'

# DB 초기화
if not os.path.exists(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, author TEXT)''')
        conn.commit()

# DB 연결 함수
def get_db():
    return sqlite3.connect(DB_PATH)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return redirect('/login')
            except:
                return '이미 존재하는 사용자입니다.'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['user'] = username
                return redirect('/board')
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        new_pw = request.form['password']
        with get_db() as conn:
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_pw, session['user']))
            conn.commit()
        return '비밀번호 변경 완료'
    return render_template('mypage.html')

@app.route('/board')
def board():
    if 'user' not in session:
        return redirect('/login')
    keyword = request.args.get('q', '')
    with get_db() as conn:
        if keyword:
            posts = conn.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC", (f'%{keyword}%', f'%{keyword}%')).fetchall()
        else:
            posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return render_template('board.html', posts=posts, keyword=keyword)

@app.route('/board/write', methods=['GET', 'POST'])
def write():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        with get_db() as conn:
            conn.execute("INSERT INTO posts (title, content, author) VALUES (?, ?, ?)", (title, content, session['user']))
            conn.commit()
        return redirect('/board')
    return render_template('write.html')

@app.route('/board/<int:post_id>')
def view(post_id):
    if 'user' not in session:
        return redirect('/login')
    with get_db() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    return render_template('view.html', post=post)

@app.route('/board/<int:post_id>/edit', methods=['GET', 'POST'])
def edit(post_id):
    if 'user' not in session:
        return redirect('/login')
    with get_db() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        if post is None:
            return '해당 게시글이 존재하지 않습니다.'
        if post[3] != session['user']:
            return '수정 권한이 없습니다.'

        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            conn.execute("UPDATE posts SET title=?, content=? WHERE id=?", (title, content, post_id))
            conn.commit()
            return redirect(f'/board/{post_id}')
    return render_template('edit.html', post=post)

@app.route('/board/<int:post_id>/delete')
def delete(post_id):  
    if 'user' not in session:
        return redirect('/login')
    with get_db() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        if post is None:
            return '해당 게시글이 존재하지 않습니다.'
        if post[3] != session['user']:
            return '삭제 권한이 없습니다.'

        conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
        conn.commit()
    return redirect('/board')


if __name__ == '__main__':
    app.run(debug=True, port=8000)
