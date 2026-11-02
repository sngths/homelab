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
| nas | NFS | 192.168.1.40:/volume1/pve | vzdump 完整备份（旧） |
| nas-pbs | NFS | 192.168.1.40:/volume1/pbs | 只放 PBS 的 2T 数据盘 |
| pbs | PBS | 192.168.1.51，datastore `nas` | 每日增量备份 |

虚拟机磁盘都在各自节点的本地盘上，所以目前**没有 HA**：一台主机挂了，上面的虚拟机只能从备份恢复到别的节点。

## 备份策略

- 原来的每月备份任务 `backup-00133daf-2ec8`（每月 1 号 0 点，备份到 nas）**已于 2026-11-01 停用**，
  因为它和 pve4 死机有关（见 [../runbooks/pve4-freeze.md](../runbooks/pve4-freeze.md)）。
- 2026-11-01 升级前做过一次全量备份；清理后 NAS 上每台虚拟机只保留最新一份（共 29 份，约 928G）。
- **2026-11-01 起：每日增量备份到 PBS**（任务 `daily-pbs`，03:00，目前只有 VM 200），详见 [../services/pbs.md](../services/pbs.md)。
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

## pve3 核显切分（Intel GVT-g，2026-11-01）

pve3 的 Intel UHD 630 支持 GVT-g，可以切成虚拟显卡分给虚拟机，主机自己的显示输出不受影响。
AMD 消费级核显（pve2 的 780M、pve4 的 Vega）不支持切分，只能整块直通，还有 reset bug，所以不用。

- GRUB 参数：`intel_iommu=on iommu=pt i915.enable_gvt=1`（原文件备份 `/etc/default/grub.bak-gvt`）
- 模块：`/etc/modules-load.d/gvt.conf`（vfio、vfio_iommu_type1、vfio_pci、kvmgt）
- 可用类型（`/sys/bus/pci/devices/0000:00:02.0/mdev_supported_types/`）：

  | 类型 | 显存 | 最高分辨率 | 可用数量 |
  |---|---|---|---|
  | `i915-GVTg_V5_4` | 128M + 512M | 1920×1200 | 1 |
  | `i915-GVTg_V5_8` | 64M + 384M | 1024×768 | 2 |

  两种类型共用同一份显存，开 1 个 V5_4 后 V5_8 的数量会减少。想多开，可以在 BIOS 里调大核显显存（Aperture Size）。
- 虚拟机里配置：`hostpci0: 0000:00:02.0,mdev=i915-GVTg_V5_4`。Windows 需要装支持 GVT-g 的旧版 Intel 显卡驱动，新版驱动不支持。

## 已清理

- 2026-11-01：删除了已退役节点 pve1 的残留 `/etc/pve/nodes/pve1`，其中有一个找不回来的容器 CT 121 `jellyfin-ct` 的配置。
  pve1 那台主机已经改装成日常用的 Ubuntu 机器。
- 2026-11-02：删除了 VM 118 `jump`（pve2，JumpServer v3.10.0 堡垒机，Debian 12，2024-04 从 VMware 迁来，2024-06 之后没再用过）
  及其 NAS 上的备份（4.3G），用户确认不再需要。它里面写死的 IP 是 192.168.1.50，和现在的 VM 200 冲突。
  家里的跳板改用新建的 CT 203 `home-jump`。
- 2026-11-02：删除旧 k8s 集群及配套服务共 10 台虚拟机和它们在 NAS 上的备份（用户确认，内容事先只读检查过）：
  - k8s：103 k8s-load-balancer、105 k8s-master01、106 k8s-worker03、107 k8s-worker01、108 k8s-worker02
  - 配套：110 harbor、111 jenkins、113 prometheus、117 gitlab（只有 1 个仓库 tianxing/proto，已在 GitHub）、
    123 minio（只有公开模型 mistral-7b-instruct-v0.2.Q4_K_M.gguf 和两个小脚本）
  - 释放本地盘约 923G，NAS 约 358G。删除后 NAS 备份剩 18 份共 566G，NAS 剩余约 7.0T。
