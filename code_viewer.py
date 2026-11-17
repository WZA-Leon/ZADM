# -*- coding: utf-8 -*-
"""ZADM 代码查看器：只读展示源码，带浅色主题语法高亮"""

import os
import re
import tkinter as tk

# ---------------------------------------------------------------- 配色
BG = '#ffffff'
FG = '#1f2328'
SELECT_BG = '#b9dcff'
INSERT_BG = '#1f2328'

# 标签样式：颜色 + 字体样式
TAG_STYLE = {
    'keyword': ('#0b5cad', 'bold'),
    'builtin': ('#795e26', None),
    'string': ('#a31515', None),
    'comment': ('#008000', 'italic'),
    'number': ('#098658', None),
}

KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
]

BUILTINS = [
    "print", "len", "range", "int", "str", "float", "list", "dict", "tuple", "set",
    "open", "input", "type", "dir", "help", "map", "filter", "zip", "enumerate",
    "sorted", "reversed", "bool", "abs", "sum", "min", "max", "round", "format",
    "hex", "oct", "bin", "chr", "ord", "super", "isinstance", "issubclass",
    "hasattr", "getattr", "setattr", "delattr", "staticmethod", "classmethod",
    "property", "__import__",
]


def _highlight(text_widget, code):
    """用 Python 正则扫描全文，再按字符偏移给 Text 打标签。

    这样做避免了 Tcl 正则不支持后行断言（(?<!...)）以及
    跨行三引号字符串难以取到匹配长度的问题。
    """
    for tag, (color, style) in TAG_STYLE.items():
        font = ('Consolas', 11, style) if style else ('Consolas', 11)
        text_widget.tag_config(tag, foreground=color, font=font)

    def add(tag, pattern, flags=0, skip=()):
        for match in re.finditer(pattern, code, flags):
            start = '1.0 + %dc' % match.start()
            end = '1.0 + %dc' % match.end()
            if skip and any(t in text_widget.tag_names(start) for t in skip):
                continue
            text_widget.tag_add(tag, start, end)

    # 1. 三引号字符串（可跨行）
    add('string', r'"""(?:.*?)"""|\'\'\'(?:.*?)\'\'\'', re.S)
    # 2. 单行字符串（保留转义字符，跳过已标记部分）
    add('string', r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', 0, ('string',))
    # 3. 注释
    add('comment', r'#[^\n]*', 0, ('string',))
    # 4. 关键字与内置函数（不覆盖字符串 / 注释）
    add('keyword', r'\b(?:%s)\b' % '|'.join(re.escape(k) for k in KEYWORDS),
        0, ('string', 'comment'))
    add('builtin', r'\b(?:%s)\b' % '|'.join(re.escape(k) for k in BUILTINS),
        0, ('keyword', 'string', 'comment'))
    # 5. 数字
    add('number', r'\b\d+(?:\.\d+)?\b', 0, ('string', 'comment'))


def show_code_window(file_path):
    """弹出一个新窗口，只读显示 file_path 的源码并高亮"""
    abs_path = os.path.abspath(file_path)
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        code = '无法读取文件:\n%s\n\n%s' % (abs_path, e)

    win = tk.Toplevel()
    win.title('源代码 - %s' % os.path.basename(abs_path))
    win.geometry('800x600')
    win.resizable(True, True)
    win.configure(bg=BG)
    try:
        win.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'data', 'zadm.ico'))
    except Exception:
        pass

    text_frame = tk.Frame(win, bg=BG)
    text_frame.pack(fill=tk.BOTH, expand=True)

    text_widget = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 11),
                          bg=BG, fg=FG, insertbackground=INSERT_BG,
                          selectbackground=SELECT_BG, relief=tk.FLAT, bd=0,
                          padx=10, pady=10)
    v_scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    h_scroll = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
    text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    text_widget.grid(row=0, column=0, sticky='nsew')
    v_scroll.grid(row=0, column=1, sticky='ns')
    h_scroll.grid(row=1, column=0, sticky='ew')
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)

    text_widget.insert(tk.END, code)
    _highlight(text_widget, code)

    # 只读
    text_widget.config(state=tk.DISABLED)

    win.lift()
    win.focus_force()