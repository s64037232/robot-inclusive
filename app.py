import random
import time
import streamlit as st
import streamlit.components.v1 as components

# Robot-Inclusive — Streamlit edition
st.set_page_config(page_title="Robot-Inclusive", page_icon="🤖", layout="wide")

# ---------- Game settings ----------
WIDTH, HEIGHT = 900, 600
PANEL_HEIGHT = 170
ROBOT_SIZE = 72
CUBE_SIZE = 76
OBSTACLE_SIZE = 60
CUBE_COLORS = ["#6366f1", "#eab308", "#ec4899", "#14b8a6"]
LEVELS = [
    {"name": "Лёгкий", "cubes": 2, "obstacles": 0, "time": None, "speed": 24,
     "questions": ["add10", "sub10", "sequence3", "even", "biggest"]},
    {"name": "Средний", "cubes": 3, "obstacles": 2, "time": None, "speed": 24,
     "questions": ["add20", "sub20", "mul5", "missing20", "sequence5", "odd", "smallest", "div5"]},
    {"name": "Сложный", "cubes": 4, "obstacles": 4, "time": 40, "speed": 28,
     "questions": ["mul9", "div9", "two_step", "brackets", "missing50", "sequence9", "div3"]},
]

def near_wrongs(correct, k, lo=0):
    pool = [correct + d for d in range(-6, 7) if d != 0 and correct + d >= lo]
    random.shuffle(pool)
    return pool[:k]

def make_question(level):
    k = level["cubes"] - 1
    kind = random.choice(level["questions"])
    if kind.startswith("add"):
        hi = int(kind[3:])
        a = random.randint(1, hi - 1); b = random.randint(1, hi - a)
        q, ans, wrong = f"Реши: {a} + {b} = ?", a+b, near_wrongs(a+b, k)
    elif kind.startswith("sub"):
        hi = int(kind[3:])
        a = random.randint(3, hi); b = random.randint(1, a-1)
        q, ans, wrong = f"Реши: {a} − {b} = ?", a-b, near_wrongs(a-b, k)
    elif kind.startswith("mul"):
        m = int(kind[3:]); a,b = random.randint(2,m),random.randint(2,m)
        q, ans, wrong = f"Реши: {a} × {b} = ?", a*b, near_wrongs(a*b,k)
    elif kind.startswith("div"):
        d = int(kind[3:]); b,c = random.randint(2,d),random.randint(2,d)
        q, ans, wrong = f"Реши: {b*c} ÷ {b} = ?", c, near_wrongs(c,k,1)
    elif kind.startswith("missing"):
        hi = int(kind[7:]); a = random.randint(1,hi-1); b = random.randint(1,hi-a)
        q, ans, wrong = f"Найди пропущенное число: ? + {b} = {a+b}", a, near_wrongs(a,k)
    elif kind == "two_step":
        a,b,c = [random.randint(2,9) for _ in range(3)]
        q,ans = f"Реши: {a} + {b} × {c} = ?", a+b*c
        wrong = near_wrongs(ans,k)
    elif kind == "brackets":
        a,b,c = random.randint(2,9),random.randint(2,9),random.randint(2,6)
        q,ans = f"Реши: ({a} + {b}) × {c} = ?", (a+b)*c
        wrong = near_wrongs(ans,k)
    elif kind.startswith("sequence"):
        step_max = int(kind[8:]); d = random.randint(2,step_max); start = random.randint(1,20 if step_max==9 else 10)
        seq = [start+d*i for i in range(4)]
        q,ans = f"Продолжи ряд: {seq[0]}, {seq[1]}, {seq[2]}, ?", seq[3]
        wrong = near_wrongs(ans,k,1)
    elif kind == "biggest":
        nums = random.sample(range(1,60),k+1); ans=max(nums); q="Найди самое БОЛЬШОЕ число"; wrong=[n for n in nums if n!=ans]
    elif kind == "smallest":
        nums = random.sample(range(1,60),k+1); ans=min(nums); q="Найди самое МАЛЕНЬКОЕ число"; wrong=[n for n in nums if n!=ans]
    elif kind == "even":
        q,ans="Найди ЧЁТНОЕ число",random.randint(1,30)*2
        wrong=random.sample(range(1,60,2),k)
    elif kind == "odd":
        q,ans="Найди НЕЧЁТНОЕ число",random.randint(0,30)*2+1
        wrong=random.sample(range(2,60,2),k)
    else:
        d=int(kind[3:]); ans=d*random.randint(2,12); q=f"Найди число, которое делится на {d}"
        wrong=random.sample([n for n in range(2,60) if n%d!=0],k)
    options=[ans]+list(wrong); random.shuffle(options)
    return q, options, options.index(ans)

def overlaps(a,b):
    return not (a[0]+a[2] <= b[0] or b[0]+b[2] <= a[0] or a[1]+a[3] <= b[1] or b[1]+b[3] <= a[1])

def generate_field(count_cubes, count_obstacles, robot):
    field=(20, PANEL_HEIGHT+20, WIDTH-40, HEIGHT-PANEL_HEIGHT-55)
    for _ in range(80):
        occupied=[(robot[0]-85,robot[1]-85,ROBOT_SIZE+170,ROBOT_SIZE+170)]
        cubes=[]; obstacles=[]
        for count,size,target in [(count_cubes,CUBE_SIZE,cubes),(count_obstacles,OBSTACLE_SIZE,obstacles)]:
            for _i in range(count):
                placed=None
                for _j in range(300):
                    x=random.randint(field[0],field[0]+field[2]-size)
                    y=random.randint(field[1],field[1]+field[3]-size)
                    rect=(x,y,size,size)
                    if not any(overlaps(rect,o) for o in occupied):
                        placed=rect; occupied.append((x-15,y-15,size+30,size+30)); break
                if placed is None: break
                target.append(placed)
            if len(target)!=count: break
        if len(cubes)==count_cubes and len(obstacles)==count_obstacles:
            return cubes,obstacles
    return cubes,obstacles

def fresh_state(level_index):
    level=LEVELS[level_index]
    robot=[WIDTH//2-ROBOT_SIZE//2, PANEL_HEIGHT+(HEIGHT-PANEL_HEIGHT)//2-ROBOT_SIZE//2]
    question,values,correct_idx=make_question(level)
    cube_rects,obstacle_rects=generate_field(len(values),level["obstacles"],robot)
    return {
        "robot":robot,
        "question":question,
        "cubes":[{"rect":list(r),"value":v,"correct":i==correct_idx,"wrong":False,"color":CUBE_COLORS[i%len(CUBE_COLORS)]} for i,(r,v) in enumerate(zip(cube_rects,values))],
        "obstacles":[list(r) for r in obstacle_rects],
        "active":True,"completed":False,"start":time.time(),
        "message":"Подведи робота к кубику с верным ответом!" + (" Обойди красные преграды!" if obstacle_rects else ""),
        "kind":"info"
    }

if "level" not in st.session_state:
    st.session_state.level=0
if "game" not in st.session_state:
    st.session_state.game=fresh_state(0)
if "completed_count" not in st.session_state:
    st.session_state.completed_count=0
if "mistakes" not in st.session_state:
    st.session_state.mistakes=0

def new_task():
    st.session_state.game=fresh_state(st.session_state.level)

def set_level(i):
    st.session_state.level=i
    new_task()

def move_robot(dx,dy):
    g=st.session_state.game
    if not g["active"]:
        return
    level=LEVELS[st.session_state.level]
    old=g["robot"][:]
    nx=max(0,min(WIDTH-ROBOT_SIZE,old[0]+dx*level["speed"]))
    ny=max(PANEL_HEIGHT,min(HEIGHT-ROBOT_SIZE-8,old[1]+dy*level["speed"]))
    candidate=[nx,ny,ROBOT_SIZE,ROBOT_SIZE]
    if any(overlaps(candidate,o) for o in g["obstacles"]):
        st.session_state.mistakes+=1
        g["robot"]=[WIDTH//2-ROBOT_SIZE//2, PANEL_HEIGHT+(HEIGHT-PANEL_HEIGHT)//2-ROBOT_SIZE//2]
        g["message"]="Ой! Это преграда. Попробуй ещё раз!"
        g["kind"]="bad"
        return
    g["robot"]=[nx,ny]
    robot_rect=[nx,ny,ROBOT_SIZE,ROBOT_SIZE]
    for cube in g["cubes"]:
        if cube["wrong"] or not overlaps(robot_rect,cube["rect"]):
            continue
        if cube["correct"]:
            g["active"]=False; g["completed"]=True
            st.session_state.completed_count+=1
            g["message"]="Верно! Молодец! Задание выполнено!"
            g["kind"]="ok"
        else:
            cube["wrong"]=True
            st.session_state.mistakes+=1
            g["robot"]=[WIDTH//2-ROBOT_SIZE//2, PANEL_HEIGHT+(HEIGHT-PANEL_HEIGHT)//2-ROBOT_SIZE//2]
            g["message"]="Ответ неверный! Попробуй ещё раз."
            g["kind"]="bad"
        break

def render_board():
    g=st.session_state.game
    robot=g["robot"]
    # SVG makes the robot, answer cubes and obstacles visible in the browser.
    parts=[f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Игровое поле робота" style="width:100%;height:auto;display:block;background:#ebf2fa;border:2px solid #cbd5e1;border-radius:14px">']
    parts.append('<rect x="0" y="0" width="900" height="170" fill="#ffffff"/>')
    parts.append('<text x="20" y="35" font-size="24" font-weight="700" fill="#1e293b">Robot-Inclusive — Робот-помощник</text>')
    for i,o in enumerate(g["obstacles"]):
        x,y,w,h=o
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ef4444" stroke="#b91c1c" stroke-width="4"/>')
        parts.append(f'<path d="M{x+14} {y+14} L{x+w-14} {y+h-14} M{x+w-14} {y+14} L{x+14} {y+h-14}" stroke="white" stroke-width="5"/>')
    for c in g["cubes"]:
        x,y,w,h=c["rect"]; color="#94a3b8" if c["wrong"] else c["color"]
        parts.append(f'<rect x="{x}" y="{y+6}" width="{w}" height="{h}" rx="14" fill="#64748b"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{color}" stroke="white" stroke-width="3"/>')
        parts.append(f'<text x="{x+w/2}" y="{y+48}" text-anchor="middle" font-size="30" font-weight="700" fill="white">{c["value"]}</text>')
        if c["wrong"]:
            parts.append(f'<path d="M{x+15} {y+15} L{x+w-15} {y+h-15} M{x+w-15} {y+15} L{x+15} {y+h-15}" stroke="#ef4444" stroke-width="6"/>')
    x,y=robot
    face="#22c55e" if g["completed"] else "#3b82f6"
    mouth='M 25 48 Q 36 60 47 48' if g["completed"] else ('M 25 58 Q 36 47 47 58' if g["kind"]=="bad" else 'M 27 54 L 45 54')
    parts.append(f'<line x1="{x+36}" y1="{y}" x2="{x+36}" y2="{y-15}" stroke="#1e293b" stroke-width="4"/>')
    parts.append(f'<circle cx="{x+36}" cy="{y-19}" r="6" fill="#f97316"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{ROBOT_SIZE}" height="{ROBOT_SIZE}" rx="16" fill="{face}" stroke="#2563eb" stroke-width="4"/>')
    parts.append(f'<circle cx="{x+22}" cy="{y+27}" r="9" fill="white"/><circle cx="{x+50}" cy="{y+27}" r="9" fill="white"/>')
    parts.append(f'<circle cx="{x+22}" cy="{y+27}" r="4" fill="#1e293b"/><circle cx="{x+50}" cy="{y+27}" r="4" fill="#1e293b"/>')
    parts.append(f'<path d="{mouth}" transform="translate({x},{y})" fill="none" stroke="white" stroke-width="3" stroke-linecap="round"/>')
    parts.append('</svg>')
    components.html("".join(parts), height=HEIGHT+20, scrolling=False)

# ---------- Interface ----------
st.title("🤖 Robot-Inclusive")
st.caption("Интерактивная игра-помощник для инклюзивного образования")

g=st.session_state.game
level=LEVELS[st.session_state.level]
if g["active"] and level["time"] is not None:
    remaining=max(0,level["time"]-(time.time()-g["start"]))
    if remaining<=0:
        g["active"]=False
        g["message"]="Время вышло. Ничего страшного, нажми «ЗАДАНИЕ» и попробуй снова!"
        g["kind"]="bad"
        remaining=0
else:
    remaining=None

top=st.columns([1,1,1,1])
with top[0]:
    if st.button("🆘 ПОМОЩЬ", use_container_width=True):
        g["message"]="Я помогу тебе! Не бойся задавать вопросы. Подведи робота к кубику с верным ответом."
        g["kind"]="info"
with top[1]:
    if st.button("🟢 ЗАДАНИЕ", use_container_width=True):
        new_task()
        st.rerun()
with top[2]:
    chosen=st.selectbox("Уровень",["Лёгкий","Средний","Сложный"],index=st.session_state.level,label_visibility="collapsed")
    new_index=["Лёгкий","Средний","Сложный"].index(chosen)
    if new_index!=st.session_state.level:
        set_level(new_index)
        st.rerun()
with top[3]:
    st.metric("Время", f"{remaining:.0f} с" if remaining is not None else "∞")

st.subheader(g["question"])
msg_color={"ok":"success","bad":"error"}.get(g["kind"],"info")
getattr(st,msg_color)(g["message"])

left,right=st.columns([3,1],gap="large")
with left:
    render_board()
with right:
    st.markdown("### Управление")
    st.caption("Нажимай стрелки, чтобы перемещать робота по игровому полю.")
    a,b,c=st.columns(3)
    with b:
        if st.button("⬆️",use_container_width=True,disabled=not g["active"]):
            move_robot(0,-1); st.rerun()
    a,b,c=st.columns(3)
    with a:
        if st.button("⬅️",use_container_width=True,disabled=not g["active"]):
            move_robot(-1,0); st.rerun()
    with b:
        if st.button("⬇️",use_container_width=True,disabled=not g["active"]):
            move_robot(0,1); st.rerun()
    with c:
        if st.button("➡️",use_container_width=True,disabled=not g["active"]):
            move_robot(1,0); st.rerun()
    st.divider()
    st.metric("Верно выполнено",st.session_state.completed_count)
    st.metric("Ошибки",st.session_state.mistakes)
    st.caption("Управление на этой версии — кнопками на странице. Каждый щелчок перемещает робота на один шаг.")

if g["completed"]:
    st.balloons()
st.caption("Подсказка: на лёгком уровне нет преград; на среднем — 2, на сложном — 4. На сложном уровне действует таймер 40 секунд.")
