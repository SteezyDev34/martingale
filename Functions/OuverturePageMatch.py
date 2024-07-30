# OuverturePageMatch

from Functions import AddRunning
from Functions import UpdateMatchDone


def main(bet_item,script_num,newmatch,running_file_name,matchlist_file_name):
    try:
        UpdateMatchDone.main("add", newmatch, matchlist_file_name)
        AddRunning.main(script_num, running_file_name)
    except Exception as e:
        return False
    else:
        return True