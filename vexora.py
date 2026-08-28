#!/usr/bin/env python3
import argparse, os, subprocess, sys
def run(c): return subprocess.run(c,check=False)
def main():
 p=argparse.ArgumentParser(prog="vexora"); s=p.add_subparsers(dest="cmd",required=True)
 for x in ("version","status","health","test","security","info","restart","update","remove","backup"): s.add_parser(x)
 a=p.parse_args()
 if a.cmd=="version": print("VEXORA 2.0.0")
 elif a.cmd=="status": run(["systemctl","status","vexora","--no-pager"])
 elif a.cmd=="health": run(["curl","-fsS","http://127.0.0.1:6000/health"])
 elif a.cmd=="test":
  print("=== health ==="); run(["curl","-fsS","http://127.0.0.1:6000/health"]); print("\n=== ports ==="); run(["bash","-lc","ss -lntp | grep -E ':(443|8080|6000)\\b' || true"])
 elif a.cmd=="security": run(["bash","-lc","systemctl is-enabled vexora; systemctl is-active vexora; stat -c '%a %n' /opt/vexora/.env 2>/dev/null || true"])
 elif a.cmd=="info":
  p="/opt/vexora/.env"
  if os.path.exists(p):
   for l in open(p):
    if l.startswith(("VEXORA_VERSION=","VEXORA_HOST=","VEXORA_PORT=","VEXORA_BASE_PATH=","VEXORA_PUBLIC_HOST=","VEXORA_PUBLIC_PORT=")): print(l.strip())
 elif a.cmd=="restart": run(["systemctl","restart","vexora"])
 elif a.cmd=="update": print("Use the GitHub installer; .env/data/backups are preserved.")
 elif a.cmd=="remove":
  if os.geteuid()!=0: sys.exit("root required")
  run(["systemctl","disable","--now","vexora"]); print("Service stopped; data preserved.")
 elif a.cmd=="backup":
  sys.path.insert(0,"/opt/vexora"); from app.backup import make_backup; print(make_backup())
if __name__=="__main__": main()
