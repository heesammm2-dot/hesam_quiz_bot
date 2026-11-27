import random
from questions import QUESTIONS
from config import WIN_SCORE
import database

def normalize(text):
    text = (text or "").strip().lower()
    text = text.replace("ي","ی").replace("ك","ک").replace("\u200c","")
    return " ".join(text.split())

def choose_question(user_id):
    used = database.used_questions(user_id)
    available = [q for q in QUESTIONS if q["id"] not in used]
    return random.choice(available) if available else None

def is_correct(text, question):
    answer = normalize(text)
    return any(answer == normalize(a) for a in question["answers"])

def check_win(user_id, username):
    user = database.get_user(user_id)
    return bool(user and user["score"] >= WIN_SCORE and database.mark_winner(user_id, username))
