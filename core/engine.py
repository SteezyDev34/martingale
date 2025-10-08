# core/engine.py
# A light class-based orchestrator to simplify and structure the 4315A script flow

import config
from Functions import Functions_431a
from Functions.GetJsonData import DispatchPerte


class MartingaleEngine:
    """
    Encapsulates the main execution loop for the 4315A strategy.
    This class wraps the existing procedural code so the outer script becomes simpler
    and we can reuse the same orchestrator elsewhere if needed.
    """

    def __init__(self, driver):
        self.driver = driver

    def prepare(self):
        """Prepare per-script config objects and runtime files."""
        # Ensure per-script config objects are instantiated
        for st in config.scriptTypeList:
            config.ScriptConfig(st)

        # Set file paths used by the strategy
        # Keep the same locations as before to preserve behavior
        config.running_file_name = f"{config.projectPath}/SCRIPTS 4315A/running"
        config.matchlist_file_name = f"{config.projectPath}/SCRIPTS 4315A/matchlist"

    def _reset_between_matches(self):
        """
        After a successful pass of Functions_431a.all_script, reset per-strategy state
        and dispatch losses if needed, reproducing the previous behavior.
        """
        if config.perte > 0:
            DispatchPerte()

        for st in config.scriptTypeList:
            # temporarily switch to 4315A to access/reset shared state, then back to each script
            config.switchScript('4315A')
            config.ScriptConfig(st).reset()
            config.init_variable()
            config.switchScript(st)
            DispatchPerte()
            # Reset counters for the next loop
            config.global_match_win[st] = 0
            config.winmatch[st] = 0

        # Ensure the browser is back to the site url for the next iteration
        success = False
        while not success:
            try:
                self.driver.get(config.site_url)
                success = True
            except Exception:
                # keep trying until navigation succeeds
                continue

    def run(self, max_total_wins: int = 100):
        """Run the main 4315A loop until total wins reach the given threshold."""
        # Safety: in case prepare() wasn't called
        if not getattr(config, 'running_file_name', None) or not getattr(config, 'matchlist_file_name', None):
            self.prepare()

        while config.win < max_total_wins:
            try:
                Functions_431a.all_script(self.driver)
            except Exception as e:
                config.log(f"ERROR SCRIPT : {e}", 'error', False)
            else:
                self._reset_between_matches()

        print('TOTAL WIN : ' + str(config.win))
