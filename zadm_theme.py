# -*- coding: utf-8 -*-
"""ZADM 主题：配色方案 + 背景装饰动画

每个主题包含：
    · palette   颜色字典（主界面所有颜色都从这里取）
    · decor     背景动画类型：stars / circuit / petals / minimal

背景装饰对象统一暴露 step(frame) 接口，由主循环逐帧调用；
它们只依赖传入的 canvas / 尺寸 / palette，不依赖主程序。
"""

import math
import random as r

# ---------------------------------------------------------------- 默认主题（原本的浅蓝风格）
DEFAULT = {
    'id': 'default',
    'label': '当前（默认）',
    'desc': '浅蓝渐变 + 漂浮星点',
    'decor': 'stars',
    'bg_top': '#f8fbff',
    'bg_bottom': '#dbe9f7',
    'bg_mid': '#eaf3fb',
    'card_bg': '#ffffff',
    'accent': '#1b86bd',
    'accent_soft': '#2f86c9',
    'accent_text': '#15678f',
    'gold': '#e69a1d',
    'gold_text': '#96650a',
    'warm': '#c0431f',
    'flash': '#f08a1e',
    'text': '#1d2c3b',
    'muted': '#5a6f88',
    'shadow': '#cdddec',
    'line': '#cfdeee',
    'footer': '#4f6479',
    'card_rolling': '#0d6e9e',
    'star_colors': ('#5f93c9', '#7fb0dd', '#6e8fb5', '#d99a4e', '#4fb3cf'),
    'confetti': ('#1b86bd', '#e69a1d', '#ee4266', '#06b6a4', '#6c5ce7', '#c0431f'),
    'btn_main_base': '#2f86c9',
    'btn_main_hover': '#1d6fa8',
    'btn_main_text': '#ffffff',
    'btn_stop_base': '#c9483c',
    'btn_stop_hover': '#b13a2e',
    'btn_stop_text': '#ffffff',
    'btn_soft_base': '#e6f1fb',
    'btn_soft_hover': '#d3e5f7',
    'btn_soft_text': '#4d6c8c',
    # 仅部分主题使用
    'circuit_dim': '#cfdeee',
    'circuit_node': '#9fc4dd',
    'circuit_pulse': '#1b86bd',
    'petal_colors': ('#f7b7ce', '#f49ac1', '#ffd1e0'),
    'minimal_colors': ('#e63946', '#f4b400', '#1d4ed8'),
}

# ---------------------------------------------------------------- 科技电路
CIRCUIT = {
    'id': 'circuit',
    'label': '科技电路',
    'desc': '深蓝电路纹理 + 流光脉冲',
    'decor': 'circuit',
    'bg_top': '#061321',
    'bg_bottom': '#0c2436',
    'bg_mid': '#0d2537',
    'card_bg': '#0a1c2b',
    'accent': '#35e0ff',
    'accent_soft': '#4fd8ff',
    'accent_text': '#8fe9ff',
    'gold': '#ffd166',
    'gold_text': '#ffe3a3',
    'warm': '#ff7b72',
    'flash': '#5ffbf1',
    'text': '#e8f6ff',
    'muted': '#8aa9c0',
    'shadow': '#04101a',
    'line': '#1d3f57',
    'footer': '#7ba0b8',
    'card_rolling': '#1f7f9e',
    'star_colors': ('#35e0ff', '#4fd8ff', '#2fb8d6', '#7cffcb', '#9ad9ff'),
    'confetti': ('#35e0ff', '#ffd166', '#ff7b72', '#7cffcb', '#8a7bff', '#ffffff'),
    'btn_main_base': '#22c3e6',
    'btn_main_hover': '#17a8c7',
    'btn_main_text': '#041824',
    'btn_stop_base': '#d1495b',
    'btn_stop_hover': '#b23a4a',
    'btn_stop_text': '#ffffff',
    'btn_soft_base': '#12293a',
    'btn_soft_hover': '#1a3a4f',
    'btn_soft_text': '#9fd8ec',
    'circuit_dim': '#12384f',
    'circuit_node': '#1e5b78',
    'circuit_pulse': '#5ff3ff',
    'petal_colors': ('#f7b7ce', '#f49ac1', '#ffd1e0'),
    'minimal_colors': ('#e63946', '#f4b400', '#1d4ed8'),
}

# ---------------------------------------------------------------- 梦幻樱花
SAKURA = {
    'id': 'sakura',
    'label': '梦幻樱花',
    'desc': '粉色渐变 + 飘落花瓣',
    'decor': 'petals',
    'bg_top': '#fff8fb',
    'bg_bottom': '#ffdfeb',
    'bg_mid': '#fff0f5',
    'card_bg': '#ffffff',
    'accent': '#e07a9f',
    'accent_soft': '#ec8fb2',
    'accent_text': '#a03a5e',
    'gold': '#e58aa8',
    'gold_text': '#b83f6b',
    'warm': '#c2477a',
    'flash': '#ff9ec4',
    'text': '#3f2833',
    'muted': '#8b6d7a',
    'shadow': '#f3d3e0',
    'line': '#f2cfe0',
    'footer': '#9a6f80',
    'card_rolling': '#d98aae',
    'star_colors': ('#f7b7ce', '#f49ac1', '#ffd1e0', '#e9a8c6', '#fff0f6'),
    'confetti': ('#f7b7ce', '#f49ac1', '#ffd166', '#ff8fab', '#ffffff', '#e9a8c6'),
    'btn_main_base': '#e07a9f',
    'btn_main_hover': '#c9648a',
    'btn_main_text': '#ffffff',
    'btn_stop_base': '#c2477a',
    'btn_stop_hover': '#a83667',
    'btn_stop_text': '#ffffff',
    'btn_soft_base': '#ffeef5',
    'btn_soft_hover': '#ffdfeb',
    'btn_soft_text': '#8a3a5c',
    'circuit_dim': '#f2cfe0',
    'circuit_node': '#e9a8c6',
    'circuit_pulse': '#e07a9f',
    'petal_colors': ('#f7b7ce', '#f49ac1', '#ffd1e0', '#ef9fbf', '#ffe7f0'),
    'minimal_colors': ('#e63946', '#f4b400', '#1d4ed8'),
}

# ---------------------------------------------------------------- 极简三色
MINIMAL = {
    'id': 'minimal',
    'label': '极简三色',
    'desc': '白底 + 红黄蓝点缀',
    'decor': 'minimal',
    'bg_top': '#ffffff',
    'bg_bottom': '#f7f8fa',
    'bg_mid': '#f4f6f8',
    'card_bg': '#ffffff',
    'accent': '#e63946',
    'accent_soft': '#1d4ed8',
    'accent_text': '#1d4ed8',
    'gold': '#f4b400',
    'gold_text': '#d62828',
    'warm': '#d62828',
    'flash': '#f4b400',
    'text': '#111827',
    'muted': '#6b7280',
    'shadow': '#e5e7eb',
    'line': '#e5e7eb',
    'footer': '#6b7280',
    'card_rolling': '#1d4ed8',
    'star_colors': ('#e63946', '#f4b400', '#1d4ed8', '#d1d5db'),
    'confetti': ('#e63946', '#f4b400', '#1d4ed8', '#111827', '#ffffff'),
    'btn_main_base': '#1d4ed8',
    'btn_main_hover': '#1740b0',
    'btn_main_text': '#ffffff',
    'btn_stop_base': '#e63946',
    'btn_stop_hover': '#c62f3b',
    'btn_stop_text': '#ffffff',
    'btn_soft_base': '#f3f4f6',
    'btn_soft_hover': '#e5e7eb',
    'btn_soft_text': '#374151',
    'circuit_dim': '#e5e7eb',
    'circuit_node': '#d1d5db',
    'circuit_pulse': '#1d4ed8',
    'petal_colors': ('#f7b7ce', '#f49ac1', '#ffd1e0'),
    'minimal_colors': ('#e63946', '#f4b400', '#1d4ed8'),
}

THEMES = [DEFAULT, CIRCUIT, SAKURA, MINIMAL]

_BY_ID = {t['id']: t for t in THEMES}


def theme_ids():
    return [t['id'] for t in THEMES]


def theme_list():
    return list(THEMES)


def get_palette(theme_id):
    """取主题配色；未知 id 回落到默认主题"""
    theme = _BY_ID.get(theme_id) or DEFAULT
    palette = dict(theme)
    palette['star_colors'] = tuple(theme['star_colors'])
    palette['confetti'] = tuple(theme['confetti'])
    palette['petal_colors'] = tuple(theme['petal_colors'])
    palette['minimal_colors'] = tuple(theme['minimal_colors'])
    return palette


def _mix(c1, c2, k):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    k = max(0.0, min(1.0, k))
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- 背景装饰
class Star:
    """缓慢上浮、明暗闪烁的小光点（默认主题）"""

    def __init__(self, canvas, width, height, palette):
        self.c = canvas
        self.w, self.h = width, height
        self.x = r.uniform(0, width)
        self.y = r.uniform(0, height)
        self.r = r.uniform(0.7, 2.0)
        self.vy = -r.uniform(0.08, 0.35)
        self.phase = r.uniform(0, 6.28)
        self.speed = r.uniform(0.02, 0.06)
        self.base = r.choice(palette['star_colors'])
        self.bg = palette['bg_mid']
        self.color = self.base
        self.item = canvas.create_oval(self.x - self.r, self.y - self.r,
                                       self.x + self.r, self.y + self.r,
                                       outline='', fill=self.base)

    def step(self, frame):
        self.y += self.vy
        self.x += math.sin(frame * 0.01 + self.phase) * 0.08
        if self.y < -4:
            self.y = self.h + 4
            self.x = r.uniform(0, self.w)
        if self.x < -4:
            self.x = self.w + 4
        elif self.x > self.w + 4:
            self.x = -4
        alpha = 0.18 + 0.55 * (0.5 + 0.5 * math.sin(frame * self.speed + self.phase))
        color = _mix(self.bg, self.base, alpha)
        if color != self.color:
            self.color = color
            self.c.itemconfig(self.item, fill=color)
        self.c.coords(self.item, self.x - self.r, self.y - self.r,
                      self.x + self.r, self.y + self.r)


class CircuitTrace:
    """电路走线 + 沿线流动的脉冲光点（科技主题）"""

    def __init__(self, canvas, width, height, palette):
        self.c = canvas
        self.w, self.h = width, height
        self.dim = palette['circuit_dim']
        self.glow = palette['circuit_pulse']

        x = r.uniform(20, width - 20)
        y = r.uniform(20, height - 20)
        points = [(x, y)]
        horizontal = r.random() < 0.5
        for _ in range(r.randint(3, 6)):
            step = r.uniform(45, 170) * (1 if r.random() < 0.5 else -1)
            if horizontal:
                x = max(16, min(width - 16, x + step))
            else:
                y = max(16, min(height - 16, y + step))
            points.append((x, y))
            horizontal = not horizontal
        self.points = points

        flat = [v for p in points for v in p]
        self.line = canvas.create_line(*flat, fill=self.dim, width=1,
                                       joinstyle='miter', capstyle='butt')
        self.nodes = []
        for px, py in points:
            self.nodes.append(canvas.create_oval(px - 1.6, py - 1.6,
                                                 px + 1.6, py + 1.6,
                                                 outline='', fill=palette['circuit_node']))
        self.segments = []
        total = 0.0
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            length = math.hypot(x2 - x1, y2 - y1)
            if length <= 0:
                continue
            self.segments.append((total, length, x1, y1, x2, y2))
            total += length
        self.total = total or 1.0
        self.pos = r.uniform(0, self.total)
        self.speed = r.uniform(1.0, 3.2)
        self.pulse = canvas.create_oval(0, 0, 0, 0, outline='', fill=self.glow)
        self._place()

    def _place(self):
        for start, length, x1, y1, x2, y2 in self.segments:
            if self.pos <= start + length:
                k = (self.pos - start) / length
                x = x1 + (x2 - x1) * k
                y = y1 + (y2 - y1) * k
                self.c.coords(self.pulse, x - 2.4, y - 2.4, x + 2.4, y + 2.4)
                return
        self.c.coords(self.pulse, -10, -10, -10, -10)

    def step(self, frame):
        self.pos = (self.pos + self.speed) % self.total
        self._place()
        size = 2.2 + 0.6 * math.sin(frame * 0.2 + self.pos)
        x1, y1, x2, y2 = self.c.coords(self.pulse)
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        self.c.coords(self.pulse, cx - size, cy - size, cx + size, cy + size)


class Petal:
    """随风飘落的花瓣（樱花主题）"""

    def __init__(self, canvas, width, height, palette):
        self.c = canvas
        self.w, self.h = width, height
        self.bg = palette['bg_mid']
        self.color = r.choice(palette['petal_colors'])
        self.fill = _mix(self.bg, self.color, 0.85)
        self.size = r.uniform(5, 11)
        self.x = r.uniform(0, width)
        self.y = r.uniform(-height, height)
        self.vy = r.uniform(0.5, 1.5)
        self.vx = r.uniform(-0.35, 0.55)
        self.rot = r.uniform(0, 6.28)
        self.spin = r.uniform(-0.03, 0.03)
        self.phase = r.uniform(0, 6.28)
        self.item = canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0,
                                          smooth=True, outline='', fill=self.fill)
        self._draw()

    def _draw(self):
        size = self.size
        cos_r, sin_r = math.cos(self.rot), math.sin(self.rot)
        # 柔和的四角花瓣形状
        local = ((0, -size), (size * 0.62, 0), (0, size * 0.78), (-size * 0.62, 0))
        points = []
        for lx, ly in local:
            points.append(self.x + lx * cos_r - ly * sin_r)
            points.append(self.y + lx * sin_r + ly * cos_r)
        self.c.coords(self.item, *points)

    def step(self, frame):
        self.y += self.vy
        self.x += self.vx + math.sin(frame * 0.03 + self.phase) * 0.5
        self.rot += self.spin
        if self.y > self.h + 20:
            self.y = -20
            self.x = r.uniform(0, self.w)
        if self.x < -20:
            self.x = self.w + 20
        elif self.x > self.w + 20:
            self.x = -20
        self._draw()


class MinimalAccent:
    """极简主题的三大色块（红 / 黄 / 蓝）"""

    POSITIONS = ((0.70, 0.10, 210), (0.08, 0.80, 175), (0.90, 0.88, 140))

    def __init__(self, canvas, width, height, palette, index):
        self.c = canvas
        colors = palette['minimal_colors']
        self.color = colors[index % len(colors)]
        self.bg = palette['bg_mid']
        fx, fy, radius = self.POSITIONS[index % len(self.POSITIONS)]
        self.cx = width * fx
        self.cy = height * fy
        self.radius = radius
        self.phase = index * 1.7
        self.item = canvas.create_oval(self.cx - radius, self.cy - radius,
                                       self.cx + radius, self.cy + radius,
                                       outline='', fill=_mix(self.bg, self.color, 0.06))

    def step(self, frame):
        k = 0.05 + 0.02 * (0.5 + 0.5 * math.sin(frame * 0.02 + self.phase))
        self.c.itemconfig(self.item, fill=_mix(self.bg, self.color, k))


def create_decor(style, canvas, width, height, palette):
    """按主题创建背景装饰对象列表"""
    if style == 'circuit':
        return [CircuitTrace(canvas, width, height, palette) for _ in range(16)]
    if style == 'petals':
        return [Petal(canvas, width, height, palette) for _ in range(40)]
    if style == 'minimal':
        return [MinimalAccent(canvas, width, height, palette, i) for i in range(3)]
    return [Star(canvas, width, height, palette) for _ in range(70)]
