# 家里网络拉 Docker 镜像慢 / 拉不下来

## 现状（2026-11-01 实测）

家里网络到国内镜像站的速度很快（清华约 38MB/s），但连不上 Docker Hub、GitHub、raw.githubusercontent.com。

Docker Hub 的镜像加速站测速（拉 node:22-slim，20 秒平均）：

| 镜像站 | 结果 |
|---|---|
| docker.m.daocloud.io | 约 2.1MB/s（热门镜像） |
| docker.1ms.run | 约 350KB/s，可用 |
| dockerproxy.net、hub.rat.dev | 约 200–270KB/s |
| docker.nju.edu.cn、docker.xuanyuan.me、docker.hlmirror.com | 不可用 |

热门镜像（postgres、redis、node 等）一般很快。冷门镜像（比如 `dokploy/dokploy`）只有 76–260KB/s，800MB 要一到三个小时。

另外 Docker **Swarm 服务**创建时会直接去 registry-1.docker.io 解析镜像，不走 `registry-mirrors`，所以会卡住。
先在节点上手动 `docker pull`，再创建服务。

## 转运办法

在能访问 Docker Hub 的机器上下载，经家里的 Windows 电脑（wsd）转到目标机器上导入。

1. 在外面的机器上，用 [`scripts/ociget.py`](../scripts/ociget.py) 下载 linux/amd64 镜像，打包成 OCI 格式的 tar：

   ```bash
   python3 -I scripts/ociget.py dokploy/dokploy latest ~/imgxfer/dokploy.tar
   python3 -I scripts/ociget.py traefik v3.6.25 ~/imgxfer/traefik.tar   # 官方镜像不用写 library/
   ```

2. 在家里的 Windows 上从外面那台机器拉取（wsd 实测约 25MB/s），再 scp 到目标虚拟机：

   ```powershell
   wsd get --force tianxing-claude:imgxfer/dokploy.tar "$env:USERPROFILE\imgxfer\dokploy.tar"
   scp -i $env:USERPROFILE\.ssh\pve_claude "$env:USERPROFILE\imgxfer\dokploy.tar" ubuntu@192.168.1.50:/tmp/
   ```

3. 在目标机器上导入：

   ```bash
   docker load -i /tmp/dokploy.tar && rm /tmp/dokploy.tar
   ```

800MB 的镜像，整个过程大约一分钟。

## 长期办法

在家里网络里配一个代理（比如在路由器上，或者给 Docker daemon 配 HTTP 代理），就不用再转运了。
