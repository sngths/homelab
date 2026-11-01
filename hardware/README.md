# 硬件清单

## pve2 — GMKtec NucBox K6

| 项目 | 配置 |
|---|---|
| CPU | AMD Ryzen 7 7840HS（8 核 16 线程），Radeon 780M |
| 内存 | 64G（系统识别 61G） |
| 硬盘 | KINGBANK KP230 Pro 2TB NVMe |
| 网卡 | `enp2s0`（在用，MAC 84:47:09:31:ea:3a）、`eno1`（未接线）、Wi-Fi |
| 备注 | 安装了 amd64-microcode |

## pve3 — 旧 Intel 小主机（无品牌信息）

| 项目 | 配置 |
|---|---|
| CPU | Intel Xeon E-2286M（8 核 16 线程） |
| 内存 | 64G（系统识别 62G），**从坏掉的 GMKtec M5 上拆过来的** |
| 硬盘 | KINGBANK KP230 Pro 2TB NVMe，**从坏掉的 GMKtec M5 上拆过来的** |
| 网卡 | `eno1`（在用，MAC 30:bf:01:22:20:51）、`enp2s0`（…:52，不要同时接进网桥，会成环）、Wi-Fi |
| 显示 | 接 One-KVM（192.168.1.155） |
| 主板 | AMI Aptio BIOS，Board ID `S210H Series`，BIOS 日期 2020-11-19 |
| 核显 | Intel UHD 630，已开启 GVT-g 切分给虚拟机（见 [../pve/cluster.md](../pve/cluster.md)） |

> ⚠️ **热重启后认不到 NVMe 硬盘**：`reboot` 之后 BIOS 显示 "No NVME Device Found"，停在 BIOS 设置界面。
> 2026-11-01 出现了两次，两次都是**长按电源键关机、拔电再开机**后恢复。
> **在修好之前，pve3 要重启时一律"关机 → 断电 → 开机"，不要直接 reboot。** 待查：刷新 BIOS，或调整 BIOS 里的 NVMe / PCIe 相关设置。

**更换记录**
- 2026-11-01 之前：pve3 是一台 GMKtec M5。主板损坏（通电风扇转，不 POST、HDMI 无输出，拔内存/硬盘测试均无效）。
- 2026-11-01：把 M5 的内存和硬盘装进这台旧 Intel 主机，系统原样启动。因为网卡名变了（`enp1s0` → `eno1`），
  修改了 `/etc/network/interfaces` 的 `bridge-ports`，原文件备份为 `/etc/network/interfaces.bak-m5`。
- 待办：装 `intel-microcode`。

## pve4 — GMKtec NucBox M5

| 项目 | 配置 |
|---|---|
| CPU | AMD Ryzen 7 5700U（8 核 16 线程） |
| 内存 | 64G（系统识别 62G） |
| 硬盘 | KINGBANK KP260 1TB NVMe（MAXIO MAP1602 主控，无 DRAM 缓存） |
| 网卡 | `enp1s0`（在用，Intel I225-V，MAC 84:47:09:28:92:26）、`enp2s0`、Wi-Fi |
| 看门狗 | 主板 SP5100 TCO 硬件看门狗，已启用 |
| 备注 | **有周期性整机卡死的历史**，见 [../runbooks/pve4-freeze.md](../runbooks/pve4-freeze.md)。硬盘空闲约 57°C，偏热 |

## 2026-11-01 健康状况快照

| | CPU 空闲温度 | NVMe 温度 | NVMe 磨损 | 坏块 | 异常断电次数 |
|---|---|---|---|---|---|
| pve2 | 55°C | 48°C | 3% | 0 | 22 |
| pve3 | 49°C | 39°C | 3% | 0 | 53 |
| pve4 | 52°C | 57°C | 3% | 0 | 97 |

查看命令（三台都装了 `lm-sensors`、`nvme-cli`）：`sensors`、`nvme smart-log /dev/nvme0`

## NAS — 群晖，192.168.1.40

- NFS 导出 `/volume1/pve`，在 PVE 里叫存储 `nas`，挂载点 `/mnt/pve/nas`，只存备份。
- 容量约 25T，2026-11-01 清理后剩余约 6.7T。

## One-KVM — 192.168.1.155

- onecloud 刷的 One-KVM（kvmd 3.291），网页登录账号 admin（**默认密码未改**）。
- 目前 HDMI 和 USB 接在 pve3 上，没有接电源控制。
- 视频流设成 MJPEG 才能正常出画面（H.264 模式下显示黑屏）。
- API 要点见 [../runbooks/access.md](../runbooks/access.md)。

## Windows 台式机 — DESKTOP-0GE8DG9，192.168.1.117

- 装了 wsd（workspaced），开启了"执行命令"，是从外面操作家里网络的入口。
- 有 OpenSSH 客户端，临时密钥在 `C:\Users\tianxing\.ssh\pve_claude`。
