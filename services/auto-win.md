# Windows 自动化操作机（VM 202）

2026-11-01 创建。专门用来自动化操作**没有接口、只能点界面的软件**（微信、Bambu Studio 等）。

## 设计原则

- **虚拟机里只装普通软件，不装自动化程序。** 截屏和鼠标键盘控制都从虚拟机**外面**（PVE / QEMU）做：
  - 截屏：`qm monitor` 的 `screendump`（脚本见下）
  - 键盘：`qm sendkey <vmid> <键>`，或 QMP 的 `input-send-event`
  - 鼠标：QMP `input-send-event`（tablet 绝对坐标）
- 这样 Windows 看到的是"真实的 USB 键盘鼠标"在操作，没有 SendInput 产生的"程序注入"标记；虚拟机里也找不到自动化进程。
- 不往微信等软件里注入代码、不读内存。
- 行为要像人：鼠标有轨迹、操作间隔随机、控制频率。

## 虚拟机

| 项目 | 内容 |
|---|---|
| VMID / 名称 | 202 / auto-win，在 pve3 上，开机自启 |
| 系统 | Windows 11 专业版 **25H2**（build 26200.9711）简体中文，用 24H2 官方镜像安装后于 2026-11-02 通过 Windows 更新升级，**未激活**（用户自己处理） |
| 配置 | 8 核 / 16G（关闭 balloon）/ 150G |
| CPU | `host,hidden=1`（隐藏 KVM 特征） |
| 硬盘 / 网卡 | SATA / Intel e1000e：用 Windows 自带驱动，不出现 "Red Hat VirtIO" 设备 |
| 固件 | OVMF（UEFI）+ 安全启动 + TPM 2.0 |
| IP | 192.168.1.52（固定，DNS 192.168.1.1、223.5.5.5） |
| 账号 | `auto`（管理员），开机自动登录，密码见 [../credentials.md](../credentials.md) |
| 计算机名 | DESKTOP-AUTO01 |
| 远程桌面 | 已开启（3389） |
| 电源 | 不休眠、不关屏、无锁屏 |

## 无人值守安装

安装文件在 pve3 的 `/root/unattend-202/`（`autounattend.xml` + `setup.ps1`），打包成
`local:iso/unattend-202.iso` 挂在 ide0 上。Windows 安装程序会自动读取光驱根目录的 `autounattend.xml`：

- 自动分区、选专业版（通用安装密钥，不激活）、建本地账号、跳过联网和微软账号
- 首次登录执行 `setup.ps1`：固定 IP、关闭休眠和锁屏、开远程桌面和 ping

开机时要在 "Press any key to boot from CD" 那几秒按键，用 `qm sendkey 202 ret` 连按即可。全程约 13 分钟。

## 从外面截屏

```bash
# 在 pve3 上（需要 python3-pil）
echo 'screendump /tmp/202.ppm' | qm monitor 202
python3 -c "from PIL import Image; Image.open('/tmp/202.ppm').save('/tmp/202.jpg', quality=80)"
```

注意：screendump 截的是虚拟机的标准显示输出（`vga: std`）。以后加了 GVT-g 虚拟显卡，要确认截屏还能拿到正确的画面。

## 已安装 / 已配置（2026-11-01）

| 项目 | 说明 |
|---|---|
| GVT-g 虚拟显卡 | `hostpci0: 0000:00:02.0,mdev=i915-GVTg_V5_4`，Windows 显示为 Intel UHD Graphics 630，驱动 31.0.101.2140（Windows 更新自动装的） |
| OpenSSH 服务端 | Win32-OpenSSH 10.4（MSI），默认 shell 是 PowerShell，公钥在 `C:\ProgramData\ssh\administrators_authorized_keys`。**仅用于管理**，以后可以停掉 |
| Bambu Studio | 02.08.02.61，静默安装（`/S`）。向导：区域中国内地、不加入体验计划、只选 A1、默认耗材、装了网络插件、防火墙已放行 |
| 默认输入法 | 英文键盘（`HKCU\Control Panel\International\User Profile\InputMethodOverride = 0409:00000409`）。中文拼音保留，需要时切换 |

### 显卡的现状

桌面目前由标准虚拟显示（`vga: std`，Windows 里是 Microsoft Basic Display Adapter）输出，Intel 虚拟显卡没有接显示器。
所以 Bambu Studio 自动用了它自带的软件渲染 `C:\Program Files\Bambu Studio\mesa\opengl32.dll`（CPU 渲染），
3D 视图显示正常，8 核下够用。

想让 Intel 显卡真正参与渲染，要让桌面改由 Intel 虚拟显卡输出（GVT-g 的 display / dmabuf，或者去掉 std VGA），
但那样 `screendump` 就截不到画面了，要换截屏方式。目前启动时 QEMU 还提示 `VFIO dma-buf not supported in kernel`。暂不处理。

## 外部控制工具 vminput

[`scripts/vminput.py`](../scripts/vminput.py)，装在 pve3 的 `/usr/local/bin/vminput`。通过 QMP（`/var/run/qemu-server/<vmid>.qmp`）发送
`input-send-event`，Windows 收到的是虚拟 USB 键盘 / 平板的真实输入事件。

```bash
vminput 202 key meta_l                  # 按键 / 组合键（qcode，用 - 连接，如 ctrl-shift-ret）
vminput 202 type "bambu studio"         # 逐字输入（仅 ASCII），字符间隔随机
vminput 202 click 644 532               # 沿随机贝塞尔曲线移动后单击（坐标按 1280x800）
vminput 202 click 36 250 left 2         # 双击
vminput 202 scroll 3                    # 滚轮
```

注意：
- 中文输入法在"中"状态下，输入的字母会变成拼音候选，所以默认输入法设成了英文键盘。
- 在 PowerShell 窗口里单击会进入"选择"模式（标题出现"选择"），按 Esc 退出。
- Bambu Studio 选打印机那一页，要点卡片右上角的勾选框，点图片没用。

## 本机一体化工具 aw（推荐）

[`scripts/aw.py`](../scripts/aw.py)，在本机运行，一次往返完成"动作 → 等待 → 截屏"，截屏约 1 秒。

```bash
python3 scripts/aw.py shot /tmp/aw.jpg                          # 全屏截图（1280x800）
python3 scripts/aw.py shot /tmp/z.jpg --crop 250 90 640 60 1.5  # 裁剪并放大，看小字
python3 scripts/aw.py do "click 115 48" "wait 2" "key ctrl-i" --wait 2 --shot /tmp/aw.jpg
python3 scripts/aw.py do 'type C:\Users\auto\Desktop\in\a.stl' "key ret" --noshot
python3 scripts/aw.py text "收纳盒"        # 中文：经剪贴板 Ctrl+V 粘贴到当前输入框
python3 scripts/aw.py put ./model.stl      # 复制文件到虚拟机 C:\Users\auto\Desktop\in
python3 scripts/aw.py ps "Get-Process"     # 虚拟机里执行管理命令
```

工作方式：我（Claude）截屏 → 看图找到按钮坐标 → 点击，循环进行；不需要另外装 AI 模型。

- `text` 的原理：把文本写到虚拟机临时文件，触发计划任务 `aw-clip`（以 auto 交互身份运行隐藏的 PowerShell 执行 Set-Clipboard），再从外部按 Ctrl+V。
  这是唯一会在虚拟机里短暂启动进程的操作。
- Bambu Studio 首页搜索框是嵌入网页，**第一次点击只是激活，要再点一次**才能输入。
- 2026-11-02 实测：传入 20mm 立方体 → 导入（Ctrl+I，文件名框输入完整路径）→ 切片单盘，全程外部键鼠完成。

## 待办

- [x] 2026-11-02 登录拓竹账号 `sngths`（手机号 13045875254，短信验证码登录），同步了云端预设。
  打印机 A1 设备名 `3DP-039-506`，带 AMS lite（4 槽），在"设备"页可看摄像头、温度、打印进度。
  已选"不再提醒 Beta 版本更新"。
- [x] 通过 Windows 更新升级到 25H2（2026-11-02）。方法：策略 `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` 设 `TargetReleaseVersion=1`、`ProductVersion=Windows 11`、`TargetReleaseVersionInfo=25H2`，再以 SYSTEM 计划任务调用 `Microsoft.Update.Session` COM 扫描 → 下载 → 安装（直接通过 SSH 调用会报 E_ACCESSDENIED）
- [ ] Windows 激活（用户自己处理）
- [ ] 外部控制工具接上 AI 视觉识别（截屏 → 找按钮 → 点击）
- [ ] 中文文字输入（微信等需要）：考虑剪贴板粘贴，或外部切换输入法后输入拼音
- [ ] 以后再装：微信（扫码登录需要用户配合）
