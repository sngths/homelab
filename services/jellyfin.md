# Jellyfin 影音服务器（CT 204）

2026-11-03 新建，替代已删除的旧 VM 109 `jellyfin`（Jellyfin 10.9.8，2024-08 之后没再用过）。

## 基本信息

| 项目 | 值 |
|---|---|
| 位置 | pve2，CT 204 `jellyfin`，无特权 LXC，开机自启 |
| 系统 | Debian 12，2 核、2G 内存（+512M swap）、32G 硬盘（local-lvm） |
| 地址 | http://192.168.1.54:8096 |
| 版本 | Jellyfin 12.4.0，jellyfin-ffmpeg8 8.1.3 |
| 账号 | 管理员 `tianxing`，容器 root，密码都在 [../credentials.md](../credentials.md) |
| 备份 | 已加入 `daily-pbs`（每天 03:00）。NAS 上的视频不在备份范围内 |

放在 pve2 的原因：pve2 平时几乎空闲（只跑跳板机），而且 780M 核显比 pve3 的 UHD 630 强，还没有被其他虚拟机占用。

## 视频来源（NAS 只读）

- 视频在群晖 `backup` 共享的 `nas1/` 目录下（`/volume1/backup/nas1`，约 14T，其中视频约 7500 个、13.6T）。
- 链路：群晖 → pve2 宿主机用 SMB 只读挂载到 `/mnt/nas-backup` → 映射进容器 `/media/nas`（`mp0`，`ro=1`）。
- 宿主机 `/etc/fstab`：
  ```
  //192.168.1.40/backup /mnt/nas-backup cifs ro,vers=3.0,credentials=/root/.nas-media-ro.cred,uid=100000,gid=100000,file_mode=0444,dir_mode=0555,iocharset=utf8,_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30 0 0
  ```
- NAS 账号 `media-ro`：只对 `backup` 有只读权限（`backup` 是 ACL 模式，权限写在 ACL 里，`synoshare --get` 的列表里看不到），密码在 `/root/.nas-media-ro.cred` 和 credentials.md。
- 为什么不用 NFS：群晖的 NFS 只认 root，无特权容器里的进程在宿主机上是 uid 100000 以上，读不到。用 SMB 并把文件属主映射成 100000，容器里所有用户都能读、都不能写。

## 核显（AMD Radeon 780M）

- `dev0: /dev/dri/renderD128,gid=106`（容器里 `render` 组是 106），`jellyfin` 用户已加入 `render`、`video` 组。
- 转码设置：VAAPI，设备 `/dev/dri/renderD128`，硬解 h264/hevc/mpeg2/vc1/vp8/vp9/av1，开启硬件编码、HEVC 编码、色调映射。
- 验证：`sudo -u jellyfin /usr/lib/jellyfin-ffmpeg/vainfo --display drm --device /dev/dri/renderD128`，能列出 H.264/HEVC Main10 编解码、AV1 解码。

## 媒体库

| 库名 | 类型 | 路径 |
|---|---|---|
| 按文件夹 | 家庭视频（按文件夹浏览） | `/media/nas/nas1/video`、`/media/nas/nas1/3t`、`/media/nas/nas1/2t` |

- 关闭了 trickplay（进度条预览图）和章节图片提取：13T 视频全跑一遍要好几天，还很占硬盘。需要时在媒体库设置里打开。
- 关闭了实时监控（SMB 上不可靠），新增视频后手动扫描或等每日定时扫描。

## 软件源

- Debian：中科大镜像。
- Jellyfin：**南京大学镜像** `https://mirrors.nju.edu.cn/jellyfin/debian`（`/etc/apt/sources.list.d/jellyfin.sources`），签名密钥 `/etc/apt/keyrings/jellyfin.gpg`，指纹 `4918AABC486CA052358D778D49023CD01DE21A7B`。
- 官方源 repo.jellyfin.org 从家里下载只有约 10KB/s，装不动；清华、阿里、上交、中科大都没有 Jellyfin 镜像。

## 待做

- [ ] 装 MetaTube 插件（JavScraper 的继任者），给文件名带番号的视频（约 2860 个、9.9T）刮削封面和信息，需要另跑后端服务，刮削要走代理。
- [ ] 清理 `nas1` 里的垃圾文件（需用户确认）：迅雷未完成文件 158 个约 497G，旧回收站残留约 25G，疑似重复文件约 720G。
- [ ] 家里其他人如果也用 Jellyfin，给他们单独建账号，并且不开放这个媒体库。
- [ ] 在外面看：用 Tailscale 之类组网，不开公网端口。
