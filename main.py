"""
Robot-Inclusive — Робот-помощник для инклюзивного образования.

Как играть:
    Нажми «ЗАДАНИЕ» — появится задача (например, 2 + 2 = ?) и кубики с ответами.
    Подведи робота к кубику с правильным ответом.
    Неверный кубик — «Ответ неверный!», можно попробовать снова.

Управление:
    Стрелки   — движение робота
    Мышь      — кнопки «ПОМОЩЬ», «ЗАДАНИЕ», «УРОВЕНЬ»
    H / T     — «ПОМОЩЬ» / «ЗАДАНИЕ» с клавиатуры
    1 / 2 / 3 — выбрать уровень (лёгкий / средний / сложный)
    V         — включить/выключить голос (нужен pyttsx3)
    Esc       — выход
"""
import random
import threading

import pygame

# ---------- Параметры ----------
WIDTH, HEIGHT = 900, 600
ROBOT_SIZE = 100
CUBE_SIZE = 76
OBSTACLE_SIZE = 60
FPS = 60
PANEL_HEIGHT = 170  # верхняя панель: кнопки, задача, сообщение

# ---------- Цвета ----------
WHITE = (255, 255, 255)
BG = (235, 242, 250)
DARK = (30, 41, 59)
BLUE = (59, 130, 246)
BLUE_DARK = (37, 99, 235)
GREEN = (34, 197, 94)
GREEN_DARK = (22, 163, 74)
ORANGE = (249, 115, 22)
ORANGE_DARK = (234, 88, 12)
RED = (239, 68, 68)
RED_DARK = (185, 28, 28)
GRAY = (148, 163, 184)
LEVEL_COLORS = [GREEN, ORANGE, RED]
CUBE_COLORS = [(99, 102, 241), (234, 179, 8), (236, 72, 153), (20, 184, 166)]


# =====================================================================
#                        ГЕНЕРАТОРЫ ЗАДАЧ
# Каждый генератор принимает k — сколько НЕВЕРНЫХ ответов нужно,
# и возвращает (текст задачи, верный ответ, список неверных ответов).
# =====================================================================
def near_wrongs(correct, k, lo=0):
    """k неверных ответов, близких к верному (типичные ошибки «на 1–6»)."""
    pool = [correct + d for d in range(-6, 7) if d != 0 and correct + d >= lo]
    random.shuffle(pool)
    return pool[:k]


def q_add(k, hi):
    a = random.randint(1, hi - 1)
    b = random.randint(1, hi - a)
    return f"Реши: {a} + {b} = ?", a + b, near_wrongs(a + b, k)


def q_sub(k, hi):
    a = random.randint(3, hi)
    b = random.randint(1, a - 1)
    return f"Реши: {a} − {b} = ?", a - b, near_wrongs(a - b, k)


def q_mul(k, m):
    a, b = random.randint(2, m), random.randint(2, m)
    return f"Реши: {a} × {b} = ?", a * b, near_wrongs(a * b, k)


def q_div(k, m):
    b, c = random.randint(2, m), random.randint(2, m)
    return f"Реши: {b * c} ÷ {b} = ?", c, near_wrongs(c, k, lo=1)


def q_missing(k, hi):
    a = random.randint(1, hi - 1)
    b = random.randint(1, hi - a)
    return f"Найди пропущенное число: ? + {b} = {a + b}", a, near_wrongs(a, k, lo=0)


def q_two_step(k):
    a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
    return f"Реши: {a} + {b} × {c} = ?", a + b * c, near_wrongs(a + b * c, k)


def q_brackets(k):
    a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 6)
    return f"Реши: ({a} + {b}) × {c} = ?", (a + b) * c, near_wrongs((a + b) * c, k)


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
# cubes     — сколько кубиков-ответов на поле
# obstacles — красные преграды (касание возвращает робота на старт)
# time      — лимит времени на задачу в секундах (None = без лимита)
# speed     — скорость робота
# questions — набор типов задач уровня (выбирается случайный)
LEVELS = [
    {
        "name": "Лёгкий", "cubes": 2, "obstacles": 0, "time": None, "speed": 5,
        "questions": [
            lambda k: q_add(k, 10),
            lambda k: q_sub(k, 10),
            lambda k: q_sequence(k, 3),
            q_even,
            q_biggest,
        ],
    },
    {
        "name": "Средний", "cubes": 3, "obstacles": 2, "time": None, "speed": 5,
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
    {
        "name": "Сложный", "cubes": 4, "obstacles": 4, "time": 40, "speed": 6,
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
]


def make_question(level):
    """Возвращает (текст, [значения кубиков], индекс верного кубика)."""
    k = level["cubes"] - 1
    text, correct, wrongs = random.choice(level["questions"])(k)
    options = [correct] + list(wrongs)
    random.shuffle(options)
    return text, options, options.index(correct)


# ---------- Тексты ----------
TITLE = "Robot-Inclusive — Робот-помощник"
Q_START = "Нажми «ЗАДАНИЕ», чтобы получить задачу"
MSG_START = "Привет! Я твой робот-помощник. Выбери уровень и нажми «ЗАДАНИЕ»."
MSG_HELP = ("Я помогу тебе! Не бойся задавать вопросы. "
            "Подведи робота к кубику с верным ответом.")
MSG_TASK = "Подведи робота к кубику с верным ответом!"
MSG_TASK_OBST = "Подведи робота к верному кубику и обойди красные преграды!"
MSG_DONE = "Верно! Молодец! Задание выполнено!"
MSG_WRONG = "Ответ неверный! Попробуй ещё раз."
MSG_HIT = "Ой! Это преграда. Попробуй ещё раз!"
MSG_TIMEOUT = "Время вышло. Ничего страшного, нажми «ЗАДАНИЕ» и попробуй снова!"
HINT = "Стрелки — движение | H помощь | T задание | 1-2-3 уровень | V голос"


# ---------- Голос (необязательно) ----------
class Voice:
    """Озвучка через pyttsx3. Если библиотеки нет — тихо отключается."""

    def __init__(self):
        self.enabled = False
        self.available = False
        try:
            import pyttsx3  # noqa: F401
            self.available = True
        except ImportError:
            pass

    def toggle(self):
        if self.available:
            self.enabled = not self.enabled
        return self.enabled

    def say(self, text):
        if not (self.available and self.enabled):
            return
        for sym, word in (("+", " плюс "), ("−", " минус "), ("×", " умножить на "),
                          ("÷", " разделить на "), ("=", " равно "), ("?", "")):
            text = text.replace(sym, word)

        def _run():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()


# ---------- Вспомогательные классы ----------
class Button:
    def __init__(self, rect, text, color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color

    def draw(self, surface, font):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, self.hover_color if hovered else self.color,
                         self.rect, border_radius=12)
        label = font.render(self.text, True, WHITE)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


class Robot:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, ROBOT_SIZE, ROBOT_SIZE)
        self.speed = 5
        self.reset()

    def reset(self):
        self.rect.center = (WIDTH // 2, (HEIGHT + PANEL_HEIGHT) // 2)

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        # Ограничение движения: робот не выходит за игровое поле
        self.rect.clamp_ip(pygame.Rect(0, PANEL_HEIGHT, WIDTH, HEIGHT - PANEL_HEIGHT))

    def draw(self, surface, happy=False, sad=False):
        r = self.rect
        pygame.draw.rect(surface, BLUE, r, border_radius=18)
        pygame.draw.rect(surface, BLUE_DARK, r, width=4, border_radius=18)
        # антенна
        pygame.draw.line(surface, DARK, (r.centerx, r.top), (r.centerx, r.top - 18), 4)
        pygame.draw.circle(surface, ORANGE, (r.centerx, r.top - 22), 7)
        # глаза
        for dx in (-22, 22):
            pygame.draw.circle(surface, WHITE, (r.centerx + dx, r.y + 35), 13)
            pygame.draw.circle(surface, DARK, (r.centerx + dx, r.y + 35), 6)
        # рот
        if happy:
            pygame.draw.arc(surface, WHITE, (r.x + 25, r.y + 45, 50, 35), 3.4, 6.0, 4)
        elif sad:
            pygame.draw.arc(surface, WHITE, (r.x + 25, r.y + 62, 50, 30), 0.4, 2.9, 4)
        else:
            pygame.draw.line(surface, WHITE, (r.x + 30, r.y + 72), (r.x + 70, r.y + 72), 4)


def draw_cube(surface, cube, font):
    r = cube["rect"]
    base = GRAY if cube["wrong"] else cube["color"]
    shadow = tuple(int(c * 0.7) for c in base)
    pygame.draw.rect(surface, shadow, r.move(0, 6), border_radius=14)
    pygame.draw.rect(surface, base, r, border_radius=14)
    pygame.draw.rect(surface, WHITE, r, width=3, border_radius=14)
    label = font.render(str(cube["value"]), True, WHITE)
    surface.blit(label, label.get_rect(center=r.center))
    if cube["wrong"]:  # красный крестик на неверном кубике
        pygame.draw.line(surface, RED, r.move(12, 12).topleft, r.move(-12, -12).bottomright, 6)
        pygame.draw.line(surface, RED, r.move(12, -12).bottomleft, r.move(-12, 12).topright, 6)


def draw_obstacle(surface, o):
    pygame.draw.rect(surface, RED, o, border_radius=10)
    pygame.draw.rect(surface, RED_DARK, o, width=4, border_radius=10)
    pygame.draw.line(surface, WHITE, o.move(14, 14).topleft, o.move(-14, -14).bottomright, 5)
    pygame.draw.line(surface, WHITE, o.move(14, -14).bottomleft, o.move(-14, 14).topright, 5)


def make_font(size, bold=False):
    """Шрифт с поддержкой кириллицы."""
    names = "arial,segoeui,calibri,dejavusans,liberationsans,freesans"
    return pygame.font.SysFont(names, size, bold=bold)


def wrap_text(text, font, max_width):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def generate_field(count_cubes, count_obstacles, robot_rect):
    """Расставляет кубики и преграды так, чтобы они не перекрывали друг друга и старт."""
    field = pygame.Rect(0, PANEL_HEIGHT + 15, WIDTH, HEIGHT - PANEL_HEIGHT - 45)
    cubes, obstacles = [], []
    for _attempt in range(50):
        keep_away = [robot_rect.inflate(140, 140)]

        def place(size):
            for _ in range(300):
                x = random.randint(field.left, field.right - size)
                y = random.randint(field.top, field.bottom - size)
                rect = pygame.Rect(x, y, size, size)
                if not any(rect.colliderect(k) for k in keep_away):
                    keep_away.append(rect.inflate(30, 30))
                    return rect
            return None

        cubes = [place(CUBE_SIZE) for _ in range(count_cubes)]
        obstacles = [place(OBSTACLE_SIZE) for _ in range(count_obstacles)]
        if None not in cubes and None not in obstacles:
            break
    return [c for c in cubes if c], [o for o in obstacles if o]


# ---------- Основная программа ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font_title = make_font(28, bold=True)
    font_btn = make_font(21, bold=True)
    font_question = make_font(30, bold=True)
    font_msg = make_font(20)
    font_cube = make_font(32, bold=True)
    font_small = make_font(15)

    voice = Voice()
    robot = Robot()
    btn_help = Button((20, 52, 160, 44), "ПОМОЩЬ", BLUE, BLUE_DARK)
    btn_task = Button((195, 52, 160, 44), "ЗАДАНИЕ", GREEN, GREEN_DARK)
    btn_level = Button((370, 52, 250, 44), "", ORANGE, ORANGE_DARK)

    level_index = 0
    question = Q_START
    cubes, obstacles = [], []
    task_active = False
    task_completed = False
    task_start = 0
    completed_count = 0
    mistakes = 0
    message, message_kind = MSG_START, "info"   # kind: info / ok / bad
    voice.say(message)

    def set_message(text, kind="info", speak=True):
        nonlocal message, message_kind
        message, message_kind = text, kind
        if speak:
            voice.say(text)

    def new_task():
        nonlocal question, cubes, obstacles, task_active, task_completed, task_start
        level = LEVELS[level_index]
        robot.speed = level["speed"]
        robot.reset()
        question, values, correct_idx = make_question(level)
        rects, obstacles = generate_field(len(values), level["obstacles"], robot.rect)
        cubes = [{"rect": rect, "value": v, "correct": i == correct_idx,
                  "wrong": False, "color": CUBE_COLORS[i % len(CUBE_COLORS)]}
                 for i, (rect, v) in enumerate(zip(rects, values))]
        task_active, task_completed = True, False
        task_start = pygame.time.get_ticks()
        voice.say(question)
        set_message(MSG_TASK_OBST if obstacles else MSG_TASK, speak=False)

    def set_level(index):
        nonlocal level_index
        level_index = index % len(LEVELS)
        new_task()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h:
                    set_message(MSG_HELP)
                elif event.key == pygame.K_t:
                    new_task()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    set_level(event.key - pygame.K_1)
                elif event.key == pygame.K_v:
                    if voice.available:
                        state = "включён" if voice.toggle() else "выключен"
                        set_message(f"Голос {state}.")
                    else:
                        message = "Для голоса установите: pip install pyttsx3"
            if btn_help.clicked(event):
                set_message(MSG_HELP)
            if btn_task.clicked(event):
                new_task()
            if btn_level.clicked(event):
                set_level(level_index + 1)

        level = LEVELS[level_index]

        # --- логика ---
        robot.update(pygame.key.get_pressed())

        time_left = None
        if task_active and level["time"] is not None:
            elapsed = (pygame.time.get_ticks() - task_start) / 1000
            time_left = max(0, level["time"] - elapsed)
            if time_left <= 0:
                task_active = False
                set_message(MSG_TIMEOUT, "bad")

        if task_active:
            if any(robot.rect.colliderect(o) for o in obstacles):
                mistakes += 1
                robot.reset()
                set_message(MSG_HIT, "bad")
            else:
                for cube in cubes:
                    if cube["wrong"] or not robot.rect.colliderect(cube["rect"]):
                        continue
                    if cube["correct"]:
                        task_active, task_completed = False, True
                        completed_count += 1
                        set_message(MSG_DONE, "ok")
                    else:
                        cube["wrong"] = True
                        mistakes += 1
                        robot.reset()
                        set_message(MSG_WRONG, "bad")
                    break

        # --- отрисовка ---
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, PANEL_HEIGHT))
        pygame.draw.line(screen, GRAY, (0, PANEL_HEIGHT), (WIDTH, PANEL_HEIGHT), 2)
        screen.blit(font_title.render(TITLE, True, DARK), (20, 10))

        btn_level.color = LEVEL_COLORS[level_index]
        btn_level.hover_color = tuple(max(0, c - 25) for c in LEVEL_COLORS[level_index])
        btn_level.text = f"УРОВЕНЬ: {level['name']}"
        btn_help.draw(screen, font_btn)
        btn_task.draw(screen, font_btn)
        btn_level.draw(screen, font_btn)

        if time_left is not None:
            timer_color = RED_DARK if time_left < 10 else DARK
            timer = font_btn.render(f"Время: {time_left:0.0f} c", True, timer_color)
            screen.blit(timer, (WIDTH - timer.get_width() - 20, 62))

        # задача и сообщение
        screen.blit(font_question.render(question, True, BLUE_DARK), (20, 104))
        msg_color = {"ok": GREEN_DARK, "bad": RED_DARK}.get(message_kind, DARK)
        for i, line in enumerate(wrap_text(message, font_msg, WIDTH - 40)[:2]):
            screen.blit(font_msg.render(line, True, msg_color), (20, 140 + i * 22))

        for o in obstacles:
            draw_obstacle(screen, o)
        for cube in cubes:
            draw_cube(screen, cube, font_cube)
        robot.draw(screen, happy=task_completed, sad=(message_kind == "bad" and task_active))

        footer = f"{HINT}   |   Верно: {completed_count}   Ошибки: {mistakes}"
        screen.blit(font_small.render(footer, True, DARK), (20, HEIGHT - 24))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
