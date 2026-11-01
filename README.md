# homelab

家里的 PVE 集群和周边设备的配置、操作记录和故障处理手册。

> **密码和密钥一律不写进这个仓库。** 文档里只写"去哪里查"。

最后更新：2026-11-01

## 网络

- 网段：`192.168.1.0/24`，网关 / DNS：`192.168.1.1`
- 家里的网络**连不上** Docker Hub、GitHub、download.proxmox.com（极慢）。处理办法见
  [runbooks/docker-image-relay.md](runbooks/docker-image-relay.md)，软件源统一用国内镜像。

## IP 分配表

| IP | 设备 | 说明 |
|---|---|---|
| 192.168.1.1 | 路由器 | 网关、DNS |
| 192.168.1.2 | pve2 | PVE 节点，GMKtec NucBox K6 |
| 192.168.1.3 | pve3 | PVE 节点，旧 Intel 小主机（2026-11-01 从坏掉的 M5 换过来） |
| 192.168.1.4 | pve4 | PVE 节点，GMKtec NucBox M5 |
| 192.168.1.40 | nas | 群晖 NAS，NFS 共享给 PVE 存备份 |
| 192.168.1.50 | dokploy（VM 200） | Docker 部署平台，Dokploy 面板 :3000 |
| 192.168.1.117 | DESKTOP-0GE8DG9 | 家里的 Windows 台式机，装了 wsd，是远程操作家里网络的入口 |
| 192.168.1.155 | One-KVM | 网络 KVM（onecloud 刷机），目前接在 pve3 上 |

## 目录

| 路径 | 内容 |
|---|---|
| [hardware/](hardware/) | 每台物理设备的型号、配置、更换记录 |
| [pve/cluster.md](pve/cluster.md) | 集群、存储、备份策略、监控和防死机配置 |
| [pve/vms.md](pve/vms.md) | 虚拟机清单 |
| [pve/upgrade-8-to-9.md](pve/upgrade-8-to-9.md) | 2026-11-01 PVE 8 → 9 升级记录和踩过的坑 |
| [services/dokploy.md](services/dokploy.md) | Docker 部署平台 |
| [runbooks/](runbooks/) | 远程访问方式、故障处理手册 |
| [scripts/](scripts/) | 可复用的脚本 |

## 待办

- [ ] 修改密码：PVE root（三台相同）、One-KVM（仍是出厂默认密码）、dokploy VM 的 ubuntu 用户
- [ ] 部署 PBS（Proxmox Backup Server），给常用虚拟机配每日增量备份
- [ ] 清理不用的旧虚拟机（k8s 那一组、多个 win11 等）
- [ ] 确认 pve2 上旧的 VM 128 "Dokploy" 是否还需要（新平台是 pve3 上的 VM 200）
- [ ] pve3 安装 `intel-microcode`
- [ ] pve4 若再死机：查 pve3 上的 `/var/log/netconsole-remote.log`，考虑跑 memtest
- [ ] pve4 硬盘空闲 57°C 左右，考虑加散热片
- [ ] 不再需要时删除临时 SSH 密钥 `claude-pve-upgrade`（见 [runbooks/access.md](runbooks/access.md)）
