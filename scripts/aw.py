#!/usr/bin/env python3
"""aw —— 从本机操作自动化 Windows 虚拟机（VM 202）。

链路：本机 → wsd exec 到台式机 DESKTOP-0GE8DG9 → ssh 到 pve3（键鼠、截屏）或 VM 202（管理命令、传文件）。
键鼠和截屏都在虚拟机外部（QMP）完成，Windows 里没有自动化进程。

用法：
  aw.py shot [out.jpg] [--crop X Y W H [ZOOM]]     截屏（默认 /tmp/aw.jpg），可裁剪放大看小字
  aw.py do "click 640 272" "wait 1" "type abc" "key ret" ... [--shot out.jpg] [--wait N]
                                                   执行一串动作，结束后等 N 秒（默认 1.5）再截屏
                                                   --noshot 不截屏
  aw.py text "中文或任意文本"                         通过剪贴板粘贴（Ctrl+V）到当前输入框
  aw.py put 本地文件 [虚拟机目录]                     复制文件进虚拟机（默认 C:\\Users\\auto\\Desktop\\in）
  aw.py ps "PowerShell 命令"                         在虚拟机里执行管理命令（auto 账号，经 OpenSSH）

动作（do 里每一项）：
  click X Y [left|right|middle] [次数]   move X Y   type ASCII文本   key ctrl-a   scroll N   wait 秒
坐标按 1280x800 屏幕。
"""
import base64, os, re, subprocess, sys, shlex, shutil, time

WIN = 'DESKTOP-0GE8DG9'   # 中转的 Windows 台式机（装了 wsd 和 ssh 密钥）
SELF = 'tianxing-claude'  # 本机在 wsd 里的名字（台式机从这里取文件）
PVE = '192.168.1.3'       # VM 202 所在节点 pve3
VM_IP = '192.168.1.52'
VMID = '202'
XFER = os.path.expanduser('~/imgxfer')
NOISE = re.compile(r'NativeCommandError|RemoteException|所在位置|^\+ |^\s*\+ ~|CategoryInfo|FullyQualifiedErrorId|Permanently added')


def wsd(ps, timeout=120):
    env = dict(os.environ)
    env['no_proxy'] = env.get('no_proxy', '') + ',msg-gw.zczy.ai'
    r = subprocess.run(['wsd', 'exec', WIN, '--timeout', str(timeout), '--', ps],
                       capture_output=True, text=True, env=env, timeout=timeout + 30)
    return '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if not NOISE.search(l))


def ssh_ps(target, remote_cmd, timeout):
    """在台式机上 ssh 到 target 执行 remote_cmd（已转义好的字符串）"""
    return wsd("[Console]::OutputEncoding=[Text.Encoding]::UTF8\n"
               "$o=& ssh.exe -i (Join-Path $env:USERPROFILE '.ssh\\pve_claude') -o BatchMode=yes "
               "-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 %s '%s' 2>&1\n"
               "$o | %% { \"$_\" }; \"[exit=$LASTEXITCODE]\"" % (target, remote_cmd), timeout)


def pve(cmd, timeout=120):
    b = base64.b64encode(cmd.encode()).decode()
    return ssh_ps('root@' + PVE, 'echo %s | base64 -d | bash' % b, timeout)


def vmps(cmd, timeout=120):
    pre = '$ProgressPreference="SilentlyContinue"; [Console]::OutputEncoding=[Text.Encoding]::UTF8; '
    b = base64.b64encode((pre + cmd).encode('utf-16-le')).decode()
    return ssh_ps('auto@' + VM_IP, 'powershell -NoProfile -EncodedCommand ' + b, timeout)


def vminput(args, timeout=120):
    return pve('vminput %s %s' % (VMID, ' '.join(shlex.quote(a) for a in args)), timeout)


def save_shot(out, text):
    m = re.search(r'===SHOT===([A-Za-z0-9+/=\s]+?)===END===', text)
    if not m:
        sys.exit('截屏失败：\n' + text[-2000:])
    open(out, 'wb').write(base64.b64decode(re.sub(r'\s', '', m.group(1))))
    print('截屏已保存', out)


def opt(args, name, n):
    if name in args:
        i = args.index(name); v = args[i + 1:i + 1 + n]; del args[i:i + 1 + n]; return v
    return None


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        sys.exit(__doc__)
    cmd, a = a[0], a[1:]
    if cmd == 'shot':
        crop = opt(a, '--crop', 5 if len(a) >= 6 else 4) or []
        out = a[0] if a else '/tmp/aw.jpg'
        save_shot(out, vminput(['shot'] + crop))
    elif cmd == 'do':
        noshot = '--noshot' in a
        if noshot: a.remove('--noshot')
        out = (opt(a, '--shot', 1) or ['/tmp/aw.jpg'])[0]
        wait = (opt(a, '--wait', 1) or ['1.5'])[0]
        steps = a + ([] if noshot else ['wait %s' % wait, 'shot'])
        r = vminput(['seq'] + steps, timeout=300)
        if noshot:
            print(r)
        else:
            save_shot(out, r)
    elif cmd == 'text':
        # 文本写进虚拟机的临时文件，再用"以 auto 交互身份运行"的计划任务放进剪贴板，最后 Ctrl+V
        b = base64.b64encode(a[0].encode()).decode()
        print(vmps(
            "$f=\"$env:LOCALAPPDATA\\aw-clip.txt\"; [IO.File]::WriteAllBytes($f,[Convert]::FromBase64String('%s'));"
            "if(-not (Get-ScheduledTask aw-clip -EA 0)){"
            " $act=New-ScheduledTaskAction -Execute powershell.exe -Argument ('-NoProfile -WindowStyle Hidden -Command Get-Content -Raw -Encoding UTF8 '+$f+' | Set-Clipboard');"
            " $pr=New-ScheduledTaskPrincipal -UserId auto -LogonType Interactive;"
            " Register-ScheduledTask aw-clip -Action $act -Principal $pr -Force | Out-Null};"
            "Start-ScheduledTask aw-clip -EA Stop; Start-Sleep -m 800; while((Get-ScheduledTask aw-clip).State -eq 'Running'){Start-Sleep -m 300};"
            "Remove-Item $f; 'clip ok'" % b))
        print(vminput(['key', 'ctrl-v']))
    elif cmd == 'put':
        src = a[0]; dst = a[1] if len(a) > 1 else r'C:\Users\auto\Desktop\in'
        name = os.path.basename(src)
        os.makedirs(XFER, exist_ok=True); shutil.copy(src, os.path.join(XFER, name))
        print(wsd(
            "$t=Join-Path $env:TEMP 'aw-%s'; wsd get %s:imgxfer/%s $t | Out-Null;"
            "& ssh.exe -i (Join-Path $env:USERPROFILE '.ssh\\pve_claude') -o BatchMode=yes auto@%s "
            "'powershell -NoProfile -Command New-Item -ItemType Directory -Force \"%s\" | Out-Null' 2>&1 | Out-Null;"
            "& scp.exe -i (Join-Path $env:USERPROFILE '.ssh\\pve_claude') -o BatchMode=yes $t 'auto@%s:%s/%s' 2>&1;"
            "Remove-Item $t; \"[exit=$LASTEXITCODE]\""
            % (name, SELF, name, VM_IP, dst, VM_IP, dst.replace('\\', '/'), name), 600))
        os.remove(os.path.join(XFER, name))
    elif cmd == 'ps':
        print(vmps(a[0], int((opt(a, '--timeout', 1) or ['120'])[0])))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
