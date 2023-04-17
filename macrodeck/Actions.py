from macrodeck import ActionClasses as act

ACTIONS = [
    act.NoAction() # this should always be index 0
    ,act.PlayMedia()
    ,act.StopMedia()
    ,act.PauseMedia()
    ,act.OpenView()
    ,act.Macro()
    ,act.Web()
    ,act.OBSScene()
    # ,act.OBSMute()
    ,act.ManageWindow()
]

for i in range(len(ACTIONS)):
    ACTIONS[i].set_enum(i)