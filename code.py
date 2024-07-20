import time
import analogio
import gc
#import storage
import board
import digitalio
import pwmio
import usb_hid
microcontroller = None
try:
    import microcontroller
except:
    print("no microcontroller module support")
if microcontroller:
    microcontroller.cpu.frequency = 100000000
    print("freq: %s mhz" % (microcontroller.cpu.frequency / 1000000))

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode as K
from adafruit_hid.mouse import Mouse
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode as C

#storage.disable_usb_drive() # disable usb drive

FN = "FN"

# Sleep for a bit to avoid a race condition on some systems
time.sleep(1)

mouse = Mouse(usb_hid.devices)
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)
light = 10
light_min = 0
light_max = 100
light_pwm = pwmio.PWMOut(board.GP20, frequency = 2000)


import supervisor


def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = supervisor.ticks_ms()
        result = f(*args, **kwargs)
        delta = supervisor.ticks_ms() - t
        print('Function {} Time = {:6.3f}ms'.format(myname, delta))
        return result
    return new_func


def set_light(percent):
    light_pwm.duty_cycle = int((100 - percent) * 65535 / 100)
    
    
set_light(light) # set screen brightness


class Timer(object):
    counter = 0
    max_value = 1000

    @classmethod
    def current(cls):
        return cls.counter

    @classmethod
    # @timed_function
    def add(cls):
        cls.counter += 1
        if cls.counter >= cls.max_value:
            cls.counter = 0
        return cls.counter

    @classmethod
    # @timed_function
    def delta(cls, v):
        if cls.counter > v:
            return cls.counter - v
        else:
            return cls.counter + cls.max_value - v


class Button(object):
    def __init__(self, pin, direction, pull):
        self.io = digitalio.DigitalInOut(pin)
        self.io.direction = direction
        self.io.pull = pull
        self.last_active_time = 0
        self.last_press_time = 0
        self.keep_press_interval = 1
        self.first_press_interval = 5
        self.debounce_interval = 0
        self.status = "up"

    # @timed_function
    def click(self):
        if self.status == "up":
            if self.down():
                self.debounce()
                self.status = "debounce"
        elif self.status == "debounce":
            if Timer.delta(self.last_active_time) > self.debounce_interval:
                if self.up():
                    self.status = "up"
                    return True
        return False

    def press(self):
        return self.status == "debounce"

    # @timed_function
    def continue_click(self):
        if self.status == "up":
            if self.down():
                self.debounce(value = self.first_press_interval)
                self.status = "debounce"
        elif self.status == "debounce":
            if Timer.delta(self.last_active_time) > self.debounce_interval:
                if self.down():
                    self.debounce(value = self.keep_press_interval)
                    return True
                elif self.up():
                    self.status = "up"
                    return True
        return False

    def down(self):
        return not self.io.value

    def debounce(self, value = 2):
        self.last_active_time = Timer.current()
        self.debounce_interval = value

    def up(self):
        return self.io.value


def setup_pin(pin, direction, pull = None):
    io = digitalio.DigitalInOut(pin)
    io.direction = direction
    if pull is not None:
        io.pull = pull
    return io


led = setup_pin(board.GP25, digitalio.Direction.OUTPUT) # breathing light for status checking


class CustomKeyBoard(object):
    x_lines = [
        setup_pin(board.GP4, digitalio.Direction.OUTPUT), # 0
        setup_pin(board.GP5, digitalio.Direction.OUTPUT), # 1
        setup_pin(board.GP6, digitalio.Direction.OUTPUT), # 2
        setup_pin(board.GP7, digitalio.Direction.OUTPUT), # 3
        setup_pin(board.GP8, digitalio.Direction.OUTPUT), # 4
        setup_pin(board.GP9, digitalio.Direction.OUTPUT), # 5
        setup_pin(board.GP10, digitalio.Direction.OUTPUT), # 6
        setup_pin(board.GP11, digitalio.Direction.OUTPUT), # 7
        setup_pin(board.GP12, digitalio.Direction.OUTPUT), # 8
        setup_pin(board.GP13, digitalio.Direction.OUTPUT), # 9
    ]
    y_lines = [
        setup_pin(board.GP14, digitalio.Direction.INPUT, digitalio.Pull.UP), # 0
        setup_pin(board.GP15, digitalio.Direction.INPUT, digitalio.Pull.UP), # 1
        setup_pin(board.GP16, digitalio.Direction.INPUT, digitalio.Pull.UP), # 2
        setup_pin(board.GP17, digitalio.Direction.INPUT, digitalio.Pull.UP), # 3
        setup_pin(board.GP18, digitalio.Direction.INPUT, digitalio.Pull.UP), # 4
        setup_pin(board.GP19, digitalio.Direction.INPUT, digitalio.Pull.UP), # 5
    ]
    keys = [
        [K.Q, K.W, K.E, K.R, K.T, K.Y, K.U, K.I, K.O, K.P],
        [K.A, K.S, K.D, K.F, K.G, K.H, K.J, K.K, K.L, K.SEMICOLON],
        [K.Z, K.X, K.C, K.V, K.B, K.N, K.M, K.COMMA, K.PERIOD, K.FORWARD_SLASH],
        [K.ESCAPE, K.QUOTE, K.MINUS, K.EQUALS, K.SPACE, K.ENTER, K.LEFT_BRACKET, K.RIGHT_BRACKET, K.BACKSLASH, (K.BACKSPACE, K.PRINT_SCREEN)],
        [(K.ONE, K.F1), (K.TWO, K.F2), (K.THREE, K.F3), (K.FOUR, K.F4), (K.FIVE, K.F5), (K.SIX, K.F6), (K.SEVEN, K.DELETE), (K.EIGHT, K.CAPS_LOCK), (K.NINE, K.HOME), (K.ZERO, K.END)],
        [FN, K.TAB, K.LEFT_CONTROL, K.ALT, K.RIGHT_SHIFT, K.GRAVE_ACCENT, K.UP_ARROW, K.DOWN_ARROW, (K.LEFT_ARROW, K.PAGE_UP), (K.RIGHT_ARROW, K.PAGE_DOWN)],
        #[K.LEFT_SHIFT, (K.F1, K.F7), (K.F2, K.F8), (K.F3, K.F9), (K.F4, K.F10), (K.F5, K.F11), (K.F6, K.F12), (K.HOME, K.END), (K.CAPS_LOCK, K.DELETE), K.RIGHT_SHIFT], K.PAGE_UP, K.PAGE_DOWN
        #[FN, K.WINDOWS ,K.TAB, K.LEFT_CONTROL, K.ALT, K.GRAVE_ACCENT, K.UP_ARROW, K.DOWN_ARROW, K.LEFT_ARROW, K.RIGHT_ARROW],
        # [K.LEFT_SHIFT, K.TAB, K.LEFT_CONTROL, K.ALT, K.GRAVE_ACCENT, K.UP_ARROW, K.DOWN_ARROW, (K.LEFT_ARROW, K.PAGE_UP), (K.RIGHT_ARROW, K.PAGE_DOWN), K.RIGHT_SHIFT],
        # [FN, K.WINDOWS, (K.F1, K.F7), (K.F2, K.F8), (K.F3, K.F9), (K.F4, K.F10), (K.F5, K.F11), (K.F6, K.F12), (K.HOME, K.END), (K.DELETE, K.CAPS_LOCK)],
    ]
    last_active_time = 0
    last_press_time = 0
    debounce_interval = 0
    continue_press_interval = 0
    keep_press_interval = 2
    first_press_interval = 12
    press_buttons = [
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
    ]
    buttons = []
    release = []
    n = 0

    @classmethod
    def press_keys(cls, keys = []):
        global keyboard
        cls.buttons = []
        keyboard.press(*keys)
        keyboard.release(*keys)
        cls.release.clear()

    @classmethod
    # @timed_function
    def scan(cls):
        global light
        global light_min
        global light_max
        global mouse
        global keyboard
        if Timer.delta(cls.last_active_time) > cls.debounce_interval:
            cls.last_active_time = Timer.current()
            for x in range(10):
                for i in range(10):
                    if i == x:
                        cls.x_lines[i].value = False # scan x line
                    else:
                        cls.x_lines[i].value = True # disable other lines
                for y in range(5, -1, -1):
                    if cls.y_lines[y].value == False: # pressd
                        if cls.press_buttons[y][x]: # y,x pressed, already pressed
                            pass
                        else: # y,x not pressed, first press
                            if cls.press_buttons[5][0]: # fn pressed
                                if y == 5 and x == 0:
                                    pass
                                else:
                                    if isinstance(cls.keys[y][x], tuple):
                                        cls.buttons.append(cls.keys[y][x][1])
                                    else:
                                        cls.buttons.append(cls.keys[y][x])
                            else:
                                if y == 5 and x == 0:
                                    pass
                                else:
                                    if isinstance(cls.keys[y][x], tuple):
                                        cls.buttons.append(cls.keys[y][x][0])
                                    else:
                                        cls.buttons.append(cls.keys[y][x])
                            cls.press_buttons[y][x] = True
                            cls.continue_press_interval = cls.first_press_interval
                    else: # not press
                        if cls.press_buttons[y][x]:
                            cls.press_buttons[y][x] = False
                            if y == 5 and x == 0:
                                pass
                            else:
                                if isinstance(cls.keys[y][x], tuple):
                                    if cls.keys[y][x][0] in cls.buttons:
                                        cls.buttons.remove(cls.keys[y][x][0])
                                        cls.release.append(cls.keys[y][x][0])
                                    else:
                                        cls.buttons.remove(cls.keys[y][x][1])
                                        cls.release.append(cls.keys[y][x][1])
                                else:
                                    if cls.keys[y][x] in cls.buttons:
                                        cls.buttons.remove(cls.keys[y][x])
                                    cls.release.append(cls.keys[y][x])
            if cls.press_buttons[5][0]:
                if K.UP_ARROW in cls.buttons:
                    consumer_control.send(C.VOLUME_INCREMENT)
                    cls.buttons.remove(K.UP_ARROW)
                elif K.DOWN_ARROW in cls.buttons:
                    consumer_control.send(C.VOLUME_DECREMENT)
                    cls.buttons.remove(K.DOWN_ARROW)
                elif K.W in cls.buttons:
                    consumer_control.send(C.VOLUME_INCREMENT)
                    light -= 5
                    if light < light_min:
                        light = light_min
                    print(light)
                    set_light(light)
                    cls.buttons.remove(K.W)
                elif K.Q in cls.buttons:
                    light += 5
                    if light > light_max:
                        light = light_max
                    print(light)
                    set_light(light)
                    cls.buttons.remove(K.Q)
                elif K.O in cls.buttons: # mouse up
                    mouse.move(x = 0, y = -15)
                    cls.buttons.remove(K.O)
                elif K.L in cls.buttons: # mouse down
                    mouse.move(x = 0, y = 15)
                    cls.buttons.remove(K.L)
                elif K.K in cls.buttons: # mouse left
                    mouse.move(x = -15, y = 0)
                    cls.buttons.remove(K.K)
                elif K.SEMICOLON in cls.buttons: # right
                    mouse.move(x = 15, y = 0)
                    cls.buttons.remove(K.SEMICOLON)
                elif K.I in cls.buttons: # mouse left key
                    mouse.click(Mouse.LEFT_BUTTON)
                    cls.buttons.remove(K.I)
                elif K.P in cls.buttons: # mouse right key
                    mouse.click(Mouse.RIGHT_BUTTON)
                    cls.buttons.remove(K.P)
                elif K.U in cls.buttons: # mouse wheel up key
                    mouse.move(wheel = 3)
                    cls.buttons.remove(K.U)
                elif K.J in cls.buttons: # mouse wheel down key
                    mouse.move(wheel = -3)
                    cls.buttons.remove(K.J)
                elif K.SPACE in cls.buttons: # text mode vlc play/pause
                    cls.press_keys([K.P, K.A, K.U, K.S, K.E, K.ENTER])
                elif K.Z in cls.buttons: # text mode vlc stop
                    cls.press_keys([K.S, K.T, K.O, K.P, K.ENTER])
                elif K.X in cls.buttons: # text mode vlc prev
                    cls.press_keys([K.P, K.R, K.E, K.V, K.ENTER])
                elif K.C in cls.buttons: # text mode vlc next
                    cls.press_keys([K.N, K.E, K.X, K.T, K.ENTER])
                elif K.B in cls.buttons: # text mode vlc voldown 2
                    cls.press_keys([K.V, K.O, K.L, K.D])
                    cls.press_keys([K.O, K.W, K.N, K.SPACE, K.TWO, K.ENTER])
                elif K.N in cls.buttons: # text mode vlc volup 2
                    cls.press_keys([K.V, K.O, K.L, K.U, K.P])
                    cls.press_keys([K.SPACE, K.TWO, K.ENTER])
                elif K.M in cls.buttons: # text mode vlc backward 20 seconds
                    cls.press_keys([K.S, K.E])
                    cls.press_keys([K.E, K.K, K.SPACE])
                    cls.press_keys([K.MINUS, K.TWO, K.ZERO, K.ENTER])
                elif K.COMMA in cls.buttons: # text mode vlc forward 20 seconds
                    cls.press_keys([K.S, K.E])
                    cls.press_keys([K.E, K.K, K.SPACE])
                    cls.press_keys([K.RIGHT_SHIFT, K.EQUALS])
                    cls.press_keys([K.TWO, K.ZERO, K.ENTER])
                elif K.PERIOD in cls.buttons: # text mode vlc backward 5 seconds
                    cls.press_keys([K.S, K.E])
                    cls.press_keys([K.E, K.K, K.SPACE])
                    cls.press_keys([K.MINUS, K.FIVE, K.ENTER])
                elif K.FORWARD_SLASH in cls.buttons: # text mode vlc forward 5 seconds
                    cls.press_keys([K.S, K.E])
                    cls.press_keys([K.E, K.K, K.SPACE])
                    cls.press_keys([K.RIGHT_SHIFT, K.EQUALS])
                    cls.press_keys([K.FIVE, K.ENTER])
            try:
                keyboard.press(*cls.buttons)
                keyboard.release(*cls.release)
                cls.release.clear() # = []
                # keyboard.release_all()
            except Exception as e:
                cls.release.clear()
                try:
                    mouse.release_all()
                    keyboard.release_all()
                except Exception as e:
                    print("release_all keys error: ", e)
                try:
                    time.sleep(1)
                    mouse = Mouse(usb_hid.devices)
                    keyboard = Keyboard(usb_hid.devices)
                except Exception as e:
                    print("reinit mouse & keyboard error: ", e)
                print(e)


# @timed_function
def main(): # 25ms
    t = supervisor.ticks_ms()
    CustomKeyBoard.scan()
    Timer.add()
    tt = supervisor.ticks_ms() - t
    sleep_time = 25 - tt
    if sleep_time > 0:
        try:
            time.sleep(sleep_time / 1000)
        except Exception as e:
            print(e)


led.value = True
led_n = 0
while True: # 40Hz
    try:
        main()
        led_n += 1
        if led_n > 20:
            led_n = 0
            led.value = not led.value
            #print(float(100 - (gc.mem_free() * 100 / (264 * 1024))))
            gc.collect()
    except Exception as e:
        print(e)
        gc.collect()

microcontroller.reset() # reboot
