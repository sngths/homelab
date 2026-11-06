# pve4 整机卡死

## 现象

pve4 会周期性地整机卡死：网络不通、没有任何响应，只能断电重启。内核日志里**没有任何错误**，说明是瞬间硬卡死。

## 规律（2026-11-01 从日志里查到的）

用 `journalctl --list-boots` 和每次运行最后几行日志对比，5 次卡死全部发生在**每月 1 号的备份任务启动 VM 106 或 VM 112 的那一刻**：

| 卡死时间 | 当时在做什么 |
|---|---|
| 2025-12-01 00:11 | VM 106 备份完成，刚启动 VM 112 |
| 2026-03-01 00:13 | VM 106 备份完成，刚启动 VM 112 |
| 2026-06-01 00:00 | 刚启动 VM 106 |
| 2026-09-01 00:10 | VM 106 备份完成，刚启动 VM 112 |
| 2026-11-01 00:00 | 刚启动 VM 106 |

- 备份关机状态的虚拟机时，PVE 会先在后台把它启动起来：一次性分配 16G 内存，然后大量读硬盘。
- 其他月份同样的操作是正常的，大约每 3 个月出一次。
- 这两台虚拟机没有直通设备，配置很普通。
- 硬盘的异常断电计数有 97 次，远多于另外两台。

### 佐证：NAS 上的半截备份（2026-11-02 发现并清理）

NAS 备份目录里留着 6 份没写完的备份（`.vma.dat` + `.tmp` 目录），PVE 网页上看不到，正好都是 106 和 112，时间都是每月 1 号凌晨：

| VM | 日期 | 已写入 |
|---|---|---|
| 106 k8s-worker03 | 2025-06-01、2026-06-01、2026-11-01 | 71.6G、76.2G、89.6G |
| 112 idea | 2025-12-01、2026-03-01、2026-09-01 | 17.9G、8.5G、8.4G |

说明 pve4 是在**备份写到一半时**卡死的，进一步印证了和每月备份的关系。这些文件共约 272G，已删除。
VM 106 已于 2026-11-02 删除；112 还在（pve4）。

## 怀疑的原因

1. **内存**：一下子分配大块内存，碰到有问题的区域。→ 还没验证，需要停机跑 memtest。
2. **NVMe 硬盘**（KINGBANK KP260，MAXIO 主控，无 DRAM 缓存）的省电模式 APST 有已知的掉盘问题。→ 2026-11-01 已关闭 APST。
3. 旧内核 6.8 和 CPU 微码。→ 已升级到 7.0 内核，并装了 amd64-microcode。

## 已经做的措施（2026-11-01）

- 停用每月备份任务（去掉诱因）
- 关闭 NVMe APST：GRUB 参数 `nvme_core.default_ps_max_latency_us=0`
- 硬件看门狗：`/etc/default/pve-ha-manager` 里设 `WATCHDOG_MODULE=sp5100_tco`（watchdog-mux 负责喂狗），卡死约 10 秒后自动复位
- 卡死时自动重启：`/etc/sysctl.d/90-crash-diag.conf`
  ```
  kernel.printk = 7 4 1 7
  kernel.softlockup_panic = 1
  kernel.hardlockup_panic = 1
  kernel.panic = 10
  ```
- netconsole：pve4 的内核消息实时通过 UDP 6666 发到 pve3
  - pve4：`netconsole.service`（`modprobe netconsole netconsole=6666@192.168.1.4/vmbr0,6666@192.168.1.3/30:bf:01:22:20:51`）
  - pve3：`netconsole-recv.service`（socat），写到 `/var/log/netconsole-remote.log`，logrotate 每周轮转（`/etc/logrotate.d/netconsole-remote`，必须写成多行格式；2026-11-06 修正前写成一行，导致 pve3 的 logrotate.service 一直失败）
  - **注意**：pve3 的网卡 MAC 改了的话，pve4 这边的配置也要跟着改

## 再次卡死时怎么查

```bash
# 1. 在 pve4 上：看重启记录和上一次运行的最后几行
journalctl --list-boots | tail -5
journalctl -b -1 -n 50 --no-pager

# 2. 在 pve3 上：看 pve4 卡死前通过网络发来的最后消息
tail -100 /var/log/netconsole-remote.log

# 3. 看温度和硬盘状态
sensors; nvme smart-log /dev/nvme0
```

如果还会卡死：安排停机跑 memtest86+；考虑给硬盘加散热片；或者把重要服务都迁出 pve4。
