# pico keyboard 60 keys

60 keys handheld keyboard based on raspberry pi pico &amp; circuitpython

# how to change key mapping

In the code.py file, you can find this 'keys' definition as below, change it as you want,
the composite key definition like (K.ONE, K.F1), click key => K.ONE will be the key value,
and, click Fn + key => K.F1 will be the key value.s
```python
keys = [
    [K.Q, K.W, K.E, K.R, K.T, K.Y, K.U, K.I, K.O, K.P],
    [K.A, K.S, K.D, K.F, K.G, K.H, K.J, K.K, K.L, K.SEMICOLON],
    [K.Z, K.X, K.C, K.V, K.B, K.N, K.M, K.COMMA, K.PERIOD, K.FORWARD_SLASH],
    [K.ESCAPE, K.QUOTE, K.MINUS, K.EQUALS, K.SPACE, K.ENTER, K.LEFT_BRACKET, K.RIGHT_BRACKET, K.BACKSLASH, (K.BACKSPACE, K.PRINT_SCREEN)],
    [(K.ONE, K.F1), (K.TWO, K.F2), (K.THREE, K.F3), (K.FOUR, K.F4), (K.FIVE, K.F5), (K.SIX, K.F6), (K.SEVEN, K.DELETE), (K.EIGHT, K.CAPS_LOCK), (K.NINE, K.HOME), (K.ZERO, K.END)],
    [FN, K.TAB, K.LEFT_CONTROL, K.ALT, K.RIGHT_SHIFT, K.GRAVE_ACCENT, K.UP_ARROW, K.DOWN_ARROW, (K.LEFT_ARROW, K.PAGE_UP), (K.RIGHT_ARROW, K.PAGE_DOWN)],
]
```
