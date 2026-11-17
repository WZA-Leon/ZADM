# -*- coding: utf-8 -*-
"""ZADM 姓名管理窗口（浅色主题，与主界面保持一致的视觉风格）"""

import json
import os
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------- 主题
BG = '#f4f8fd'
PANEL = '#ffffff'
FIELD = '#f8fbff'
ROW = '#ffffff'
ROW_HOVER = '#eef6ff'
ROW_SELECTED = '#dceeff'
BORDER = '#d5e3f0'
TEXT = '#22313f'
MUTED = '#5a6f88'
ACCENT = '#1b86bd'
GREEN = '#2e9e6b'
GREEN_HOVER = '#38b57c'
RED = '#d1495b'
RED_HOVER = '#e05b6d'
DIM = '#e6f1fb'
DIM_HOVER = '#d5e6f6'


def _rgb(color):
    color = color.lstrip('#')
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _mix(c1, c2, k):
    """颜色插值，用于悬停 / 勾选的平滑过渡"""
    k = max(0.0, min(1.0, k))
    a, b = _rgb(c1), _rgb(c2)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- 动画按钮
class FlatButton(tk.Button):
    """扁平按钮，鼠标移入 / 移出时底色平滑渐变"""

    def __init__(self, master, base, hover, **kwargs):
        # 浅色主题：深底配白字、浅底配深字，自动选择可读的前景色
        if 'fg' not in kwargs:
            lum = sum(_rgb(base)) / 3.0
            kwargs['fg'] = '#ffffff' if lum < 150 else TEXT
        kwargs.setdefault('font', ('微软雅黑', 10))
        kwargs.setdefault('relief', 'flat')
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('cursor', 'hand2')
        kwargs.setdefault('activebackground', hover)
        kwargs.setdefault('activeforeground', kwargs['fg'])
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('padx', 12)
        kwargs.setdefault('pady', 5)
        tk.Button.__init__(self, master, bg=base, **kwargs)
        self._base = base
        self._hover = hover
        self._t = 0.0
        self._target = 0.0
        self._job = None
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, event=None):
        self._go(1.0)

    def _on_leave(self, event=None):
        self._go(0.0)

    def _go(self, target):
        self._target = target
        if self._job is None:
            self._step()

    def _step(self):
        self._t += (self._target - self._t) * 0.3
        if abs(self._target - self._t) < 0.02:
            self._t = self._target
            self._job = None
        else:
            try:
                self._job = self.after(16, self._step)
            except tk.TclError:
                self._job = None
                return
        try:
            self.configure(bg=_mix(self._base, self._hover, self._t))
        except tk.TclError:
            self._job = None


# ---------------------------------------------------------------- 名单行
class CheckRow:
    """名单中的一行：整行可点击勾选，带悬停 / 勾选过渡动画"""

    HEIGHT = 34

    def __init__(self, master, name, on_change, wheel=None):
        self.name = name
        self.checked = False
        self.hover = False
        self.hover_t = 0.0
        self.check_t = 0.0
        self.settled = True
        self.on_change = on_change
        self.width = 320

        self.c = tk.Canvas(master, height=self.HEIGHT, bg=ROW, highlightthickness=0,
                           bd=0, cursor='hand2')
        self.c.pack(fill=tk.X, pady=1)
        self._draw()
        self.c.bind('<Configure>', self._on_configure)
        self.c.bind('<Button-1>', self.toggle)
        self.c.bind('<Enter>', self._on_enter)
        self.c.bind('<Leave>', self._on_leave)
        if wheel is not None:
            for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                self.c.bind(seq, wheel)

    def _draw(self):
        self.c.delete('all')
        height = self.HEIGHT
        self.bg_item = self.c.create_rectangle(0, 0, self.width, height,
                                               outline='', fill=ROW)
        # 行分隔线，让长名单在浅色背景上更易读
        self.line_item = self.c.create_line(12, height - 1, self.width - 12, height - 1,
                                            fill='#edf3fa')
        box, x = 18, 12
        y = (height - box) / 2.0
        self.box_item = self.c.create_rectangle(x, y, x + box, y + box,
                                                outline=BORDER, width=2, fill=ROW)
        # 勾选用折线绘制，避免字体缺少 U+2713 时显示成方块
        self.tick_item = self.c.create_line(x + 5, y + 9, x + 8, y + 12, x + 14, y + 5,
                                            fill=ROW, width=2,
                                            capstyle=tk.ROUND, joinstyle=tk.ROUND)
        self.text_item = self.c.create_text(42, height / 2.0, text=self.name,
                                            anchor='w', font=('微软雅黑', 11),
                                            fill=TEXT)

    def _on_configure(self, event):
        if event.width != self.width:
            self.width = event.width
            self.c.coords(self.bg_item, 0, 0, self.width, self.HEIGHT)
            self.c.coords(self.line_item, 12, self.HEIGHT - 1,
                          self.width - 12, self.HEIGHT - 1)

    def _on_enter(self, event=None):
        self.hover = True
        self.settled = False

    def _on_leave(self, event=None):
        self.hover = False
        self.settled = False

    def toggle(self, event=None):
        self.checked = not self.checked
        self.settled = False
        if self.on_change is not None:
            self.on_change()
        return 'break'

    def update(self):
        """逐帧过渡；动画结束后自动跳过，避免无谓开销"""
        if self.settled:
            return
        check_target = 1.0 if self.checked else 0.0
        hover_target = 1.0 if self.hover else 0.0
        self.check_t += (check_target - self.check_t) * 0.3
        self.hover_t += (hover_target - self.hover_t) * 0.3
        if abs(self.check_t - check_target) < 0.02:
            self.check_t = check_target
        if abs(self.hover_t - hover_target) < 0.02:
            self.hover_t = hover_target
        if self.check_t == check_target and self.hover_t == hover_target:
            self.settled = True
        try:
            base = _mix(ROW, ROW_SELECTED, self.check_t)
            bg = _mix(base, ROW_HOVER, self.hover_t * 0.85)
            box_fill = _mix(ROW, ACCENT, self.check_t)
            self.c.itemconfig(self.bg_item, fill=bg)
            self.c.configure(bg=bg)
            self.c.itemconfig(self.box_item, fill=box_fill,
                              outline=_mix(BORDER, ACCENT,
                                           max(self.check_t, self.hover_t)))
            self.c.itemconfig(self.tick_item,
                              fill=_mix(box_fill, '#ffffff', self.check_t))
            self.c.itemconfig(self.text_item,
                              fill=_mix(TEXT, ACCENT, 0.35 * self.hover_t))
        except tk.TclError:
            self.settled = True


# ---------------------------------------------------------------- 窗口
class NameManager:
    def __init__(self, master, json_path):
        self.master = master
        self.json_path = json_path
        self.names = []
        self.rows = []
        self.alive = True
        self.status_dirty = True
        self._flash_text = ''
        self._flash_job = None

        self.load_names()
        self.create_widgets()
        self.refresh_list()
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        # 打开后光标直接落在输入框，输入完按回车即可添加
        self.master.after(60, self._focus_input)
        self.tick()

    # ---------------- 数据 ----------------
    def load_names(self):
        """从 JSON 文件加载名单"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.names = [str(n).strip() for n in data if str(n).strip()]
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
            self.names = []

    def save_names(self):
        """将名单保存回 JSON 文件"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.names, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror('错误', '保存失败：%s' % e, parent=self.master)

    # ---------------- 界面 ----------------
    def create_widgets(self):
        self.master.configure(bg=BG)
        self.master.title('名单管理')
        self.master.geometry('560x660')
        self.master.minsize(520, 560)

        header = tk.Frame(self.master, bg=BG)
        header.pack(fill=tk.X, padx=16, pady=(14, 8))
        tk.Label(header, text='名单管理', bg=BG, fg=TEXT,
                 font=('华文中宋', 16, 'bold')).pack(side=tk.LEFT)
        self.count_label = tk.Label(header, text='', bg=BG, fg=MUTED,
                                    font=('微软雅黑', 9))
        self.count_label.pack(side=tk.RIGHT)

        # ---- 添加姓名（按钮读取下方输入框，一行一个，可一次多行） ----
        add_panel = tk.Frame(self.master, bg=PANEL, highlightthickness=1,
                             highlightbackground=BORDER)
        add_panel.pack(fill=tk.X, padx=16)

        add_head = tk.Frame(add_panel, bg=PANEL)
        add_head.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(add_head, text='每行一个姓名，可一次粘贴多行（重复的会自动忽略）',
                 bg=PANEL, fg=MUTED, font=('微软雅黑', 9)).pack(side=tk.LEFT)
        FlatButton(add_head, GREEN, GREEN_HOVER, text='添加姓名',
                   command=self.add_names).pack(side=tk.RIGHT)

        self.text_input = tk.Text(add_panel, height=5, font=('微软雅黑', 11),
                                  bg=FIELD, fg=TEXT, insertbackground=ACCENT,
                                  relief=tk.FLAT, bd=0, padx=8, pady=6,
                                  highlightthickness=1,
                                  highlightbackground=BORDER, highlightcolor=ACCENT,
                                  selectbackground='#bfe0f5', selectforeground=TEXT,
                                  wrap=tk.WORD)
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # ---- 名单列表 ----
        list_panel = tk.Frame(self.master, bg=BG)
        list_panel.pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 0))
        head = tk.Frame(list_panel, bg=BG)
        head.pack(fill=tk.X)
        tk.Label(head, text='当前名单（点击行勾选）', bg=BG, fg=MUTED,
                 font=('微软雅黑', 9)).pack(side=tk.LEFT)
        self.sel_label = tk.Label(head, text='', bg=BG, fg=MUTED,
                                  font=('微软雅黑', 9))
        self.sel_label.pack(side=tk.RIGHT)

        body = tk.Frame(list_panel, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        body.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self.canvas = tk.Canvas(body, bg=PANEL, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(body, orient=tk.VERTICAL,
                                      command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=PANEL)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner,
                                                  anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.inner.bind('<Configure>', self._on_inner_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self.canvas.bind(seq, self._on_wheel)
            self.inner.bind(seq, self._on_wheel)

        # ---- 底部操作 ----
        bottom = tk.Frame(self.master, bg=BG)
        bottom.pack(fill=tk.X, padx=16, pady=10)
        FlatButton(bottom, RED, RED_HOVER, text='删除选中',
                   command=self.delete_selected).pack(side=tk.LEFT)
        self.all_btn = FlatButton(bottom, DIM, DIM_HOVER, text='全选',
                                  command=self.toggle_all)
        self.all_btn.pack(side=tk.LEFT, padx=(8, 0))
        FlatButton(bottom, DIM, DIM_HOVER, text='刷新列表',
                   command=self.refresh_list).pack(side=tk.LEFT, padx=(8, 0))
        self.status_label = tk.Label(bottom, text='', bg=BG, fg=MUTED,
                                     font=('微软雅黑', 9))
        self.status_label.pack(side=tk.RIGHT)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_wheel(self, event):
        if getattr(event, 'delta', 0):
            step = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(step, 'units')
        elif getattr(event, 'num', None) == 4:
            self.canvas.yview_scroll(-1, 'units')
        elif getattr(event, 'num', None) == 5:
            self.canvas.yview_scroll(1, 'units')
        return 'break'

    # ---------------- 列表刷新 ----------------
    def refresh_list(self, goto_bottom=False):
        """重建列表（同时重新读取文件，避免外部修改不同步）"""
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.rows = []
        self.load_names()

        if not self.names:
            tk.Label(self.inner, text='名单还是空的\n在上方输入框里输入姓名（每行一个）\n'
                                      '然后点击“添加姓名”',
                     bg=PANEL, fg=MUTED, font=('微软雅黑', 10),
                     justify=tk.CENTER).pack(pady=42)
        else:
            for name in self.names:
                self.rows.append(CheckRow(self.inner, name, self.on_row_change,
                                          wheel=self._on_wheel))

        self.status_dirty = True
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        if goto_bottom:
            # 添加后滚到底部，让刚加入的姓名直接可见
            self.canvas.yview_moveto(1.0)
        else:
            self.canvas.yview_moveto(0)

    def on_row_change(self):
        self.status_dirty = True

    def toggle_all(self):
        if not self.rows:
            return
        target = not all(row.checked for row in self.rows)
        for row in self.rows:
            if row.checked != target:
                row.checked = target
                row.settled = False
        self.status_dirty = True

    # ---------------- 逐帧动画 ----------------
    def tick(self):
        if not self.alive:
            return
        try:
            for row in self.rows:
                row.update()
            if self.status_dirty:
                self._refresh_status()
        except tk.TclError:
            return
        self.master.after(40, self.tick)

    def _refresh_status(self):
        total = len(self.rows)
        selected = sum(1 for row in self.rows if row.checked)
        self.count_label.configure(text='共 %d 人' % total)
        self.sel_label.configure(text=('已选 %d 人' % selected) if selected else '')
        self.all_btn.configure(text='取消全选' if total and selected == total else '全选')
        if self._flash_text:
            self.status_label.configure(text=self._flash_text, fg=GREEN)
        else:
            self.status_label.configure(text='共 %d 人 · 已选 %d 人' % (total, selected),
                                       fg=MUTED)
        self.status_dirty = False

    def _flash(self, text, color=GREEN):
        """在底部状态栏短暂显示一条提示（1.8 秒后恢复统计信息）"""
        self._flash_text = text
        self.status_label.configure(text=text, fg=color)
        if self._flash_job is not None:
            try:
                self.master.after_cancel(self._flash_job)
            except tk.TclError:
                pass
        self._flash_job = self.master.after(1800, self._clear_flash)

    def _clear_flash(self):
        self._flash_job = None
        self._flash_text = ''
        self.status_dirty = True

    def _focus_input(self):
        try:
            self.text_input.focus_set()
        except tk.TclError:
            pass

    # ---------------- 增删 ----------------
    def add_names(self):
        """添加姓名：读取输入框，每行一个，可一次添加多行"""
        text = self.text_input.get('1.0', tk.END)
        new_names = [line.strip() for line in text.splitlines()]
        new_names = [n for n in new_names if n]

        if not new_names:
            self._flash('请先在输入框中输入姓名（每行一个）', MUTED)
            self.text_input.focus_set()
            return

        added = 0
        for name in new_names:
            if name not in self.names:
                self.names.append(name)
                added += 1

        if added == 0:
            self._flash('这些姓名都已经在名单里了', RED)
            self.text_input.focus_set()
            return

        self.save_names()
        self.text_input.delete('1.0', tk.END)
        self.refresh_list(goto_bottom=True)
        skipped = len(new_names) - added
        if skipped:
            self._flash('成功添加 %d 个姓名（%d 个重复已忽略）' % (added, skipped))
        else:
            self._flash('成功添加 %d 个姓名' % added)
        self.text_input.focus_set()

    def delete_selected(self):
        """批量删除选中的姓名"""
        selected = [row.name for row in self.rows if row.checked]
        if not selected:
            messagebox.showinfo('提示', '请至少勾选一个姓名。', parent=self.master)
            return

        if messagebox.askyesno('确认删除',
                               '确定要删除选中的 %d 个姓名吗？' % len(selected),
                               parent=self.master):
            removed = set(selected)
            self.names = [n for n in self.names if n not in removed]
            self.save_names()
            self.refresh_list()
            messagebox.showinfo('完成', '已删除 %d 个姓名。' % len(selected),
                                parent=self.master)

    def close(self):
        self.alive = False
        try:
            self.master.destroy()
        except tk.TclError:
            pass


_manager_window = None


def open_name_manager(json_path):
    """外部调用的接口：弹出姓名管理窗口（已打开时只做置顶）"""
    global _manager_window
    if _manager_window is not None:
        try:
            if _manager_window.winfo_exists():
                _manager_window.lift()
                _manager_window.focus_force()
                return
        except tk.TclError:
            pass

    win = tk.Toplevel()
    win.configure(bg=BG)
    win.resizable(True, True)
    try:
        win.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'data', 'zadm.ico'))
    except Exception:
        pass

    NameManager(win, json_path)
    win.lift()
    win.focus_force()
    _manager_window = win

    # 窗口淡入
    try:
        steps = 10
        win.attributes('-alpha', 0.0)

        def fade(i=1):
            try:
                win.attributes('-alpha', min(1.0, i / float(steps)))
            except tk.TclError:
                return
            if i < steps:
                win.after(16, lambda: fade(i + 1))

        win.after(16, fade)
    except tk.TclError:
        pass