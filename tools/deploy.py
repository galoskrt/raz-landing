# -*- coding: utf-8 -*-
"""Push the site to tom-harush.co.il/raz-meir-cohen/ over FTPS.

Only changed files go up, tracked by a local sha1 manifest, so a copy tweak
is a two second deploy instead of re-sending every icon.

    python tools/deploy.py            upload what changed
    python tools/deploy.py --all      ignore the manifest, send everything
    python tools/deploy.py --prune    also delete remote files we no longer have
    python tools/deploy.py --list     show the remote tree and exit

Credentials live in tools/.ftp.json and are gitignored:

    {"host": "...", "user": "...", "password": "...", "dir": "/"}
"""
import io, os, sys, json, ftplib, hashlib, posixpath

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "tools", ".ftp.json")
MANIFEST = os.path.join(ROOT, "tools", ".deploy-manifest.json")

SKIP_DIRS = {".git", "tools", "__pycache__", ".github", "dash"}
# the dashboard lives on its own short path, away from the marketing URL
DASH_LOCAL, DASH_REMOTE = "dash", "public_html/raz-leads"
SKIP_FILES = {".gitignore", "README.md", ".deploy-manifest.json"}
KEEP_DOTFILES = {".htaccess"}


def local_files():
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            if n in SKIP_FILES or (n.startswith(".") and n not in KEEP_DOTFILES):
                continue
            full = os.path.join(base, n)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            yield rel, full


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def connect(cfg):
    """cPanel here answers plain FTP fine but hangs on the FTPS data channel,
    so TLS is opt in through the config rather than the default."""
    if cfg.get("tls"):
        ftp = ftplib.FTP_TLS(timeout=30)
        ftp.connect(cfg["host"], int(cfg.get("port", 21)))
        ftp.login(cfg["user"], cfg["password"])
        ftp.prot_p()
        print("  connected over FTPS")
    else:
        ftp = ftplib.FTP(timeout=30)
        ftp.connect(cfg["host"], int(cfg.get("port", 21)))
        ftp.login(cfg["user"], cfg["password"])
        print("  connected over FTP")
    ftp.set_pasv(True)

    base = cfg.get("dir", "/").strip("/")
    if base:
        for part in base.split("/"):
            try:
                ftp.cwd(part)
            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)
                print("  created remote %s" % part)
    print("  remote root: %s" % ftp.pwd())
    return ftp


def ensure_dir(ftp, remote_dir, made):
    if remote_dir in ("", ".", "/") or remote_dir in made:
        return
    parent = posixpath.dirname(remote_dir)
    ensure_dir(ftp, parent, made)
    try:
        ftp.mkd(remote_dir)
        print("  mkdir %s" % remote_dir)
    except ftplib.error_perm:
        pass          # already there
    made.add(remote_dir)


def walk_remote(ftp, path="."):
    """List every remote file, depth first, tolerating servers without MLSD."""
    out = []
    try:
        entries = list(ftp.mlsd(path))
    except Exception:
        return out
    for name, facts in entries:
        if name in (".", ".."):
            continue
        p = posixpath.join(path, name).lstrip("./")
        if facts.get("type") == "dir":
            out.extend(walk_remote(ftp, p))
        elif facts.get("type") == "file":
            out.append(p)
    return out


def main():
    if not os.path.exists(CONF):
        print("Missing %s\nCreate it with host, user, password and dir." % CONF)
        return 1
    cfg = json.load(io.open(CONF, encoding="utf-8"))
    args = set(sys.argv[1:])

    manifest = {}
    if os.path.exists(MANIFEST) and "--all" not in args:
        manifest = json.load(io.open(MANIFEST, encoding="utf-8"))

    files = sorted(local_files())
    print("deploying %d files to %s%s" % (len(files), cfg["host"], cfg.get("dir", "/")))
    ftp = connect(cfg)

    if "--list" in args:
        for p in sorted(walk_remote(ftp)):
            print("   ", p)
        ftp.quit()
        return 0

    made, sent, skipped = set(), 0, 0
    fresh = {}
    for rel, full in files:
        digest = sha1(full)
        fresh[rel] = digest
        if manifest.get(rel) == digest:
            skipped += 1
            continue
        ensure_dir(ftp, posixpath.dirname(rel), made)
        with open(full, "rb") as fh:
            ftp.storbinary("STOR " + rel, fh)
        print("  up  %-34s %6.1f KB" % (rel, os.path.getsize(full) / 1024.0))
        sent += 1

    if "--prune" in args:
        keep = set(fresh)
        for p in walk_remote(ftp):
            if p not in keep:
                try:
                    ftp.delete(p)
                    print("  del %s" % p)
                except ftplib.error_perm as e:
                    print("  could not delete %s (%s)" % (p, e))

    # second target: the dashboard
    ftp.cwd("/")
    for part in DASH_REMOTE.split("/"):
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part); ftp.cwd(part); print("  created remote %s" % part)
    for name in sorted(os.listdir(os.path.join(ROOT, DASH_LOCAL))):
        full = os.path.join(ROOT, DASH_LOCAL, name)
        if not os.path.isfile(full):
            continue
        key = "dash/" + name
        digest = sha1(full)
        fresh[key] = digest
        if manifest.get(key) == digest:
            skipped += 1
            continue
        with open(full, "rb") as fh:
            ftp.storbinary("STOR " + name, fh)
        print("  up  %-34s %6.1f KB  -> /raz-leads/" % (key, os.path.getsize(full) / 1024.0))
        sent += 1

    ftp.quit()
    io.open(MANIFEST, "w", encoding="utf-8").write(json.dumps(fresh, indent=1, sort_keys=True))
    print("done. %d uploaded, %d unchanged." % (sent, skipped))
    print("live at https://tom-harush.co.il/raz-meir-cohen/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
