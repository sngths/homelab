#!/usr/bin/env python3
# 按试运行结果批量"识别"：文件名番号与候选番号完全一致才应用；跳过分辨率误配
import json,re,os,urllib.request
J='http://127.0.0.1:8096'; JT=os.environ['JT']
H={'Authorization':'MediaBrowser Client="fixnum", Device="ct", DeviceId="fixnum1", Version="1", Token="%s"'%JT,'Content-Type':'application/json'}
def req(m,p,b=None):
    r=urllib.request.urlopen(urllib.request.Request(J+p,data=json.dumps(b).encode() if b is not None else None,headers=H,method=m),timeout=180)
    t=r.read(); return json.loads(t) if t else None
rows=[l.rstrip('\n').split('\t') for l in open('/root/fixnum-dry.tsv')]
rows=[r for r in rows if not r[1].startswith(('搜索失败','无一致')) and not re.search(r'-(480|720|1080|1440|2160)$',r[0])]
items={i['Path']:i for i in req('GET','/Items?Recursive=true&IncludeItemTypes=Movie&Fields=ProviderIds,Path&Limit=100000')['Items']}
norm=lambda s:re.sub(r'[^A-Z0-9]','',re.sub(r'(?<=[A-Z])0+(?=\d)','',s.upper()))
pref={'FANZA':0,'MGS':1,'JAV321':2}
ok=fail=skip=0; log=open('/root/fixnum-apply.tsv','w')
for num,_,_,path in rows:
    it=items.get(path)
    if not it or it.get('ProviderIds',{}).get('MetaTube'): skip+=1; continue
    try: cands=req('POST','/Items/RemoteSearch/Movie',{'ItemId':it['Id'],'SearchInfo':{'Name':num},'SearchProviderName':'MetaTube'})
    except Exception as e: cands=[]
    def cnum(c): m=re.match(r'\[\w+\]\s*(\S+)',c['Name']); return m.group(1) if m else ''
    cands=[c for c in cands if norm(cnum(c))==norm(num)]
    cands.sort(key=lambda c:pref.get(c['ProviderIds']['MetaTube'].split(':')[0],9))
    done=''
    for c in cands[:3]:
        try:
            req('POST','/Items/RemoteSearch/Apply/%s?replaceAllImages=true'%it['Id'],c)
            x=req('GET','/Items/%s?Fields=ProviderIds,People'%it['Id'])
            if x.get('ProviderIds',{}).get('MetaTube') and x.get('ImageTags',{}).get('Primary'): done=c['ProviderIds']['MetaTube']; break
        except Exception as e: pass
    if done: ok+=1
    else: fail+=1
    log.write('\t'.join([num,done or '失败',path])+'\n'); log.flush()
print('成功',ok,'失败',fail,'跳过',skip)
