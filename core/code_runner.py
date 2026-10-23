import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TIME_LIMIT = 5  # saniyə


def _python_exe():
    """Həqiqi Python faylını tapır (serverdə sys.executable uwsgi ola bilər)."""
    exe = sys.executable
    if exe and os.path.basename(exe).lower().startswith('python'):
        return exe
    for base in (sys.prefix, sys.exec_prefix):
        candidate = os.path.join(base, 'bin', 'python')
        if os.path.exists(candidate):
            return candidate
    return shutil.which('python3') or shutil.which('python') or 'python3'

HARNESS = "#HARNESS\n"


def run_python(code, input_data=""):
    """Kodu işə salır. (nəticə, xəta) qaytarır."""
    stdin = input_data
    if input_data.startswith(HARNESS):
        # sinif tapşırığı: gizli test kodu tələbənin koduna əlavə olunur
        code = code.rstrip("\n") + "\n\n" + input_data[len(HARNESS):]
        stdin = ""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "solution.py"
        file.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(
                [_python_exe(), "-I", "-X", "utf8", str(file)],
                input=stdin,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=TIME_LIMIT,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return "", "Vaxt limiti aşıldı"
    return r.stdout.strip(), r.stderr.strip()


def check_task(task, code):
    """Hər test halını yoxlayır. (keçən, ümumi) qaytarır."""
    passed = 0
    tests = list(task.test_cases.all())
    tests = tests[1:] if len(tests) > 1 else tests
    for t in tests:
        out, err = run_python(code, t.input_data)
        if not err and out == t.expected_output.strip():
            passed += 1
    return passed, len(tests)