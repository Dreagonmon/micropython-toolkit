'''
    ESP32 Micropython mid micro player, using a bee
'''
import umid

# index 0 is note C(-1)
note_freq = [16, 17, 18, 19, 21, 22, 23, 24, 26, 28, 29, 31, 33, 35, 37, 39, 41, 44, 46, 49, 52, 55, 58, 62, 65, 69, 73, 78, 82, 87, 92, 98, 104, 110, 117, 123, 131, 139, 147, 156, 165, 175, 185, 196, 208, 220, 233, 247, 262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494, 523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 932, 988, 1046, 1109, 1175, 1244, 1318, 1397, 1480, 1568, 1661, 1760, 1865, 1976, 2093, 2218, 2349, 2489, 2637, 2794, 2960, 3136, 3322, 3520, 3729, 3951, 4186, 4435, 4699, 4978, 5274, 5588, 5920, 6272, 6645, 7040, 7459, 7902, 8372, 8870, 9397, 9956, 10548, 11175, 11840, 12544, 13290, 14080, 14917, 15804]
volume_duty = [1023, 1022, 1021, 1020, 1017, 1015, 1013, 1010, 1000, 512]

from machine import Pin, PWM, Timer
from micropython import schedule
# tim0 = Timer(0)
# tim0.init(period=5000, mode=Timer.ONE_SHOT, callback=lambda t:print(0))
SIGNAL_DEFAULT = 0
SIGNAL_STOP = -1
class BeeSinger():
    def __init__(self, bee_io, timer_id, mid_path):
        self.__pwm = PWM(Pin(bee_io), freq=100000, duty=volume_duty[0])
        with open(mid_path, "rb") as f:
            self.__player = umid.MIDIPlayer(f)
        self.__timer = Timer(timer_id)
        self.__volume = volume_duty[0]
        self.__loop = False
        self.__track = 0
    
    def turn_on(self):
        self.__pwm.init(freq=100000, duty=volume_duty[0])

    def turn_off(self):
        ''' not just stop, but turn off completely'''
        self.__pwm.deinit()
    
    def _timer_callback(self, _):
        schedule(self.play_next_note, None)

    def start(self):
        self.__player.reset(self.__track)
        self.__timer.init(mode=Timer.ONE_SHOT, period=0, callback=self._timer_callback)

    def stop(self):
        self.__timer.deinit()
        self.__pwm.freq(100000)
        self.__pwm.duty(volume_duty[0])

    def play_next_note(self, _):
        during, event = self.__player.next_event(self.__track)
        if event[0] == umid.TRACK_EVENT_TYPE_META_RESET and event[1] == umid.META_TYPE_END_OF_TRACK:
            self.start() if self.__loop else self.stop()
            return
        if event[0] & umid.TRACK_EVENT_TYPE_MASK1 == umid.TRACK_EVENT_TYPE_NOTE_OFF:
            note = event[4]
            note = 0 if note < 0 else note
            note = len(note_freq) - 1 if note >= len(note_freq) else note
            self.__pwm.freq(note_freq[note])
            self.__pwm.duty(volume_duty[1])
        elif event[0] & umid.TRACK_EVENT_TYPE_MASK1 == umid.TRACK_EVENT_TYPE_NOTE_ON:
            note = event[4]
            note = 0 if note < 0 else note
            note = len(note_freq) - 1 if note >= len(note_freq) else note
            self.__pwm.freq(note_freq[note])
            self.__pwm.duty(self.__volume)
        during = during // 1000 # us -> ms
        self.__timer.init(mode=Timer.ONE_SHOT, period=during, callback=self._timer_callback)

    def set_volume(self, select):
        ''' set volume 0~9 '''
        self.__volume = volume_duty[select]

    def set_loop(self, is_loop):
        self.__loop = is_loop

    def select_track(self, track_id):
        self.__track = track_id
