# PBS 备份服务器（VM 201）

2026-11-01 部署。Proxmox Backup Server 负责 PVE 虚拟机的**增量、去重**备份。

## 虚拟机

| 项目 | 内容 |
|---|---|
| VMID / 名称 | 201 / pbs，在 pve3 上，开机自启 |
| 系统 | Debian 13（cloud image）+ apt 安装的 proxmox-backup-server 4.2.8 |
| 配置 | 2 核 / 4G / 32G 系统盘（local-lvm） |
| 数据盘 | `scsi1`：2T qcow2，放在 NAS 上（PVE 存储 `nas-pbs` = 192.168.1.40:/volume1/pbs），`backup=0`（备份 PBS 自己时不包含这块盘） |
| IP | 192.168.1.51 |
| 网页 | https://192.168.1.51:8007，账号 `root@pam`（**密码不在这里**） |
| SSH | 用户 `debian`（cloud-init 放了临时密钥），有 sudo |
| 软件源 | 中科大：debian（`/etc/apt/mirrors/*.list`）、pbs-no-subscription（`/etc/apt/sources.list.d/pbs.sources`），enterprise 源已禁用 |

## 存储结构

```
群晖 /volume1/pbs（NFS，Squash = 映射所有用户为 admin）
 └─ images/201/vm-201-disk-0.qcow2   ← 2T 虚拟磁盘，精简置备，实际用多少占多少
     └─ （PBS 虚拟机里是 /dev/sdb，ext4，挂载到 /mnt/pbsdata）
         └─ datastore/                ← PBS 数据存储 "nas"
```

### 为什么不直接把 PBS 数据放在 NFS 共享里

试过两次，都不行：

1. 用已有的 `/volume1/pve` 共享（Squash = 不映射）：群晖只放行 root，**其他所有用户都被拒绝**
   （连 777 目录都写不进去）。PBS 服务以 `backup`（uid 34）用户运行，所以无法读写。
2. 新建 `/volume1/pbs` 共享（Squash = 映射所有用户为 admin）：能写了，但文件属主全部变成 admin（1024:100）。
   PBS 要求数据目录的属主必须是 `backup` 用户，`chown` 会报 EPERM；即使用 `--reuse-datastore` 也会被拒绝
   （"permissions or owner not correct"）。

最终方案：在 NAS 上放一个 qcow2 虚拟磁盘，由 PVE 以 root 身份读写这个文件；PBS 在虚拟机里把它格式化成 ext4，
权限就都在 PBS 自己的文件系统里处理了。

**如果 pve3 坏了**：在任意节点重建一台 PBS 虚拟机，把 `nas-pbs:201/vm-201-disk-0.qcow2` 挂上去，挂载后用
`proxmox-backup-manager datastore create nas /mnt/pbsdata/datastore --reuse-datastore true` 重新接入即可。

## PBS 上的配置

| 项目 | 设置 |
|---|---|
| 数据存储 | `nas`，路径 `/mnt/pbsdata/datastore` |
| 垃圾回收（GC） | 每天 04:30 |
| 保留策略（prune-job `daily-prune`） | 每天 04:00，保留 7 天 / 4 周 / 3 个月 |
| 校验（verify-job `weekly-verify`） | 每周日 05:00，已校验过的 30 天内不再重复校验 |
| PVE 用的账号 | 用户 `pve@pbs`，API token `pve@pbs!pve`，权限 `DatastoreBackup` |

token 的 secret 存在 PBS 虚拟机的 `/root/pve-token.json` 里，PVE 那边保存在 `/etc/pve/priv/storage/pbs.pw`。

proxy 服务加了依赖：`/etc/systemd/system/proxmox-backup-proxy.service.d/nas.conf`
（`RequiresMountsFor=/mnt/pbsdata`），确保数据盘挂载后才启动。

## PVE 上的配置

- 存储 `pbs`：server 192.168.1.51，datastore `nas`，`prune-backups keep-all=1`（保留策略交给 PBS 管）
- 存储 `nas-pbs`：NFS 192.168.1.40:/volume1/pbs，只存放 PBS 的数据盘，不要放别的虚拟机磁盘
- 备份任务 `daily-pbs`：每天 03:00，snapshot 模式，目前只备份 **VM 200（dokploy）**

以后要给其他虚拟机加每日备份，修改 `daily-pbs` 任务的 vmid 列表就行（网页：数据中心 → 备份）。
**pve4 上的虚拟机先不要加**，见 [../runbooks/pve4-freeze.md](../runbooks/pve4-freeze.md)。

## 实测（2026-11-01，VM 200，200G 磁盘）

| | 耗时 | 传输量 |
|---|---|---|
| 第一次备份 | 76 秒 | 200G（其中 95% 是空白，实际数据约 9G） |
| 第二次备份（增量） | **2 秒** | 52MB |
| 校验 | 19 秒 | 0 错误 |

两次备份在 PBS 上一共只占约 3.3G。

## 常用操作

```bash
# PVE 上手动备份某台虚拟机到 PBS
vzdump <vmid> --storage pbs --mode snapshot

# 查看备份列表
pvesm list pbs

# PBS 上手动校验 / 回收空间
proxmox-backup-manager verify nas
proxmox-backup-manager garbage-collection start nas
```

恢复：PVE 网页 → 存储 `pbs` → 选中某个备份 → 恢复（整机），或者"文件恢复"（单个文件）。
