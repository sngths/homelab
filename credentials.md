# 账号密码

> ⚠️ 本文件是**明文**密码，仓库必须保持**私有**。这是用户的决定（2026-11-01）。
> 改了密码要同步更新这里。所有密码都是 2026-11-01 实际登录验证过的。

## PVE 集群

| 设备 | 地址 | 账号 | 密码 | 备注 |
|---|---|---|---|---|
| pve2 / pve3 / pve4 | https://192.168.1.{2,3,4}:8006 | `root`（领域 Linux PAM） | `8887387466` | 三台相同，也是 SSH 的 root 密码。建议修改 |

## 虚拟机

| 虚拟机 | 地址 | 账号 | 密码 | 备注 |
|---|---|---|---|---|
| VM 200 dokploy | 192.168.1.50（SSH / PVE 控制台） | `ubuntu` | `mg5N8tJizKSV` | 有 sudo。cloud-init 设置的初始密码 |
| VM 200 Dokploy 面板 | http://192.168.1.50:3000 | `1035273486@qq.com` | `8887387466` | 管理员，2026-11-01 登录验证过 |
| VM 201 pbs（网页） | https://192.168.1.51:8007 | `root`（领域 Linux PAM） | `T8hDndkiDHqT` | PBS 管理界面 |
| VM 201 pbs（系统） | 192.168.1.51（SSH / PVE 控制台） | `root` / `debian` | `T8hDndkiDHqT` | 两个账号同一个密码。debian 有 sudo，但不能登录 PBS 网页 |
| VM 202 auto-win（Windows） | 192.168.1.52（远程桌面 / PVE 控制台） | `auto` | `6Xy55Wj0CWAa1` | 管理员，开机自动登录。Windows 未激活 |
| CT 204 jellyfin（系统） | 192.168.1.54（SSH / `pct enter 204`） | `root` | `xfS0933mpbe5` | 也可用 PVE 的密钥登录 |
| Jellyfin 网页 | http://192.168.1.54:8096 | `tianxing` | `pbnlLDcxK7oMD2` | 管理员，2026-11-03 建 |
| CT 203 home-jump（跳板） | 192.168.1.53 | `root`；wsd 跑在普通用户 `jump` 下 | `h5EOr87uMJMt` | root 也可用 PVE 的密钥登录；`jump` 用户有自己的 SSH 密钥 `jump@homelab`（`/home/jump/.ssh/id_ed25519`） |

## 周边设备

| 设备 | 地址 | 账号 | 密码 | 备注 |
|---|---|---|---|---|
| One-KVM | https://192.168.1.155 | `admin` | `admin` | 出厂默认密码，建议修改 |
| 群晖 NAS（DSM 网页） | http://192.168.1.40:5000 | `tianxing` | `Tx123456` | 大写 T、小写 x。2026-11-01 登录验证过。SSH（22 端口）也能用这个账号登录，有 sudo |
| 群晖 NAS Jellyfin 只读账号 | SMB `\\192.168.1.40\backup` | `media-ro` | `GLt5rBlRnqkCFjAV` | 2026-11-03 建。只对 `backup` 共享只读（ACL）。pve2 上存在 `/root/.nas-media-ro.cred`，用于挂载 `/mnt/nas-backup` |
| 群晖 NAS 摄像头专用账号 | SMB `\\192.168.1.40\surveillance` | `xiaomi-cam` | `4teKG9AaDlicwcEZ` | 2026-11-03 建。只能读写 `surveillance` 共享，应用权限只开 SMB（DSM、File Station 等全部拒绝），不能改密码。填在米家 App 摄像头的 NAS 存储设置里 |
| 路由器（iStoreOS） | http://192.168.1.1，SSH 22 | `root` | `8887387466` | 和 Dokploy 面板密码相同。2026-11-03 SSH 登录验证过 |

## 密钥和令牌（不是登录密码，一般不用手动处理）

| 名称 | 位置 | 用途 |
|---|---|---|
| SSH 密钥 `claude-pve-upgrade` | 私钥：Windows `C:\Users\tianxing\.ssh\pve_claude` | 免密 SSH 到 PVE 三台节点（root）、VM 200（ubuntu）、VM 201（debian） |
| PBS API token `pve@pbs!pve` | PBS：`/root/pve-token.json`；PVE：`/etc/pve/priv/storage/pbs.pw` | PVE 往 PBS 写备份用 |

## 拓竹（Bambu Lab）账号

- 用户名 `sngths`，手机号 13045875254，用**短信验证码**登录，没有设密码。VM 202 的 Bambu Studio 已登录。
