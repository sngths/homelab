# 跳板机 jump（CT 203）

2026-11-02 创建。替代 Windows 台式机，作为 Claude 从外面进入家里网络的常驻入口。台式机保留为备用通道。

| 项目 | 配置 |
|---|---|
| 位置 | pve2，LXC 非特权容器，`nesting=1`，开机自启 `startup order=1` |
| 系统 | Debian 12（模板 `debian-12-standard_12.2-1`），软件源中科大，时区 Asia/Shanghai |
| 资源 | 1 核、512M 内存 + 512M swap、4G 硬盘（local-lvm） |
| 网络 | 192.168.1.53/24，网关、DNS 192.168.1.1 |
| 软件 | curl、openssh-client、cron、tmux、python3、sudo |
| 用户 | `root`（密码见 credentials.md）；`jump`（跑 wsd，SSH 密钥 `jump@homelab`） |

选 pve2 的原因：pve3 有热重启认不到 NVMe 的问题且跑着 VM 202，pve4 有死机历史，pve2 最稳定。

## 进度

- [x] 创建容器、装基础包、建 `jump` 用户、生成密钥（2026-11-02）
- [ ] 把 `jump@homelab` 公钥授权到 PVE 三台（root）、VM 200（ubuntu）、VM 201（debian）、VM 202（auto）
- [ ] 用官方接入命令安装 wsd，用户扫码认领，开启"执行命令"
- [ ] `aw` 等工具改为走 jump，Windows 台式机降为备用
