# Dokploy 部署平台（VM 200）

2026-11-01 创建，用来快速部署软件项目和数据库。

## 虚拟机

| 项目 | 内容 |
|---|---|
| VMID / 名称 | 200 / dokploy，在 pve3 上，开机自启 |
| 系统 | Ubuntu 24.04 LTS（cloud image + cloud-init） |
| 配置 | 8 核 / 16G / 200G（local-lvm，开了 discard 和 iothread） |
| CPU 类型 | `x86-64-v3`，可以在 Intel（pve3）和 AMD（pve2 / pve4）节点之间迁移 |
| IP | 192.168.1.50/24，网关 192.168.1.1，DNS 192.168.1.1 和 223.5.5.5 |
| 登录 | 用户 `ubuntu`，SSH 密钥 + 控制台密码（**密码不在这里**），有 sudo |
| 其他 | 已装 qemu-guest-agent，时区 Asia/Shanghai |

创建命令（以后再建同类虚拟机可以照着做）：

```bash
# 在 pve3 上。中科大的 cloud image 会返回 403，用清华镜像
wget https://mirrors.tuna.tsinghua.edu.cn/ubuntu-cloud-images/noble/current/noble-server-cloudimg-amd64.img -O /root/noble.img
qm create 200 --name dokploy --memory 16384 --cores 8 --cpu x86-64-v3 \
  --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-single --agent enabled=1 --ostype l26 --onboot 1
qm set 200 --scsi0 local-lvm:0,import-from=/root/noble.img,iothread=1,discard=on,ssd=1
qm resize 200 scsi0 200G
qm set 200 --ide2 local-lvm:cloudinit --boot order=scsi0 --serial0 socket
qm set 200 --ciuser ubuntu --cipassword '<密码>' --sshkeys <公钥文件> \
  --ipconfig0 ip=192.168.1.50/24,gw=192.168.1.1 --nameserver '192.168.1.1 223.5.5.5'
qm start 200
```

`/root/noble.img` 留在 pve3 上了，可以重复使用。

## 系统里的配置

- apt 源：清华镜像（`/etc/apt/sources.list.d/ubuntu.sources`）
- Docker CE：清华 docker-ce 源，版本 29.9.2，带 compose 插件
- `/etc/docker/daemon.json`：

  ```json
  {
    "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"],
    "log-driver": "json-file",
    "log-opts": {"max-size": "50m", "max-file": "3"}
  }
  ```

## Dokploy

- 面板：http://192.168.1.50:3000
- 运行方式：Docker Swarm（advertise 192.168.1.50）
  - 服务：`dokploy`、`dokploy-postgres`（postgres:16）
  - 容器：`dokploy-traefik`（traefik:v3.6.25），占用 80 / 443
- 安装命令（GitHub 不通，要显式指定版本和 IP）：

  ```bash
  curl -fsSL https://dokploy.com/install.sh -o /root/dokploy-install.sh
  DOKPLOY_VERSION=latest ADVERTISE_ADDR=192.168.1.50 bash /root/dokploy-install.sh
  ```

- **坑**：Swarm 创建服务时会直接去 registry-1.docker.io 解析镜像，不走 registry-mirrors，所以安装卡在
  "overall progress: 0 out of 1 tasks"。解决办法是先手动 `docker pull` 好所有镜像。
  其中 `dokploy/dokploy` 镜像在国内镜像站很慢，是转运过来的（见 [../runbooks/docker-image-relay.md](../runbooks/docker-image-relay.md)）。

## 待办

- [ ] 配每日备份（PBS）
- [ ] 改 ubuntu 用户的控制台密码
