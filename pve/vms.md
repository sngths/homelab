# 虚拟机清单

2026-11-01 时的状态。除了 VM 200，其他都处于关机状态。

> 内存说明：表里的内存是**配置值**，关机时不占用。每台主机同时开着的虚拟机，内存加起来不要超过约 60G。

| ID | 类型 | 节点 | 名称 | CPU | 内存 | 磁盘 | 备注 |
|---|---|---|---|---|---|---|---|
| 100 | VM | pve3 | win11-script | 8 | 16G | 100G | |
| 101 | VM | pve2 | win11-demo | 8 | 16G | 200G | |
| 102 | VM | pve2 | debian | 4 | 16G | 16G | |
| 103 | VM | pve3 | k8s-load-balancer | 2 | 2G | 50G | 旧 k8s 集群 |
| 104 | VM | pve2 | debian-test | 4 | 2G | 50G | |
| 105 | VM | pve2 | k8s-master01 | 4 | 4G | 50G | 旧 k8s 集群 |
| 106 | VM | pve4 | k8s-worker03 | 8 | 16G | 160G | 旧 k8s 集群；NAS 上最新备份是 2026-10-01 |
| 107 | VM | pve3 | k8s-worker01 | 8 | 16G | 160G | 旧 k8s 集群 |
| 108 | VM | pve3 | k8s-worker02 | 8 | 16G | 160G | 旧 k8s 集群 |
| 109 | VM | pve2 | jellyfin | 8 | 8G | 100G | |
| 110 | VM | pve2 | harbor | 4 | 8G | 160G | |
| 111 | VM | pve3 | jenkins | 4 | 4G | 50G | |
| 112 | VM | pve4 | idea | 8 | 16G | 200G | NAS 上最新备份是 2026-10-01 |
| 113 | VM | pve2 | prometheus | 2 | 4G | 100G | |
| 114 | VM | pve2 | ubuntu | 8 | 16G | 250G | |
| 115 | VM | pve2 | win11-download | 8 | 8G | 150G | |
| 116 | VM | pve2 | win11 | 4 | 8G | 150G | |
| 117 | VM | pve2 | gitlab | 4 | 4G | 100G | |
| 118 | VM | pve2 | jump | 4 | 8G | 100G | |
| 119 | VM | pve2 | win11-1 | 8 | 16G | 80G | |
| 120 | VM | pve2 | win11-RL | 8 | 8G | 150G | |
| 122 | VM | pve2 | debian-desktop | 8 | 32G | 300G | |
| 123 | VM | pve3 | minio | 2 | 4G | 100G | |
| 124 | VM | pve3 | win11-code | 8 | 32G | 200G | |
| 125 | LXC | pve2 | llm-server | 8 | 16G | 300G | 非特权容器 |
| 126 | VM | pve2 | FabStation | 4 | 4G | 500G | |
| 127 | VM | pve4 | ubuntu-desktop | 8 | 32G | 300G | |
| 128 | VM | pve2 | Dokploy | 1 | 32G | 800G | 旧的 Dokploy，用户确认不需要处理（2026-11-01） |
| 129 | VM | pve2 | mcp-server | 8 | 16G | 300G | |
| **200** | VM | pve3 | **dokploy** | 8 | 16G | 200G | **新的部署平台，开机自启**，见 [../services/dokploy.md](../services/dokploy.md) |

## 各节点分配情况（配置值合计）

| 节点 | 虚拟机数 | vCPU | 内存 | 磁盘分配 / 本地盘容量 |
|---|---|---|---|---|
| pve2 | 19 | 107 | 226G | 3.9T / 1.75T（精简置备，实际已用约 50%） |
| pve3 | 8 | 48 | 106G | 1.0T / 1.75T |
| pve4 | 3 | 24 | 64G | 660G / 0.8T |

pve2 最挤，新服务优先放 pve3。pve4 有死机历史，先不要放重要服务。
