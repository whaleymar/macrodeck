from macrodeck import ActionClasses as act

HAS_OBSWS = act.HAS_OBSWS

ACTIONS = [
    act.NoAction(),  # this should always be index 0
    act.PlayMedia(),
    act.StopMedia(),
    act.PauseMedia(),
    act.MediaVolume(),
    act.OpenView(),
    act.Macro(),
    act.Web(),
    act.OBSScene()
    # ,act.OBSMute()
    ,
    act.ManageWindow(),
    act.EnterText(),
]

for i in range(len(ACTIONS)):
    ACTIONS[i].set_enum(i)


def add_action(actionclass):
    """
    adds action to ACTIONS and sets enum
    I use this to add MultiAction within App.py & avoid circular import of ActionButton
    """
    actionclass.set_enum(len(ACTIONS))
    ACTIONS.append(actionclass)
