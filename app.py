from flask import Flask, render_template, jsonify, request, session
import json
import random
import os

app = Flask(__name__)
app.secret_key = "neet_secret_key_2024"

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")
SUBJECTS = ["Physics", "Chemistry", "Botany", "Zoology"]
QUESTIONS_PER_SUBJECT = 45


def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_test_questions():
    all_questions = load_questions()
    selected = []
    for subject in SUBJECTS:
        subject_qs = [q for q in all_questions if q["subject"] == subject]
        count = min(QUESTIONS_PER_SUBJECT, len(subject_qs))
        selected.extend(random.sample(subject_qs, count))
    # Re-number questions 1..180
    for i, q in enumerate(selected, 1):
        q["num"] = i
    return selected


@app.route("/")
def index():
    return render_template("test.html")


@app.route("/api/questions")
def api_questions():
    questions = get_test_questions()
    # Strip correct answer before sending to frontend
    safe = []
    for q in questions:
        safe.append({
            "id": q["id"],
            "num": q["num"],
            "subject": q["subject"],
            "question": q["question"],
            "options": q["options"],
        })
    return jsonify(safe)


@app.route("/api/submit", methods=["POST"])
def api_submit():
    data = request.get_json()
    user_answers = data.get("answers", {})   # { "question_id": "chosen_option" }
    question_nums = data.get("question_nums", {})  # { "question_id": num }

    all_questions = load_questions()
    answer_map = {str(q["id"]): q["answer"] for q in all_questions}

    score = 0
    correct = 0
    incorrect = 0
    unattempted = 0
    details = []

    for qid, correct_ans in answer_map.items():
        if qid not in question_nums:
            continue  # Not part of this test
        user_ans = user_answers.get(qid)
        num = question_nums.get(qid)
        q_obj = next((q for q in all_questions if str(q["id"]) == qid), {})
        if user_ans is None or user_ans == "":
            unattempted += 1
            result = "unattempted"
        elif user_ans == correct_ans:
            score += 4
            correct += 1
            result = "correct"
        else:
            score -= 1
            incorrect += 1
            result = "incorrect"
        details.append({
            "num": num,
            "id": qid,
            "subject": q_obj.get("subject", ""),
            "question": q_obj.get("question", ""),
            "options": q_obj.get("options", []),
            "correct_answer": correct_ans,
            "user_answer": user_ans,
            "result": result,
        })

    details.sort(key=lambda x: x["num"])

    subject_stats = {}
    for subj in SUBJECTS:
        subj_details = [d for d in details if d["subject"] == subj]
        subject_stats[subj] = {
            "correct": sum(1 for d in subj_details if d["result"] == "correct"),
            "incorrect": sum(1 for d in subj_details if d["result"] == "incorrect"),
            "unattempted": sum(1 for d in subj_details if d["result"] == "unattempted"),
            "score": sum(4 if d["result"] == "correct" else (-1 if d["result"] == "incorrect" else 0) for d in subj_details),
        }

    return jsonify({
        "score": score,
        "correct": correct,
        "incorrect": incorrect,
        "unattempted": unattempted,
        "total": len(details),
        "subject_stats": subject_stats,
        "details": details,
    })


@app.route("/result")
def result():
    return render_template("result.html")


if __name__ == "__main__":
    app.run(debug=True)