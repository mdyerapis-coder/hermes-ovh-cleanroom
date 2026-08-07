from pathlib import Path
import subprocess
import os

ROOT = Path(__file__).resolve().parents[2]

def test_backup_and_restore(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    env = os.environ.copy()
    env["HERMES_BACKUP_DIR"] = str(backup_dir)
    r1 = subprocess.run(["bash", str(ROOT / "scripts/backup.sh")], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr
    r2 = subprocess.run(["bash", str(ROOT / "scripts/restore-test.sh")], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr + r2.stdout
