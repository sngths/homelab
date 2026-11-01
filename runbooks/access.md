# 远程访问家里设备的方式

## 入口：Windows 台式机 + wsd

外面的机器通过 wsd 连到家里的 Windows 台式机 `DESKTOP-0GE8DG9`（192.168.1.117），再从它访问家里网络：

```bash
wsd exec DESKTOP-0GE8DG9 --timeout 60 -- "<PowerShell 命令>"
wsd get --force DESKTOP-0GE8DG9:<路径> <本地路径>
```

- 单次 exec 的超时最长 600 秒；耗时长的任务在目标机器上用 `systemd-run` 或 `nohup` 放到后台跑。
- 如果本机设了 HTTP 代理（比如 saiai 本地代理），wsd 会报"机器认证失败"，要把 `msg-gw.zczy.ai` 加进 `no_proxy`。
- Windows PowerShell 5 的几个坑：
  - 变量名**不区分大小写**（`$t` 会覆盖 `$T`）
  - `TYPE` 是 Get-Content 的别名，不能拿来当函数名
  - 传给 ssh.exe 的参数里双引号会被吃掉，复杂命令先 base64 编码，再在远端 `base64 -d | bash`
  - 自签名证书需要一个 TrustAll 的 ICertificatePolicy
  - `Invoke-RestMethod` 会丢掉 Cookie 头，要用 WebClient / HttpWebRequest

## SSH 到 PVE 节点

- 临时密钥：Windows 上的 `C:\Users\tianxing\.ssh\pve_claude`，注释是 `claude-pve-upgrade`
- 公钥加在 `/etc/pve/priv/authorized_keys`。这个文件在集群内共享，三台节点同时生效
- 这把公钥也通过 cloud-init 放进了 VM 200 的 `ubuntu` 用户和 VM 201 的 `debian` 用户
- 撤销：
  ```bash
  sed -i '/claude-pve-upgrade/d' /etc/pve/priv/authorized_keys   # 任意一台 PVE 节点上执行
  ```
  Windows 上删除 `pve_claude*` 两个文件。

```powershell
ssh.exe -i $env:USERPROFILE\.ssh\pve_claude -o BatchMode=yes root@192.168.1.3 "<命令>"
```

## PVE API

- 登录：`POST https://<ip>:8006/api2/json/access/ticket`（username=root@pam），返回 ticket 和 CSRFPreventionToken
- 请求时带 Cookie `PVEAuthCookie=<ticket>`；非 GET 请求还要加头 `CSRFPreventionToken`
- ticket 有效期约 2 小时
- 常用接口：`/cluster/resources`、`/cluster/backup`（开关备份任务时参数名是 `enabled`）、
  `/nodes/<node>/storage/nas/content`、`/nodes/<node>/qemu/<id>/status/{start,shutdown}`

## One-KVM（192.168.1.155）API

- 认证：请求头 `X-KVMD-User` / `X-KVMD-Passwd`
- 截图：`GET /api/streamer/snapshot`
  - **注意**：视频流只有在有 websocket 客户端连着时才会运行。没人连的时候截图会返回 503，要先连上
    `wss://192.168.1.155/api/ws?stream=1` 并保持连接
- 键盘输入文字：`POST /api/hid/print?limit=0`（body 是要输入的文本）
- 单个按键：`POST /api/hid/events/send_key?key=Enter`
- 通过 KVM 登录 pve3 控制台：依次输入 `root\n`、密码 `\n`、命令 `\n`，再截图看结果
