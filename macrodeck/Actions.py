from macrodeck import ActionClasses as act

# [do_nothing, self.player.__call__, self.player.reset, self.player.toggle_pause, self.open_view, None, web.open]

ACTIONS = [
    act.NoAction(),
    act.PlayMedia(),
    act.StopMedia(),
    act.PauseMedia(),
    act.OpenView(),
    act.Macro(),
    act.Web()
]

for i in range(len(ACTIONS)):
    ACTIONS[i].set_enum(i)