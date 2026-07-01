import json, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd=ROOT, ok=True):
    res=subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if ok and res.returncode: raise AssertionError(res.stdout + res.stderr)
    if not ok and res.returncode == 0: raise AssertionError('expected failure')
    return res

def copy_repo(tmp_path):
    dst=tmp_path/'repo'; shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','dist/*.sqlite'))
    return dst

def test_validate_passes_on_starter_data():
    assert 'validate ok' in run([sys.executable,'scripts/vaultctx.py','validate']).stdout

def test_invalid_jsonl_fails(tmp_path):
    repo=copy_repo(tmp_path); (repo/'records/claims.jsonl').write_text('{bad json}\n'); run([sys.executable,'scripts/vaultctx.py','validate'], cwd=repo, ok=False)

def test_duplicate_ids_fail(tmp_path):
    repo=copy_repo(tmp_path); p=repo/'records/entities.jsonl'; first=p.read_text().splitlines()[0]; p.write_text(p.read_text()+first+'\n'); run([sys.executable,'scripts/vaultctx.py','validate'], cwd=repo, ok=False)

def test_missing_references_fail(tmp_path):
    repo=copy_repo(tmp_path); p=repo/'records/tasks.jsonl'; row=json.loads(p.read_text().splitlines()[0]); row['source_id']='source.missing'; p.write_text(json.dumps(row)+'\n'); run([sys.executable,'scripts/vaultctx.py','validate'], cwd=repo, ok=False)

def test_attachment_sha_mismatch_fails(tmp_path):
    repo=copy_repo(tmp_path); p=repo/'records/attachments.jsonl'; row=json.loads(p.read_text().splitlines()[0]); row['sha256']='0'*64; p.write_text(json.dumps(row)+'\n'); run([sys.executable,'scripts/vaultctx.py','validate'], cwd=repo, ok=False)

def test_scan_and_render_do_not_mutate_daily(tmp_path):
    repo=copy_repo(tmp_path); daily=repo/'vault/daily/2026-01-01.md'; before=daily.read_bytes(); run([sys.executable,'scripts/vaultctx.py','scan-daily'], cwd=repo); run([sys.executable,'scripts/vaultctx.py','render-views'], cwd=repo); assert daily.read_bytes() == before

def test_extract_generates_typed_records_from_raw_bullets(tmp_path):
    repo=copy_repo(tmp_path)
    run([sys.executable,'scripts/vaultctx.py','scan-daily'], cwd=repo)
    res=run([sys.executable,'scripts/vaultctx.py','extract'], cwd=repo)
    assert 'generated' in res.stdout
    claims=[json.loads(line) for line in (repo/'records/claims.jsonl').read_text().splitlines()]
    tasks=[json.loads(line) for line in (repo/'records/tasks.jsonl').read_text().splitlines()]
    decisions=[json.loads(line) for line in (repo/'records/decisions.jsonl').read_text().splitlines()]
    entities=[json.loads(line) for line in (repo/'records/entities.jsonl').read_text().splitlines()]
    assert any('never edit this daily note' in c['text'] for c in claims)
    assert any('clone in two minutes' in t['title'] for t in tasks)
    assert any('structured records in JSONL' in d['title'] for d in decisions)
    assert {'entity.alex-example','entity.sam-example'} <= {e['id'] for e in entities}
    assert all(row['source_id'].startswith('source.') for row in claims + tasks + decisions + entities)

def test_extract_is_idempotent_and_does_not_mutate_daily(tmp_path):
    repo=copy_repo(tmp_path)
    daily=repo/'vault/daily/2026-01-01.md'
    before=daily.read_bytes()
    run([sys.executable,'scripts/vaultctx.py','scan-daily'], cwd=repo)
    run([sys.executable,'scripts/vaultctx.py','extract'], cwd=repo)
    first=(repo/'records/tasks.jsonl').read_text()
    run([sys.executable,'scripts/vaultctx.py','extract'], cwd=repo)
    assert (repo/'records/tasks.jsonl').read_text() == first
    assert daily.read_bytes() == before

def test_bundle_contains_must_cite():
    data=json.loads(run([sys.executable,'scripts/vaultctx.py','bundle','--goal','plan the week']).stdout); assert data['must_cite']; assert all(x.startswith('source.') for x in data['must_cite'])

def test_generated_views_exist(tmp_path):
    repo=copy_repo(tmp_path); run([sys.executable,'scripts/vaultctx.py','scan-daily'], cwd=repo); run([sys.executable,'scripts/vaultctx.py','render-views'], cwd=repo); assert (repo/'views/markdown/open-loops.md').exists(); assert (repo/'vault/ai-daily/2026-01-01.ai.md').exists()

def test_privacy_guard_catches_fake_secret_path(tmp_path):
    repo=copy_repo(tmp_path); (repo/'leak.txt').write_text('C:\\Users\\RealPerson\\vault and sk-1234567890abcdef'); run([sys.executable,'scripts/vaultctx.py','validate'], cwd=repo, ok=False)
