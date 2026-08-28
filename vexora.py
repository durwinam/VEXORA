#!/usr/bin/env python3
import argparse, os, subprocess, sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser(prog='vexora'); sub=p.add_subparsers(dest='cmd')
 sub.add_parser('version'); sub.add_parser('status'); sub.add_parser('health'); sub.add_parser('test')
 sub.add_parser('restart'); sub.add_parser('update'); sub.add_parser('remove')
 x=sub.add_parser('backup'); x.add_argument('--send',action='store_true')
 a=sub.add_parser('passwd'); a.add_argument('username',nargs='?')
 ns=sub.parse_args()
 if ns.cmd=='version': print('VEXORA 1.0.0'); return
 if ns.cmd=='status': subprocess.run(['systemctl','status','vexora','--no-pager']); return
 if ns.cmd=='health': subprocess.run(['curl','-fsS','http://127.0.0.1:6000/health']); print(); return
 if ns.cmd=='test':
  subprocess.run(['curl','-fsS','http://127.0.0.1:6000/health']); print('\nHealth test complete'); return
 if ns.cmd=='restart': subprocess.run(['systemctl','restart','vexora']); return
 if ns.cmd=='update': print('Use the GitHub installer/update process to update safely.'); return
 if ns.cmd=='remove':
  if os.geteuid()!=0: print('root required'); sys.exit(1)
  subprocess.run(['systemctl','disable','--now','vexora'],check=False); print('Service stopped; data was preserved.')
  return
 if ns.cmd=='backup':
  sys.path.insert(0,'/opt/vexora'); from app.backup import make_backup; print(make_backup()); return
 p.print_help()
if __name__=='__main__': main()
