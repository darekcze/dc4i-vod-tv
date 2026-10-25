"""Shared release identity and fail-closed diagnostics; never read credentials."""
import argparse,json,re
from pathlib import Path

def candidate(app_dir,selected=None):
 meta=json.loads((Path(app_dir)/'appinfo.json').read_text())
 version=meta.get('version','')
 if meta.get('id')!='com.dc4i.vodtv' or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)',version):raise ValueError('Invalid production identity/version')
 if selected is not None and selected!=version:raise ValueError('Selected version must match built app metadata')
 return meta['id'],version

def safe_error(error):
 # Do not echo arbitrary exception text: query/header/body credentials can have
 # unknown names or encoding. An exception category is sufficient diagnostics.
 return type(error).__name__

def options(root,publishing=False):
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=root);parser.add_argument('--app-dir',type=Path);parser.add_argument('--release-version');parser.add_argument('--offline',action='store_true')
 if publishing:parser.add_argument('--output-root',type=Path)
 args=parser.parse_args();args.root=args.root.resolve();args.app_dir=(args.app_dir or args.root/'build/dc4i-vodtv').resolve()
 if publishing:
  explicit_output=args.output_root is not None
  args.output_root=(args.output_root or args.root).resolve()
  if explicit_output and args.output_root==args.root:raise ValueError('Explicit isolated output cannot be source root')
  if args.output_root!=args.root:
   if args.output_root.exists() and any(args.output_root.iterdir()):raise ValueError('Isolated output must be absent or empty')
   if args.output_root in args.root.parents or args.root in args.output_root.parents:raise ValueError('Isolated output must be outside source tree')
   args.output_root.mkdir(parents=True,exist_ok=True)
 return args
