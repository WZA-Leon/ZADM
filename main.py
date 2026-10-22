# -*- coding: utf-8 -*-
"""
ZADM 随机点名系统（主界面）

界面全部使用 Canvas 自绘，并带有逐帧动画：
    · 渐变背景 + 漂移星点
    · 标题逐字浮动变色、分隔线流光
    · 卡牌呼吸描边、四角光标
    · 滚动姓名带残影 / 浮动 / 变色
    · 停止时减速缓冲，结果弹出、光环扩散、彩纸爆炸
    · 按钮悬停发光、按下下沉、文字淡入淡出

抽选逻辑使用「抽签袋」：一轮之内不会重复抽到同一个人，
并且任何模式下都不会连续两次抽到同一个人，
因此结果不再受“点击间隔是否相似”影响。
"""

import json
import math
import os
import random as r
import tkinter as t
import tkinter.font as tkfont

# 导入代码查看模块
import code_viewer

# 导入修改名单模块
import name_manager

# ---------------------------------------------------------------- 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, 'data', 'names.json')
ICON_PATH = os.path.join(BASE_DIR, 'data', 'zadm.ico')
DEFAULT_NAMES = ['张三', '李四', '王五', '赵六']

# ---------------------------------------------------------------- 尺寸
W, H = 1000, 600
FRAME_MS = 33                      # 主循环帧间隔（毫秒）
CARD_BOX = (120, 168, 880, 392)    # 中央卡牌
NAME_CX, NAME_CY = 500, 280        # 姓名中心
HINT_Y = 424                       # 提示文字

# ---------------------------------------------------------------- 配色（浅色主题）
BG_TOP = '#f8fbff'
BG_BOTTOM = '#dbe9f7'
BG_MID = '#eaf3fb'
CARD_BG = '#ffffff'
ACCENT = '#1b86bd'
ACCENT_SOFT = '#2f86c9'
ACCENT_TEXT = '#15678f'
GOLD = '#e69a1d'
GOLD_TEXT = '#96650a'
WARM = '#c0431f'
FLASH = '#f08a1e'
TEXT = '#1d2c3b'
MUTED = '#5a6f88'
SHADOW = '#cdddec'


# ---------------------------------------------------------------- 颜色工具
def _rgb(color):
    color = color.lstrip('#')
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def mix(c1, c2, k):
    """在两个颜色之间线性插值，k 取 0~1"""
    k = max(0.0, min(1.0, k))
    a, b = _rgb(c1), _rgb(c2)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def ease_out(k):
    """缓出曲线，用于减速、扩散等动画"""
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def round_rect(canvas, x1, y1, x2, y2, radius=18, **options):
    """在画布上画一个圆角矩形（用平滑多边形实现）"""
    radius = min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0)
    points = (
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    )
    return canvas.create_polygon(points, smooth=True, **options)


# ---------------------------------------------------------------- 抽签袋
class NameBag:
    """抽签袋：一轮之内不重复，跨轮也不会连续抽到同一个人"""

    def __init__(self):
        self.pool = []
        self.last = None

    def reset(self):
        self.pool = []

    def draw(self, names, bag_mode=True):
        """抽出一个姓名；bag_mode 为 False 时是纯随机（但仍避开上一次的结果）"""
        if not names:
            return None
        if bag_mode:
            self.pool = [n for n in self.pool if n in names]
            if not self.pool:
                self.pool = list(names)
                r.shuffle(self.pool)
                # 新一轮的第一个不能和上一轮最后一个相同，避免“跨轮重复”
                if len(self.pool) > 1 and self.pool[0] == self.last:
                    self.pool.append(self.pool.pop(0))
            name = self.pool.pop(0)
        else:
            candidates = [n for n in names if n != self.last] or list(names)
            name = r.choice(candidates)
        self.last = name
        return name


# ---------------------------------------------------------------- 背景星点
class Star:
    """缓慢上浮、明暗闪烁的小光点"""

    def __init__(self, canvas):
        self.c = canvas
        self.x = r.uniform(0, W)
        self.y = r.uniform(0, H)
        self.r = r.uniform(0.7, 2.0)
        self.vy = -r.uniform(0.08, 0.35)
        self.phase = r.uniform(0, 6.28)
        self.speed = r.uniform(0.02, 0.06)
        self.base = r.choice(('#5f93c9', '#7fb0dd', '#6e8fb5', '#d99a4e', '#4fb3cf'))
        self.color = self.base
        self.item = canvas.create_oval(self.x - self.r, self.y - self.r,
                                       self.x + self.r, self.y + self.r,
                                       outline='', fill=self.base)

    def step(self, frame):
        self.y += self.vy
        self.x += math.sin(frame * 0.01 + self.phase) * 0.08
        if self.y < -4:
            self.y = H + 4
            self.x = r.uniform(0, W)
        if self.x < -4:
            self.x = W + 4
        elif self.x > W + 4:
            self.x = -4
        alpha = 0.18 + 0.55 * (0.5 + 0.5 * math.sin(frame * self.speed + self.phase))
        color = mix(BG_MID, self.base, alpha)
        if color != self.color:
            self.color = color
            self.c.itemconfig(self.item, fill=color)
        self.c.coords(self.item, self.x - self.r, self.y - self.r,
                      self.x + self.r, self.y + self.r)


# ---------------------------------------------------------------- 一次性特效
class PulseRing:
    """结果揭晓时向外扩散的光环"""

    def __init__(self, canvas, cx, cy, life=22, delay=0):
        self.c = canvas
        self.cx, self.cy = cx, cy
        self.life = life
        self.t = -delay
        radius = 44
        self.item = canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                       outline=GOLD, width=3,
                                       state='normal' if delay == 0 else 'hidden')

    def step(self):
        self.t += 1
        if self.t <= 0:
            return True
        progress = self.t / float(self.life)
        if progress >= 1:
            self.c.delete(self.item)
            return False
        if self.t == 1:
            self.c.itemconfig(self.item, state='normal')
        radius = 44 + 250 * ease_out(progress)
        self.c.coords(self.item, self.cx - radius, self.cy - radius,
                      self.cx + radius, self.cy + radius)
        self.c.itemconfig(self.item, outline=mix(GOLD, CARD_BG, progress ** 0.7),
                          width=max(1, int(round(4 - 3 * progress))))
        return True

    def dispose(self):
        self.c.delete(self.item)


class Confetti:
    """结果揭晓时喷出的彩纸"""

    COLORS = (ACCENT, GOLD, '#ee4266', '#06b6a4', '#6c5ce7', WARM)

    def __init__(self, canvas, cx, cy, count=90, life=56):
        self.c = canvas
        self.life = life
        self.age = 0
        self.parts = []
        for _ in range(count):
            angle = r.uniform(-math.pi * 0.95, -math.pi * 0.05)
            speed = r.uniform(3.5, 11.0)
            w = r.uniform(4, 9)
            h = r.uniform(2, 5)
            color = r.choice(self.COLORS)
            item = canvas.create_rectangle(0, 0, w, h, outline='', fill=color)
            self.parts.append({
                'item': item,
                'x': cx + r.uniform(-30, 30),
                'y': cy + r.uniform(-16, 16),
                'vx': math.cos(angle) * speed * r.uniform(0.6, 1.4),
                'vy': math.sin(angle) * speed,
                'w': w,
                'h': h,
                'color': color,
                'spin': r.uniform(0.15, 0.45),
                'rot': r.uniform(0, 6.28),
                'delay': r.uniform(0, 4),
            })

    def step(self):
        self.age += 1
        if self.age > self.life:
            self.dispose()
            return False
        fade = max(0.0, (self.age - self.life * 0.6) / (self.life * 0.4))
        for p in self.parts:
            if p['delay'] > 0:
                p['delay'] -= 1
                continue
            p['vy'] += 0.32
            p['vx'] *= 0.992
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['rot'] += p['spin']
            if p['y'] > H + 30:
                continue
            half_w = p['w'] * (0.35 + 0.65 * abs(math.cos(p['rot']))) / 2.0
            half_h = p['h'] / 2.0
            self.c.coords(p['item'], p['x'] - half_w, p['y'] - half_h,
                          p['x'] + half_w, p['y'] + half_h)
            self.c.itemconfig(p['item'], fill=mix(p['color'], CARD_BG, fade))
        return True

    def dispose(self):
        for p in self.parts:
            self.c.delete(p['item'])


class NamePop:
    """结果姓名的弹出缩放动画"""

    def __init__(self, app, life=18):
        self.app = app
        self.t = 0
        self.life = life

    def step(self):
        self.t += 1
        progress = self.t / float(self.life)
        if progress < 0.5:
            k = 0.55 + 0.55 * ease_out(progress / 0.5)      # 0.55 -> 1.10
        else:
            k = 1.10 - 0.10 * ease_out((progress - 0.5) / 0.5)   # 1.10 -> 1.0
        self.app.name_font.configure(size=max(14, int(self.app.name_size * k)))
        self.app.canvas.itemconfig(self.app.name_item,
                                   fill=mix(FLASH, GOLD_TEXT, min(1.0, progress * 1.8)))
        if self.t >= self.life:
            self.app.name_font.configure(size=self.app.name_size)
            self.app.canvas.itemconfig(self.app.name_item, fill=GOLD_TEXT)
            return False
        return True

    def dispose(self):
        self.app.name_font.configure(size=self.app.name_size)
        self.app.canvas.itemconfig(self.app.name_item, fill=GOLD_TEXT)


# ---------------------------------------------------------------- 自绘按钮
class GlowButton:
    """Canvas 圆角按钮：悬停发光、按下下沉、换色与文字淡入淡出"""

    def __init__(self, canvas, box, text, command, base, hover, text_color,
                 font, radius=16, halo=False):
        self.c = canvas
        self.box = box
        self.command = command
        self.base = base
        self.hover_color = hover
        self.cur_base = base
        self.cur_hover = hover
        self.text_color = text_color
        # 悬停时文字颜色朝对比度更高的方向变化（浅色主题下是变深）
        lum = sum(_rgb(text_color)) / 3.0
        self.text_hover = mix(text_color, '#000000' if lum < 128 else '#ffffff', 0.35)
        self.text = text
        self.pending = None
        self.fade = 1.0
        self.fade_dir = 0
        self.hover_t = 0.0
        self.target = 0.0
        self.press = 0.0

        x1, y1, x2, y2 = box
        self.cx, self.cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

        self.halo = None
        if halo:
            self.halo = round_rect(canvas, x1 - 10, y1 - 10, x2 + 10, y2 + 10,
                                   radius + 10, fill=mix(BG_MID, base, 0.12),
                                   outline='')
        self.shape = round_rect(canvas, x1, y1, x2, y2, radius, fill=base, outline='')
        self.label = canvas.create_text(self.cx, self.cy, text=text, font=font,
                                        fill=text_color)

        for item in (self.shape, self.label):
            canvas.tag_bind(item, '<Enter>', self._on_enter)
            canvas.tag_bind(item, '<Leave>', self._on_leave)
            canvas.tag_bind(item, '<ButtonPress-1>', self._on_press)
            canvas.tag_bind(item, '<ButtonRelease-1>', self._on_release)

    # ---- 事件处理 ----
    def _on_enter(self, event=None):
        self.target = 1.0
        try:
            self.c.configure(cursor='hand2')
        except t.TclError:
            pass

    def _on_leave(self, event=None):
        self.target = 0.0
        self.press = 0.0
        try:
            self.c.configure(cursor='')
        except t.TclError:
            pass

    def _on_press(self, event=None):
        self.press = 1.0

    def _on_release(self, event=None):
        self.press = 0.0
        if event is None:
            return
        x, y = self.c.canvasx(event.x), self.c.canvasy(event.y)
        x1, y1, x2, y2 = self.box
        if x1 <= x <= x2 and y1 <= y <= y2:
            self.command()

    # ---- 外观设置 ----
    def set(self, text=None, text_color=None, base=None, hover=None):
        if base is not None:
            self.base = base
        if hover is not None:
            self.hover_color = hover
        if text_color is not None:
            self.text_color = text_color
        if text is not None and text != self.text and text != self.pending:
            self.pending = text
            self.fade_dir = -1

    def update(self, frame):
        self.hover_t += (self.target - self.hover_t) * 0.22
        self.cur_base = mix(self.cur_base, self.base, 0.18)
        self.cur_hover = mix(self.cur_hover, self.hover_color, 0.18)
        fill = mix(self.cur_base, self.cur_hover, self.hover_t)
        if self.press:
            fill = mix(fill, '#000000', 0.15 * self.press)
        self.c.itemconfig(self.shape, fill=fill)

        # 文字淡出 -> 换字 -> 淡入
        if self.fade_dir < 0:
            self.fade -= 0.22
            if self.fade <= 0:
                self.fade = 0.0
                if self.pending is not None:
                    self.text = self.pending
                    self.pending = None
                    self.c.itemconfig(self.label, text=self.text)
                self.fade_dir = 1
        elif self.fade_dir > 0:
            self.fade = min(1.0, self.fade + 0.22)
            if self.fade >= 1.0:
                self.fade_dir = 0

        text_color = mix(self.text_color, self.text_hover, self.hover_t)
        self.c.itemconfig(self.label, fill=mix(fill, text_color, self.fade))
        self.c.coords(self.label, self.cx, self.cy - 1.5 * self.hover_t + 2.5 * self.press)
        if self.halo is not None:
            glow = 0.22 + 0.08 * math.sin(frame * 0.08) + 0.12 * self.hover_t
            self.c.itemconfig(self.halo, fill=mix(BG_MID, self.cur_base, glow))


# ---------------------------------------------------------------- 主程序
class ZadmApp:
    def __init__(self, root):
        self.root = root
        self.alive = True
        self.frame = 0
        self.state = 'idle'          # idle / rolling / slowing / result
        self.effects = []
        self.roll_job = None
        self.slow_job = None
        self.flash = 0.0
        self.name_text = ''
        self.name_size = 64
        self.name_color = ACCENT_SOFT
        self.name_cycle = 0
        self.bag_mode = True
        self.bag = NameBag()
        self.hint_full = ''
        self.hint_shown = 0
        self.slow_delay = 55
        self.slow_step = 0
        self.winner = None
        self.names = []

        self.load_names(initial=True)

        root.title('ZADM 1.4.0 · 随机点名')
        root.geometry('%dx%d' % (W, H))
        root.resizable(False, False)
        root.configure(bg=BG_TOP)
        try:
            root.iconbitmap(ICON_PATH)
        except Exception:
            pass

        self.canvas = t.Canvas(root, width=W, height=H, bg=BG_TOP,
                               highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        self.title_font = tkfont.Font(family='华文中宋', size=25, weight='bold')
        self.name_font = tkfont.Font(family='华文中宋', size=64, weight='bold')

        self.build_background()
        self.build_header()
        self.build_card()
        self.build_buttons()
        self.build_footer()

        self.name_text = '点击开始'
        self.canvas.itemconfig(self.name_item, text=self.name_text, fill=ACCENT_SOFT)
        self.set_hint('点击按钮开始抽选 · 也可以按空格键')

        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<space>', self.toggle)
        root.bind('<Return>', self.toggle)
        root.lift()
        self.tick()

    # ---------------- 数据 ----------------
    def load_names(self, initial=False):
        """读取名单；文件不存在时写入默认名单，读取失败时沿用旧名单"""
        names = None
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                names = [str(n).strip() for n in data if str(n).strip()]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            names = None

        if names is None:
            if not initial:
                return
            names = list(DEFAULT_NAMES)
            try:
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(names, f, ensure_ascii=False, indent=2)
            except OSError:
                pass

        if names != self.names:
            self.bag.reset()
            self.names = names

    # ---------------- 界面搭建 ----------------
    def build_background(self):
        steps = 100
        for i in range(steps):
            y1 = H * i / float(steps)
            y2 = H * (i + 1) / float(steps) + 1
            self.canvas.create_rectangle(0, y1, W, y2, outline='',
                                         fill=mix(BG_TOP, BG_BOTTOM,
                                                  (i / (steps - 1.0)) ** 0.85))
        self.stars = [Star(self.canvas) for _ in range(70)]

    def build_header(self):
        text = 'ZADM · 随机点名'
        total = self.title_font.measure(text)
        x = (W - total) / 2.0
        self.title_items = []
        for i, ch in enumerate(text):
            cw = self.title_font.measure(ch)
            item = self.canvas.create_text(x + cw / 2.0, 60, text=ch,
                                           font=self.title_font, fill=TEXT)
            self.title_items.append((item, x + cw / 2.0, i))
            x += cw
        self.canvas.create_line(310, 100, 690, 100, fill='#cfdeee', width=2)
        self.sweep_item = self.canvas.create_line(310, 100, 380, 100,
                                                  fill=ACCENT_SOFT, width=2,
                                                  capstyle='round')

    def build_card(self):
        x1, y1, x2, y2 = CARD_BOX
        self.card_halo = []
        for grow, strength in ((26, 0.07), (16, 0.10), (8, 0.13)):
            item = round_rect(self.canvas, x1 - grow, y1 - grow, x2 + grow, y2 + grow,
                              30, fill=mix(BG_MID, ACCENT, strength), outline='')
            self.card_halo.append((item, strength))
        self.card_body = round_rect(self.canvas, x1, y1, x2, y2, 24,
                                    fill=CARD_BG, outline='')
        self.card_edge = round_rect(self.canvas, x1, y1, x2, y2, 24,
                                    fill='', outline=ACCENT, width=2)

        # 四角光标
        length, inset = 22, 16
        self.brackets = []
        corners = ((x1 + inset, y1 + inset, 1, 1),
                   (x2 - inset, y1 + inset, -1, 1),
                   (x1 + inset, y2 - inset, 1, -1),
                   (x2 - inset, y2 - inset, -1, -1))
        for cx, cy, sx, sy in corners:
            self.brackets.append(self.canvas.create_line(
                cx, cy, cx + length * sx, cy, fill=ACCENT, width=2, capstyle='round'))
            self.brackets.append(self.canvas.create_line(
                cx, cy, cx, cy + length * sy, fill=ACCENT, width=2, capstyle='round'))

        # 姓名：阴影 / 上下残影 / 主文字
        self.name_shadow = self.canvas.create_text(NAME_CX + 4, NAME_CY + 5, text='',
                                                   font=self.name_font, fill=SHADOW)
        self.ghost_top = self.canvas.create_text(NAME_CX, NAME_CY - 30, text='',
                                                 font=self.name_font,
                                                 fill=mix(CARD_BG, ACCENT, 0.38))
        self.ghost_bottom = self.canvas.create_text(NAME_CX, NAME_CY + 30, text='',
                                                    font=self.name_font,
                                                    fill=mix(CARD_BG, ACCENT, 0.20))
        self.name_item = self.canvas.create_text(NAME_CX, NAME_CY, text='',
                                                 font=self.name_font, fill=ACCENT_SOFT)

    def build_buttons(self):
        self.btn_main = GlowButton(
            self.canvas, (352, 468, 648, 546), '点名', self.toggle,
            base='#2f86c9', hover='#1d6fa8', text_color='#ffffff',
            font=('华文中宋', 26, 'bold'), radius=24, halo=True)
        self.btn_bag = GlowButton(
            self.canvas, (24, 22, 168, 56), '不重复 · 开', self.toggle_bag,
            base='#e6f1fb', hover='#d3e5f7', text_color=ACCENT_TEXT,
            font=('微软雅黑', 10), radius=17)
        self.btn_names = GlowButton(
            self.canvas, (836, 22, 976, 56), '修改 / 查看名单', self.open_manager,
            base='#e6f1fb', hover='#d3e5f7', text_color='#4d6c8c',
            font=('微软雅黑', 10), radius=17)
        self.btn_code = GlowButton(
            self.canvas, (866, 64, 976, 92), '查看代码', self.show_code,
            base='#e6f1fb', hover='#d3e5f7', text_color='#4d6c8c',
            font=('微软雅黑', 10), radius=14)
        self.buttons = [self.btn_main, self.btn_bag, self.btn_names, self.btn_code]

    def build_footer(self):
        self.hint_item = self.canvas.create_text(W / 2.0, HINT_Y, text='',
                                                 font=('微软雅黑', 13), fill=MUTED)
        self.canvas.create_text(
            W / 2.0, 578,
            text='空格 / 回车 也能开始或停止    ·    由 WZA 设计制作    ·    v1.4.0',
            font=('微软雅黑', 9), fill='#4f6479')

    # ---------------- 提示文字 ----------------
    def set_hint(self, text, color=MUTED):
        self.hint_full = text
        self.hint_shown = 0
        self.canvas.itemconfig(self.hint_item, text='', fill=color)

    def animate_hint(self):
        if self.hint_shown < len(self.hint_full):
            self.hint_shown += 1
            self.canvas.itemconfig(self.hint_item,
                                   text=self.hint_full[:self.hint_shown])

    # ---------------- 逐帧动画 ----------------
    def tick(self):
        if not self.alive:
            return
        self.frame += 1
        try:
            for star in self.stars:
                star.step(self.frame)
            self.animate_title()
            self.animate_hint()
            self.animate_card()
            self.animate_name()
            for btn in self.buttons:
                btn.update(self.frame)
            for fx in list(self.effects):
                if not fx.step():
                    self.effects.remove(fx)
        except t.TclError:
            return
        self.root.after(FRAME_MS, self.tick)

    def animate_title(self):
        for item, x, i in self.title_items:
            y = 60 + math.sin(self.frame * 0.05 + i * 0.42) * 3
            color = mix(TEXT, ACCENT, 0.3 + 0.3 * math.sin(self.frame * 0.045 + i * 0.5))
            self.canvas.coords(item, x, y)
            self.canvas.itemconfig(item, fill=color)
        # 分隔线上的流光
        pos = self.frame * 5 % 760
        if pos > 380:
            pos = 760 - pos
        self.canvas.coords(self.sweep_item, 310 + pos, 100,
                           min(690, 310 + pos + 70), 100)

    def animate_card(self):
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.05)
        if self.state == 'result':
            base = mix(ACCENT, GOLD, 0.7)
        elif self.state in ('rolling', 'slowing'):
            base = mix(ACCENT, '#0d6e9e', 0.3 + 0.2 * pulse)
        else:
            base = mix(ACCENT, BG_MID, 0.35 + 0.15 * pulse)
        edge = mix(base, ACCENT, 0.2)
        if self.flash:
            edge = mix(edge, GOLD, 0.75 * self.flash)
        self.canvas.itemconfig(self.card_edge, outline=edge)
        bracket = mix(edge, CARD_BG, 0.35)
        for item in self.brackets:
            self.canvas.itemconfig(item, fill=bracket)
        for item, strength in self.card_halo:
            self.canvas.itemconfig(item,
                                   fill=mix(BG_MID, base, strength * (0.75 + 0.6 * pulse)))
        self.flash = max(0.0, self.flash - 0.06)

    def animate_name(self):
        if self.state in ('rolling', 'slowing'):
            offset = math.sin(self.frame * 0.55) * 5
            self.canvas.coords(self.name_item, NAME_CX, NAME_CY + offset)
            self.canvas.coords(self.name_shadow, NAME_CX + 4, NAME_CY + offset + 5)
            self.canvas.itemconfig(self.name_item, fill=self.name_color)
            self.canvas.coords(self.ghost_top, NAME_CX, NAME_CY + offset - 30)
            self.canvas.itemconfig(self.ghost_top, text=self.name_text,
                                   fill=mix(CARD_BG, self.name_color, 0.38))
            self.canvas.coords(self.ghost_bottom, NAME_CX, NAME_CY + offset + 30)
            self.canvas.itemconfig(self.ghost_bottom, text=self.name_text,
                                   fill=mix(CARD_BG, self.name_color, 0.22))
        else:
            self.canvas.coords(self.name_item, NAME_CX, NAME_CY)
            self.canvas.coords(self.name_shadow, NAME_CX + 4, NAME_CY + 5)
            if self.canvas.itemcget(self.ghost_top, 'text'):
                self.canvas.itemconfig(self.ghost_top, text='')
                self.canvas.itemconfig(self.ghost_bottom, text='')

    # ---------------- 抽选流程 ----------------
    def fit_size(self, text, base=64, minimum=26, max_width=660):
        """按姓名长度自动选取字号，保证完整显示在卡牌内"""
        size = base
        while size >= minimum:
            self.name_font.configure(size=size)
            if self.name_font.measure(text) <= max_width:
                return size
            size -= 2
        self.name_font.configure(size=minimum)
        return minimum

    def fit_for_current_names(self):
        self.name_font.configure(size=64)
        longest, longest_width = '', -1
        for name in self.names:
            width = self.name_font.measure(name)
            if width > longest_width:
                longest, longest_width = name, width
        return self.fit_size(longest)

    def show_name(self, text):
        self.name_text = text
        self.canvas.itemconfig(self.name_item, text=text)

    def toggle(self, event=None):
        if self.state == 'rolling':
            self.stop_roll()
        elif self.state == 'slowing':
            return
        else:
            self.start_roll()

    def start_roll(self):
        if self.state in ('rolling', 'slowing'):
            return
        self.load_names()                      # 同步名单管理窗口里的修改
        if not self.names:
            self.flash = 1.0
            self.set_hint('名单是空的，请先在“修改 / 查看名单”里添加姓名', color=WARM)
            return

        self.clear_effects()
        self.state = 'rolling'
        self.flash = 0.0
        self.name_size = self.fit_for_current_names()
        self.name_color = ACCENT_SOFT
        self.canvas.itemconfig(self.name_item, fill=ACCENT_SOFT)
        self.btn_main.set(text='停止', base='#c9483c', hover='#b13a2e', text_color='#ffffff')
        self.set_hint('正在抽选 · 再次点击按钮定格', color=ACCENT_TEXT)
        self.roll()

    def roll(self):
        if not self.alive or self.state != 'rolling':
            return
        n = len(self.names)
        if n == 0:
            self.to_idle()
            return
        if n == 1:
            self.name_cycle = 0
        else:
            self.name_cycle = (self.name_cycle + r.randint(1, n - 1)) % n
        self.show_name(self.names[self.name_cycle])
        self.name_color = r.choice((ACCENT_SOFT, '#1b86bd', '#1180b5', '#1a6f9c'))
        self.roll_job = self.root.after(45, self.roll)

    def stop_roll(self):
        """停止滚动：先决定结果，再做减速动画，最后揭晓"""
        if self.state != 'rolling':
            return
        self.cancel_job('roll_job')
        self.state = 'slowing'
        self.winner = self.bag.draw(self.names, self.bag_mode)
        if self.winner is None:
            self.to_idle()
            return
        self.slow_delay = 55
        self.slow_step = 0
        self._slow()

    def _slow(self):
        if not self.alive or self.state != 'slowing':
            return
        self.slow_step += 1
        if self.slow_delay >= 240:
            self.reveal(self.winner)
            return
        n = len(self.names)
        if n > 1:
            idx = r.randrange(n)
            if self.names[idx] == self.winner:
                idx = (idx + 1) % n
            self.name_cycle = idx
            self.show_name(self.names[idx])
        self.name_color = mix(ACCENT_SOFT, GOLD_TEXT, min(1.0, self.slow_step / 6.0))
        self.slow_delay = min(240, int(self.slow_delay * 1.28))
        self.slow_job = self.root.after(self.slow_delay, self._slow)

    def reveal(self, winner):
        self.state = 'result'
        self.name_text = winner
        self.name_color = GOLD_TEXT
        self.name_size = self.fit_size(winner, max_width=660)
        self.canvas.itemconfig(self.name_item, text=winner, fill=GOLD_TEXT)
        self.canvas.coords(self.name_item, NAME_CX, NAME_CY)
        self.canvas.itemconfig(self.ghost_top, text='')
        self.canvas.itemconfig(self.ghost_bottom, text='')
        self.flash = 1.0

        self.effects.append(NamePop(self))
        self.effects.append(PulseRing(self.canvas, NAME_CX, NAME_CY, delay=0))
        self.effects.append(PulseRing(self.canvas, NAME_CX, NAME_CY, delay=8))
        self.effects.append(Confetti(self.canvas, NAME_CX, NAME_CY))
        self.canvas.tag_raise(self.name_shadow)
        self.canvas.tag_raise(self.name_item)

        self.btn_main.set(text='点名', base='#2f86c9', hover='#1d6fa8', text_color='#ffffff')
        self.set_hint('恭喜 “%s” 被抽中！' % winner, color=GOLD_TEXT)

    def to_idle(self):
        self.state = 'idle'
        self.name_color = ACCENT_SOFT
        self.canvas.itemconfig(self.name_item, fill=ACCENT_SOFT)
        self.btn_main.set(text='点名', base='#2f86c9', hover='#1d6fa8', text_color='#ffffff')

    # ---------------- 其它按钮 ----------------
    def toggle_bag(self):
        self.bag_mode = not self.bag_mode
        self.bag.reset()
        if self.bag_mode:
            self.btn_bag.set(text='不重复 · 开', text_color=ACCENT_TEXT)
            self.set_hint('已开启“不重复”：一轮抽完才会重新洗牌', color=ACCENT_TEXT)
        else:
            self.btn_bag.set(text='不重复 · 关', text_color=MUTED)
            self.set_hint('已关闭“不重复”：每次都独立随机（仍不会连续抽到同一人）',
                          color=ACCENT_TEXT)

    def open_manager(self):
        name_manager.open_name_manager(json_path)

    def show_code(self):
        # 传递当前脚本的路径
        code_viewer.show_code_window(__file__)

    # ---------------- 收尾 ----------------
    def cancel_job(self, name):
        job = getattr(self, name, None)
        if job:
            try:
                self.root.after_cancel(job)
            except t.TclError:
                pass
            setattr(self, name, None)

    def clear_effects(self):
        for fx in self.effects:
            try:
                fx.dispose()
            except t.TclError:
                pass
        self.effects = []

    def close(self):
        self.alive = False
        self.cancel_job('roll_job')
        self.cancel_job('slow_job')
        try:
            self.root.destroy()
        except t.TclError:
            pass


def main():
    root = t.Tk()
    ZadmApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
