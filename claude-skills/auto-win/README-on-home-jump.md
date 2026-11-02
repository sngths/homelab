# 自动化 Windows 机（VM 202）使用说明 —— 给任何机器上的 Claude 会话看

**始终用中文和用户交流**，包括工具调用之间的短句说明。

## 这是什么

- 家里 pve3 上的 VM 202，Windows 11，屏幕 1280x800，默认英文键盘。
- 装了 Bambu Studio，已登录拓竹账号 sngths，连着打印机 A1（`3DP-039-506`，AMS lite 4 槽，走拓竹云）。
- 操作方式：从虚拟机**外部**截屏、发送键盘鼠标（QEMU QMP），Windows 里没有自动化进程。
- 工具 `aw` 装在跳板机 home-jump 上，任何装了 wsd 的电脑都能调用。

## 用法（在你的电脑上执行，整条 aw 命令放在单引号里）

```bash
export no_proxy="$no_proxy,msg-gw.zczy.ai"   # 本机设了 HTTP 代理时需要

# 截屏取回（一条命令），然后用 Read 看图
wsd exec home-jump -- 'aw shot -' | base64 -d > /tmp/aw.jpg
# 裁剪放大看小字：X Y W H 倍数
wsd exec home-jump -- 'aw shot - --crop 860 80 380 330 2' | base64 -d > /tmp/z.jpg

# 一串动作，结束后等 1.5 秒截屏取回
wsd exec home-jump -- 'aw do "click 115 48" "wait 2" "key ctrl-i" --wait 1.5 --shot -' | base64 -d > /tmp/aw.jpg
# 只做动作不截屏
wsd exec home-jump -- 'aw do "key esc" --noshot'

# 输入 ASCII（路径里的反斜杠会保留）
wsd exec home-jump -- 'aw do "type C:\Users\auto\Desktop\in\a.stl" "key ret" --noshot'
# 输入中文：经剪贴板粘贴到当前焦点
wsd exec home-jump -- 'aw text "收纳盒"'

# 把你电脑上的文件放进虚拟机 C:\Users\auto\Desktop\in\（跳板机用 wsd get 拉取，你的机器要开放文件读取）
wsd exec home-jump -- 'aw put 你的机器名:相对用户目录的路径/model.stl'

# 在虚拟机里执行 PowerShell 管理命令
wsd exec home-jump -- 'aw ps "Get-Process bambu*"'
```

动作：`click X Y [left|right] [次数]`、`move X Y`、`type 文本`、`key 组合键`（如 `ret` `esc` `ctrl-v` `alt-f4`）、`scroll N`、`wait 秒`。

## 工作循环

截屏 → 看图找坐标（拿不准就裁剪放大）→ 执行动作并截屏 → 确认结果 → 下一步。不要盲点多步。

## 规矩

- **发送打印前必须先问用户确认。** 只切片可以直接做。
- 关机、重启虚拟机，删除文件，先征得用户同意。
- **同一时间只能有一个会话操作**，开始前先截屏，发现有别人在操作就停下来问用户。
- 不要在 Windows 里装任何自动化软件。

## Bambu Studio 要点（坐标仅供参考，以截图为准）

- 顶部标签：首页(20,48) 准备(115,48) 预览 设备(400,48)；右上"切片单盘"(1088,48)、"打印单盘"(1215,48)。
- 导入模型：准备页按 `ctrl-i`，在"文件名"框输入完整路径回车。
- 首页搜索框是嵌入网页，第一次点击只激活，要再点一次。
- 启动时可能弹"配置包更新"，点确认。

## 出问题时

链路：你的电脑 → wsd → home-jump（pve2 上的 CT 203，192.168.1.53）→ ssh pve3（`vminput` 发键鼠、截屏）/ ssh VM 202。
详细文档在 GitHub 私有仓库 sngths/homelab 的 `services/auto-win.md`、`services/home-jump.md`。
