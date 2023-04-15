from macrodeck.gui.App import App

if __name__=='__main__':
    layout = 'layouts/numpad_tall.json'
    # layout = 'layouts/numpad.json'
    
    app = App(layout)
    app.init_hotkeys()
    app.mainloop()