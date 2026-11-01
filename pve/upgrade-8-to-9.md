# PVE 8 → 9 升级记录（2026-11-01）

三台节点都从 8.x 原地升级到 **9.2.24**，没有重装，虚拟机都保留了。

## 顺序

1. 关闭所有虚拟机，全部备份到 NAS。
2. pve3 先升级（它的备份最先完成），pve2 / pve4 在这期间继续备份。
3. 再升级 pve4，最后升级 pve2。每次只重启一台，集群始终保持 quorum。

升级期间集群里 8.x 和 9.x 节点同时存在是正常的。注意不要把虚拟机从 9 迁移回 8。

## 每台的步骤

```bash
# 1. 软件源换成中科大镜像（官方源太慢），先升到 8.4 最新
#    （sources.list 内容见 cluster.md，先用 bookworm）
systemd-run --unit=pve-upg84 bash -c "(export DEBIAN_FRONTEND=noninteractive; apt-get update && \
  apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold dist-upgrade; \
  echo EXIT=\$?) > /root/upgrade-8.4.log 2>&1"

# 2. 升级检查，必须做到 0 FAIL
pve8to9 --full

# 3. 切到 trixie，升级到 9
sed -i "s/bookworm/trixie/g" /etc/apt/sources.list /etc/apt/sources.list.d/*.list
systemd-run --unit=pve-upg9 bash -c "(... 同上 ...) > /root/upgrade-9.log 2>&1"

# 4. 装时间同步，然后重启
apt-get install -y chrony
systemd-run --on-active=3 --unit=pve-reboot /bin/systemctl reboot
```

用 `systemd-run` 跑升级，是为了 SSH 断开时升级不会被中断。日志在各节点的 `/root/upgrade-*.log`。

## 踩过的坑

| 问题 | 节点 | 处理 |
|---|---|---|
| `apt-get update` 卡住：security.debian.org 解析失败，download.proxmox.com 只有几 KB/s | 全部 | 换中科大镜像 |
| pve8to9 FAIL：装了 `systemd-boot` 元包（实际启动用的是 GRUB） | pve4、pve2 | `apt remove systemd-boot` |
| pve8to9 WARN：存在备用启动路径 `EFI/BOOT/BOOTX64.efi`，但 GRUB 不会更新它。**pve4 实际就是从这个路径启动的**（BootCurrent=0005），不修的话升级后可能开不了机 | pve4、pve2 | `echo "grub-efi-amd64 grub2/force_efi_extra_removable boolean true" \| debconf-set-selections` 然后 `apt install --reinstall grub-efi-amd64` |
| pve8to9 WARN：没装 CPU 微码 | pve4、pve2 | `apt install amd64-microcode`（需要 non-free-firmware 源） |
| pve8to9 WARN：没有 NTP | 全部 | `apt install chrony` |
| pve3 重启后一直没回来，KVM 黑屏 | pve3 | 不是新内核起不来，是旧内核**关机时卡在** "Sending SIGTERM"。强制断电后正常进入 7.0 内核 |
| 换硬件后 pve3 网络不通 | pve3 | 网卡名从 `enp1s0` 变成 `eno1`，改 `/etc/network/interfaces` |

## 备份时遇到的问题

- 部分虚拟机原来是"休眠"状态（有 vmstate），备份前要先恢复运行再正常关机；VM 108 有残留锁，执行了 `qm unlock`。
- 非特权 LXC 125 备份到 NFS 失败，加 `tmpdir=/var/tmp` 后成功。
- 备份速度：pve3 约 7 台 / 1 小时；pve4 的 VM 127 限速 50MB/s，约 1.7 小时。
