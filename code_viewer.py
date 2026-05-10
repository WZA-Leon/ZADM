import tkinter as tk
from tkinter import scrolledtext
import re
import os

def show_code_window(file_path):
    """弹出一个新窗口，显示 file_path 的 Python 源代码，并带语法高亮"""
    # 读取源文件内容
    abs_path = os.path.abspath(file_path)
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        code = f"无法读取文件:\n{abs_path}\n\n{e}"

    # 创建顶层窗口
    win = tk.Toplevel()
    win.title(f"源代码 - {os.path.basename(abs_path)}")
    win.geometry("800x600")
    win.resizable(True, True)
    # 如果图标文件存在则设置，否则忽略
    try:
        win.iconbitmap(r'data/zadm.ico')
    except:
        pass


    # 创建一个带滚动条的文本框
    text_frame = tk.Frame(win)
    text_frame.pack(fill=tk.BOTH, expand=True)

    text_widget = tk.Text(text_frame, wrap=tk.NONE, font=("Consolas", 11), bg="#1e1e1e", fg="#d4d4d4",
                          insertbackground="white", padx=10, pady=10)
    v_scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    h_scroll = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
    text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    # 网格布局
    text_widget.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    h_scroll.grid(row=1, column=0, sticky="ew")
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)

    # 插入代码文本
    text_widget.insert(tk.END, code)

    # ---------- 定义高亮样式 ----------
    # 关键字：蓝色、加粗
    text_widget.tag_config("keyword", foreground="#569CD6", font=("Consolas", 11, "bold"))
    # 内置函数：紫色
    text_widget.tag_config("builtin", foreground="#C586C0")
    # 字符串：橙色
    text_widget.tag_config("string", foreground="#CE9178")
    # 注释：绿色、斜体
    text_widget.tag_config("comment", foreground="#6A9955", font=("Consolas", 11, "italic"))
    # 数字：浅绿
    text_widget.tag_config("number", foreground="#B5CEA8")

    # ---------- 高亮逻辑 ----------
    # 关键字和内置函数列表
    KEYWORDS = [
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield"
    ]
    BUILTINS = [
        "print", "len", "range", "int", "str", "float", "list", "dict", "tuple", "set",
        "open", "input", "type", "dir", "help", "map", "filter", "zip", "enumerate",
        "sorted", "reversed", "bool", "abs", "sum", "min", "max", "round", "format",
        "hex", "oct", "bin", "chr", "ord", "super", "isinstance", "issubclass",
        "hasattr", "getattr", "setattr", "delattr", "staticmethod", "classmethod",
        "property", "__import__"
    ]

    # 获取全部文本内容
    code_text = text_widget.get("1.0", tk.END)

    # 辅助函数：标记指定模式
    def mark_pattern(pattern, tag, start="1.0", end=tk.END, regexp=True, stop_tag=None):
        """在指定范围内查找模式并应用 tag，可指定 stop_tag 避免覆盖已标记区域"""
        text_widget.mark_set("matchStart", start)
        text_widget.mark_set("matchEnd", start)
        while True:
            if regexp:
                # 使用正则搜索
                pos = text_widget.search(pattern, "matchEnd", end, regexp=True, stopindex=end)
                if not pos:
                    break
                # 获取匹配长度
                match = re.match(pattern, text_widget.get(pos, f"{pos} lineend+1c"))
                if match:
                    match_end = f"{pos}+{len(match.group())}c"
                else:
                    match_end = f"{pos}+1c"
            else:
                # 精确文本搜索（备用，这里主要用正则）
                pos = text_widget.search(pattern, "matchEnd", end, stopindex=end)
                if not pos:
                    break
                match_end = f"{pos}+{len(pattern)}c"

            # 检查是否被 stop_tag 占据
            if stop_tag is None or not text_widget.tag_names(pos).count(stop_tag):
                text_widget.tag_add(tag, pos, match_end)
            text_widget.mark_set("matchEnd", match_end)

    # 1. 先标记三引号字符串（多行）
    triple_str_pattern = r'("""|\'\'\')(.|\n)*?\1'
    mark_pattern(triple_str_pattern, "string")

    # 2. 标记普通字符串（单双引号）
    # 注意：避免匹配到三引号内部，这里简单处理：如果某个位置已经有 string 标签，就跳过
    single_str_pattern = r"(?<!\\)\".*?(?<!\\)\"|(?<!\\)\'.*?(?<!\\)\'"
    mark_pattern(single_str_pattern, "string", stop_tag="string")

    # 3. 标记注释（从 # 到行尾）
    comment_pattern = r"#.*$"
    mark_pattern(comment_pattern, "comment", regexp=True, stop_tag="string")

    # 4. 标记关键字和内置函数（必须完整单词）
    for kw in KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        mark_pattern(pattern, "keyword", stop_tag="string")
    for built in BUILTINS:
        pattern = r"\b" + re.escape(built) + r"\b"
        mark_pattern(pattern, "builtin", stop_tag="string")

    # 5. 标记数字（可选）
    number_pattern = r"\b\d+(\.\d+)?\b"
    mark_pattern(number_pattern, "number", stop_tag="string")

    # 设置文本框为只读，并禁用编辑
    text_widget.config(state=tk.DISABLED)

    # 窗口置顶并聚焦
    win.lift()
    win.focus_force()