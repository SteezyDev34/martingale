# OuverturePageMatch

from Functions._to_remove import AddRunning


def main(bet_item, script_num, newmatch, running_file_name, matchlist_file_name):
    try:
        AddRunning.main(script_num, running_file_name)
    except Exception as e:
        return False
    else:
        return True
