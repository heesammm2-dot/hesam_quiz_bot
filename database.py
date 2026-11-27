import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH

@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_connection() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER NOT NULL DEFAULT 0,
            is_winner INTEGER NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS questions_answered(
            user_id INTEGER NOT NULL, question_id TEXT NOT NULL,
            PRIMARY KEY(user_id, question_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS winners(
            user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER NOT NULL,
            won_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def register_user(user_id, username):
    with get_connection() as c:
        c.execute("INSERT INTO users(user_id,username) VALUES(?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
                  (user_id, username or "بدون‌نام"))

def get_user(user_id):
    with get_connection() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

def used_questions(user_id):
    with get_connection() as c:
        return {r["question_id"] for r in c.execute(
            "SELECT question_id FROM questions_answered WHERE user_id=?", (user_id,))}

def record_answer(user_id, question_id, correct, points):
    with get_connection() as c:
        cur = c.execute("INSERT OR IGNORE INTO questions_answered(user_id,question_id) VALUES(?,?)",
                        (user_id, question_id))
        if cur.rowcount == 0:
            return False
        if correct:
            c.execute("UPDATE users SET score=score+? WHERE user_id=?", (points, user_id))
        return True

def leaderboard():
    with get_connection() as c:
        return c.execute("SELECT username,score FROM users ORDER BY score DESC, username LIMIT 10").fetchall()

def reset_user(user_id):
    with get_connection() as c:
        c.execute("UPDATE users SET score=0,is_winner=0 WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM questions_answered WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM winners WHERE user_id=?", (user_id,))

def mark_winner(user_id, username):
    with get_connection() as c:
        cur = c.execute("UPDATE users SET is_winner=1 WHERE user_id=? AND is_winner=0", (user_id,))
        if cur.rowcount:
            row = c.execute("SELECT score FROM users WHERE user_id=?", (user_id,)).fetchone()
            c.execute("INSERT OR REPLACE INTO winners(user_id,username,score) VALUES(?,?,?)",
                      (user_id, username or "بدون‌نام", row["score"]))
            return True
        return False

def get_winners():
    with get_connection() as c:
        return c.execute("SELECT username,score,won_at FROM winners ORDER BY won_at DESC").fetchall()
