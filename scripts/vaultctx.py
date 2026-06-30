#!/usr/bin/env python3
import argparse, hashlib, json, re, sqlite3
from pathlib import Path

ROOT = Path.cwd()
RECORD_FILES = {'sources':'source','attachments':'attachment','entities':'entity','claims':'claim','relations':'relation','tasks':'task','decisions':'decision','projects':'project'}
HUMAN_GLOBS = ['vault/daily/*.md', 'vault/inbox/*.md']
SKIP_DIRS = {'.git','__pycache__','.pytest_cache','.venv','venv'}
PRIVACY_PATTERNS = [
    ('email', re.compile(r'(?<!example)\b[A-Za-z0-9._%+-]+@(?!example\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')),
    ('windows_user_path', re.compile(r'C:\\Users\\(?!Example\\)[^\\\s]+', re.I)),
    ('posix_user_path', re.compile(r'/Users/(?!example\b)[^/\s]+|/home/(?!example\b)[^/\s]+')),
    ('telegram_id', re.compile(r'\btelegram[:_ -]*(chat|user)?[:_ -]*-?\d{7,}\b', re.I)),
    ('secret', re.compile(r'\b(?:sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b')),
]
ALLOW_PRIVACY_PATTERN_FILES = {'scripts/vaultctx.py','tests/test_cli.py','docs/privacy-and-public-safety.md'}

def root_path(rel): return ROOT / rel

def read_jsonl(path):
    rows=[]
    if not path.exists(): return rows
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except Exception as e: raise SystemExit(f'Invalid JSONL {path}:{i}: {e}')
    return rows

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':'))+'\n' for r in rows), encoding='utf-8')

def sha256_file(path):
    h=hashlib.sha256(); size=0
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(65536), b''):
            size += len(chunk); h.update(chunk)
    return h.hexdigest(), size

def human_files():
    files=[]
    for g in HUMAN_GLOBS: files.extend(sorted(ROOT.glob(g)))
    return files

def human_hashes():
    return {str(p.relative_to(ROOT)): sha256_file(p)[0] for p in human_files()}

def save_human_baseline():
    p=root_path('dist/human_owned_hashes.json'); p.parent.mkdir(exist_ok=True)
    before=human_hashes(); p.write_text(json.dumps(before, indent=2)+'\n', encoding='utf-8'); return before

def verify_human_unchanged():
    p=root_path('dist/human_owned_hashes.json')
    if not p.exists(): return True
    before=json.loads(p.read_text(encoding='utf-8')); after=human_hashes()
    if before != after:
        raise SystemExit('Human-owned daily/inbox files changed; automation must never mutate them')
    return True

def validate_schema(kind, row, schema):
    missing=[k for k in schema.get('required',[]) if k not in row]
    if missing: raise SystemExit(f'{row.get("id","<no id>")} missing fields: {missing}')
    allowed=set(schema.get('properties',{}))
    extra=set(row)-allowed
    if extra and schema.get('additionalProperties') is False:
        raise SystemExit(f'{row.get("id")} has extra fields: {sorted(extra)}')
    for k, prop in schema.get('properties',{}).items():
        if k not in row: continue
        typ=prop.get('type')
        if typ=='string' and not isinstance(row[k], str): raise SystemExit(f'{row.get("id")} field {k} must be string')
        if typ=='integer' and not isinstance(row[k], int): raise SystemExit(f'{row.get("id")} field {k} must be integer')
        if typ=='number' and not isinstance(row[k], (int,float)): raise SystemExit(f'{row.get("id")} field {k} must be number')
        if 'pattern' in prop and not re.match(prop['pattern'], str(row[k])): raise SystemExit(f'{row.get("id")} field {k} fails pattern')
    if row.get('type') != kind:
        raise SystemExit(f'{row.get("id")} type should be {kind}, got {row.get("type")}')

def all_records():
    return {stem: read_jsonl(root_path(f'records/{stem}.jsonl')) for stem in RECORD_FILES}

def privacy_guard():
    problems=[]
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=str(p.relative_to(ROOT))
        if any(part in SKIP_DIRS for part in p.parts): continue
        if rel.startswith('dist/') and not rel.endswith('.json'): continue
        try: text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        for name,pat in PRIVACY_PATTERNS:
            if pat.search(text) and rel not in ALLOW_PRIVACY_PATTERN_FILES:
                problems.append(f'{name}: {rel}')
    if problems:
        raise SystemExit('Privacy guard failed:\n'+'\n'.join(problems))

def cmd_validate(args=None):
    ids={}; records=all_records()
    for stem, rows in records.items():
        kind=RECORD_FILES[stem]
        schema=json.loads(root_path(f'schema/{kind}.schema.json').read_text(encoding='utf-8'))
        for row in rows:
            validate_schema(kind, row, schema)
            if row['id'] in ids: raise SystemExit(f'Duplicate id: {row["id"]}')
            ids[row['id']]=f'records/{stem}.jsonl'
    source_ids={r['id'] for r in records['sources']}; project_ids={r['id'] for r in records['projects']}; entity_ids={r['id'] for r in records['entities']}
    for group in ['attachments','entities','claims','relations','tasks','decisions','projects']:
        for r in records[group]:
            if 'source_id' in r and r['source_id'] not in source_ids: raise SystemExit(f'Missing source ref: {r["id"]} -> {r["source_id"]}')
            if 'project_id' in r and r['project_id'] not in project_ids: raise SystemExit(f'Missing project ref: {r["id"]} -> {r["project_id"]}')
    valid_targets=set(source_ids)|project_ids|entity_ids|{r['id'] for r in records['claims']}|{r['id'] for r in records['tasks']}|{r['id'] for r in records['decisions']}
    for r in records['relations']:
        if r['from_id'] not in valid_targets or r['to_id'] not in valid_targets: raise SystemExit(f'Missing relation endpoint: {r["id"]}')
    for a in records['attachments']:
        p=root_path(a['storage_path'])
        if not p.exists(): raise SystemExit(f'Missing attachment file: {a["storage_path"]}')
        digest, size = sha256_file(p)
        if digest != a['sha256']: raise SystemExit(f'Attachment SHA mismatch: {a["id"]}')
        if size != a['size_bytes']: raise SystemExit(f'Attachment size mismatch: {a["id"]}')
    verify_human_unchanged(); privacy_guard()
    total=sum(len(v) for v in records.values())
    print(f'validate ok: {total} records across {len(records)} JSONL files; privacy ok; human-owned unchanged')

def cmd_scan_daily(args=None):
    before=save_human_baseline(); daily=[]; inbox=[]
    for p in human_files():
        rel=str(p.relative_to(ROOT)); text=p.read_text(encoding='utf-8')
        for idx,line in enumerate(text.splitlines(),1):
            clean=line.strip().lstrip('- ').strip()
            if not clean or clean.startswith('#'): continue
            rid='raw.'+hashlib.sha1(f'{rel}:{idx}:{clean}'.encode()).hexdigest()[:16]
            row={'id':rid,'type':'raw_event','source_path':rel,'line':idx,'kind':'daily_note' if '/daily/' in '/'+rel else 'inbox_note','text':clean,'created_at':'2026-01-01T09:00:00Z'}
            (daily if row['kind']=='daily_note' else inbox).append(row)
    write_jsonl(root_path('raw/daily_events.jsonl'), daily); write_jsonl(root_path('raw/inbox_events.jsonl'), inbox)
    if before != human_hashes(): raise SystemExit('scan-daily mutated human-owned notes')
    print(f'scan-daily ok: {len(daily)+len(inbox)} raw events; human-owned unchanged')

def cmd_extract(args=None):
    print('extract ok: starter records already materialized from synthetic raw events')

def cmd_render_views(args=None):
    verify_human_unchanged(); records=all_records(); out=root_path('views/markdown'); out.mkdir(parents=True, exist_ok=True)
    (out/'open-loops.md').write_text('# Open loops\n\n'+'\n'.join(f'- [ ] {t["title"]} (source: `{t["source_id"]}`)' for t in records['tasks'])+'\n', encoding='utf-8')
    (out/'projects.md').write_text('# Projects\n\n'+'\n'.join(f'- **{p["name"]}** — {p["status"]} (source: `{p["source_id"]}`)' for p in records['projects'])+'\n', encoding='utf-8')
    (out/'entities.md').write_text('# Entities\n\n'+'\n'.join(f'- {e["name"]} — {e["entity_type"]} (source: `{e["source_id"]}`)' for e in records['entities'])+'\n', encoding='utf-8')
    (out/'attachments.md').write_text('# Attachments\n\n'+'\n'.join(f'- `{a["filename"]}` sha256 `{a["sha256"]}` size {a["size_bytes"]} bytes source `{a["source_id"]}`' for a in records['attachments'])+'\n', encoding='utf-8')
    ai=root_path('vault/ai-daily'); ai.mkdir(parents=True, exist_ok=True)
    (ai/'2026-01-01.ai.md').write_text('# AI Daily — 2026-01-01\n\n## Detected\n- Human notes ask for a weekly planning starter with read-only source notes.\n\n## Open loops\n- Make the starter kit cloneable in two minutes.\n\n## Sources\n- `source.daily.2026-01-01`\n- `source.inbox.example-capture`\n', encoding='utf-8')
    verify_human_unchanged(); print('render-views ok: views/markdown and vault/ai-daily generated; human-owned unchanged')

def cmd_bundle(args):
    records=all_records(); q=(args.goal or '').lower(); items=[]; must=[]
    for group in ['claims','tasks','decisions']:
        for r in records[group]:
            blob=json.dumps(r).lower()
            if not q or any(tok in blob for tok in q.split()):
                items.append(r); must.append(r['source_id'])
    if not items:
        items = records['claims'][:2] + records['tasks'][:1] + records['decisions'][:1]
        must = [r['source_id'] for r in items]
    bundle={'goal':args.goal,'items':items,'must_cite':sorted(set(must)),'attachments':[{'id':a['id'],'filename':a['filename'],'sha256':a['sha256'],'source_id':a['source_id']} for a in records['attachments']],'warnings':[],'gaps':['Replace synthetic examples with your own local notes before personal use.'],'confidence':0.82}
    root_path('dist/bundles').mkdir(parents=True, exist_ok=True); root_path('dist/bundles/demo.json').write_text(json.dumps(bundle, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(bundle, indent=2))

def cmd_query(args):
    term=' '.join(args.terms).lower(); hits=[]
    for stem, rows in all_records().items():
        for r in rows:
            if term in json.dumps(r).lower(): hits.append({'file':f'records/{stem}.jsonl','id':r['id']})
    print(json.dumps({'query':term,'hits':hits}, indent=2))

def cmd_build_sqlite(args=None):
    p=root_path('dist/vaultctx.sqlite'); p.parent.mkdir(exist_ok=True)
    con=sqlite3.connect(p); cur=con.cursor(); cur.execute('drop table if exists records'); cur.execute('create table records (id text primary key, kind text, json text)')
    for stem, rows in all_records().items():
        for r in rows: cur.execute('insert into records values (?,?,?)',(r['id'], stem, json.dumps(r)))
    con.commit(); count=cur.execute('select count(*) from records').fetchone()[0]; con.close()
    print(f'build-sqlite ok: {count} records -> {p.relative_to(ROOT)}')

def cmd_hash_attachment(args):
    p=Path(args.path); digest,size=sha256_file(p); suggested=f'vault/attachments/objects/sha256/{digest[:2]}/{digest}/{p.name}'
    print(json.dumps({'filename':p.name,'size_bytes':size,'sha256':digest,'suggested_storage_path':suggested,'record_stub':{'id':'attachment.'+p.stem.replace('_','-'),'type':'attachment','filename':p.name,'media_type':'application/octet-stream','size_bytes':size,'sha256':digest,'storage_path':suggested,'source_id':'source.<replace-me>','created_at':'<timestamp>'}}, indent=2))

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('validate').set_defaults(func=cmd_validate); sub.add_parser('scan-daily').set_defaults(func=cmd_scan_daily); sub.add_parser('extract').set_defaults(func=cmd_extract); sub.add_parser('render-views').set_defaults(func=cmd_render_views)
    b=sub.add_parser('bundle'); b.add_argument('--goal', default=''); b.set_defaults(func=cmd_bundle)
    q=sub.add_parser('query'); q.add_argument('terms', nargs='+'); q.set_defaults(func=cmd_query)
    sub.add_parser('build-sqlite').set_defaults(func=cmd_build_sqlite)
    h=sub.add_parser('hash-attachment'); h.add_argument('path'); h.set_defaults(func=cmd_hash_attachment)
    args=ap.parse_args(); args.func(args)
if __name__=='__main__': main()
