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
| 系统 | Windows 11 专业版 24H2 简体中文（官方镜像），**未激活**（用户自己处理） |
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

## 待办

- [ ] 挂上 GVT-g 虚拟显卡（`hostpci0: 0000:00:02.0,mdev=i915-GVTg_V5_4`），装支持 GVT-g 的 Intel 显卡驱动
- [ ] 安装微信、Bambu Studio
- [ ] 通过 Windows 更新升级到 25H2，打补丁
- [ ] 外部控制工具：截屏 + 鼠标（带轨迹）+ 键盘，接上 AI 视觉识别
- [ ] 卸载安装光盘（ide0、ide2）
