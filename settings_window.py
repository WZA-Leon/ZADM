# -*- coding: utf-8 -*-
"""ZADM 设置窗口

· 入口密码：由用户自行设置（首次打开时设置，之后每次进入需输入）
· 抽选设置：不重复模式 / 每轮抽取人数 / 姓名滚动频率
· 概率设置：自动均衡开关、均衡强度、重置历史、平均概率展示
· 特定人物概率：独立密码（tr520）解锁，手动概率优先于平均 / 均衡
"""

import tkinter as tk
from tkinter import messagebox

import zadm_config as cfg
import zadm_theme as themes

# ---------------------------------------------------------------- 主题（与名单管理窗口一致）
BG = '#f4f8fd'
PANEL = '#ffffff'
FIELD = '#f8fbff'
BORDER = '#d5e3f0'
TEXT = '#22313f'
MUTED = '#5a6f88'
ACCENT = '#1b86bd'
ACCENT_DARK = '#15678f'
GREEN = '#2e9e6b'
GREEN_HOVER = '#38b57c'
RED = '#d1495b'
RED_HOVER = '#e05b6d'
DIM = '#e6f1fb'
DIM_HOVER = '#d5e6f6'

TITLE_FONT = ('华文中宋', 16, 'bold')
BODY_FONT = ('微软雅黑', 10)
SMALL_FONT = ('微软雅黑', 9)

ICON_PATH = cfg.DATA_DIR + '/zadm.ico'


def _rgb(color):
    color = color.lstrip('#')
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _mix(c1, c2, k):
    k = max(0.0, min(1.0, k))
    a, b = _rgb(c1), _rgb(c2)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- 扁平按钮
class FlatButton(tk.Button):
    def __init__(self, master, base, hover, **kwargs):
        if 'fg' not in kwargs:
            lum = sum(_rgb(base)) / 3.0
            kwargs['fg'] = '#ffffff' if lum < 150 else TEXT
        kwargs.setdefault('font', BODY_FONT)
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


# ---------------------------------------------------------------- 密码对话框
class _PasswordDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, confirm=False,
                 ok_text='确定', hint=''):
        tk.Toplevel.__init__(self, parent)
        self.withdraw()
        self.result = None
        self.title(title)
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(parent)

        box = tk.Frame(self, bg=PANEL)
        box.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(box, text=prompt, bg=PANEL, fg=TEXT, font=BODY_FONT,
                 wraplength=330, justify=tk.LEFT).pack(anchor=tk.W)
        if hint:
            tk.Label(box, text=hint, bg=PANEL, fg=MUTED, font=SMALL_FONT,
                     wraplength=330, justify=tk.LEFT).pack(anchor=tk.W, pady=(4, 0))

        self.entries = []
        tk.Label(box, text='密码', bg=PANEL, fg=MUTED, font=SMALL_FONT).pack(
            anchor=tk.W, pady=(10, 2))
        first = self._entry(box)
        self.entries.append(first)
        if confirm:
            tk.Label(box, text='确认密码', bg=PANEL, fg=MUTED, font=SMALL_FONT).pack(
                anchor=tk.W, pady=(8, 2))
            self.entries.append(self._entry(box))

        row = tk.Frame(box, bg=PANEL)
        row.pack(fill=tk.X, pady=(14, 0))
        FlatButton(row, GREEN, GREEN_HOVER, text=ok_text, command=self._ok,
                   width=8).pack(side=tk.RIGHT)
        FlatButton(row, DIM, DIM_HOVER, text='取消', command=self._cancel,
                   width=6).pack(side=tk.RIGHT, padx=(0, 8))

        self.bind('<Return>', lambda e: self._ok())
        self.bind('<Escape>', lambda e: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

        self.update_idletasks()
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            w, h = self.winfo_reqwidth(), self.winfo_reqheight()
            self.geometry('+%d+%d' % (px + (pw - w) // 2, py + (ph - h) // 3))
        except tk.TclError:
            pass
        self.deiconify()
        self.grab_set()
        first.focus_set()
        self.wait_window(self)

    def _entry(self, master):
        e = tk.Entry(master, font=('微软雅黑', 11), bg=FIELD, fg=TEXT, show='●',
                     insertbackground=ACCENT, relief=tk.FLAT, bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, width=24)
        e.pack(fill=tk.X, ipady=5)
        return e

    def _ok(self, event=None):
        self.result = [e.get() for e in self.entries]
        self.destroy()

    def _cancel(self, event=None):
        self.result = None
        self.destroy()


def ask_password(parent, title='需要密码', prompt='请输入密码',
                 confirm=False, ok_text='确定', hint=''):
    """弹出密码框，返回输入的密码（取消返回 None）"""
    dlg = _PasswordDialog(parent, title, prompt, confirm=confirm,
                          ok_text=ok_text, hint=hint)
    if dlg.result is None:
        return None
    return dlg.result[0]


def setup_password(parent, title='设置密码', prompt='首次使用设置界面，请设置一个密码'):
    """首次设置密码：两次输入需一致"""
    while True:
        dlg = _PasswordDialog(parent, title, prompt, confirm=True,
                              ok_text='设置', hint='密码至少 2 个字符')
        if dlg.result is None:
            return None
        first, second = dlg.result
        if len(first) < 2:
            messagebox.showwarning('密码太短', '密码至少需要 2 个字符。', parent=parent)
            continue
        if first != second:
            messagebox.showwarning('两次输入不一致', '两次输入的密码不一致，请重新设置。',
                                   parent=parent)
            continue
        return first


def _check_access(parent):
    """进入设置界面的密码校验

    · 密码保护已关闭（用户主动清空过）→ 直接进入
    · 还没设置过密码 → 引导设置
    · 已设置 → 输入校验（最多 3 次）
    """
    settings = cfg.load_settings()
    if not settings.get('password_protected', True):
        return True
    if not cfg.has_password(settings):
        password = setup_password(parent)
        if password is None:
            return False
        cfg.set_password(settings, password)
        settings['password_protected'] = True
        cfg.save_settings(settings)
        messagebox.showinfo('设置成功', '密码已设置，请牢记。下次进入设置界面需要输入该密码。',
                            parent=parent)
        return True

    for _ in range(3):
        password = ask_password(parent, title='进入设置',
                                prompt='请输入设置密码',
                                hint='密码由你在首次使用设置界面时设置')
        if password is None:
            return False
        if cfg.verify_password(settings, password):
            return True
        messagebox.showerror('密码错误', '密码不正确，请重试。', parent=parent)
    return False


def _verify_manual_password(parent):
    """特定人物概率区域的独立密码（tr520）"""
    for _ in range(3):
        password = ask_password(parent, title='特定人物概率',
                                prompt='该区域受密码保护，请输入密码',
                                hint='密码区分大小写')
        if password is None:
            return False
        if password == cfg.MANUAL_PASSWORD:
            return True
        messagebox.showerror('密码错误', '密码不正确，请重试。', parent=parent)
    return False


# ---------------------------------------------------------------- 设置窗口
class SettingsWindow:
    def __init__(self, master, app):
        self.master = master
        self.app = app
        self.settings = cfg.load_settings()
        self.names = list(app.names)
        self.manual_unlocked = False
        self.current_tab = 'general'
        self.tabs = {}
        self.tab_buttons = {}
        self.manual_rows = []

        self._build()
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        self.select_tab('general')

    # ---------------- 界面骨架 ----------------
    def _build(self):
        m = self.master
        m.configure(bg=BG)
        m.title('ZADM 设置')
        m.geometry('840x680')
        m.minsize(780, 620)
        try:
            m.iconbitmap(ICON_PATH)
        except Exception:
            pass

        header = tk.Frame(m, bg=BG)
        header.pack(fill=tk.X, padx=20, pady=(16, 6))
        tk.Label(header, text='设置', bg=BG, fg=TEXT, font=TITLE_FONT).pack(side=tk.LEFT)
        tk.Label(header, text='关闭窗口时也会自动保存',
                 bg=BG, fg=MUTED, font=SMALL_FONT).pack(side=tk.RIGHT)

        tabbar = tk.Frame(m, bg=BG)
        tabbar.pack(fill=tk.X, padx=20)
        for key, text in (('general', '抽选设置'), ('prob', '概率设置'),
                          ('manual', '特定人物概率'), ('appearance', '外观主题'),
                          ('security', '安全')):
            btn = tk.Button(tabbar, text=text, font=BODY_FONT, bd=0,
                            relief=tk.FLAT, cursor='hand2', padx=16, pady=7,
                            bg=DIM, fg=MUTED, activebackground=DIM_HOVER,
                            activeforeground=TEXT, highlightthickness=0,
                            command=lambda k=key: self.select_tab(k))
            btn.pack(side=tk.LEFT, padx=(0, 8))
            self.tab_buttons[key] = btn

        self.body = tk.Frame(m, bg=BG)
        self.body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 0))

        self.tabs['general'] = self._build_general(self.body)
        self.tabs['prob'] = self._build_probability(self.body)
        self.tabs['manual'] = self._build_manual(self.body)
        self.tabs['appearance'] = self._build_appearance(self.body)
        self.tabs['security'] = self._build_security(self.body)

        footer = tk.Frame(m, bg=BG)
        footer.pack(fill=tk.X, padx=20, pady=12)
        FlatButton(footer, GREEN, GREEN_HOVER, text='保存并生效',
                   command=lambda: self.save_and_apply(notify=True),
                   width=12).pack(side=tk.LEFT)
        FlatButton(footer, DIM, DIM_HOVER, text='关闭',
                   command=self.close, width=8).pack(side=tk.LEFT, padx=(8, 0))
        self.tip_label = tk.Label(footer, text='', bg=BG, fg=GREEN, font=SMALL_FONT)
        self.tip_label.pack(side=tk.RIGHT)

    def select_tab(self, key):
        for k, frame in self.tabs.items():
            if k == key:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(bg=PANEL, fg=ACCENT_DARK,
                              font=('微软雅黑', 10, 'bold'))
            else:
                btn.configure(bg=DIM, fg=MUTED, font=BODY_FONT)
        self.current_tab = key
        if key == 'prob':
            self._refresh_stats()
        elif key == 'appearance':
            self._refresh_theme_buttons()
        elif key == 'security':
            self._refresh_security_state()

    # ---------------- 通用小部件 ----------------
    def _panel(self, master, title, hint=''):
        wrap = tk.Frame(master, bg=BG)
        wrap.pack(fill=tk.X)
        card = tk.Frame(wrap, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(card, text=title, bg=PANEL, fg=TEXT,
                 font=('微软雅黑', 11, 'bold')).pack(anchor=tk.W,
                                                    padx=14, pady=(12, 2))
        if hint:
            tk.Label(card, text=hint, bg=PANEL, fg=MUTED, font=SMALL_FONT,
                     wraplength=740, justify=tk.LEFT).pack(anchor=tk.W,
                                                           padx=14, pady=(0, 8))
        return card

    def _check(self, master, text, var):
        return tk.Checkbutton(master, text=text, variable=var, bg=PANEL,
                              fg=TEXT, font=BODY_FONT, activebackground=PANEL,
                              activeforeground=TEXT, selectcolor='#ffffff',
                              bd=0, highlightthickness=0, cursor='hand2',
                              anchor=tk.W, padx=14)

    def _slider(self, master, var, low, high, unit='', step=1):
        row = tk.Frame(master, bg=PANEL)
        row.pack(fill=tk.X, padx=14, pady=(0, 10))
        scale = tk.Scale(row, variable=var, from_=low, to=high, orient=tk.HORIZONTAL,
                         resolution=step, bg=PANEL, fg=TEXT, troughcolor='#dbe9f7',
                         activebackground=ACCENT, highlightthickness=0, bd=1,
                         sliderrelief=tk.RAISED, font=SMALL_FONT, length=400,
                         showvalue=0, sliderlength=18, width=12)
        scale.pack(side=tk.LEFT)
        value_label = tk.Label(row, text=str(var.get()), bg=PANEL, fg=ACCENT_DARK,
                               font=('微软雅黑', 10, 'bold'), width=4, anchor='e')
        value_label.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(row, text=unit, bg=PANEL, fg=MUTED, font=SMALL_FONT).pack(
            side=tk.LEFT, padx=(6, 0))

        def sync(*_args):
            try:
                value_label.configure(text=str(var.get()))
            except tk.TclError:
                pass

        var.trace_add('write', sync)
        return scale

    def _entry_row(self, master, label, var, width=10, show=None):
        row = tk.Frame(master, bg=PANEL)
        row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(row, text=label, bg=PANEL, fg=TEXT, font=BODY_FONT,
                 width=10, anchor=tk.W).pack(side=tk.LEFT)
        entry = tk.Entry(row, textvariable=var, font=BODY_FONT, bg=FIELD, fg=TEXT,
                         insertbackground=ACCENT, relief=tk.FLAT, bd=0, width=width,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, show=show)
        entry.pack(side=tk.LEFT, ipady=4)
        return entry

    # ---------------- 抽选设置 ----------------
    def _build_general(self, master):
        frame = tk.Frame(master, bg=BG)
        card = self._panel(frame, '抽选方式',
                           '这些设置会立即影响主界面的抽选行为。')

        self.var_bag = tk.BooleanVar(value=bool(self.settings.get('bag_mode', True)))
        self._check(card, '不重复模式（一轮抽完才重新洗牌，任何人都不会连续两轮被抽中）',
                    self.var_bag).pack(fill=tk.X, pady=(0, 8))

        row = tk.Frame(card, bg=PANEL)
        row.pack(fill=tk.X, padx=14, pady=(0, 10))
        tk.Label(row, text='每轮抽取人数', bg=PANEL, fg=TEXT, font=BODY_FONT).pack(
            side=tk.LEFT)
        max_count = max(1, min(cfg.MAX_DRAW, len(self.names) or 1))
        self.var_count = tk.StringVar(value=str(min(int(self.settings.get('draw_count', 1)),
                                                   max_count)))
        tk.Spinbox(row, from_=1, to=max_count, width=4, textvariable=self.var_count,
                   font=BODY_FONT, bg=FIELD, fg=TEXT, bd=0, relief=tk.FLAT,
                   highlightthickness=1, highlightbackground=BORDER,
                   justify=tk.CENTER, buttonbackground=FIELD).pack(side=tk.LEFT,
                                                                   padx=(12, 8),
                                                                   ipady=2)
        tk.Label(row, text='人（名单共 %d 人，主界面也可直接调整）' % len(self.names),
                 bg=PANEL, fg=MUTED, font=SMALL_FONT).pack(side=tk.LEFT)

        tk.Label(card, text='姓名滚动频率', bg=PANEL, fg=TEXT, font=BODY_FONT).pack(
            anchor=tk.W, padx=14, pady=(4, 0))
        self.var_speed = tk.IntVar(value=self._interval_to_speed(
            int(self.settings.get('roll_interval', 45))))
        self._slider(card, self.var_speed, 1, 10, '（1 = 慢，10 = 很快）')
        self.speed_label = tk.Label(card, text='', bg=PANEL, fg=MUTED, font=SMALL_FONT)
        self.speed_label.pack(anchor=tk.W, padx=14, pady=(0, 10))
        self.var_speed.trace_add('write', lambda *a: self._update_speed_label())
        self._update_speed_label()

        hint = tk.Frame(frame, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        hint.pack(fill=tk.X, pady=(0, 12))
        tk.Label(hint, text='提示：每轮人数越多，主界面的姓名滚动区域会自动变大，'
                            '字号相应缩小；名单人数不足时会自动限制。',
                 bg=PANEL, fg=MUTED, font=SMALL_FONT, wraplength=740,
                 justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=10)
        return frame

    @staticmethod
    def _interval_to_speed(interval):
        interval = max(10, min(400, interval))
        return max(1, min(10, int(round((160 - interval) / 15.0)) + 1))

    @staticmethod
    def _speed_to_interval(speed):
        speed = max(1, min(10, int(speed)))
        return max(15, 160 - (speed - 1) * 15)

    def _update_speed_label(self):
        try:
            interval = self._speed_to_interval(self.var_speed.get())
            self.speed_label.configure(
                text='当前：约每 %d 毫秒切换一次姓名' % interval)
        except (tk.TclError, ValueError):
            pass

    # ---------------- 概率设置 ----------------
    def _build_probability(self, master):
        frame = tk.Frame(master, bg=BG)
        card = self._panel(frame, '自动均衡概率',
                           '根据 data/history.json 中记录的抽取次数动态调整概率，'
                           '抽得越少的人权重越高，避免总是抽到固定的几个人。')

        self.var_balance = tk.BooleanVar(value=bool(self.settings.get('auto_balance', True)))
        self._check(card, '开启自动均衡（关闭后所有人概率相同）',
                    self.var_balance).pack(fill=tk.X, pady=(0, 6))

        tk.Label(card, text='均衡强度', bg=PANEL, fg=TEXT, font=BODY_FONT).pack(
            anchor=tk.W, padx=14)
        self.var_strength = tk.IntVar(
            value=int(round(float(self.settings.get('balance_strength', 1.0)) * 100)))
        self._slider(card, self.var_strength, 0, 200, '（100% = 标准，越大越向“抽得少的人”倾斜）')

        self.stats_label = tk.Label(card, text='', bg=PANEL, fg=TEXT, font=SMALL_FONT,
                                    justify=tk.LEFT, anchor=tk.W)
        self.stats_label.pack(anchor=tk.W, padx=14)
        self.avg_label = tk.Label(card, text='', bg=PANEL, fg=MUTED, font=SMALL_FONT)
        self.avg_label.pack(anchor=tk.W, padx=14, pady=(4, 0))

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(anchor=tk.W, padx=14, pady=(10, 12))
        FlatButton(actions, ACCENT, '#15678f', text='平均所有人概率',
                   command=self._average_all).pack(side=tk.LEFT)
        FlatButton(actions, DIM, DIM_HOVER, text='重置抽取历史',
                   command=self._reset_history).pack(side=tk.LEFT, padx=(8, 0))

        note = tk.Frame(frame, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        note.pack(fill=tk.X, pady=(0, 12))
        tk.Label(note, text='优先级：特定人物手动概率（绝对百分比）> 历史均衡 > 平均概率。\n'
                            '例如手动给某人设 20%，则他从 100% 中固定拿走 20%，'
                            '其余人再按均衡规则分配剩下的 80%。',
                 bg=PANEL, fg=MUTED, font=SMALL_FONT, wraplength=740,
                 justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=10)
        self._refresh_stats()
        return frame

    def _refresh_stats(self):
        names = self.names
        if not names:
            text = '名单为空'
            avg = '平均概率：—'
        else:
            summary = cfg.history_summary(names)
            if summary['rounds'] == 0:
                text = '尚无抽取记录：所有人概率相同'
            else:
                text = ('已记录抽取 %d 次 · 合计 %d 人次 · 每人平均 %.1f 次'
                        % (summary['rounds'], summary['total'], summary['avg']))
                if summary['max'] > 0:
                    text += ('\n最多：%s（%d 次）   最少：%s（%d 次）'
                             % (summary['max_name'], summary['max'],
                                summary['min_name'], summary['min']))
            avg = ('平均概率：每人 %.2f%%（1/%d）'
                   % (cfg.average_probability(names), len(names)))
        for label, value in ((self.stats_label, text), (self.avg_label, avg)):
            try:
                label.configure(text=value)
            except (tk.TclError, AttributeError):
                pass

    def _reset_history(self):
        if not messagebox.askyesno('重置历史', '确定要清空所有抽取记录吗？\n'
                                               '清空后概率会回到完全平均。',
                                   parent=self.master):
            return
        cfg.reset_history()
        self._refresh_stats()
        self._refresh_manual_probs()
        if hasattr(self.app, 'reload_history'):
            self.app.reload_history()
        self._tip('抽取历史已清空')

    def _average_all(self):
        """一键把所有人的概率恢复为平均：关闭均衡 + 清空手动概率"""
        if not self.names:
            messagebox.showwarning('名单为空', '名单里还没有姓名，无法设置概率。',
                                   parent=self.master)
            return
        self.var_balance.set(False)
        self.settings['auto_balance'] = False
        self.settings['manual_probs'] = {}
        self.collect()
        cfg.save_settings(self.settings)
        if hasattr(self.app, 'apply_settings'):
            self.app.apply_settings()
        self._refresh_stats()
        if self.manual_unlocked and self.manual_rows:
            for _name, var, _label, _row in self.manual_rows:
                var.set('')
            self._refresh_manual_probs()
        avg = cfg.average_probability(self.names)
        self._tip('已保存：所有人概率已平均')
        messagebox.showinfo('已保存',
                            '已将所有人概率设置为平均：每人 %.2f%%。' % avg,
                            parent=self.master)

    # ---------------- 特定人物概率 ----------------
    def _build_manual(self, master):
        frame = tk.Frame(master, bg=BG)
        self.manual_frame = frame
        self._render_manual_lock()
        return frame

    def _render_manual_lock(self):
        for widget in self.manual_frame.winfo_children():
            widget.destroy()
        card = tk.Frame(self.manual_frame, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(card, bg=PANEL)
        inner.pack(expand=True)
        tk.Label(inner, text='🔒', bg=PANEL, fg=MUTED,
                 font=('微软雅黑', 26)).pack(pady=(40, 6))
        tk.Label(inner, text='特定人物概率区域受密码保护', bg=PANEL, fg=TEXT,
                 font=('微软雅黑', 12, 'bold')).pack()
        tk.Label(inner, text='解锁后可为个别人单独设置中签概率，\n手动概率优先于自动均衡 / 平均概率。',
                 bg=PANEL, fg=MUTED, font=SMALL_FONT,
                 justify=tk.CENTER).pack(pady=(6, 14))
        FlatButton(inner, ACCENT, '#15678f', text='解锁编辑',
                   command=self._unlock_manual, width=10).pack(pady=(0, 40))

    def _unlock_manual(self):
        if not _verify_manual_password(self.master):
            return
        self.manual_unlocked = True
        self._render_manual_editor()

    def _lock_manual(self):
        self.manual_unlocked = False
        self._render_manual_lock()

    def _render_manual_editor(self):
        for widget in self.manual_frame.winfo_children():
            widget.destroy()

        head = tk.Frame(self.manual_frame, bg=BG)
        head.pack(fill=tk.X)
        tk.Label(head, text='在“指定概率”里填写百分比（留空 = 按均衡 / 平均计算）',
                 bg=BG, fg=MUTED, font=SMALL_FONT).pack(anchor=tk.W)
        self.manual_sum_label = tk.Label(self.manual_frame, text='', bg=BG, fg=MUTED,
                                         font=SMALL_FONT)
        self.manual_sum_label.pack(anchor=tk.W, pady=(2, 6))

        card = tk.Frame(self.manual_frame, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(card, bg=PANEL, highlightthickness=0, bd=0)
        scroll = tk.Scrollbar(card, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL)
        window = canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=6)
        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfigure(window, width=e.width))
        for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            canvas.bind(seq, lambda e: self._manual_wheel(e, canvas))

        def make_cell(parent, bg, width, text='', font=SMALL_FONT, color=MUTED):
            box = tk.Frame(parent, bg=bg, width=width, height=26)
            box.pack(side=tk.LEFT)
            box.pack_propagate(False)
            if text:
                tk.Label(box, text=text, bg=bg, fg=color, font=font,
                         anchor='w').pack(fill=tk.BOTH, expand=True)
            return box

        header = tk.Frame(inner, bg='#eef4fb')
        header.pack(fill=tk.X)
        make_cell(header, '#eef4fb', 150, '姓名')
        make_cell(header, '#eef4fb', 150, '指定概率 %')
        make_cell(header, '#eef4fb', 130, '当前概率')

        self.manual_rows = []
        probs = cfg.compute_probabilities(self.names, self.settings,
                                          cfg.load_history())
        manual = self.settings.get('manual_probs') or {}
        for index, name in enumerate(self.names):
            bg = '#ffffff' if index % 2 == 0 else '#f8fbff'
            row = tk.Frame(inner, bg=bg)
            row.pack(fill=tk.X)
            make_cell(row, bg, 150, name, font=BODY_FONT, color=TEXT)
            prob_cell = tk.Frame(row, bg=bg, width=150, height=26)
            prob_cell.pack(side=tk.LEFT)
            prob_cell.pack_propagate(False)
            var = tk.StringVar(value=('%.2f' % manual[name]) if name in manual else '')
            entry = tk.Entry(prob_cell, textvariable=var, font=BODY_FONT, bg=FIELD,
                             fg=TEXT, insertbackground=ACCENT, relief=tk.FLAT,
                             bd=0, width=8, justify=tk.CENTER,
                             highlightthickness=1, highlightbackground=BORDER,
                             highlightcolor=ACCENT)
            entry.pack(side=tk.LEFT, padx=(2, 0), ipady=2)
            entry.bind('<KeyRelease>', lambda e: self._refresh_manual_probs())
            pct_cell = tk.Frame(row, bg=bg, width=130, height=26)
            pct_cell.pack(side=tk.LEFT)
            pct_cell.pack_propagate(False)
            pct_label = tk.Label(pct_cell, text=cfg.format_percent(probs.get(name, 0.0)),
                                 bg=bg, fg=MUTED, font=SMALL_FONT, anchor='w')
            pct_label.pack(fill=tk.BOTH, expand=True)
            self.manual_rows.append((name, var, pct_label, row))

        bar = tk.Frame(self.manual_frame, bg=BG)
        bar.pack(fill=tk.X, pady=(8, 0))
        FlatButton(bar, GREEN, GREEN_HOVER, text='应用并保存',
                   command=self._apply_manual).pack(side=tk.LEFT)
        FlatButton(bar, DIM, DIM_HOVER, text='全部清空',
                   command=self._clear_manual).pack(side=tk.LEFT, padx=(8, 0))
        FlatButton(bar, DIM, DIM_HOVER, text='重新上锁',
                   command=self._lock_manual).pack(side=tk.LEFT, padx=(8, 0))
        self._update_manual_sum()

    def _manual_wheel(self, event, canvas):
        if getattr(event, 'delta', 0):
            canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
        elif getattr(event, 'num', None) == 4:
            canvas.yview_scroll(-1, 'units')
        elif getattr(event, 'num', None) == 5:
            canvas.yview_scroll(1, 'units')
        return 'break'

    def _read_manual(self):
        """读取输入框里的手动概率，返回 (dict, 合计, 是否有非法值)"""
        probs = {}
        total = 0.0
        bad = []
        for name, var, _, _ in self.manual_rows:
            text = var.get().strip()
            if not text:
                continue
            try:
                value = float(text)
            except ValueError:
                bad.append(name)
                continue
            if value < 0 or value > 100:
                bad.append(name)
                continue
            if value == 0:
                continue
            probs[name] = round(value, 3)
            total += value
        return probs, total, bad

    def _update_manual_sum(self):
        try:
            _, total, bad = self._read_manual()
            text = '手动概率合计：%.2f%%' % total
            color = RED if (total > 100 or bad) else MUTED
            if bad:
                text += '（有 %d 项无效）' % len(bad)
            self.manual_sum_label.configure(text=text, fg=color)
        except (tk.TclError, AttributeError):
            pass

    def _apply_manual(self):
        probs, total, bad = self._read_manual()
        if bad:
            messagebox.showwarning('数值无效',
                                   '以下姓名的概率不是 0~100 之间的数字：\n%s'
                                   % '、'.join(bad[:10]), parent=self.master)
            return
        if total > 100.0001:
            messagebox.showwarning('合计超过 100%',
                                   '手动概率合计为 %.2f%%，不能超过 100%%。' % total,
                                   parent=self.master)
            return
        self.settings['manual_probs'] = probs
        self.collect()
        cfg.save_settings(self.settings)
        if hasattr(self.app, 'apply_settings'):
            self.app.apply_settings()
        self._refresh_manual_probs()
        self._tip('特定人物概率已保存')

    def _clear_manual(self):
        if not messagebox.askyesno('清空手动概率', '确定清空所有特定人物的手动概率吗？',
                                   parent=self.master):
            return
        self.settings['manual_probs'] = {}
        cfg.save_settings(self.settings)
        if hasattr(self.app, 'apply_settings'):
            self.app.apply_settings()
        for name, var, _, _ in self.manual_rows:
            var.set('')
        self._refresh_manual_probs()
        self._tip('已清空所有手动概率')

    def _refresh_manual_probs(self):
        """刷新“当前概率”列：直接用输入框里的数值做预览"""
        if not self.manual_rows:
            return
        probs_in, total, bad = self._read_manual()
        preview = dict(self.settings)
        if not bad and total <= 100.0001:
            preview['manual_probs'] = probs_in
        probs = cfg.compute_probabilities(self.names, preview, cfg.load_history())
        for name, var, label, _ in self.manual_rows:
            try:
                label.configure(text=cfg.format_percent(probs.get(name, 0.0)))
            except tk.TclError:
                return
        self._update_manual_sum()

    # ---------------- 外观主题 ----------------
    def _build_appearance(self, master):
        frame = tk.Frame(master, bg=BG)
        card = self._panel(frame, '界面主题',
                           '点击“使用”立即切换主题；如果正在抽选，会在下一轮开始时生效。')
        self.theme_rows = {}
        for theme in themes.theme_list():
            row = tk.Frame(card, bg=PANEL, highlightthickness=1,
                           highlightbackground=BORDER)
            row.pack(fill=tk.X, padx=14, pady=(0, 8))

            swatch = tk.Frame(row, bg=theme['bg_top'], width=66, height=40,
                              highlightthickness=1, highlightbackground=BORDER)
            swatch.pack(side=tk.LEFT, padx=(8, 10), pady=8)
            swatch.pack_propagate(False)
            for i, color in enumerate((theme['accent'], theme['gold'],
                                       theme['text'])):
                tk.Frame(swatch, bg=color, width=14, height=14).place(
                    x=8 + i * 17, y=13)

            info = tk.Frame(row, bg=PANEL)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(info, text=theme['label'], bg=PANEL, fg=TEXT,
                     font=('微软雅黑', 10, 'bold')).pack(anchor=tk.W)
            tk.Label(info, text=theme['desc'], bg=PANEL, fg=MUTED,
                     font=SMALL_FONT).pack(anchor=tk.W)

            btn = FlatButton(row, DIM, DIM_HOVER, text='使用', width=6,
                             command=lambda tid=theme['id']: self._select_theme(tid))
            btn.pack(side=tk.RIGHT, padx=(8, 10))
            self.theme_rows[theme['id']] = (row, btn)
        self._refresh_theme_buttons()
        return frame

    def _refresh_theme_buttons(self):
        current = self.settings.get('theme', 'default')
        for theme_id, (_row, btn) in getattr(self, 'theme_rows', {}).items():
            try:
                if theme_id == current:
                    btn.configure(text='当前', bg=GREEN, fg='#ffffff',
                                  activebackground=GREEN_HOVER)
                else:
                    btn.configure(text='使用', bg=DIM, fg=TEXT,
                                  activebackground=DIM_HOVER)
            except tk.TclError:
                pass

    def _select_theme(self, theme_id):
        self.settings['theme'] = theme_id
        cfg.save_settings(self.settings)
        if hasattr(self.app, 'apply_settings'):
            self.app.apply_settings()
        self._refresh_theme_buttons()
        label = themes.get_palette(theme_id)['label']
        self._tip('主题已切换：%s' % label)

    # ---------------- 安全 ----------------
    def _build_security(self, master):
        frame = tk.Frame(master, bg=BG)
        card = self._panel(frame, '设置密码',
                           '设置界面入口需要密码；密码以加盐哈希形式保存在 '
                           'data/settings.json 中。')
        self.pwd_state_label = tk.Label(card, text='', bg=PANEL, fg=MUTED,
                                        font=SMALL_FONT, anchor=tk.W)
        self.pwd_state_label.pack(anchor=tk.W, padx=14, pady=(0, 8))

        self.var_old = tk.StringVar()
        self.var_new = tk.StringVar()
        self.var_new2 = tk.StringVar()
        self._entry_row(card, '当前密码', self.var_old, width=20, show='●')
        self._entry_row(card, '新密码', self.var_new, width=20, show='●')
        self._entry_row(card, '确认新密码', self.var_new2, width=20, show='●')

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(anchor=tk.W, padx=14, pady=(2, 14))
        FlatButton(actions, ACCENT, '#15678f', text='设置 / 修改密码',
                   command=self._change_password).pack(side=tk.LEFT)
        FlatButton(actions, RED, RED_HOVER, text='清空密码',
                   command=self._clear_password).pack(side=tk.LEFT, padx=(8, 0))

        about = self._panel(frame, '关于与数据文件', '')
        info = ('版本：ZADM 2.1.0\n'
                '名单文件：data/names.json\n'
                '设置文件：data/settings.json\n'
                '抽取历史：data/history.json\n'
                '特定人物概率区域密码：由内置规则固定保护')
        tk.Label(about, text=info, bg=PANEL, fg=MUTED, font=SMALL_FONT,
                 justify=tk.LEFT, anchor=tk.W).pack(anchor=tk.W, padx=14,
                                                    pady=(0, 14))
        self._refresh_security_state()
        return frame

    def _refresh_security_state(self):
        try:
            protected = (bool(self.settings.get('password_protected', True))
                         and cfg.has_password(self.settings))
            if protected:
                self.pwd_state_label.configure(text='当前状态：已开启密码保护',
                                               fg=GREEN)
            else:
                self.pwd_state_label.configure(
                    text='当前状态：未设置密码（进入设置无需密码）', fg=MUTED)
        except (tk.TclError, AttributeError):
            pass

    def _change_password(self):
        old = self.var_old.get()
        new = self.var_new.get()
        new2 = self.var_new2.get()
        has = cfg.has_password(self.settings)
        if has and not cfg.verify_password(self.settings, old):
            messagebox.showerror('密码错误', '当前密码不正确。', parent=self.master)
            return
        if len(new) < 2:
            messagebox.showwarning('密码太短', '新密码至少需要 2 个字符。',
                                   parent=self.master)
            return
        if new != new2:
            messagebox.showwarning('两次输入不一致', '两次输入的新密码不一致。',
                                   parent=self.master)
            return
        cfg.set_password(self.settings, new)
        self.settings['password_protected'] = True
        cfg.save_settings(self.settings)
        self.var_old.set('')
        self.var_new.set('')
        self.var_new2.set('')
        self._refresh_security_state()
        self._tip('设置密码已保存')
        messagebox.showinfo('已保存', '设置密码已保存，下次进入设置需要输入它。',
                            parent=self.master)

    def _clear_password(self):
        if not cfg.has_password(self.settings):
            messagebox.showinfo('提示', '当前没有设置密码。', parent=self.master)
            return
        if not messagebox.askyesno('清空密码',
                                   '确定要清空设置界面的密码吗？\n清空后进入设置将不再需要密码。',
                                   parent=self.master):
            return
        self.settings['password_hash'] = ''
        self.settings['password_salt'] = ''
        self.settings['password_protected'] = False
        cfg.save_settings(self.settings)
        self._refresh_security_state()
        self._tip('密码已清空')
        messagebox.showinfo('已保存', '设置密码已清空，下次进入设置不再需要密码。',
                            parent=self.master)

    # ---------------- 保存 / 关闭 ----------------
    def collect(self):
        try:
            self.settings['bag_mode'] = bool(self.var_bag.get())
            self.settings['auto_balance'] = bool(self.var_balance.get())
            self.settings['balance_strength'] = self.var_strength.get() / 100.0
            self.settings['roll_interval'] = self._speed_to_interval(self.var_speed.get())
            count = int(self.var_count.get())
            limit = max(1, min(cfg.MAX_DRAW, len(self.names) or 1))
            self.settings['draw_count'] = max(1, min(limit, count))
        except (tk.TclError, ValueError):
            pass

    def save_and_apply(self, notify=False):
        self.collect()
        cfg.save_settings(self.settings)
        if hasattr(self.app, 'apply_settings'):
            self.app.apply_settings()
        self._refresh_stats()
        if self.manual_unlocked:
            self._refresh_manual_probs()
        self._refresh_theme_buttons()
        self._refresh_security_state()
        self._tip('已保存并生效')
        if notify:
            messagebox.showinfo('已保存', '设置已保存并生效。', parent=self.master)

    def _tip(self, text):
        try:
            self.tip_label.configure(text=text)
            self.master.after(2600, self._clear_tip)
        except tk.TclError:
            pass

    def _clear_tip(self):
        try:
            self.tip_label.configure(text='')
        except tk.TclError:
            pass

    def close(self):
        try:
            self.save_and_apply()
        except tk.TclError:
            pass
        try:
            self.master.destroy()
        except tk.TclError:
            pass


# ---------------------------------------------------------------- 外部入口
_window = None


def open_settings(app):
    """打开设置窗口（密码校验通过后才创建）"""
    global _window
    try:
        if _window is not None and _window.winfo_exists():
            _window.lift()
            _window.focus_force()
            return
    except tk.TclError:
        pass

    if not _check_access(app.root):
        return

    win = tk.Toplevel(app.root)
    win.configure(bg=BG)
    try:
        win.iconbitmap(ICON_PATH)
    except Exception:
        pass
    win.settings_panel = SettingsWindow(win, app)
    win.lift()
    win.focus_force()
    try:
        win.attributes('-topmost', True)
        win.after(320, lambda: win.attributes('-topmost', False))
    except tk.TclError:
        pass
    _window = win
