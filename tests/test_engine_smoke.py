import types

import config

# Dummy driver with get method
class DummyDriver:
    def __init__(self):
        self.visited = []
    def get(self, url):
        self.visited.append(url)


def test_engine_prepare_and_no_run_loop():
    from core.engine import MartingaleEngine

    driver = DummyDriver()
    engine = MartingaleEngine(driver)

    # Ensure running/matchlist are set by prepare
    engine.prepare()
    assert hasattr(config, 'running_file_name') and config.running_file_name.endswith('SCRIPTS 4315A/running')
    assert hasattr(config, 'matchlist_file_name') and config.matchlist_file_name.endswith('SCRIPTS 4315A/matchlist')

    # Run with 0 wins threshold to avoid invoking heavy automation
    prev_win = getattr(config, 'win', 0)
    engine.run(max_total_wins=0)
    # win should be unchanged
    assert getattr(config, 'win', 0) == prev_win
