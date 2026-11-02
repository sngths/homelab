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

## 周边设备

| 设备 | 地址 | 账号 | 密码 | 备注 |
|---|---|---|---|---|
| One-KVM | https://192.168.1.155 | `admin` | `admin` | 出厂默认密码，建议修改 |
| 群晖 NAS（DSM 网页） | http://192.168.1.40:5000 | `tianxing` | `Tx123456` | 大写 T、小写 x。2026-11-01 登录验证过 |
| 路由器 | http://192.168.1.1 | 待补充 | 待补充 | |

## 密钥和令牌（不是登录密码，一般不用手动处理）

| 名称 | 位置 | 用途 |
|---|---|---|
| SSH 密钥 `claude-pve-upgrade` | 私钥：Windows `C:\Users\tianxing\.ssh\pve_claude` | 免密 SSH 到 PVE 三台节点（root）、VM 200（ubuntu）、VM 201（debian） |
| PBS API token `pve@pbs!pve` | PBS：`/root/pve-token.json`；PVE：`/etc/pve/priv/storage/pbs.pw` | PVE 往 PBS 写备份用 |

## 拓竹（Bambu Lab）账号

- 用户名 `sngths`，手机号 13045875254，用**短信验证码**登录，没有设密码。VM 202 的 Bambu Studio 已登录。
