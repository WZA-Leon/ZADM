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

抽选逻辑：
    · 支持一轮抽多人（主界面左下角 + / − 调整），卡牌区域随人数自动变大变小
    · 每次结果都会写入 data/history.json，下次打开自动按历史均衡概率
    · 设置界面里可以调整滚动频率、均衡强度、特定人物概率（手动概率优先）
"""

import json
import math
import os
import random as r
import tkinter as t
import tkinter.font as tkfont

import code_viewer
import name_manager
import settings_window
import zadm_config as cfg
import zadm_theme as themes

# ---------------------------------------------------------------- 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, 'data', 'names.json')
ICON_PATH = os.path.join(BASE_DIR, 'data', 'zadm.ico')
DEFAULT_NAMES = ['张三', '李四', '王五', '赵六']

# ---------------------------------------------------------------- 尺寸
W, H = 1000, 600
FRAME_MS = 33                      # 主循环帧间隔（毫秒）
CARD_CY = 286                      # 卡牌中心
HINT_Y = 434                       # 提示文字

# ---------------------------------------------------------------- 主题配色
# 这些颜色由 apply_palette() 按当前主题动态写入，界面元素创建时读取
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
STAR_COLORS = ('#5f93c9', '#7fb0dd', '#6e8fb5', '#d99a4e', '#4fb3cf')
CONFETTI_COLORS = ('#1b86bd', '#e69a1d', '#ee4266', '#06b6a4', '#6c5ce7', '#c0431f')


def apply_palette(palette):
    """把主题配色写入模块级变量（切换主题后重建界面即可生效）"""
    global BG_TOP, BG_BOTTOM, BG_MID, CARD_BG, ACCENT, ACCENT_SOFT
    global ACCENT_TEXT, GOLD, GOLD_TEXT, WARM, FLASH, TEXT, MUTED, SHADOW
    global STAR_COLORS, CONFETTI_COLORS
    BG_TOP = palette['bg_top']
    BG_BOTTOM = palette['bg_bottom']
    BG_MID = palette['bg_mid']
    CARD_BG = palette['card_bg']
    ACCENT = palette['accent']
    ACCENT_SOFT = palette['accent_soft']
    ACCENT_TEXT = palette['accent_text']
    GOLD = palette['gold']
    GOLD_TEXT = palette['gold_text']
    WARM = palette['warm']
    FLASH = palette['flash']
    TEXT = palette['text']
    MUTED = palette['muted']
    SHADOW = palette['shadow']
    STAR_COLORS = tuple(palette['star_colors'])
    CONFETTI_COLORS = tuple(palette['confetti'])


apply_palette(themes.get_palette('default'))


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


# ---------------------------------------------------------------- 抽签袋（带权重）
class WeightedBag:
    """抽签袋：一轮之内不重复，跨轮也不会连续抽到同一个人

    bag_mode=True 时按“袋”抽：一轮里每个人只会出现一次；
    bag_mode=False 时按权重独立随机，但会避开上一轮的结果。
    """

    def __init__(self):
        self.pool = []
        self.last_batch = []

    def reset(self):
        self.pool = []
        self.last_batch = []

    def draw_many(self, names, probs, count, bag_mode=True):
        names = list(names)
        picked = []
        if not names or count <= 0:
            return picked
        total = min(count, len(names))
        if bag_mode:
            for _ in range(total):
                pool = [n for n in self.pool if n not in picked]
                if not pool:
                    pool = [n for n in names if n not in picked]
                    self.pool = list(pool)
                name = cfg.weighted_pick(pool, probs)
                if name is None:
                    break
                # 新一轮的第一个尽量避开上一轮抽中的人
                if len(pool) > 1 and name in self.last_batch:
                    others = [n for n in pool if n not in self.last_batch]
                    if others:
                        name = cfg.weighted_pick(others, probs)
                picked.append(name)
                if name in self.pool:
                    self.pool.remove(name)
        else:
            for _ in range(total):
                candidates = [n for n in names
                              if n not in picked and n not in self.last_batch]
                if not candidates:
                    candidates = [n for n in names if n not in picked]
                name = cfg.weighted_pick(candidates, probs)
                if name is None:
                    break
                picked.append(name)
        self.last_batch = list(picked)
        return picked


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
            color = r.choice(CONFETTI_COLORS)
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
    """结果姓名的弹出缩放动画（所有格子共用同一字号）"""

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
        for slot in self.app.name_items:
            self.app.canvas.itemconfig(
                slot['text'], fill=mix(FLASH, GOLD_TEXT, min(1.0, progress * 1.8)))
        if self.t >= self.life:
            self.dispose()
            return False
        return True

    def dispose(self):
        try:
            self.app.name_font.configure(size=self.app.name_size)
        except t.TclError:
            return
        for slot in self.app.name_items:
            self.app.canvas.itemconfig(slot['text'], fill=GOLD_TEXT)


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
        self.target_text = text
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
        if text is not None and text != self.target_text:
            self.target_text = text
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
        self.tick_job = None
        self.flash = 0.0
        self.name_size = 64
        self.name_color = ACCENT_SOFT
        self.hint_full = ''
        self.hint_shown = 0
        self.slow_delay = 55
        self.slow_step = 0
        self.winners = []
        self.names = []
        self._pending_count = None
        self._pending_theme = None
        self.theme_id = 'default'
        self.palette = themes.get_palette('default')
        self.decor = []
        self.card_items = []
        self.name_items = []
        self.brackets = []
        self.card_halo = []

        self.settings = cfg.load_settings()
        self.history = cfg.load_history()
        self.theme_id = str(self.settings.get('theme') or 'default')
        self.palette = themes.get_palette(self.theme_id)
        apply_palette(self.palette)
        self.bag = WeightedBag()
        self.load_names(initial=True)
        self.draw_count = self._safe_count(int(self.settings.get('draw_count', 1)))
        self.roll_interval = max(10, min(400, int(self.settings.get('roll_interval', 45))))
        self.bag_mode = bool(self.settings.get('bag_mode', True))

        root.title('ZADM 2.1.0 · 随机点名')
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

        self.build_ui()

        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<space>', self.toggle)
        root.bind('<Return>', self.toggle)
        root.lift()
        self.tick()

    # ---------------- 整体界面（含主题切换） ----------------
    def build_ui(self):
        """（重新）搭建整个界面；切换主题时也走这里"""
        self.canvas.delete('all')
        self.clear_effects()
        self.effects = []
        self.buttons = []
        self.card_items = []
        self.name_items = []
        self.brackets = []
        self.card_halo = []
        self.title_items = []
        self.decor = []
        self.hint_item = None
        self.balance_item = None
        self.count_item = None
        self.sweep_item = None
        self.canvas.configure(bg=BG_TOP)
        try:
            self.root.configure(bg=BG_TOP)
        except t.TclError:
            pass
        self.build_background()
        self.build_header()
        self.rebuild_card()
        self.build_buttons()
        self.build_footer()
        self.restore_display()

    def restore_display(self):
        """重建界面后恢复当前状态（结果 / 初始）"""
        if self.state == 'result' and self.winners:
            self.show_names(self.winners)
            for slot in self.name_items:
                self.canvas.itemconfig(slot['text'], fill=GOLD_TEXT)
            if len(self.winners) == 1:
                self.set_hint('恭喜 “%s” 被抽中！' % self.winners[0],
                              color=GOLD_TEXT)
            else:
                self.set_hint('本轮抽中 %d 人：%s'
                              % (len(self.winners), '、'.join(self.winners)),
                              color=GOLD_TEXT)
        else:
            self.state = 'idle'
            self.show_idle(True)
            self.set_hint('点击按钮开始抽选 · 也可以按空格键')

    def set_theme(self, theme_id):
        """切换主题并重建界面"""
        palette = themes.get_palette(theme_id)
        self.theme_id = palette.get('id', 'default')
        self.palette = palette
        apply_palette(palette)
        self.build_ui()
        self.update_balance_text()

    # ---------------- 数据 ----------------
    def _safe_count(self, value):
        limit = max(1, min(cfg.MAX_DRAW, len(self.names) or 1))
        try:
            return max(1, min(limit, int(value)))
        except (TypeError, ValueError):
            return 1

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
            self.clamp_draw_count()

    def clamp_draw_count(self):
        """名单变少时自动收敛每轮人数"""
        limit = max(1, min(cfg.MAX_DRAW, len(self.names) or 1))
        if getattr(self, 'draw_count', 1) > limit:
            self.draw_count = limit
            self.settings['draw_count'] = limit
            cfg.save_settings(self.settings)
            if hasattr(self, 'canvas'):
                self.rebuild_card()
                self.update_count_text()
                self.reset_display()

    def reload_history(self):
        self.history = cfg.load_history()
        self.update_balance_text()

    # ---------------- 界面搭建 ----------------
    def build_background(self):
        steps = 100
        for i in range(steps):
            y1 = H * i / float(steps)
            y2 = H * (i + 1) / float(steps) + 1
            self.canvas.create_rectangle(0, y1, W, y2, outline='',
                                         fill=mix(BG_TOP, BG_BOTTOM,
                                                  (i / (steps - 1.0)) ** 0.85))
        self.decor = themes.create_decor(self.palette.get('decor', 'stars'),
                                         self.canvas, W, H, self.palette)

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
        self.canvas.create_line(310, 100, 690, 100,
                                fill=self.palette.get('line', '#cfdeee'), width=2)
        self.sweep_item = self.canvas.create_line(310, 100, 380, 100,
                                                  fill=ACCENT_SOFT, width=2,
                                                  capstyle='round')

    # ---------------- 卡牌布局 ----------------
    def card_layout(self):
        """根据人数计算卡牌大小与每个姓名的位置（人多则区域变大、格子变小）"""
        k = max(1, self.draw_count)
        if k == 1:
            cols, width, height = 1, 760.0, 224.0
        elif k == 2:
            cols, width, height = 2, 760.0, 224.0
        elif k <= 4:
            cols, width, height = 2, 760.0, 262.0
        elif k <= 6:
            cols, width, height = 3, 820.0, 258.0
        else:
            cols, width, height = 4, 872.0, 264.0
        rows = int(math.ceil(k / float(cols)))
        x1 = 500.0 - width / 2.0
        x2 = 500.0 + width / 2.0
        y1 = CARD_CY - height / 2.0
        y2 = CARD_CY + height / 2.0
        cell_w = width / cols
        cell_h = height / rows
        slots = []
        last_row = k % cols
        # 最后一行不满时整体居中，避免看起来偏左
        shift = (cols - last_row) * cell_w / 2.0 if last_row else 0.0
        for i in range(k):
            row, col = divmod(i, cols)
            cx = x1 + cell_w * (col + 0.5)
            if shift and row == rows - 1:
                cx += shift
            slots.append((cx, y1 + cell_h * (row + 0.5)))
        return (x1, y1, x2, y2), slots, cell_w, cell_h

    def slot_font_size(self, cell_w, cell_h):
        base = int(min(64, cell_h * 0.56, cell_w * 0.32))
        base = max(14, base)
        longest = ''
        for name in self.names:
            if len(name) > len(longest):
                longest = name
        max_width = max(40, cell_w - 40)
        return self.fit_size(longest or '点击开始', base=base, minimum=13,
                             max_width=max_width)

    def rebuild_card(self):
        """重建整张卡牌（人数变化时调用）"""
        self.clear_effects()
        for item in self.card_items:
            try:
                self.canvas.delete(item)
            except t.TclError:
                pass
        self.card_items = []

        box, slots, cell_w, cell_h = self.card_layout()
        self.card_box = box
        self.slots = slots
        x1, y1, x2, y2 = box
        self.card_cx = (x1 + x2) / 2.0
        self.card_cy = (y1 + y2) / 2.0

        self.card_halo = []
        for grow, strength in ((26, 0.07), (16, 0.10), (8, 0.13)):
            item = round_rect(self.canvas, x1 - grow, y1 - grow, x2 + grow, y2 + grow,
                              30, fill=mix(BG_MID, ACCENT, strength), outline='')
            self.card_halo.append((item, strength))
            self.card_items.append(item)
        self.card_body = round_rect(self.canvas, x1, y1, x2, y2, 24,
                                    fill=CARD_BG, outline='')
        self.card_edge = round_rect(self.canvas, x1, y1, x2, y2, 24,
                                    fill='', outline=ACCENT, width=2)
        self.card_items.extend([self.card_body, self.card_edge])

        # 四角光标
        length, inset = 22, 16
        self.brackets = []
        corners = ((x1 + inset, y1 + inset, 1, 1),
                   (x2 - inset, y1 + inset, -1, 1),
                   (x1 + inset, y2 - inset, 1, -1),
                   (x2 - inset, y2 - inset, -1, -1))
        for cx, cy, sx, sy in corners:
            for item in (self.canvas.create_line(
                    cx, cy, cx + length * sx, cy, fill=ACCENT, width=2,
                    capstyle='round'),
                    self.canvas.create_line(
                    cx, cy, cx, cy + length * sy, fill=ACCENT, width=2,
                    capstyle='round')):
                self.brackets.append(item)
                self.card_items.append(item)

        # 姓名格子：阴影 / 上下残影 / 主文字
        self.name_size = self.slot_font_size(cell_w, cell_h)
        self.name_font.configure(size=self.name_size)
        ghost_dy = max(18, int(self.name_size * 0.48))
        self.name_items = []
        for cx, cy in slots:
            shadow = self.canvas.create_text(cx + 3, cy + 4, text='',
                                             font=self.name_font, fill=SHADOW)
            ghost_top = self.canvas.create_text(cx, cy - ghost_dy, text='',
                                                font=self.name_font,
                                                fill=mix(CARD_BG, ACCENT, 0.38))
            ghost_bottom = self.canvas.create_text(cx, cy + ghost_dy, text='',
                                                   font=self.name_font,
                                                   fill=mix(CARD_BG, ACCENT, 0.20))
            text = self.canvas.create_text(cx, cy, text='',
                                           font=self.name_font, fill=ACCENT_SOFT)
            self.name_items.append({'text': text, 'shadow': shadow,
                                    'top': ghost_top, 'bottom': ghost_bottom,
                                    'cx': cx, 'cy': cy, 'dy': ghost_dy})
            self.card_items.extend([shadow, ghost_top, ghost_bottom, text])

        self.idle_item = self.canvas.create_text(self.card_cx, self.card_cy,
                                                 text='', font=self.name_font,
                                                 fill=ACCENT_SOFT)
        self.card_items.append(self.idle_item)

        if self.state != 'result':
            self.show_idle(True)
        else:
            self.show_idle(False)
        self.raise_chrome()

    def raise_chrome(self):
        """重建卡牌后把按钮 / 提示 / 标题重新提到最上层，避免被卡牌光晕遮住"""
        for attr in ('hint_item', 'balance_item', 'count_item', 'sweep_item'):
            item = getattr(self, attr, None)
            if item:
                try:
                    self.canvas.tag_raise(item)
                except t.TclError:
                    pass
        for item, _x, _i in getattr(self, 'title_items', []):
            self.canvas.tag_raise(item)
        for btn in getattr(self, 'buttons', []):
            try:
                if getattr(btn, 'halo', None) is not None:
                    self.canvas.tag_raise(btn.halo)
                self.canvas.tag_raise(btn.shape)
                self.canvas.tag_raise(btn.label)
            except t.TclError:
                pass

    def show_idle(self, show, text='点击开始'):
        try:
            if show:
                self.canvas.itemconfig(self.idle_item, text=text,
                                       state='normal')
                for slot in self.name_items:
                    self.canvas.itemconfig(slot['text'], text='')
            else:
                self.canvas.itemconfig(self.idle_item, text='', state='hidden')
        except t.TclError:
            pass

    def build_buttons(self):
        p = self.palette
        soft_base, soft_hover = p['btn_soft_base'], p['btn_soft_hover']
        self.btn_main = GlowButton(
            self.canvas, (352, 468, 648, 546), '点名', self.toggle,
            base=p['btn_main_base'], hover=p['btn_main_hover'],
            text_color=p['btn_main_text'],
            font=('华文中宋', 26, 'bold'), radius=24, halo=True)
        self.btn_bag = GlowButton(
            self.canvas, (24, 22, 168, 56), '不重复 · 开', self.toggle_bag,
            base=soft_base, hover=soft_hover, text_color=ACCENT_TEXT,
            font=('微软雅黑', 10), radius=17)
        self.btn_settings = GlowButton(
            self.canvas, (700, 22, 790, 56), '设置', self.open_settings,
            base=soft_base, hover=soft_hover, text_color=ACCENT_TEXT,
            font=('微软雅黑', 10), radius=17)
        self.btn_names = GlowButton(
            self.canvas, (800, 22, 976, 56), '修改 / 查看名单', self.open_manager,
            base=soft_base, hover=soft_hover, text_color=p['btn_soft_text'],
            font=('微软雅黑', 10), radius=17)
        self.btn_code = GlowButton(
            self.canvas, (866, 64, 976, 92), '查看代码', self.show_code,
            base=soft_base, hover=soft_hover, text_color=p['btn_soft_text'],
            font=('微软雅黑', 10), radius=14)

        # 每轮人数：− [n 人] +
        self.canvas.create_text(26, 92, text='每轮抽取', anchor='w',
                                font=('微软雅黑', 9), fill=MUTED)
        self.btn_minus = GlowButton(
            self.canvas, (112, 76, 146, 106), '−', lambda: self.change_count(-1),
            base=soft_base, hover=soft_hover, text_color=ACCENT_TEXT,
            font=('微软雅黑', 13, 'bold'), radius=15)
        self.count_item = self.canvas.create_text(
            172, 91, text='1 人', font=('微软雅黑', 10, 'bold'), fill=TEXT)
        self.btn_plus = GlowButton(
            self.canvas, (198, 76, 232, 106), '+', lambda: self.change_count(1),
            base=soft_base, hover=soft_hover, text_color=ACCENT_TEXT,
            font=('微软雅黑', 13, 'bold'), radius=15)
        self.update_count_text()

        # 均衡状态提示
        self.balance_item = self.canvas.create_text(
            26, 124, text='', anchor='w', font=('微软雅黑', 9), fill=MUTED)
        self.update_balance_text()
        self.update_bag_button()

        self.buttons = [self.btn_main, self.btn_bag, self.btn_settings,
                        self.btn_names, self.btn_code, self.btn_minus,
                        self.btn_plus]

    def update_count_text(self):
        try:
            self.canvas.itemconfig(self.count_item, text='%d 人' % self.draw_count)
        except t.TclError:
            pass

    def update_bag_button(self):
        if self.bag_mode:
            self.btn_bag.set(text='不重复 · 开', text_color=ACCENT_TEXT)
        else:
            self.btn_bag.set(text='不重复 · 关', text_color=MUTED)

    def update_balance_text(self):
        try:
            if self.settings.get('auto_balance', True):
                text = '均衡中 · 已记录 %d 次抽选' % len(self.history)
            else:
                text = '平均概率 · 已记录 %d 次抽选' % len(self.history)
            self.canvas.itemconfig(self.balance_item, text=text)
        except t.TclError:
            pass

    def build_footer(self):
        self.hint_item = self.canvas.create_text(W / 2.0, HINT_Y, text='',
                                                 font=('微软雅黑', 13), fill=MUTED)
        self.canvas.create_text(
            W / 2.0, 578,
            text='空格 / 回车 也能开始或停止    ·    设置里可调人数 / 概率 / 主题    ·    v2.1.0',
            font=('微软雅黑', 9), fill=self.palette.get('footer', '#4f6479'))

    # ---------------- 提示文字 ----------------
    def set_hint(self, text, color=None):
        if color is None:
            color = MUTED
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
            for obj in self.decor:
                obj.step(self.frame)
            self.animate_title()
            self.animate_hint()
            self.animate_card()
            self.animate_name()
            for btn in self.buttons:
                btn.update(self.frame)
            for fx in list(self.effects):
                try:
                    still_alive = fx.step()
                except t.TclError:
                    still_alive = False
                if not still_alive:
                    try:
                        self.effects.remove(fx)
                    except ValueError:
                        pass
        except t.TclError:
            return
        try:
            self.tick_job = self.root.after(FRAME_MS, self.tick)
        except t.TclError:
            self.tick_job = None

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
            base = mix(ACCENT, self.palette.get('card_rolling', '#0d6e9e'), 0.3 + 0.2 * pulse)
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
        rolling = self.state in ('rolling', 'slowing')
        show_ghost = len(self.name_items) == 1      # 多格子时残影会互相干扰，只保留单人格子
        for index, slot in enumerate(self.name_items):
            try:
                if rolling:
                    offset = math.sin(self.frame * 0.55 + index * 0.9) * 5
                    cx, cy = slot['cx'], slot['cy'] + offset
                    self.canvas.coords(slot['text'], cx, cy)
                    self.canvas.coords(slot['shadow'], cx + 3, cy + 4)
                    self.canvas.itemconfig(slot['text'], fill=self.name_color)
                    text = self.canvas.itemcget(slot['text'], 'text')
                    for key, alpha in (('top', 0.38), ('bottom', 0.22)):
                        self.canvas.coords(slot[key], cx, cy - slot['dy']
                                           if key == 'top' else cy + slot['dy'])
                        self.canvas.itemconfig(
                            slot[key], text=text if show_ghost else '',
                            fill=mix(CARD_BG, self.name_color, alpha))
                else:
                    self.canvas.coords(slot['text'], slot['cx'], slot['cy'])
                    self.canvas.coords(slot['shadow'], slot['cx'] + 3, slot['cy'] + 4)
                    if self.canvas.itemcget(slot['top'], 'text'):
                        self.canvas.itemconfig(slot['top'], text='')
                        self.canvas.itemconfig(slot['bottom'], text='')
            except t.TclError:
                return

    # ---------------- 抽选流程 ----------------
    def fit_size(self, text, base=64, minimum=26, max_width=660):
        """按姓名长度自动选取字号，保证完整显示在格子内"""
        size = base
        while size >= minimum:
            self.name_font.configure(size=size)
            if self.name_font.measure(text) <= max_width:
                return size
            size -= 2
        self.name_font.configure(size=minimum)
        return minimum

    def show_names(self, texts):
        for slot, text in zip(self.name_items, texts):
            try:
                self.canvas.itemconfig(slot['text'], text=text)
            except t.TclError:
                return

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
        self.flush_pending_count()             # 滚动中改过人数的话，这里再生效
        self.load_names()                      # 同步名单管理窗口里的修改
        if not self.names:
            self.flash = 1.0
            self.set_hint('名单是空的，请先在“修改 / 查看名单”里添加姓名', color=WARM)
            return

        self.clear_effects()
        self.state = 'rolling'
        self.flash = 0.0
        self.name_color = ACCENT_SOFT
        self.show_idle(False)
        self.btn_main.set(text='停止', base=self.palette['btn_stop_base'],
                          hover=self.palette['btn_stop_hover'],
                          text_color=self.palette['btn_stop_text'])
        self.set_hint('正在抽选 · 再次点击按钮定格', color=ACCENT_TEXT)
        self.roll()

    def roll(self):
        if not self.alive or self.state != 'rolling':
            return
        n = len(self.names)
        if n == 0:
            self.to_idle()
            return
        self.show_names([self.names[r.randrange(n)] for _ in self.name_items])
        self.name_color = r.choice((ACCENT_SOFT, '#1b86bd', '#1180b5', '#1a6f9c'))
        self.roll_job = self.root.after(self.roll_interval, self.roll)

    def stop_roll(self):
        """停止滚动：先按概率决定结果，再做减速动画，最后揭晓"""
        if self.state != 'rolling':
            return
        self.cancel_job('roll_job')
        self.state = 'slowing'
        probs = cfg.compute_probabilities(self.names, self.settings, self.history)
        count = min(self.draw_count, len(self.names))
        self.winners = self.bag.draw_many(self.names, probs, count, self.bag_mode)
        if not self.winners:
            self.to_idle()
            return
        # 记录本次结果，用于下次启动时的自动均衡
        cfg.append_history(self.winners, 'bag' if self.bag_mode else 'random')
        self.history = cfg.load_history()
        self.update_balance_text()
        self.slow_delay = 55
        self.slow_step = 0
        self._slow()

    def _slow(self):
        if not self.alive or self.state != 'slowing':
            return
        self.slow_step += 1
        if self.slow_delay >= 240:
            self.reveal(self.winners)
            return
        n = len(self.names)
        if n > 1:
            texts = [self.names[r.randrange(n)] for _ in self.name_items]
            self.show_names(texts)
        self.name_color = mix(ACCENT_SOFT, GOLD_TEXT, min(1.0, self.slow_step / 6.0))
        self.slow_delay = min(240, int(self.slow_delay * 1.28))
        self.slow_job = self.root.after(self.slow_delay, self._slow)

    def reveal(self, winners):
        self.state = 'result'
        self.winners = list(winners)
        self.name_color = GOLD_TEXT
        self.show_names(winners)
        for slot in self.name_items:
            self.canvas.itemconfig(slot['text'], fill=GOLD_TEXT)
            self.canvas.coords(slot['text'], slot['cx'], slot['cy'])
            self.canvas.coords(slot['shadow'], slot['cx'] + 3, slot['cy'] + 4)
            self.canvas.itemconfig(slot['top'], text='')
            self.canvas.itemconfig(slot['bottom'], text='')
        self.flash = 1.0

        self.effects.append(NamePop(self))
        self.effects.append(PulseRing(self.canvas, self.card_cx, self.card_cy, delay=0))
        self.effects.append(PulseRing(self.canvas, self.card_cx, self.card_cy, delay=8))
        self.effects.append(Confetti(self.canvas, self.card_cx, self.card_cy))
        for slot in self.name_items:
            self.canvas.tag_raise(slot['shadow'])
            self.canvas.tag_raise(slot['text'])

        self.btn_main.set(text='点名', base=self.palette['btn_main_base'],
                          hover=self.palette['btn_main_hover'],
                          text_color=self.palette['btn_main_text'])
        if len(winners) == 1:
            self.set_hint('恭喜 “%s” 被抽中！' % winners[0], color=GOLD_TEXT)
        else:
            self.set_hint('本轮抽中 %d 人：%s'
                          % (len(winners), '、'.join(winners)), color=GOLD_TEXT)
        # 光环 / 彩纸之上仍保证提示文字可读
        try:
            self.canvas.tag_raise(self.hint_item)
        except t.TclError:
            pass

    def to_idle(self):
        self.state = 'idle'
        self.name_color = ACCENT_SOFT
        self.show_idle(True)
        self.btn_main.set(text='点名', base=self.palette['btn_main_base'],
                          hover=self.palette['btn_main_hover'],
                          text_color=self.palette['btn_main_text'])

    def reset_display(self):
        """人数变化后回到初始状态"""
        self.state = 'idle'
        self.winners = []
        self.name_color = ACCENT_SOFT
        self.show_idle(True)
        self.btn_main.set(text='点名', base=self.palette['btn_main_base'],
                          hover=self.palette['btn_main_hover'],
                          text_color=self.palette['btn_main_text'])
        self.set_hint('点击按钮开始抽选 · 也可以按空格键')

    # ---------------- 其它按钮 ----------------
    def change_count(self, delta):
        if self.state in ('rolling', 'slowing'):
            return
        self.flush_pending_count()
        limit = max(1, min(cfg.MAX_DRAW, len(self.names) or 1))
        new_count = max(1, min(limit, self.draw_count + delta))
        if new_count == self.draw_count:
            if delta > 0:
                self.set_hint('最多每轮抽 %d 人（受名单人数与上限限制）' % limit,
                              color=MUTED)
            return
        self.draw_count = new_count
        self.settings['draw_count'] = new_count
        cfg.save_settings(self.settings)
        self.bag.reset()
        self.update_count_text()
        self.rebuild_card()
        self.reset_display()

    def toggle_bag(self):
        self.bag_mode = not self.bag_mode
        self.bag.reset()
        self.settings['bag_mode'] = self.bag_mode
        cfg.save_settings(self.settings)
        self.update_bag_button()
        if self.bag_mode:
            self.set_hint('已开启“不重复”：一轮抽完才会重新洗牌', color=ACCENT_TEXT)
        else:
            self.set_hint('已关闭“不重复”：每次都独立随机（仍不会连续抽到同一人）',
                          color=ACCENT_TEXT)

    def open_manager(self):
        name_manager.open_name_manager(json_path)

    def open_settings(self):
        settings_window.open_settings(self)

    def show_code(self):
        self.code_window = code_viewer.show_code_window(__file__)

    def flush_pending_count(self):
        """把“滚动中设置窗口改过的人数 / 主题”在空闲时补上"""
        if self._pending_theme is not None:
            theme_id = self._pending_theme
            self._pending_theme = None
            self.set_theme(theme_id)
        if self._pending_count is None:
            return
        new_count = self._pending_count
        self._pending_count = None
        new_count = self._safe_count(new_count)
        if new_count != self.draw_count:
            self.draw_count = new_count
            self.bag.reset()
            self.rebuild_card()
            self.update_count_text()
            self.reset_display()

    def apply_settings(self):
        """设置窗口保存后调用：同步模式 / 人数 / 滚动频率 / 概率 / 主题"""
        self.settings = cfg.load_settings()
        self.history = cfg.load_history()
        self.bag_mode = bool(self.settings.get('bag_mode', True))
        try:
            self.roll_interval = max(10, min(400, int(self.settings.get('roll_interval', 45))))
        except (TypeError, ValueError):
            self.roll_interval = 45
        new_count = self._safe_count(int(self.settings.get('draw_count', 1)))
        self.update_bag_button()
        self.update_balance_text()

        theme_id = str(self.settings.get('theme') or 'default')
        if theme_id != self.theme_id:
            if self.state in ('rolling', 'slowing'):
                # 抽选动画中先记下来，下一次开始时再切换
                self._pending_theme = theme_id
            else:
                self._pending_theme = None
                self.set_theme(theme_id)

        if new_count != self.draw_count:
            if self.state in ('rolling', 'slowing'):
                # 正在抽选时不要打断动画，等下一次开始时再应用
                self._pending_count = new_count
            else:
                self._pending_count = None
                self.draw_count = new_count
                self.bag.reset()
                self.rebuild_card()
                self.update_count_text()
                self.reset_display()

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
        self.cancel_job('tick_job')
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
