from macrodeck.gui.App import App

if __name__=='__main__':
    layout = 'layouts/numpad_tall.json'
    # layout = 'layouts/numpad.json'
    app = App(layout)
    ACTION_CALLS = app._callbacks()

    # initialize macros
    app.init_hotkeys()

    app.mainloop()