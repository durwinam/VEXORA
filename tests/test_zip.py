from pathlib import Path

def test_no_cache_artifacts():
 root=Path(__file__).parents[1]
 assert not list(root.rglob('*.pyc'))
 assert not list(root.rglob('__pycache__'))
