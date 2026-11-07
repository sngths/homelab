# homelab

家里的 PVE 集群和周边设备的配置、操作记录和故障处理手册。

> 账号密码见 [credentials.md](credentials.md)（明文，**仓库必须保持私有**）。

最后更新：2026-11-01

## 网络

- 网段：`192.168.1.0/24`，网关 / DNS：`192.168.1.1`
- 家里的网络**连不上** Docker Hub、GitHub、download.proxmox.com（极慢）。处理办法见
  [runbooks/docker-image-relay.md](runbooks/docker-image-relay.md)，软件源统一用国内镜像。

## IP 分配表

| IP | 设备 | 说明 |
|---|---|---|
| 192.168.1.1 | 路由器 | 网关、DNS，iStoreOS；局域网代理 SOCKS5 :1070 / HTTP :1071（日本节点），见 [hardware/README.md](hardware/README.md) |
| 192.168.1.2 | pve2 | PVE 节点，GMKtec NucBox K6 |
| 192.168.1.3 | pve3 | PVE 节点，旧 Intel 小主机（2026-11-01 从坏掉的 M5 换过来） |
| 192.168.1.4 | pve4 | PVE 节点，GMKtec NucBox M5 |
| 192.168.1.40 | nas | 群晖 NAS，NFS 共享给 PVE 存备份 |
| 192.168.1.50 | dokploy（VM 200） | Docker 部署平台，Dokploy 面板 :3000 |
| 192.168.1.51 | pbs（VM 201） | Proxmox Backup Server，网页 :8007 |
| 192.168.1.52 | auto-win（VM 202） | Windows 11 自动化操作机（微信、Bambu Studio 等） |
| 192.168.1.53 | home-jump（CT 203，pve2） | 跳板机：wsd + ssh，Claude 从外面进家里网络的入口，见 [services/home-jump.md](services/home-jump.md) |
| 192.168.1.54 | jellyfin（CT 204，pve2） | Jellyfin 影音服务器 :8096，见 [services/jellyfin.md](services/jellyfin.md) |
| 192.168.1.117 | DESKTOP-0GE8DG9 | 家里的 Windows 台式机，装了 wsd，是远程操作家里网络的**备用**入口（主入口是 home-jump） |
| 192.168.1.155 | One-KVM | 网络 KVM（onecloud 刷机），目前接在 pve3 上 |

## 目录

| 路径 | 内容 |
|---|---|
| [hardware/](hardware/) | 每台物理设备的型号、配置、更换记录 |
| [pve/cluster.md](pve/cluster.md) | 集群、存储、备份策略、监控和防死机配置 |
| [pve/vms.md](pve/vms.md) | 虚拟机清单 |
| [pve/upgrade-8-to-9.md](pve/upgrade-8-to-9.md) | 2026-11-01 PVE 8 → 9 升级记录和踩过的坑 |
| [services/dokploy.md](services/dokploy.md) | Docker 部署平台 |
| [services/pbs.md](services/pbs.md) | PBS 备份服务器、备份策略 |
| [services/auto-win.md](services/auto-win.md) | Windows 自动化操作机 |
| [services/jellyfin.md](services/jellyfin.md) | Jellyfin 影音服务器 |
| [runbooks/](runbooks/) | 远程访问方式、故障处理手册 |
| [scripts/](scripts/) | 可复用的脚本 |

## 待办

- [ ] 修改密码：PVE root（三台相同）、One-KVM（仍是出厂默认密码）、dokploy VM 的 ubuntu 用户、PBS 的 root 和 debian 用户
- [x] 部署 PBS，VM 200 每日增量备份（2026-11-01）
- [x] auto-win（202）、home-jump（203）加进 `daily-pbs`（2026-11-02）；以后新的常用虚拟机也要加进去
- [x] 清理旧虚拟机第一批（2026-11-02）：k8s 一组及配套、旧 jump、idea、llm-server、旧 Dokploy、mcp-server，共 15 台及其备份
- [ ] 继续清理：剩下 7 台旧 Windows（100、101、115、116、119、120、124）和几台 Linux 桌面，等用户决定
- [x] Jellyfin 重建为 CT 204（pve2，2026-11-03），旧 VM 109 已删；后续 MetaTube 刮削和清理见 services/jellyfin.md
- [ ] pve3 安装 `intel-microcode`
- [ ] pve3 热重启后认不到 NVMe 硬盘，待查（见 hardware/README.md），修好前重启要"关机 → 断电 → 开机"
- [ ] pve4 若再死机：查 pve3 上的 `/var/log/netconsole-remote.log`，考虑跑 memtest
- [ ] pve4 硬盘空闲 57°C 左右，考虑加散热片
- [ ] 异地组网（用户说后面再做）：路由器上开 WireGuard，用 Cloudflare 做 DDNS，iPhone 用小火箭按规则把 `192.168.1.0/24` 走 WireGuard。备用方案是 Tailscale，见 [hardware/README.md](hardware/README.md) 路由器一节
- [ ] 不再需要时删除临时 SSH 密钥 `claude-pve-upgrade`（见 [runbooks/access.md](runbooks/access.md)）
