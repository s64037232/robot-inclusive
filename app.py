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

def render_board():
    g=st.session_state.game
    robot=g["robot"]
    level=LEVELS[st.session_state.level]
    parts=[f'<div id="game-frame" tabindex="0" style="outline:none;width:100%;background:#ebf2fa;border:2px solid #cbd5e1;border-radius:14px;overflow:hidden">']
    parts.append(f'<svg id="game-svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Игровое поле робота" style="width:100%;height:auto;display:block;background:#ebf2fa">')
    parts.append('<rect x="0" y="0" width="900" height="170" fill="#ffffff"/>')
    parts.append('<text x="20" y="35" font-size="24" font-weight="700" fill="#1e293b">Robot-Inclusive — Робот-помощник</text>')
    parts.append(f'<rect x="16" y="52" width="868" height="104" rx="12" fill="#eff6ff" stroke="#bfdbfe" stroke-width="2"/>')
    parts.append(f'<text id="question-text" x="34" y="96" font-size="25" font-weight="700" fill="#1e293b">{g["question"]}</text>')
    parts.append('<text x="34" y="132" font-size="15" fill="#475569">Найди правильный ответ и доведи до него робота</text>')
    for i,o in enumerate(g["obstacles"]):
        x,y,w,h=o
        parts.append(f'<rect id="obstacle-{i}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ef4444" stroke="#b91c1c" stroke-width="4"/>')
        parts.append(f'<path d="M{x+14} {y+14} L{x+w-14} {y+h-14} M{x+w-14} {y+14} L{x+14} {y+h-14}" stroke="white" stroke-width="5"/>')
    for i,c in enumerate(g["cubes"]):
        x,y,w,h=c["rect"]; color="#94a3b8" if c["wrong"] else c["color"]
        parts.append(f'<g id="cube-{i}" data-correct="{str(c["correct"]).lower()}" data-wrong="{str(c["wrong"]).lower()}">')
        parts.append(f'<rect x="{x}" y="{y+6}" width="{w}" height="{h}" rx="14" fill="#64748b"/>')
        parts.append(f'<rect class="cube-face" x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{color}" stroke="white" stroke-width="3"/>')
        parts.append(f'<text x="{x+w/2}" y="{y+48}" text-anchor="middle" font-size="30" font-weight="700" fill="white">{c["value"]}</text>')
        if c["wrong"]:
            parts.append(f'<path d="M{x+15} {y+15} L{x+w-15} {y+h-15} M{x+w-15} {y+15} L{x+15} {y+h-15}" stroke="#ef4444" stroke-width="6"/>')
        parts.append('</g>')
    x,y=robot
    face="#22c55e" if g["completed"] else "#3b82f6"
    mouth='M 25 48 Q 36 60 47 48' if g["completed"] else ('M 25 58 Q 36 47 47 58' if g["kind"]=="bad" else 'M 27 54 L 45 54')
    parts.append(f'<g id="robot" transform="translate({x} {y})">')
    parts.append('<line x1="36" y1="0" x2="36" y2="-15" stroke="#1e293b" stroke-width="4"/><circle cx="36" cy="-19" r="6" fill="#f97316"/>')
    parts.append(f'<rect id="robot-body" x="0" y="0" width="{ROBOT_SIZE}" height="{ROBOT_SIZE}" rx="16" fill="{face}" stroke="#2563eb" stroke-width="4"/>')
    parts.append('<circle cx="22" cy="27" r="9" fill="white"/><circle cx="50" cy="27" r="9" fill="white"/><circle cx="22" cy="27" r="4" fill="#1e293b"/><circle cx="50" cy="27" r="4" fill="#1e293b"/>')
    parts.append(f'<path d="{mouth}" fill="none" stroke="white" stroke-width="3" stroke-linecap="round"/>')
    parts.append('</g></svg>')
    
    # Добавляем мобильную панель управления (D-pad кнопки и блок под джойстик)
    parts.append('''
    <div style="background:#ffffff; padding:15px; border-top:2px solid #cbd5e1; display:flex; flex-wrap:wrap; justify-content:space-around; align-items:center; gap:15px;">
        <div id="joystick-container" style="position:relative; width:130px; height:130px; background:#f8fafc; border:2px dashed #cbd5e1; border-radius:50%; display:flex; align-items:center; justify-content:center;">
            <span style="font-size:12px; color:#64748b; font-family:Arial;">Джойстик</span>
        </div>
        <div style="display:grid; grid-template-columns: repeat(3, 60px); grid-template-rows: repeat(2, 50px); gap:6px; justify-content:center;">
            <div></div>
            <button id="mob-up" style="font-size:22px; background:#3b82f6; color:white; border:none; border-radius:10px; cursor:pointer; touch-action:manipulation;">⬆️</button>
            <div></div>
            <button id="mob-left" style="font-size:22px; background:#3b82f6; color:white; border:none; border-radius:10px; cursor:pointer; touch-action:manipulation;">⬅️</button>
            <button id="mob-down" style="font-size:22px; background:#3b82f6; color:white; border:none; border-radius:10px; cursor:pointer; touch-action:manipulation;">⬇️</button>
            <button id="mob-right" style="font-size:22px; background:#3b82f6; color:white; border:none; border-radius:10px; cursor:pointer; touch-action:manipulation;">➡️</button>
        </div>
    </div>
    ''')
    
    parts.append(f'<div id="game-message" style="padding:10px 14px;color:#1e293b;font:600 15px Arial;background:white">{g["message"]}</div>')
    parts.append(f'<div id="game-stats" style="padding:0 14px 8px;background:white;color:#475569;font:13px Arial">Верно выполнено: {st.session_state.completed_count} · Ошибки: {st.session_state.mistakes}</div>')
    parts.append('<div style="padding:0 14px 12px;color:#475569;font:13px Arial">Используй клавиатуру (стрелки/WASD), сенсорный джойстик или экранные кнопки.</div></div>')
    
    # Подключаем библиотеку nipplejs для мобильного джойстика и логику управления
    parts.append(f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/nipplejs/0.10.1/nipplejs.min.js"></script>
<script>
(() => {{
  const frame = document.getElementById('game-frame');
  const svg = document.getElementById('game-svg');
  const robot = document.getElementById('robot');
  const message = document.getElementById('game-message');
  const stats = document.getElementById('game-stats');
  const body = document.getElementById('robot-body');
  let x = {robot[0]}, y = {robot[1]};
  let active = {str(g["active"]).lower()};
  let completed = {str(g["completed"]).lower()};
  let completedCount = {st.session_state.completed_count};
  let mistakes = {st.session_state.mistakes};
  function updateStats() {{ const left = timeLimit > 0 ? ` · Время: ${{Math.max(0, Math.ceil(timeLimit-(performance.now()-started)/1000))}} с` : ''; stats.textContent = `Верно выполнено: ${{completedCount}} · Ошибки: ${{mistakes}}${{left}}`; }}
  const speed = 230;
  const robotSize = {ROBOT_SIZE};
  const maxX = {WIDTH-ROBOT_SIZE};
  const minY = {PANEL_HEIGHT};
  const maxY = {HEIGHT-ROBOT_SIZE-8};
  const keys = new Set();
  let joystickDx = 0, joystickDy = 0;

  const obstacles = [...svg.querySelectorAll('[id^="obstacle-"]')].map(el => ({{x:+el.getAttribute('x'),y:+el.getAttribute('y'),w:+el.getAttribute('width'),h:+el.getAttribute('height')}}));
  const cubes = [...svg.querySelectorAll('[id^="cube-"]')].map(el => ({{el,x:+el.querySelector('.cube-face').getAttribute('x'),y:+el.querySelector('.cube-face').getAttribute('y'),w:+el.querySelector('.cube-face').getAttribute('width'),h:+el.querySelector('.cube-face').getAttribute('height')}}));
  let last = performance.now();
  const timeLimit = {level["time"] if level["time"] is not None else 0};
  let started = performance.now();
  let nextPending = false;
  const levelIndex = {st.session_state.level};
  const cubeColors = ['#6366f1','#eab308','#ec4899','#14b8a6'];
  function hit(a,b) {{ return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y; }}
  function resetRobot() {{ x={WIDTH//2-ROBOT_SIZE//2}; y={PANEL_HEIGHT+(HEIGHT-PANEL_HEIGHT)//2-ROBOT_SIZE//2}; }}
  function say(text, color='#1e293b') {{ message.textContent=text; message.style.color=color; }}
  
  function buildQuestion() {{
    let a,b,answer,q;
    if(levelIndex===0) {{
      if(Math.random()<0.5) {{ a=1+Math.floor(Math.random()*9); b=1+Math.floor(Math.random()*(10-a)); answer=a+b; q=`Реши: ${{a}} + ${{b}} = ?`; }}
      else {{ a=3+Math.floor(Math.random()*8); b=1+Math.floor(Math.random()*(a-1)); answer=a-b; q=`Реши: ${{a}} − ${{b}} = ?`; }}
    }} else if(levelIndex===1) {{
      const mode=Math.floor(Math.random()*3);
      if(mode===0) {{ a=2+Math.floor(Math.random()*9); b=2+Math.floor(Math.random()*9); answer=a+b; q=`Реши: ${{a}} + ${{b}} = ?`; }}
      else if(mode===1) {{ a=2+Math.floor(Math.random()*9); b=2+Math.floor(Math.random()*9); answer=a*b; q=`Реши: ${{a}} × ${{b}} = ?`; }}
      else {{ a=5+Math.floor(Math.random()*15); b=1+Math.floor(Math.random()*(a-1)); answer=a-b; q=`Реши: ${{a}} − ${{b}} = ?`; }}
    }} else {{
      const mode=Math.floor(Math.random()*3);
      if(mode===0) {{ a=2+Math.floor(Math.random()*8); b=2+Math.floor(Math.random()*8); answer=a*b; q=`Реши: ${{a}} × ${{b}} = ?`; }}
      else if(mode===1) {{ b=2+Math.floor(Math.random()*8); a=2+Math.floor(Math.random()*8); answer=a; q=`Реши: ${{a*b}} ÷ ${{b}} = ?`; }}
      else {{ a=10+Math.floor(Math.random()*30); b=2+Math.floor(Math.random()*9); answer=a+b; q=`Реши: ${{a}} + ${{b}} = ?`; }}
    }}
    const vals=[answer];
    while(vals.length<cubes.length) {{ const v=Math.max(0,answer+Math.floor(Math.random()*13)-6); if(!vals.includes(v)) vals.push(v); }}
    for(let i=vals.length-1;i>0;i--) {{ const j=Math.floor(Math.random()*(i+1)); [vals[i],vals[j]]=[vals[j],vals[i]]; }}
    document.getElementById('question-text').textContent=q;
    const placed=[];
    cubes.forEach((c,i)=>{{
      let px,py,tries=0,rect;
      do {{ px=20+Math.random()* (840-c.w); py=190+Math.random()*(525-190-c.h); rect={{x:px,y:py,w:c.w,h:c.h}}; tries++; }}
      while(tries<300 && (hit(rect,{{x,y,w:robotSize,h:robotSize}}) || obstacles.some(o=>hit(rect,o)) || placed.some(o=>hit(rect,o))));
      c.x=px; c.y=py; placed.push(rect); c.el.dataset.wrong='false'; c.el.dataset.correct=String(vals[i]===answer);
      const rs=c.el.querySelectorAll('rect'); rs[0].setAttribute('x',px); rs[0].setAttribute('y',py+6); rs[1].setAttribute('x',px); rs[1].setAttribute('y',py); rs[1].setAttribute('fill',cubeColors[i%cubeColors.length]);
      const label=c.el.querySelector('text'); label.setAttribute('x',px+c.w/2); label.setAttribute('y',py+48); label.textContent=vals[i];
      const cross=c.el.querySelector('path'); if(cross) cross.remove();
    }});
    resetRobot(); robot.setAttribute('transform',`translate(${{x}} ${{y}})`);
    body.setAttribute('fill','#3b82f6'); active=true; completed=false; nextPending=false; started=performance.now();
    say('Новое задание! Найди правильный ответ.'); keys.clear(); joystickDx = 0; joystickDy = 0;
  }}

  function tick(now) {{
    const dt = Math.min((now-last)/1000, 0.05); last=now;
    if (active) {{
      updateStats();
      if (timeLimit > 0 && (now-started)/1000 >= timeLimit) {{ active=false; keys.clear(); joystickDx=0; joystickDy=0; say('Время вышло. Нажми «ЗАДАНИЕ» и попробуй снова!', '#dc2626'); }}
      
      let kbDx = (keys.has('ArrowRight')||keys.has('d')||keys.has('D')?1:0) - (keys.has('ArrowLeft')||keys.has('a')||keys.has('A')?1:0);
      let kbDy = (keys.has('ArrowDown')||keys.has('s')||keys.has('S')?1:0) - (keys.has('ArrowUp')||keys.has('w')||keys.has('W')?1:0);
      
      let dx = kbDx !== 0 ? kbDx : joystickDx;
      let dy = kbDy !== 0 ? kbDy : joystickDy;
      
      if (dx || dy) {{ const len=Math.hypot(dx,dy); if(len > 1) {{ dx/=len; dy/=len; }} }}
      
      const nx=Math.max(0,Math.min(maxX,x+dx*speed*dt));
      const ny=Math.max(minY,Math.min(maxY,y+dy*speed*dt));
      const candidate={{x:nx,y:ny,w:robotSize,h:robotSize}};
      if (obstacles.some(o=>hit(candidate,o))) {{
        resetRobot(); keys.clear(); joystickDx=0; joystickDy=0; mistakes++; updateStats(); say('Ой! Это преграда. Попробуй ещё раз!', '#dc2626');
      }} else {{
        x=nx; y=ny;
        for (const c of cubes) {{
          if (c.el.dataset.wrong==='true' || !hit(candidate,c)) continue;
          if (c.el.dataset.correct==='true') {{
            active=false; completed=true; completedCount++; updateStats(); keys.clear(); joystickDx=0; joystickDy=0; body.setAttribute('fill','#22c55e');
            say('Верно! Молодец! Сейчас появится новое задание…', '#16a34a');
            if(!nextPending) {{ nextPending=true; setTimeout(buildQuestion, 1100); }}
          }} else {{
            c.el.dataset.wrong='true'; c.el.querySelector('.cube-face').setAttribute('fill','#94a3b8');
            resetRobot(); keys.clear(); joystickDx=0; joystickDy=0; mistakes++; updateStats(); say('Ответ неверный! Попробуй ещё раз.', '#dc2626');
          }}
          break;
        }}
      }}
      robot.setAttribute('transform',`translate(${{x}} ${{y}})`);
    }}
    requestAnimationFrame(tick);
  }}

  // Обработка клавиатуры
  window.addEventListener('keydown', e => {{
    if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' ','w','a','s','d','W','A','S','D'].includes(e.key)) e.preventDefault();
    keys.add(e.key);
  }});
  window.addEventListener('keyup', e => keys.delete(e.key));
  window.addEventListener('blur', () => {{ keys.clear(); joystickDx=0; joystickDy=0; }});

  // Обработка экранных кнопок D-pad для мобильных
  const bindBtn = (id, kx, ky) => {{
    const el = document.getElementById(id);
    if(!el) return;
    ['touchstart', 'mousedown'].forEach(evt => el.addEventListener(evt, e => {{ e.preventDefault(); keys.add(kx); keys.add(ky); }}));
    ['touchend', 'mouseup', 'mouseleave'].forEach(evt => el.addEventListener(evt, e => {{ e.preventDefault(); keys.delete(kx); keys.delete(ky); }}));
  }};
  bindBtn('mob-up', 'ArrowUp', 'ArrowUp');
  bindBtn('mob-down', 'ArrowDown', 'ArrowDown');
  bindBtn('mob-left', 'ArrowLeft', 'ArrowLeft');
  bindBtn('mob-right', 'ArrowRight', 'ArrowRight');

  // Инициализация сенсорного джойстика NippleJS
  try {{
    const manager = nipplejs.create({{
      zone: document.getElementById('joystick-container'),
      mode: 'static',
      position: {{left: '50%', top: '50%'}},
      color: '#3b82f6',
      size: 100
    }});
    manager.on('move', (evt, data) => {{
      if (data && data.vector) {{
        joystickDx = data.vector.x;
        joystickDy = -data.vector.y; // Инвертируем Y для экрана SVG
      }}
    }});
    manager.on('end', () => {{
      joystickDx = 0;
      joystickDy = 0;
    }});
  }} catch(err) {{
    console.log("Joystick init error:", err);
  }}

  frame.addEventListener('pointerdown', () => frame.focus());
  frame.focus();
  requestAnimationFrame(tick);
}})();
</script>
""")
    components.html("".join(parts), height=HEIGHT+230, scrolling=False)

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
    st.caption("Управление: ПК / Смартфон")

left,right=st.columns([3,1],gap="large")
with left:
    render_board()
with right:
    st.markdown("### Управление")
    st.caption("• **ПК:** Стрелки или клавиши W, A, S, D.")
    st.caption("• **Смартфон/Планшет:** Используйте виртуальный джойстик или кнопки направления прямо под игровым полем.")
    st.divider()
    st.caption("Счётчики обновляются прямо на игровом поле.")

if g["completed"]:
    st.balloons()
st.caption("Подсказка: на лёгком уровне нет преград; на среднем — 2, на сложном — 4. На сложном уровне действует таймер 40 секунд.")
