# PVE 集群

- 集群名：`pve`，3 个节点：pve2 / pve3 / pve4（nodeid 4 / 2 / 3），3 票，2 票即可保持 quorum
- 版本：**PVE 9.2.24**，Debian 13（trixie），内核 7.0.14-26-pve（2026-11-01 升级）
- 网页管理：`https://192.168.1.{2,3,4}:8006`，账号 `root@pam`
- 时间同步：chrony

## 软件源（三台相同）

官方源 download.proxmox.com 在家里网络下几乎下载不动，统一用中科大镜像：

```
# /etc/apt/sources.list
deb https://mirrors.ustc.edu.cn/debian trixie main contrib non-free-firmware
deb https://mirrors.ustc.edu.cn/debian trixie-updates main contrib non-free-firmware
deb https://mirrors.ustc.edu.cn/debian-security trixie-security main contrib non-free-firmware
deb https://mirrors.ustc.edu.cn/proxmox/debian/pve trixie pve-no-subscription
```

enterprise 和 ceph 源已注释掉。注意：pve3 的 pve 源在 `sources.list.d/pve-no-subscription.list`，pve2 / pve4 写在 `sources.list` 里。

## 存储

| 名称 | 类型 | 位置 | 用途 |
|---|---|---|---|
| local | 目录 | `/var/lib/vz`（约 94G） | ISO、模板、备份 |
| local-lvm | LVM-thin | 每台本地 NVMe | 虚拟机磁盘（各节点独立，**不共享**） |
| nas | NFS | 192.168.1.40:/volume1/pve | 备份 |

虚拟机磁盘都在各自节点的本地盘上，所以目前**没有 HA**：一台主机挂了，上面的虚拟机只能从备份恢复到别的节点。

## 备份策略

- 原来的每月备份任务 `backup-00133daf-2ec8`（每月 1 号 0 点，备份到 nas）**已于 2026-11-01 停用**，
  因为它和 pve4 死机有关（见 [../runbooks/pve4-freeze.md](../runbooks/pve4-freeze.md)）。
- 2026-11-01 升级前做过一次全量备份；清理后 NAS 上每台虚拟机只保留最新一份（共 29 份，约 928G）。
- 计划：部署 PBS（Proxmox Backup Server），用增量去重备份替代。
- 手动备份 / 删除备份的注意事项：
  - 非特权 LXC 备份到 NFS 要加 `tmpdir=/var/tmp`，否则会失败。
  - 通过 API 批量删除 NAS 上的备份时要**一个一个删**，并发删除会出现 `cfs-lock 'storage-nas' ... timeout`。

## 监控与防死机配置（2026-11-01）

| 配置 | 节点 | 位置 |
|---|---|---|
| lm-sensors、nvme-cli | 三台 | `sensors`、`nvme smart-log /dev/nvme0` |
| AMD CPU 微码 | pve2、pve4 | `amd64-microcode` 包 |
| 硬件看门狗 SP5100 TCO | pve4 | `/etc/default/pve-ha-manager`：`WATCHDOG_MODULE=sp5100_tco` |
| 内核卡死自动重启 | pve4 | `/etc/sysctl.d/90-crash-diag.conf` |
| netconsole 发送内核日志到 pve3 | pve4 | `netconsole.service` |
| netconsole 接收 | pve3 | `netconsole-recv.service`，写到 `/var/log/netconsole-remote.log`，UDP 6666 |
| 关闭 NVMe 省电（APST） | pve4 | GRUB 参数 `nvme_core.default_ps_max_latency_us=0`，原文件备份 `/etc/default/grub.bak-apst` |

PVE 防火墙在三台上都没启用。

## 已清理

- 2026-11-01：删除了已退役节点 pve1 的残留 `/etc/pve/nodes/pve1`，其中有一个找不回来的容器 CT 121 `jellyfin-ct` 的配置。
  pve1 那台主机已经改装成日常用的 Ubuntu 机器。
