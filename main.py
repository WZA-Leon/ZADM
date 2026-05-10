import random as r
import tkinter as t
import os
import json



# 导入代码查看模块
import code_viewer

#导入修改名单模块
import name_manager



# ---------- 1. 从 JSON 文件加载姓名列表 ----------
names = []
json_path = r'data\names.json'
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        names = json.load(f)
except FileNotFoundError:
    names = ["张三", "李四", "王五", "赵六"]   # 你原先的默认名单
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(names, f, ensure_ascii=False, indent=2)

# ---------- 2. 创建主窗口 ----------
w = t.Tk()
w.geometry('1000x600')
w.title('ZADM 1.2.4')
# 如果图标文件存在则设置，否则忽略
try:
    w.iconbitmap(r'data/zadm.ico')
except:
    pass
w.lift()
w.resizable(False, False)

# ---------- 3. 标题 ----------
title = t.Label(w, text='由WZA设计制作', font=('华文中宋', 30), fg='navy')
title.pack(pady=(20, 10))

# ---------- 4. 滚动名字标签 ----------
rolling_name = t.Label(w, text='点击开始', font=('华文中宋', 50), fg='cornflowerblue')
rolling_name.place(relx=0.5, y=200, anchor='n')   # 初始显示在窗口中间

# ---------- 5. 结果标签（初始隐藏）----------
result_name = t.Label(w, text='', font=('华文中宋', 50), fg='mediumaquamarine')
# 初始不放置，等到停止时才显示

# ---------- 6. 控制滚动的变量 ----------
after_id = None
running = False

def scroll_name():
    p = r.randint(0, len(names) - 1)
    rolling_name.config(text=names[p])
    global after_id
    after_id = rolling_name.after(50, scroll_name)

def next_p():
    global running, after_id
    if not running:
        running = True
        result_name.place_forget()               # 隐藏结果标签
        rolling_name.place(relx=0.5, y=200, anchor='n')   # 用相对定位
        nameb.place_forget()
        stopb.place(x=70, y=430)
        scroll_name()

def stop():
    global running, after_id
    if running:
        if after_id is not None:
            rolling_name.after_cancel(after_id)
            after_id = None
        running = False
        chosen = rolling_name.cget('text')
        rolling_name.place_forget()
        result_name.config(text=chosen)
        result_name.place(relx=0.5, y=200, anchor='n')    # 用相对定位
        stopb.place_forget()
        nameb.place(x=70, y=430)# ---------- 按钮 ----------
nameb = t.Button(w, text='点名', width=20, bg='azure', font=('华文中宋', 50), command=next_p)
nameb.place(x=70, y=430)

stopb = t.Button(w, text='停止', width=20, bg='azure', font=('华文中宋', 50), command=stop)
# 初始不放置

#==============修改名单===============
def open_manager():
    name_manager.open_name_manager(json_path)

nt = t.Button(w, text='修改/查看名单', font=('华文中宋', 15), command=open_manager)
nt.place(x=850, y=0)

# ---------- 查看代码按钮（调用 code_viewer 模块）----------
def show_code():
    # 传递当前脚本的路径
    code_viewer.show_code_window(__file__)

dm = t.Button(w, text='查看代码', font=('华文中宋', 15), command=show_code)
dm.place(x=850, y=50)

w.mainloop()
