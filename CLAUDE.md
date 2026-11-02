# CLAUDE.md

## 语言

**始终用中文和用户交流。** 包括回复、提问、总结、提交信息和文档。只有命令、代码、路径、技术名词保持原样。

## 这个项目是什么

家里 PVE 集群和周边设备（NAS、One-KVM、Windows 台式机、Dokploy、PBS）的文档仓库，推送到 GitHub 私有仓库 `sngths/homelab`。

- 先读 [README.md](README.md)：IP 分配表、目录、待办。
- 访问家里设备的方法见 [runbooks/access.md](runbooks/access.md)：主入口是跳板机 `home-jump`（wsd exec 后 SSH）；备用入口是 Windows 台式机 `DESKTOP-0GE8DG9`。
- 账号密码见 [credentials.md](credentials.md)（明文，这是用户的决定，仓库必须保持私有）。

## 约定

- 改了家里设备的配置，要同步更新对应的文档，然后提交并推送。
- 改了密码，要同步更新 `credentials.md`。
- 关机、重启、删除数据、删除备份这类操作，先征得用户同意。
- 写进文档的事实（版本、IP、配置）要实际查过，不要凭记忆。
