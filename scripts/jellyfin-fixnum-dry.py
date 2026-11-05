#!/usr/bin/env python3
# 从文件名提取番号 → MetaTube 搜索 → 番号完全一致才记录（DRY=1 只记录不应用）
import json,re,os,sys,urllib.request,urllib.parse,concurrent.futures as cf
J='http://127.0.0.1:8096'; MT='http://127.0.0.1:8080'
TOK=[l.split('=',1)[1].strip() for l in open('/etc/default/metatube') if l.startswith('TOKEN=')][0]
JT=os.environ['JT']; DRY=os.environ.get('DRY','1')=='1'
JH={'Authorization':'MediaBrowser Client="fixnum", Device="ct", DeviceId="fixnum1", Version="1", Token="%s"'%JT,'Content-Type':'application/json'}
def get(url,h): return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=90))
items=get(J+'/Items?Recursive=true&IncludeItemTypes=Movie&Fields=ProviderIds,Path&Limit=100000',JH)['Items']
todo=[i for i in items if not i.get('ProviderIds')]
BAD={'IMG','DSC','MOV','VID','HEIC','MP','PART','CD','DISC','HD','FHD','MR','IPX0'}
pat=re.compile(r'(?<![A-Za-z])([A-Za-z]{2,6})[-_ ]?0*(\d{3,5})(?!\d)')
def cand(path):
    f=os.path.splitext(path.split('/')[-1])[0]
    f=re.sub(r'^[\w.-]*\.(com|cc|net|top|xyz)[@-]','',f,flags=re.I)   # 去掉 gc2048.com- 4k2.com@ 之类前缀
    if re.search(r'[一-鿿]',f) and not re.match(r'^\[?[A-Za-z]{2,6}-\d{3,5}',f): return None
    m=pat.search(f)
    if not m or m.group(1).upper() in BAD: return None
    n=m.group(2); n=n if len(n)>=3 else n.zfill(3)
    return '%s-%s'%(m.group(1).upper(),n.zfill(3))
def norm(s): return re.sub(r'[^A-Z0-9]','',s.upper()).replace('00','0') if s else ''
def work(i):
    c=cand(i['Path'])
    if not c: return None
    try: r=get(MT+'/v1/movies/search?'+urllib.parse.urlencode({'q':c,'fallback':'true'}),{'Authorization':'Bearer '+TOK}).get('data') or []
    except Exception as e: return (i,c,None,'搜索失败 %s'%e)
    ok=[m for m in r if norm(m['number'])==norm(c)]
    if not ok: return (i,c,None,'无一致结果')
    pref={'FANZA':0,'MGS':1,'JAV321':2}
    ok.sort(key=lambda m:pref.get(m['provider'],9))
    return (i,c,ok,'')
res=[]
with cf.ThreadPoolExecutor(4) as ex:
    for x in ex.map(work,todo):
        if x: res.append(x)
hit=[x for x in res if x[2]]
print('无资料影片',len(todo),'提取到番号',len(res),'可匹配',len(hit),flush=True)
out=open('/root/fixnum-%s.tsv'%('dry' if DRY else 'apply'),'w')
for i,c,ok,err in res:
    out.write('\t'.join([c, ok[0]['provider']+':'+ok[0]['id'] if ok else err, (ok[0].get('title') or '')[:40] if ok else '', i['Path']])+'\n')
out.close()
if DRY: sys.exit()
applied=fail=0
for i,c,ok,err in hit:
    done=False
    for m in ok[:3]:   # FANZA 资料不全时换下一个来源
        body={'Name':c,'ProviderIds':{'MetaTube':'%s:%s'%(m['provider'],m['id'])},'SearchProviderName':'MetaTube'}
        try:
            urllib.request.urlopen(urllib.request.Request(J+'/Items/RemoteSearch/Apply/%s?ReplaceAllImages=true'%i['Id'],data=json.dumps(body).encode(),headers=JH,method='POST'),timeout=180)
            it=get(J+'/Items/%s?Fields=ProviderIds'%i['Id'] if False else J+'/Users/%s/Items/%s'%(os.environ['UID_'],i['Id']),JH)
            if it.get('ProviderIds'): done=True; break
        except Exception as e: pass
    applied+=done; fail+=(not done)
    if (applied+fail)%50==0: print('进度',applied,fail,flush=True)
print('应用成功',applied,'失败',fail)
