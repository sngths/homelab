# 硬件清单

## pve2 — GMKtec NucBox K6

| 项目 | 配置 |
|---|---|
| CPU | AMD Ryzen 7 7840HS（8 核 16 线程），Radeon 780M |
| 内存 | 64G（系统识别 61G） |
| 硬盘 | KINGBANK KP230 Pro 2TB NVMe |
| 网卡 | `enp2s0`（在用，MAC 84:47:09:31:ea:3a）、`eno1`（未接线）、Wi-Fi |
| 备注 | 安装了 amd64-microcode |

## pve3 — 旧 Intel 小主机（无品牌信息）

| 项目 | 配置 |
|---|---|
| CPU | Intel Xeon E-2286M（8 核 16 线程） |
| 内存 | 64G（系统识别 62G），**从坏掉的 GMKtec M5 上拆过来的** |
| 硬盘 | KINGBANK KP230 Pro 2TB NVMe，**从坏掉的 GMKtec M5 上拆过来的** |
| 网卡 | `eno1`（在用，MAC 30:bf:01:22:20:51）、`enp2s0`（…:52，不要同时接进网桥，会成环）、Wi-Fi |
| 显示 | 接 One-KVM（192.168.1.155） |
| 主板 | AMI Aptio BIOS，Board ID `S210H Series`，BIOS 日期 2020-11-19 |
| 核显 | Intel UHD 630，已开启 GVT-g 切分给虚拟机（见 [../pve/cluster.md](../pve/cluster.md)） |

> ⚠️ **热重启后认不到 NVMe 硬盘**：`reboot` 之后 BIOS 显示 "No NVME Device Found"，停在 BIOS 设置界面。
> 2026-11-01 出现了两次，两次都是**长按电源键关机、拔电再开机**后恢复。
> **在修好之前，pve3 要重启时一律"关机 → 断电 → 开机"，不要直接 reboot。** 待查：刷新 BIOS，或调整 BIOS 里的 NVMe / PCIe 相关设置。

**更换记录**
- 2026-11-01 之前：pve3 是一台 GMKtec M5。主板损坏（通电风扇转，不 POST、HDMI 无输出，拔内存/硬盘测试均无效）。
- 2026-11-01：把 M5 的内存和硬盘装进这台旧 Intel 主机，系统原样启动。因为网卡名变了（`enp1s0` → `eno1`），
  修改了 `/etc/network/interfaces` 的 `bridge-ports`，原文件备份为 `/etc/network/interfaces.bak-m5`。
- 待办：装 `intel-microcode`。

## pve4 — GMKtec NucBox M5

| 项目 | 配置 |
|---|---|
| CPU | AMD Ryzen 7 5700U（8 核 16 线程） |
| 内存 | 64G（系统识别 62G） |
| 硬盘 | KINGBANK KP260 1TB NVMe（MAXIO MAP1602 主控，无 DRAM 缓存） |
| 网卡 | `enp1s0`（在用，Intel I225-V，MAC 84:47:09:28:92:26）、`enp2s0`、Wi-Fi |
| 看门狗 | 主板 SP5100 TCO 硬件看门狗，已启用 |
| 备注 | **有周期性整机卡死的历史**，见 [../runbooks/pve4-freeze.md](../runbooks/pve4-freeze.md)。硬盘空闲约 57°C，偏热 |

## 2026-11-01 健康状况快照

| | CPU 空闲温度 | NVMe 温度 | NVMe 磨损 | 坏块 | 异常断电次数 |
|---|---|---|---|---|---|
| pve2 | 55°C | 48°C | 3% | 0 | 22 |
| pve3 | 49°C | 39°C | 3% | 0 | 53 |
| pve4 | 52°C | 57°C | 3% | 0 | 97 |

查看命令（三台都装了 `lm-sensors`、`nvme-cli`）：`sensors`、`nvme smart-log /dev/nvme0`

## NAS — 群晖，192.168.1.40

- NFS 导出 `/volume1/pve`，在 PVE 里叫存储 `nas`，挂载点 `/mnt/pve/nas`，只存备份。
- 容量约 25T，2026-11-01 清理后剩余约 6.7T。
- SSH 开在 22 端口（`tianxing` 账号，有 sudo），管理命令 `/usr/syno/sbin/synouser`、`synoshare`。DSM 7.2.2，会自动更新系统。
- SMB：协议 SMB1~SMB3，NTLMv1 认证关闭。

### 小米摄像头录像

两台摄像头都通过 SMB 把录像写到 `surveillance/xiaomi_camera_videos/<MAC>/`，用专用账号 `xiaomi-cam`（密码见 credentials.md）。

| 摄像头 | IP | 目录（MAC） |
|---|---|---|
| 1 号 | 192.168.1.137 | `78DF72CD5D8E` |
| 2 号 | 192.168.1.232 | `78DF72E8862B` |

- 1 号以前录过 2024-12-11 ～ 2025-07-12 的录像（约 15760 个文件、2.1T），之后摄像头里的 NAS 配置丢失，停止上传。
- 2026-11-03：新建账号 `xiaomi-cam`（只能读写 `surveillance`，应用权限只开 SMB，已验证），用户在米家 App 里把两台都重新配好，2 号是第一次接入。
- 重新接入后，1 号按保留时长自动删除超期的旧录像（从新往旧删，每分钟约 2000 个）。用户确认旧录像不要了，任其删除。
- 米家 App 里保留时长最多 12 个月，到期自动删除，NAS 不会无限增长。
- 米家 App 配置位置：摄像头 → 设置 → 存储设置 → NAS 网络存储。
- 如果以后摄像头登录不上 NAS，再考虑打开 NTLMv1（会降低 SMB 安全性）。

### 视频（Jellyfin 用）

- 在 `backup` 共享的 `nas1/` 下（`/volume1/backup/nas1`，约 14T）：`video/` 11T、`3t/` 2.7T、`2t/` 432G、`suning/`、`picture/`。视频约 7500 个、13.6T。
- `backup` 共享占了 NAS 大部分空间（14T），用 ACL 权限模式，NFS 也导出给了 192.168.1.0/24。
- 只读账号 `media-ro` 给 pve2 挂载用，见 [../services/jellyfin.md](../services/jellyfin.md)。

## 路由器 — iStoreOS，192.168.1.1

- iStoreOS 22.03.7（OpenWrt），x86_64。SSH 22 端口，`root` 登录（密码见 credentials.md）。
- 外网：电信 PPPoE 拨号，**有公网 IPv4**（2026-11-07 为 `114.221.84.8`，重新拨号会变），另有公网 IPv6 前缀 /60。当天从外网 ping 并在 `pppoe-wan` 抓包确认，回包来自路由器本身。2026-11-08 在路由器临时开了 18080 测试网页，用户用**联通手机流量**打开成功，确认跨运营商可直接访问（测试页已关闭）。带宽约下行 200M、上行 50M。已装但没启用：WireGuard 内核模块、ZeroTier、DDNS 脚本（含 Cloudflare）、Lucky、DDNSTO。
- 跳板机没有路由器的 SSH 密钥，目前只能用密码登录。
- 实测速度（2026-11-07，跳板机直连）：下载约 240 Mbps（腾讯 CDN，10 线程），上传约 57 Mbps（Cloudflare，4 线程）。
- **外网方向放行的端口**（IPv4 和 IPv6 都放行，wan 区默认 DROP，没有端口转发，UPnP 已关闭）：
  | 端口 | 来源 | 说明 |
  |---|---|---|
  | ~~7890 TCP+UDP~~ | PassWall 服务端（`PSW-SERVER` 链） | **2026-11-08 已关闭**（`passwall_server.global.enable=0`，备份 `/etc/config/passwall_server.bak-20261108`）。原来是 2024-09 建的 VLESS 入站，无 TLS、`accept_lan=1`，等于一个不加密的公网回家入口。和 OpenClash 的 7890（局域网 HTTP 代理，OpenClash 已关）不是一回事。关闭后局域网代理 1070/1071 实测正常 |
  | 8897 TCP | 易有云 linkease（fw3 规则） | 在运行，当天看到有外部连接 |
  | ~~18811 TCP~~ | Lucky（`LUCKY` 链） | **2026-11-09 已关闭**（关掉 FileBrowser 的 `AutoFirewall`，删除规则）。原来：没有程序监听。2026-11-09 查明：是 Lucky 内置 **FileBrowser（网页文件管理）** 模块的端口，模块已关闭（`Enable=false`），但开着"自动放行防火墙"（`AutoFirewall=true`），规则残留。Lucky 的端口转发、STUN、DDNS 都是空的；管理页不允许外网访问（`AllowInternetaccess=false`）。Lucky 所有功能都没有规则（定时任务、网络唤醒、反向代理、证书等全空），实际没在用；配置备份 `/root/lucky-config-bak-20261108.tgz` |
- 从外网测 TCP 端口时注意：公司的测试环境会替任意 TCP 连接假应答，结果不能用，要在路由器上用 `tcpdump -ni pppoe-wan` 看包是否真的到达。ICMP 不受影响。
- 装了 OpenClash 0.46.110、PassWall 4.78、PassWall2，**主开关都是关的**：家里设备上网全部直连，不做透明代理。
- 7890 端口原来是 PassWall **服务端**（passwall_server，xray 入站），不是给局域网用的代理；2026-11-08 已关闭，见上方端口表。

### 局域网代理（2026-11-03 开启）

- PassWall 只开了"Socks 服务"（`socks_enabled=1`），主开关 `enabled=0` 保持关闭，所以**只提供代理端口，不接管任何设备的流量**。
- **SOCKS5：`192.168.1.1:1070`**，**HTTP：`192.168.1.1:1071`**，节点"日本-优化"（`4G9M7EQ1`，vmess），出口东京。
- 用途：Jellyfin/MetaTube 刮削（FANZA 只认日本 IP）、家里机器下载 GitHub 等被墙的资源。
- 改之前的配置备份在路由器 `/etc/config/passwall.bak-20261104`。
- 节点来自 6 个机场订阅、共 30 个 vmess 节点；节点失效时在 PassWall 网页"Socks 配置"里换节点（备用：日本-优化2、日本-优化3）。
- 已验证：经代理能访问 JavBus、FANZA、MGStage、GitHub；JavDB、AVBASE 对 curl 返回 Cloudflare 403。不走代理时出口仍是南京。

## One-KVM — 192.168.1.155

- onecloud 刷的 One-KVM（kvmd 3.291），网页登录账号 admin（**默认密码未改**）。
- 目前 HDMI 和 USB 接在 pve3 上，没有接电源控制。
- 视频流设成 MJPEG 才能正常出画面（H.264 模式下显示黑屏）。
- API 要点见 [../runbooks/access.md](../runbooks/access.md)。

## Windows 台式机 — DESKTOP-0GE8DG9，192.168.1.117

- 装了 wsd（workspaced），开启了"执行命令"，是从外面操作家里网络的入口。
- 有 OpenSSH 客户端，临时密钥在 `C:\Users\tianxing\.ssh\pve_claude`。
