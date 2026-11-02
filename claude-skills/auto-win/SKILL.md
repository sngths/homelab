---
name: auto-win
description: 操作家里的自动化 Windows 虚拟机（VM 202，192.168.1.52，跑 Bambu Studio 连拓竹 A1 打印机）。用户要求点 Windows 界面、用 Bambu Studio 切片/打印、看打印机状态，或者"用那台自动化机器"时使用。通过截屏看图 + 外部键鼠操作。
---

# 自动化 Windows 机（VM 202）使用说明

**始终用中文和用户交流**，包括工具调用之间的短句说明。

详细背景见 `~/projects/homelab/services/auto-win.md`（必要时再读）。

## 这台机器

- pve3 上的 VM 202，Windows 11 25H2，账号 auto（密码见 `~/projects/homelab/credentials.md`）。
- 已装 Bambu Studio 02.08，已登录拓竹账号 sngths，打印机 A1（`3DP-039-506`，带 AMS lite 4 槽）通过拓竹云连接。
- 屏幕 1280x800。默认输入法是英文键盘。

## 工具：`aw`（已在 PATH，任意目录可用）

```bash
aw shot /tmp/aw.jpg                              # 全屏截图，然后用 Read 看图
aw shot /tmp/z.jpg --crop X Y W H 2              # 裁剪并放大 2 倍，看小字、确认细节
aw do "click 640 272" "wait 1" "key ctrl-a" --wait 1.5 --shot /tmp/aw.jpg   # 一串动作后截屏
aw do 'type C:\Users\auto\Desktop\in\a.stl' "key ret" --noshot              # 输入 ASCII（保留反斜杠）
aw text "中文内容"                               # 中文/任意文本：经剪贴板 Ctrl+V 粘贴到当前焦点
aw put ./model.stl                               # 文件复制到虚拟机 C:\Users\auto\Desktop\in\
aw ps "Get-Process bambu*"                       # 虚拟机里执行 PowerShell 管理命令
```

动作：`click X Y [left|right] [次数]`、`move X Y`、`type 文本`、`key 组合键`（qcode，如 `ret` `esc` `ctrl-v` `alt-f4` `meta_l`）、`scroll N`（正数向下）、`wait 秒`。

## 工作循环

1. `aw shot` → Read 看图 → 判断坐标；拿不准就 `--crop` 放大再看。
2. `aw do ...` 执行动作，自动截屏，再 Read 确认结果。
3. 每一步都确认后再继续，不要盲点多步。

## 规矩

- **发送打印前必须先问用户确认**（耗材、时间、打印机上有没有东西）。只切片可以直接做。
- 关机、重启虚拟机，删除文件，先征得用户同意。
- **同一时间只能有一个会话操作这台机器**，开始前先截屏，看到有别人正在操作的迹象就停下来问用户。
- 不要在 Windows 里装自动化软件（按键精灵、pyautogui 等），键鼠一律走 `aw`（从虚拟机外部发送）。
- 改了虚拟机配置要更新 `~/projects/homelab/services/auto-win.md` 并提交推送。

## Bambu Studio 操作要点

- 顶部标签：首页(20,48) 准备(115,48) 预览 设备(400,48)，右上"切片单盘"(1088,48)、"打印单盘"(1215,48)。坐标仅供参考，以截图为准。
- 导入模型：准备页按 `ctrl-i`，在"文件名"框输入完整路径后回车。
- 首页搜索框是嵌入网页，第一次点击只激活，要再点一次才能输入。
- 启动时可能弹"配置包更新"，点确认即可。

## 链路（出问题时排查用）

本机 → `wsd exec` 到 Windows 台式机 `DESKTOP-0GE8DG9`（192.168.1.117，必须开机）→ ssh 到 pve3（192.168.1.3，`vminput` 走 QMP 发键鼠、截屏）或 VM 202（OpenSSH）。
工具源码：`~/projects/homelab/scripts/aw.py`、`scripts/vminput.py`（pve3 上是 `/usr/local/bin/vminput`）。
