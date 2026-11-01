#!/usr/bin/env python3
"""从虚拟机外部（QEMU QMP）发送键盘、鼠标事件。对 Windows 来说就是真实的 USB 键盘鼠标。

用法（在 PVE 节点上）：
  vminput.py <vmid> type "文本"            逐字输入（只支持 ASCII），字符间随机停顿
  vminput.py <vmid> key ctrl-shift-ret     组合键（qcode 名，用 - 连接）
  vminput.py <vmid> move X Y               鼠标沿曲线移动到屏幕坐标 (X, Y)
  vminput.py <vmid> click X Y [left|right] [2]   移动后点击（可双击）
  vminput.py <vmid> scroll N               滚轮，正数向下
屏幕尺寸用 --screen WxH 指定（默认 1280x800）。
"""
import json, math, os, random, socket, sys, time

SHIFTED = {'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
           '_': 'minus', '+': 'equal', '{': 'bracket_left', '}': 'bracket_right', '|': 'backslash',
           ':': 'semicolon', '"': 'apostrophe', '<': 'comma', '>': 'dot', '?': 'slash', '~': 'grave_accent'}
PLAIN = {' ': 'spc', '-': 'minus', '=': 'equal', '[': 'bracket_left', ']': 'bracket_right', '\\': 'backslash',
         ';': 'semicolon', "'": 'apostrophe', ',': 'comma', '.': 'dot', '/': 'slash', '`': 'grave_accent',
         '\n': 'ret', '\t': 'tab'}
STATE = '/run/vminput-%s.pos'


class QMP:
    def __init__(self, vmid):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.connect('/var/run/qemu-server/%s.qmp' % vmid)
        self.f = self.s.makefile('rw')
        self.f.readline()
        self.cmd('qmp_capabilities')

    def cmd(self, name, args=None):
        self.f.write(json.dumps({'execute': name, **({'arguments': args} if args else {})}) + '\n')
        self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if 'return' in r or 'error' in r:
                if 'error' in r:
                    raise RuntimeError(r['error'])
                return r['return']

    def events(self, ev):
        self.cmd('input-send-event', {'events': ev})


def keyev(q, down):
    return {'type': 'key', 'data': {'down': down, 'key': {'type': 'qcode', 'data': q}}}


def combo(qmp, spec):
    keys = spec.split('-')
    for k in keys:
        qmp.events([keyev(k, True)]); time.sleep(random.uniform(0.03, 0.07))
    for k in reversed(keys):
        qmp.events([keyev(k, False)]); time.sleep(random.uniform(0.02, 0.05))


def type_text(qmp, text):
    for ch in text:
        if ch.isalpha() and ch.isascii():
            spec = ('shift-' if ch.isupper() else '') + ch.lower()
        elif ch.isdigit():
            spec = ch
        elif ch in SHIFTED:
            spec = 'shift-' + SHIFTED[ch]
        elif ch in PLAIN:
            spec = PLAIN[ch]
        else:
            raise SystemExit('不支持的字符: %r' % ch)
        combo(qmp, spec)
        time.sleep(random.uniform(0.04, 0.16))


def move(qmp, vmid, x, y, sw, sh):
    try:
        x0, y0 = map(float, open(STATE % vmid).read().split())
    except Exception:
        x0, y0 = sw / 2, sh / 2
    dist = math.hypot(x - x0, y - y0)
    steps = max(8, int(dist / 18))
    # 二次贝塞尔曲线，控制点随机偏移，速度先快后慢
    cx = (x0 + x) / 2 + random.uniform(-0.25, 0.25) * dist
    cy = (y0 + y) / 2 + random.uniform(-0.25, 0.25) * dist
    for i in range(1, steps + 1):
        t = i / steps
        t = 1 - (1 - t) ** 2
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y
        qmp.events([{'type': 'abs', 'data': {'axis': 'x', 'value': int(px / sw * 32767)}},
                    {'type': 'abs', 'data': {'axis': 'y', 'value': int(py / sh * 32767)}}])
        time.sleep(random.uniform(0.006, 0.016))
    open(STATE % vmid, 'w').write('%f %f' % (x, y))


def click(qmp, button='left', times=1):
    for _ in range(times):
        qmp.events([{'type': 'btn', 'data': {'down': True, 'button': button}}])
        time.sleep(random.uniform(0.05, 0.11))
        qmp.events([{'type': 'btn', 'data': {'down': False, 'button': button}}])
        time.sleep(random.uniform(0.08, 0.15))


def main():
    a = sys.argv[1:]
    sw, sh = 1280, 800
    if '--screen' in a:
        i = a.index('--screen'); sw, sh = map(int, a[i + 1].split('x')); del a[i:i + 2]
    vmid, op, rest = a[0], a[1], a[2:]
    q = QMP(vmid)
    if op == 'type':
        type_text(q, rest[0])
    elif op == 'key':
        combo(q, rest[0])
    elif op == 'move':
        move(q, vmid, float(rest[0]), float(rest[1]), sw, sh)
    elif op == 'click':
        move(q, vmid, float(rest[0]), float(rest[1]), sw, sh)
        time.sleep(random.uniform(0.08, 0.2))
        click(q, rest[2] if len(rest) > 2 else 'left', int(rest[3]) if len(rest) > 3 else 1)
    elif op == 'scroll':
        n = int(rest[0])
        for _ in range(abs(n)):
            q.events([{'type': 'btn', 'data': {'down': True, 'button': 'wheel-down' if n > 0 else 'wheel-up'}}])
            q.events([{'type': 'btn', 'data': {'down': False, 'button': 'wheel-down' if n > 0 else 'wheel-up'}}])
            time.sleep(random.uniform(0.05, 0.12))
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
