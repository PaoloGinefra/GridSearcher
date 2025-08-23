import os
import shutil
import tempfile
import yaml
from GridSearcher.GridSearcher import GridSearcher


def test_toYAML_writes_file_and_contents_match_and_cleans_up():
    # create a temporary directory manually so we can delete it explicitly
    temp_dir = tempfile.mkdtemp()
    try:
        config = {"run1": {"a": 1, "nested": {"b": [1, 2]}}}
        # write to the directory path (should create grid_config.yaml inside)
        GridSearcher.toYAML(config, temp_dir)
        out_path = os.path.join(temp_dir, 'grid_config.yaml')
        assert os.path.exists(out_path)
        # read back and compare
        with open(out_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert loaded == config
    finally:
        # explicitly remove the temp directory
        shutil.rmtree(temp_dir)
