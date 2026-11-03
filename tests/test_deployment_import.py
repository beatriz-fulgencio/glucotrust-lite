"""Exercise app imports without pytest's configured src path hiding stale wheels."""
import os
from pathlib import Path
import subprocess
import sys


def test_app_prefers_checked_out_package_over_stale_install(tmp_path):
    stale = tmp_path / 'glucotrust'
    stale.mkdir()
    (stale / '__init__.py').write_text('raise RuntimeError("Stale installed package was imported")')
    script = '''
import sys,runpy,inspect
from pathlib import Path
sys.path.insert(0, sys.argv[1])
runpy.run_path('app.py', run_name='__main__')
import glucotrust.pipeline
assert Path(glucotrust.pipeline.__file__).resolve() == Path('src/glucotrust/pipeline.py').resolve()
assert 'language' in inspect.signature(glucotrust.pipeline.assess_claim).parameters
'''
    env = {k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','GROQ_API_KEY'}}
    result = subprocess.run([sys.executable, '-I', '-c', script, str(tmp_path)],
                            cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode == 0, result.stderr
