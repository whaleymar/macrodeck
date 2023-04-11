# this format is for pynput hotkey class
MODIFIERKEYSHOTKEY = ['',
                '<ctrl>','<shift>','<alt>',
             '<ctrl>+<shift>', '<ctrl>+<alt>', 
             '<shift>+<alt>']

# this format is nicer to read, and can be converted to virtual key codes with the map below
MODIFIERKEYSMACRO = ['',
                'CONTROL', 'SHIFT', 'ALT', 'WIN',
                'CONTROL+SHIFT','CONTROL+ALT','CONTROL+WIN',
                'SHIFT+ALT','SHIFT+WIN','ALT+WIN']
MODIFIER_TO_VK = {
    'CONTROL':'CONTROL',
    'SHIFT':'SHIFT',
    'ALT': 'MENU',
    'WIN':'LWIN'
}


NUMPADKEYS = ['<NUMPAD0>','<NUMPAD1>','<NUMPAD2>','<NUMPAD3>','<NUMPAD4>',
        '<NUMPAD5>','<NUMPAD6>','<NUMPAD7>','<NUMPAD8>','<NUMPAD9>',
        '+','-','*','/','<DECIMAL>','<RETURN>']

FUNCTIONKEYS = ['<F1>','<F2>','<F3>','<F4>','<F5>','<F6>',
        '<F7>','<F8>','<F9>','<F10>','<F11>','<F12>',
        '<F13>','<F14>','<F15>','<F16>','<F17>','<F18>',
        '<F19>','<F20>','<F21>','<F22>','<F23>','<F24>']

ALPHANUMERICKEYS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

SYSTEMKEYS = ['SLEEP',
'ZOOM']

MISCKEYS = ['BACK',
'TAB',
'RETURN',
'PAUSE',
'ESCAPE',
'SPACE',
'END',
'HOME',
'LEFT',
'UP',
'RIGHT',
'DOWN',
'INSERT',
'DELETE']

MOUSEKEYS = ['LBUTTON',
'RBUTTON',
'MBUTTON']

MEDIAKEYS = ['VOLUME_MUTE',
'VOLUME_DOWN',
'VOLUME_UP',
'MEDIA_NEXT_TRACK',
'MEDIA_PREV_TRACK',
'MEDIA_STOP',
'MEDIA_PLAY_PAUSE']

# special characters
# TODO?

# unsorted
# CANCEL
# XBUTTON1
# XBUTTON2

# CLEAR

# PAUSE
# CAPITAL
# KANA
# HANGEUL
# HANGUL
# JUNJA
# FINAL
# HANJA
# KANJI
# CONVERT
# NONCONVERT
# ACCEPT
# MODECHANGE

# PRIOR
# NEXT


# SELECT
# PRINT
# EXECUTE
# SNAPSHOT

# HELP

# SCROLL
# OEM_NEC_EQUAL
# OEM_FJ_JISHO
# OEM_FJ_MASSHOU
# OEM_FJ_TOUROKU
# OEM_FJ_LOYA
# OEM_FJ_ROYA
# BROWSER_BACK
# BROWSER_FORWARD
# BROWSER_REFRESH
# BROWSER_STOP
# BROWSER_SEARCH
# BROWSER_FAVORITES
# BROWSER_HOME

# LAUNCH_MAIL
# LAUNCH_MEDIA_SELECT
# LAUNCH_APP1
# LAUNCH_APP2
# OEM_1
# OEM_PLUS
# OEM_COMMA
# OEM_MINUS
# OEM_PERIOD
# OEM_2
# OEM_3
# OEM_4
# OEM_5
# OEM_6
# OEM_7
# OEM_8
# OEM_AX
# OEM_102
# ICO_HELP
# ICO_00
# PROCESSKEY
# ICO_CLEAR
# PACKET
# OEM_RESET
# OEM_JUMP
# OEM_PA1
# OEM_PA2
# OEM_PA3
# OEM_WSCTRL
# OEM_CUSEL
# OEM_ATTN
# OEM_FINISH
# OEM_COPY
# OEM_AUTO
# OEM_ENLW
# OEM_BACKTAB
# ATTN
# CRSEL
# EXSEL
# EREOF
# PLAY
# NONAME
# PA1
# OEM_CLEAR