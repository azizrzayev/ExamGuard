import subprocess
import sys
import tempfile
from pathlib import Path

TIME_LIMIT = 5  # saniyə


def run_python(code, input_data=""):
    """Kodu işə salır. (nəticə, xəta) qaytarır."""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "solution.py"
        file.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(
                [sys.executable, "-I", str(file)],
                input=input_data,
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
    for t in tests:
        out, err = run_python(code, t.input_data)
        if not err and out == t.expected_output.strip():
            passed += 1
    return passed, len(tests)