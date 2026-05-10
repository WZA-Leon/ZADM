import tkinter as tk
from tkinter import messagebox
import json
import os

class NameManager:
    def __init__(self, master, json_path):
        self.master = master
        self.json_path = json_path
        self.names = []
        self.check_vars = []  # 存储每个姓名的 BooleanVar

        # 先加载数据
        self.load_names()

        # 创建界面
        self.create_widgets()
        self.refresh_list()   # 填充初始列表

    def load_names(self):
        """从 JSON 文件加载名单"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.names = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.names = []

    def save_names(self):
        """将名单保存回 JSON 文件"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.names, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def create_widgets(self):
        """搭建界面"""
        self.master.title("姓名管理")

        # ---- 批量添加区域 ----
        add_frame = tk.LabelFrame(self.master, text="批量添加（每行一个姓名）", padx=5, pady=5)
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        self.text_input = tk.Text(add_frame, height=8, width=40, font=("微软雅黑", 11))
        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(add_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(5, 0))

        add_btn = tk.Button(btn_frame, text="添加到名单", command=self.add_names, bg="#4CAF50", fg="white",
                            font=("微软雅黑", 11), width=10)
        add_btn.pack(pady=5)

        # ---- 列表展示区域 ----
        list_frame = tk.LabelFrame(self.master, text="当前名单（勾选后点击删除）", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Canvas + Scrollbar 实现滚动
        self.canvas = tk.Canvas(list_frame, bg="white", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	

	    # ---------- 绑定鼠标滚轮 ----------
        def _on_mousewheel(event):
            # Windows / macOS
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                # Linux: Button-4 向上，Button-5 向下
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")

        # 绑定到 Canvas 和内部的 scrollable_frame（让滚轮在整个列表区域都有效）
        self.canvas.bind("<MouseWheel>", _on_mousewheel)      # Windows/macOS
        self.scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        # Linux 滚轮事件
        self.canvas.bind("<Button-4>", lambda e: _on_mousewheel(e))
        self.canvas.bind("<Button-5>", lambda e: _on_mousewheel(e))
        self.scrollable_frame.bind("<Button-4>", lambda e: _on_mousewheel(e))
        self.scrollable_frame.bind("<Button-5>", lambda e: _on_mousewheel(e))


        # ---- 底部操作按钮 ----
        bottom_frame = tk.Frame(self.master)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        delete_btn = tk.Button(bottom_frame, text="删除选中", command=self.delete_selected,
                               bg="#f44336", fg="white", font=("微软雅黑", 11), width=10)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))

        refresh_btn = tk.Button(bottom_frame, text="刷新列表", command=self.refresh_list,
                                bg="#2196F3", fg="white", font=("微软雅黑", 11), width=10)
        refresh_btn.pack(side=tk.LEFT)

    def refresh_list(self):
        """刷新界面中的姓名列表（重新加载文件并重建复选框）"""
        # 清除旧控件
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()

        # 重新加载文件（以防外部修改）
        self.load_names()

        # 为每个姓名创建一行（复选框 + 标签）
        for i, name in enumerate(self.names):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(self.scrollable_frame, text=name, variable=var,
                                font=("微软雅黑", 11), bg="white", anchor="w")
            cb.pack(fill=tk.X, padx=5, pady=2)
            self.check_vars.append((name, var))

    def add_names(self):
        """处理批量添加"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            return

        new_names = [line.strip() for line in text.splitlines()]
        new_names = [n for n in new_names if n]  # 滤空

        if not new_names:
            return

        # 去重
        added = 0
        for name in new_names:
            if name not in self.names:
                self.names.append(name)
                added += 1

        if added == 0:
            messagebox.showinfo("提示", "没有新姓名添加（全部已存在）。")
        else:
            self.save_names()
            self.text_input.delete("1.0", tk.END)  # 清空输入框
            self.refresh_list()
            messagebox.showinfo("成功", f"成功添加 {added} 个姓名。")

    def delete_selected(self):
        """批量删除选中的姓名"""
        selected_names = [name for name, var in self.check_vars if var.get()]
        if not selected_names:
            messagebox.showinfo("提示", "请至少勾选一个姓名。")
            return

        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_names)} 个姓名吗？"):
            for name in selected_names:
                if name in self.names:
                    self.names.remove(name)
            self.save_names()
            self.refresh_list()
            messagebox.showinfo("完成", f"已删除 {len(selected_names)} 个姓名。")


def open_name_manager(json_path):
    """外部调用的接口：弹出姓名管理窗口"""
    win = tk.Toplevel()
    win.geometry("500x600")
    win.resizable(True, True)
    app = NameManager(win, json_path)
    win.lift()
    win.focus_force()
    # 如果图标文件存在则设置，否则忽略
    try:
        win.iconbitmap(r'data/zadm.ico')
    except:
        pass