# Jellyfin 影音服务器（CT 204）

2026-11-03 新建，替代已删除的旧 VM 109 `jellyfin`（Jellyfin 10.9.8，2024-08 之后没再用过）。

## 基本信息

| 项目 | 值 |
|---|---|
| 位置 | pve2，CT 204 `jellyfin`，无特权 LXC，开机自启 |
| 系统 | Debian 12，8 核、8G 内存（+1G swap）、32G 硬盘（local-lvm） |
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
| 视频 | 电影，元数据只用 MetaTube，图片 MetaTube → 截图兜底，语言日语/日本 | `/media/nas/nas1/` 下的 `video`、`3t/e/download`、`3t/e/BaiduYunDownload`、`3t/e/迅雷下载`、`2t/g/电影` |

- 2026-11-04 建，替代原来的"按文件夹"（家庭视频类型）和"番号测试"两个库。**两个库不能用重叠的目录**：同一个文件只会归到一个库，"番号测试"的目录包含在"按文件夹"里，结果一直是 0 部影片。
- 想按文件夹浏览：已打开服务器设置 `EnableFolderView`（控制台 → 媒体库 → 显示 → 显示文件夹视图），首页会多一个"文件夹"入口。
- 没有番号的视频刮削不到，按文件名显示，封面是视频截图。偶尔会把普通文件名误配到某个作品上，可以在网页上对该影片"识别"手动改，或者删掉元数据。
- 改库之前的备份：容器里 `/root/jellyfin-before-merge-lib.tgz`（配置）、`/root/jellyfin.db.before-merge-lib`（数据库，1.3G），确认新库没问题后可以删掉。
- 2026-11-04 按用户确认缩小了范围：不再包含整个 `2t`、`3t`，排除了 `2t/f/D盘备份`（旧电脑软件备份）、`2t/g/250ssd`、`2t/g/.Trashes`、课程视频、`3t/e/系统镜像` 等。原因是这些目录里大量 `.img`/`.bin`/`.iso` 被当成视频，扫描卡在上面好几个小时。NAS 是只读挂载，没法放 `.ignore`，只能靠库路径排除。
- 关闭了 trickplay（进度条预览图）和章节图片提取：13T 视频全跑一遍要好几天，还很占硬盘。需要时在媒体库设置里打开。
- 关闭了实时监控（SMB 上不可靠），新增视频后手动扫描或等每日定时扫描。

## 软件源

- Debian：中科大镜像。
- Jellyfin：**南京大学镜像** `https://mirrors.nju.edu.cn/jellyfin/debian`（`/etc/apt/sources.list.d/jellyfin.sources`），签名密钥 `/etc/apt/keyrings/jellyfin.gpg`，指纹 `4918AABC486CA052358D778D49023CD01DE21A7B`。
- 官方源 repo.jellyfin.org 从家里下载只有约 10KB/s，装不动；清华、阿里、上交、中科大都没有 Jellyfin 镜像。

## MetaTube 刮削（2026-11-03 装）

给文件名带番号的视频抓封面、标题、演员、标签。分两部分，都在 CT 204 里：

| 部分 | 说明 |
|---|---|
| 后端 `metatube-server` | v1.4.0，**从源码编译**（官方 v1.4.0 没发 Linux 程序包；源码提交 `c0e053f8` 已和 GitHub 标签核对一致）。程序 `/usr/local/bin/metatube-server`，systemd 服务 `metatube`，`metatube` 用户运行，只监听 `127.0.0.1:8080`，数据库 SQLite `/var/lib/metatube/metatube.db` |
| 后端配置 | `/etc/default/metatube`：`TOKEN`（访问令牌）、`HTTP(S)_PROXY=socks5://192.168.1.1:1070`（路由器的日本节点代理，FANZA 只认日本 IP） |
| Jellyfin 插件 | MetaTube 2025.1102.2200.0（官方最后一版，给 10.11 做的），在 12.4 上加载正常、搜索正常。目录 `/var/lib/jellyfin/plugins/MetaTube_2025.1102.2200.0/`，MD5 已按官方清单校验 |
| 插件设置 | 后端 `http://127.0.0.1:8080` + 令牌；开启名称模板 `{number} {title}`；翻译关闭（标题是日文） |

- 实测：FANZA、MGS、JAV321 都能返回结果和封面；JavBus、JavDB 等对 curl 有 Cloudflare 拦截。
- **升级 Jellyfin 前先确认插件还兼容**。插件很久没更新，Jellyfin 大版本升级后可能失效。装插件前的配置备份在 `/root/jellyfin-before-metatube.tgz`（含 /etc/jellyfin、config、data、plugins）。
- 这个容器**不能拍快照**（PVE 不支持带宿主机目录映射 mp0 的容器做快照），改动前用 tar 备份。

### 补刮（文件名里有番号、但没刮到的）

- 原因：影片单独放在一个文件夹里时，Jellyfin 用**文件夹名**当片名去搜，像 `SSNI081MP4`、`ABP627CMP4` 这种 MetaTube 认不出番号；还有一些 FANZA 返回"资料不全"（500）。
- 脚本（容器里 `/root/`，仓库 `scripts/`）：
  1. `jellyfin-fixnum-dry.py`：从**文件名**提取番号去 MetaTube 搜，只记录番号完全一致的结果到 `/root/fixnum-dry.tsv`，不改任何东西。
  2. `jellyfin-fixnum-apply.py`：按上面的结果调用 Jellyfin 的"识别"（`/Items/RemoteSearch/Apply`），来源优先 FANZA → MGS → JAV321，跳过把 480/720/1080/2160 当番号的误配（例如 `Big Dildo_1080p` 被认成 `DILDO-1080`）。
  - 运行：在容器里 `JT=<Jellyfin 令牌> DRY=1 python3 -I /root/fixnum.py`，再 `JT=<令牌> python3 -I /root/fixnum-apply.py`。
- 2026-11-05 跑过一次：修好 196 部（147 个作品）。约 6800 部没资料的是国产、推特、欧美等本来就没有番号的视频。
- 定时扫描：从默认每 12 小时改成**每周六 20:00 UTC**（北京时间周日 04:00，避开 03:00 的 PBS 备份）。每次扫描都会把没资料的影片重新搜一遍，太频繁没意义。新下载了视频就在网页上手动扫描。

## 已知问题

- 2026-11-03 第一次全库扫描到 77% 时，Jellyfin 内存超过 2G 被 OOM 杀掉，自动重启后扫描没有继续。2026-11-04 把内存调到 4G、swap 调到 1G（`pct set 204 --memory 4096 --swap 1024`，不用重启），并重新扫描。
- 2026-11-04 19:00（UTC）又一次 OOM：给 8K 视频截图的 ffmpeg 单个进程占了 3.5G，撑爆 4G，systemd 默认会把整个 jellyfin 服务停掉，扫描中止。处理：内存调到 8G，并加了 `/etc/systemd/system/jellyfin.service.d/oom.conf`（`OOMPolicy=continue`），以后只杀掉 ffmpeg，Jellyfin 和扫描继续。
- 2026-11-04 为了加快刮削：容器从 2 核加到 8 核（`pct set 204 --cores 8`），`/etc/jellyfin/system.xml` 里 `LibraryScanFanoutConcurrency`、`LibraryMetadataRefreshConcurrency` 从 0（=核数）改成 8（改前备份 `system.xml.bak-20261104`）。新建影片从每分钟约 8 部提高到约 26 部。没再往上加，是怕并发太高被 FANZA 限流。
- 第一次扫描很慢：要经 SMB 遍历约 3.5 万个文件/目录，Jellyfin 单核满载。期间重启 Jellyfin 会让扫描从头开始。

## 待做

- [x] 装 MetaTube（2026-11-03，见上）
- [x] 建正式的番号库（2026-11-04，"视频"库）
- [ ] 清理 `nas1` 里的垃圾文件（需用户确认）：迅雷未完成文件 158 个约 497G，旧回收站残留约 25G，疑似重复文件约 720G。
- [ ] （用户同意，暂缓）短片分库：约 4000 个小于 100M 的视频混在"视频"库里。方案：容器里建两个符号链接目录（≥100M → `正片`，<100M → `短片`，保持 NAS 原目录结构，顺便过滤 iso/img），分别建"视频"（电影 + MetaTube）和"短片"（家庭视频、不刮削）两个库，路径不同就不会冲突；每周扫描前用脚本同步链接。代价：全部影片重建一次（MetaTube 有缓存），播放记录丢失，补刮脚本要再跑一遍。
- [ ] 家里其他人如果也用 Jellyfin，给他们单独建账号，并且不开放这个媒体库。
- [ ] 在外面看：用 Tailscale 之类组网，不开公网端口。
