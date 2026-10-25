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

def preserve_distribution(source,destination,entries,base='https://lg.darc.dev'):
 """Preflight and copy existing public asset trees; never fetch or follow links."""
 from urllib.parse import urlsplit,unquote
 import shutil
 source=Path(source).resolve();destination=Path(destination).resolve()
 public=('packages','icons','browse','manifests')
 files={}
 for folder in public:
  parent=source/'dist'/folder if (source/'dist'/folder).exists() else source/folder
  if parent.is_symlink() or not parent.resolve().is_relative_to(source):raise ValueError('Symlink in retained public assets')
  if not parent.exists():continue
  for p in parent.rglob('*'):
   if p.is_symlink() or not p.resolve().is_relative_to(source):raise ValueError('Symlink or escaping retained public asset')
   if p.is_file():files[Path(folder)/p.relative_to(parent)]=p
 def references(value):
  if isinstance(value,dict):
   for v in value.values():yield from references(v)
  elif isinstance(value,list):
   for v in value:yield from references(v)
  elif isinstance(value,str):
   u=urlsplit(value)
   if (u.scheme in ('http','https') and u.hostname==urlsplit(base).hostname) or (value.startswith('/') and not value.startswith('//')):
    path=unquote(u.path).lstrip('/')
    if '..' in Path(path).parts or '\\' in path:raise ValueError('Unsafe retained asset path')
    yield Path(path)/'index.html' if not path or path.endswith('/') else Path(path)
 generated={'index.html','apps.json','api/apps.json','packages.json','about.html'}
 for route in references(entries):
  if route.as_posix() in generated:continue
  if route not in files and route/'index.html' in files:continue
  if route not in files:raise ValueError('Missing retained local asset: '+route.as_posix()+'; restore the trusted public distribution tree before staging')
 # Validate everything before copying anything. No source removals or rewrites.
 for route,p in files.items():
  target=destination/route
  if not target.resolve().is_relative_to(destination):raise ValueError('Escaping output asset')
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
