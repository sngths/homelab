#!/usr/bin/env python3
"""Download a linux/amd64 image from Docker Hub into an OCI layout tar that `docker load` accepts.
usage: ociget.py <repo> <tag> <out.tar>     e.g. ociget.py dokploy/dokploy latest dokploy.tar
"""
import hashlib, io, json, os, sys, tarfile, tempfile, urllib.request

repo, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
if "/" not in repo:
    repo = "library/" + repo
REG = "https://registry-1.docker.io"
ACC_IDX = "application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json"
ACC_MAN = "application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json"


def token():
    u = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"
    return json.load(urllib.request.urlopen(u, timeout=30))["token"]


TOK = token()


def get(path, accept=None):
    req = urllib.request.Request(REG + path, headers={"Authorization": f"Bearer {TOK}", **({"Accept": accept} if accept else {})})
    return urllib.request.urlopen(req, timeout=300)


r = get(f"/v2/{repo}/manifests/{tag}", ACC_IDX + "," + ACC_MAN)
top = json.loads(r.read())
if "manifests" in top:
    d = [m for m in top["manifests"] if m.get("platform", {}).get("architecture") == "amd64" and m["platform"].get("os") == "linux"][0]
    r = get(f"/v2/{repo}/manifests/{d['digest']}", ACC_MAN)
    man_bytes = r.read()
    man_type = d["mediaType"]
else:
    man_bytes = json.dumps(top).encode()
    man_type = top.get("mediaType", "application/vnd.oci.image.manifest.v1+json")
man = json.loads(man_bytes)
man_digest = "sha256:" + hashlib.sha256(man_bytes).hexdigest()

tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out)))
bdir = os.path.join(tmp, "blobs", "sha256")
os.makedirs(bdir)
with open(os.path.join(bdir, man_digest[7:]), "wb") as f:
    f.write(man_bytes)
for desc in [man["config"]] + man["layers"]:
    dg = desc["digest"]
    p = os.path.join(bdir, dg[7:])
    h = hashlib.sha256()
    with get(f"/v2/{repo}/blobs/{dg}") as resp, open(p, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)
    assert "sha256:" + h.hexdigest() == dg, f"digest mismatch {dg}"
    print(f"  {dg[:19]} {desc['size']/1e6:.1f} MB ok", flush=True)

name = ("docker.io/" + repo + ":" + tag)
index = {"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json",
         "manifests": [{"mediaType": man_type, "digest": man_digest, "size": len(man_bytes),
                        "annotations": {"io.containerd.image.name": name, "org.opencontainers.image.ref.name": tag}}]}
with open(os.path.join(tmp, "index.json"), "w") as f:
    json.dump(index, f)
with open(os.path.join(tmp, "oci-layout"), "w") as f:
    json.dump({"imageLayoutVersion": "1.0.0"}, f)
with tarfile.open(out, "w") as t:
    for n in ("oci-layout", "index.json", "blobs"):
        t.add(os.path.join(tmp, n), arcname=n)
import shutil
shutil.rmtree(tmp)
print(f"wrote {out} ({os.path.getsize(out)/1e6:.0f} MB) as {name}")
