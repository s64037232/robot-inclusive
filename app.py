"""
Robot-Inclusive — веб-версия на Streamlit.

Запуск:
    pip install streamlit
    streamlit run app.py
"""
import random

import streamlit as st

st.set_page_config(page_title="Robot-Inclusive", page_icon="🤖", layout="centered")


# =====================================================================
#                        ГЕНЕРАТОРЫ ЗАДАЧ
# Каждый генератор принимает k — сколько НЕВЕРНЫХ ответов нужно,
# и возвращает (текст задачи, верный ответ, список неверных ответов).
# =====================================================================
def near_wrongs(correct, k, lo=0):
    pool = [correct + d for d in range(-6, 7) if d != 0 and correct + d >= lo]
    random.shuffle(pool)
    return pool[:k]


def q_add(k, hi):
    a = random.randint(1, hi - 1)
    b = random.randint(1, hi - a)
    return f"{a} + {b} = ?", a + b, near_wrongs(a + b, k)


def q_sub(k, hi):
    a = random.randint(3, hi)
    b = random.randint(1, a - 1)
    return f"{a} − {b} = ?", a - b, near_wrongs(a - b, k)


def q_mul(k, m):
    a, b = random.randint(2, m), random.randint(2, m)
    return f"{a} × {b} = ?", a * b, near_wrongs(a * b, k)


def q_div(k, m):
    b, c = random.randint(2, m), random.randint(2, m)
    return f"{b * c} ÷ {b} = ?", c, near_wrongs(c, k, lo=1)


def q_missing(k, hi):
    a = random.randint(1, hi - 1)
    b = random.randint(1, hi - a)
    return f"Найди пропущенное число: ? + {b} = {a + b}", a, near_wrongs(a, k, lo=0)


def q_two_step(k):
    a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
    return f"{a} + {b} × {c} = ?", a + b * c, near_wrongs(a + b * c, k)


def q_brackets(k):
    a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 6)
    return f"({a} + {b}) × {c} = ?", (a + b) * c, near_wrongs((a + b) * c, k)


def q_sequence(k, step_max, start_max=10):
    d = random.randint(2, step_max)
    s = random.randint(1, start_max)
    seq = [s + d * i for i in range(4)]
    return (f"Продолжи ряд: {seq[0]}, {seq[1]}, {seq[2]}, ?", seq[3],
            near_wrongs(seq[3], k, lo=1))


def q_biggest(k):
    nums = random.sample(range(1, 60), k + 1)
    correct = max(nums)
    return "Найди самое БОЛЬШОЕ число", correct, [n for n in nums if n != correct]


def q_smallest(k):
    nums = random.sample(range(1, 60), k + 1)
    correct = min(nums)
    return "Найди самое МАЛЕНЬКОЕ число", correct, [n for n in nums if n != correct]


def q_even(k):
    return ("Найди ЧЁТНОЕ число", random.randint(1, 30) * 2,
            random.sample(range(1, 60, 2), k))


def q_odd(k):
    return ("Найди НЕЧЁТНОЕ число", random.randint(0, 30) * 2 + 1,
            random.sample(range(2, 60, 2), k))


def q_divisible(k, d):
    correct = d * random.randint(2, 12)
    others = [n for n in range(2, 60) if n % d != 0]
    return f"Найди число, которое делится на {d}", correct, random.sample(others, k)


# ---------- Уровни сложности ----------
LEVELS = {
    "🟢 Лёгкий": {
        "options": 2,
        "questions": [
            lambda k: q_add(k, 10),
            lambda k: q_sub(k, 10),
            lambda k: q_sequence(k, 3),
            q_even,
            q_biggest,
        ],
    },
    "🟠 Средний": {
        "options": 3,
        "questions": [
            lambda k: q_add(k, 20),
            lambda k: q_sub(k, 20),
            lambda k: q_mul(k, 5),
            lambda k: q_missing(k, 20),
            lambda k: q_sequence(k, 5),
            q_odd,
            q_smallest,
            lambda k: q_divisible(k, 5),
        ],
    },
    "🔴 Сложный": {
        "options": 4,
        "questions": [
            lambda k: q_mul(k, 9),
            lambda k: q_div(k, 9),
            q_two_step,
            q_brackets,
            lambda k: q_missing(k, 50),
            lambda k: q_sequence(k, 9, 20),
            lambda k: q_divisible(k, 3),
        ],
    },
}

MSG_START = "Привет! Я твой робот-помощник. Выбери уровень и нажми «Новое задание»."
MSG_HELP = "Я помогу тебе! Не бойся ошибаться. Выбери кубик с верным ответом."
MSG_TASK = "Выбери кубик с верным ответом!"
MSG_DONE = "Верно! Молодец! Задание выполнено!"
MSG_WRONG = "Ответ неверный! Попробуй ещё раз."


# ---------- Состояние игры ----------
def new_task():
    level = LEVELS[st.session_state.level_name]
    k = level["options"] - 1
    text, correct, wrongs = random.choice(level["questions"])(k)
    options = [correct] + list(wrongs)
    random.shuffle(options)
    st.session_state.question = text
    st.session_state.options = options
    st.session_state.correct = options.index(correct)
    st.session_state.wrong = []
    st.session_state.done = False
    st.session_state.msg = (MSG_TASK, "info")


def answer(i):
    s = st.session_state
    if s.done or i in s.wrong:
        return
    if i == s.correct:
        s.done = True
        s.score += 1
        s.msg = (MSG_DONE, "ok")
    else:
        s.wrong.append(i)
        s.mistakes += 1
        s.msg = (MSG_WRONG, "bad")


def show_help():
    st.session_state.msg = (MSG_HELP, "info")


if "question" not in st.session_state:
    st.session_state.level_name = "🟢 Лёгкий"
    st.session_state.score = 0
    st.session_state.mistakes = 0
    st.session_state.question = None
    st.session_state.options = []
    st.session_state.correct = None
    st.session_state.wrong = []
    st.session_state.done = False
    st.session_state.msg = (MSG_START, "info")

s = st.session_state

# ---------- Крупные кнопки-кубики ----------
st.markdown(
    """
    <style>
    div.stButton > button { font-size: 2rem; font-weight: 700; padding: 1rem 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Боковая панель ----------
with st.sidebar:
    st.header("Настройки")
    st.radio("Уровень", list(LEVELS), key="level_name", on_change=new_task)
    st.button("Новое задание", on_click=new_task, type="primary")
    st.button("Помощь", on_click=show_help)
    st.divider()
    st.metric("Верно", s.score)
    st.metric("Ошибки", s.mistakes)

# ---------- Основной экран ----------
st.title("🤖 Robot-Inclusive")
st.caption("Робот-помощник для изучения базовой математики")

if s.done:
    robot = "😄"
elif s.wrong:
    robot = "😟"
else:
    robot = "🤖"
st.markdown(f"<div style='font-size:4rem;text-align:center'>{robot}</div>",
            unsafe_allow_html=True)

if s.question is None:
    st.info(s.msg[0])
else:
    st.subheader(s.question)
    text, kind = s.msg
    {"ok": st.success, "bad": st.error}.get(kind, st.info)(text)

    cols = st.columns(len(s.options))
    for i, (col, value) in enumerate(zip(cols, s.options)):
        if i in s.wrong:
            label = f"❌ {value}"
        elif s.done and i == s.correct:
            label = f"✅ {value}"
        else:
            label = str(value)
        col.button(label, key=f"opt{i}", on_click=answer, args=(i,),
                   disabled=(i in s.wrong or s.done))

    if s.done:
        st.button("Следующее задание ➡️", on_click=new_task, type="primary")
