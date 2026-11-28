# -*- coding: utf-8 -*-
"""ZADM 配置 / 抽取历史 / 概率引擎

集中管理三件事，供主界面和设置界面共用：

1. data/settings.json —— 用户设置（每轮人数、滚动间隔、不重复、均衡、密码、手动概率）
2. data/history.json  —— 每次抽取的结果记录，用于自动平衡概率
3. 概率计算 —— 平均概率 → 历史均衡 → 特定人物手动概率（手动优先）
"""

import hashlib
import json
import os
import random
import secrets
from datetime import datetime

# ---------------------------------------------------------------- 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
NAMES_PATH = os.path.join(DATA_DIR, 'names.json')
SETTINGS_PATH = os.path.join(DATA_DIR, 'settings.json')
HISTORY_PATH = os.path.join(DATA_DIR, 'history.json')

# 特定人物概率区域的固定密码（设置界面入口密码由用户自行设置）
MANUAL_PASSWORD = 'tr520'

MAX_DRAW = 10          # 每轮最多抽取人数
HISTORY_LIMIT = 5000   # 历史最多保留的记录条数

DEFAULT_SETTINGS = {
    'draw_count': 1,          # 每轮抽取人数
    'roll_interval': 45,      # 姓名滚动间隔（毫秒），越小越快
    'bag_mode': True,         # 不重复模式
    'auto_balance': True,     # 按历史自动均衡概率
    'balance_strength': 1.0,  # 均衡强度（0 ~ 2）
    'password_hash': '',      # 设置界面密码（加盐 SHA-256）
    'password_salt': '',
    'password_protected': True,   # 是否启用设置界面密码
    'manual_probs': {},       # 特定人物概率（百分比，覆盖均衡/平均）
    'theme': 'default',       # 界面主题：default / circuit / sakura / minimal
}


# ---------------------------------------------------------------- 基础读写
def _ensure_data_dir():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except OSError:
        pass


def _read_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return default


def _write_json(path, data):
    """先写临时文件再替换，避免写一半时崩溃导致配置文件损坏"""
    _ensure_data_dir()
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False


def clamp(value, low, high, default):
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def clamp_float(value, low, high, default):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


# ---------------------------------------------------------------- 设置
def _normalize_settings(raw):
    s = dict(DEFAULT_SETTINGS)
    if not isinstance(raw, dict):
        return s
    s['draw_count'] = clamp(raw.get('draw_count', 1), 1, MAX_DRAW, 1)
    s['roll_interval'] = clamp(raw.get('roll_interval', 45), 10, 400, 45)
    s['bag_mode'] = bool(raw.get('bag_mode', True))
    s['auto_balance'] = bool(raw.get('auto_balance', True))
    s['balance_strength'] = round(clamp_float(raw.get('balance_strength', 1.0),
                                              0.0, 2.0, 1.0), 3)
    s['password_hash'] = str(raw.get('password_hash') or '')
    s['password_salt'] = str(raw.get('password_salt') or '')
    s['password_protected'] = bool(raw.get('password_protected', True))
    s['theme'] = str(raw.get('theme') or 'default')
    probs = {}
    manual = raw.get('manual_probs')
    if isinstance(manual, dict):
        for name, value in manual.items():
            try:
                pct = float(value)
            except (TypeError, ValueError):
                continue
            if pct > 0:
                probs[str(name)] = round(min(pct, 100.0), 3)
    s['manual_probs'] = probs
    return s


def load_settings():
    return _normalize_settings(_read_json(SETTINGS_PATH, {}))


def save_settings(settings):
    return _write_json(SETTINGS_PATH, _normalize_settings(settings))


def update_settings(**changes):
    """局部更新并落盘，返回更新后的完整设置"""
    settings = load_settings()
    settings.update(changes)
    settings = _normalize_settings(settings)
    save_settings(settings)
    return settings


# ---------------------------------------------------------------- 密码
def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


def has_password(settings=None):
    settings = settings if settings is not None else load_settings()
    return bool(settings.get('password_hash'))


def set_password(settings, password):
    """在设置字典中写入新密码（需自行 save_settings）"""
    salt = secrets.token_hex(8)
    settings['password_salt'] = salt
    settings['password_hash'] = _hash_password(password, salt)


def verify_password(settings, password):
    salt = settings.get('password_salt') or ''
    expected = settings.get('password_hash') or ''
    if not expected:
        return False
    return secrets.compare_digest(_hash_password(password, salt), expected)


# ---------------------------------------------------------------- 历史记录
def load_history():
    data = _read_json(HISTORY_PATH, [])
    entries = []
    if not isinstance(data, list):
        return entries
    for item in data:
        if isinstance(item, dict) and isinstance(item.get('names'), list):
            names = [str(n).strip() for n in item['names'] if str(n).strip()]
            if names:
                entries.append({
                    'time': str(item.get('time') or ''),
                    'names': names,
                    'mode': str(item.get('mode') or ''),
                })
        elif isinstance(item, str) and item.strip():
            # 兼容极简格式：["张三", "李四"]
            entries.append({'time': '', 'names': [item.strip()], 'mode': ''})
    return entries


def save_history(entries):
    entries = list(entries)[-HISTORY_LIMIT:]
    return _write_json(HISTORY_PATH, entries)


def append_history(names, mode=''):
    """追加一次抽取记录"""
    entries = load_history()
    entries.append({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'names': [str(n) for n in names],
        'mode': mode,
    })
    save_history(entries)
    return entries


def reset_history():
    return save_history([])


def history_counts(names=None, entries=None):
    """统计每个人的累计被抽中次数（只统计仍在名单中的人）"""
    entries = load_history() if entries is None else entries
    counts = {}
    for entry in entries:
        for name in entry.get('names', []):
            if names is not None and name not in names:
                continue
            counts[name] = counts.get(name, 0) + 1
    return counts


def history_summary(names, entries=None):
    """返回用于设置界面展示的统计信息"""
    entries = load_history() if entries is None else entries
    names = list(names)
    counts = history_counts(names, entries)
    total = sum(counts.values())
    values = [counts.get(n, 0) for n in names]
    if not values:
        return {'total': total, 'rounds': len(entries), 'avg': 0.0,
                'max': 0, 'min': 0, 'max_name': '', 'min_name': '', 'counts': counts}
    most = max(values)
    least = min(values)
    return {
        'total': total,
        'rounds': len(entries),
        'avg': total / float(len(values)),
        'max': most,
        'min': least,
        'max_name': next(n for n in names if counts.get(n, 0) == most),
        'min_name': next(n for n in names if counts.get(n, 0) == least),
        'counts': counts,
    }


# ---------------------------------------------------------------- 概率
def average_probability(names):
    return 100.0 / float(len(names)) if names else 0.0


def compute_probabilities(names, settings=None, entries=None):
    """计算每个人的中签概率（百分比，总和 100）

    优先级：特定人物手动概率 > 历史均衡 / 平均概率
        · 手动概率是"绝对百分比"，直接从 100% 中切走
        · 剩余概率按历史次数做均衡：抽得越少，权重越大
        · 关闭均衡（或强度为 0）时，剩余概率平均分配
    """
    names = [n for n in names if str(n).strip()]
    if not names:
        return {}
    settings = load_settings() if settings is None else settings
    entries = load_history() if entries is None else entries

    manual = {}
    raw = settings.get('manual_probs') or {}
    for name in names:
        try:
            pct = float(raw.get(name, 0) or 0)
        except (TypeError, ValueError):
            pct = 0.0
        if pct > 0:
            manual[name] = pct

    manual_total = sum(manual.values())
    if manual_total >= 100.0:
        # 手动概率合计已满，按比例归一（保证总和 100）
        return {name: manual.get(name, 0.0) / manual_total * 100.0
                for name in names}

    counts = history_counts(names, entries)
    total_draws = sum(counts.values())
    auto = bool(settings.get('auto_balance', True))
    strength = clamp_float(settings.get('balance_strength', 1.0), 0.0, 2.0, 1.0)

    weights = {}
    for name in names:
        if name in manual:
            continue
        weight = 1.0
        if auto and strength > 0 and total_draws > 0:
            expected = total_draws / float(len(names))
            weight = ((expected + 1.0) / (counts.get(name, 0) + 1.0)) ** strength
        weights[name] = weight

    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        for name in weights:
            weights[name] = 1.0
        weight_sum = float(len(weights)) or 1.0

    remaining = max(0.0, 100.0 - manual_total)
    probs = {}
    for name in names:
        if name in manual:
            probs[name] = manual[name]
        else:
            probs[name] = remaining * weights.get(name, 0.0) / weight_sum
    return probs


def weighted_pick(candidates, probs):
    """按概率从候选名单中挑一个（概率缺失时按 1 处理）"""
    if not candidates:
        return None
    weights = [max(float(probs.get(n, 0.0)), 1e-9) for n in candidates]
    total = sum(weights)
    point = random.random() * total
    acc = 0.0
    for name, weight in zip(candidates, weights):
        acc += weight
        if point <= acc:
            return name
    return candidates[-1]


def format_percent(value):
    return '%.2f%%' % value
