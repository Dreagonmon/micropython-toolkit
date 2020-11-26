
TRACK_TYPE_SINGLE = 0x00
TRACK_TYPE_MULTI_SYNC = 0x01
TRACK_TYPE_MULTI_NOSYNC = 0x02
DIVISION_TYPE_TICKS = 0X00 # default 4/4 note length, 120bpm, 6beat
DIVISION_TYPE_SMTPE = 0X01
TRACK_EVENT_TYPE_MASK1 = 0b1111_0000
TRACK_EVENT_TYPE_NOTE_OFF = 0b1000_0000
TRACK_EVENT_TYPE_NOTE_ON = 0b1001_0000
TRACK_EVENT_TYPE_POLYPHONIC_KEY_PRESSURE  = 0b1010_0000
TRACK_EVENT_TYPE_CONTROL_CHANGE = 0b1011_0000
TRACK_EVENT_TYPE_PROGRAM_CHANGE = 0b1100_0000
TRACK_EVENT_TYPE_CHANNEL_PRESSURE = 0b1101_0000
TRACK_EVENT_TYPE_PITCH_WHEEL_CHANGE = 0b1110_0000
TRACK_EVENT_TYPE_SYSTEM = 0b1111_0000
TRACK_EVENT_TYPE_MASK2 = 0b0000_1111
TRACK_EVENT_TYPE_SYSTEM_EXCLUSIVE = 0b1111_0000
TRACK_EVENT_TYPE_SONG_POSITION_POINTER = 0b1111_0010
TRACK_EVENT_TYPE_SONG_SELECT = 0b1111_0011
TRACK_EVENT_TYPE_TUNE_REQUEST = 0b1111_0110
TRACK_EVENT_TYPE_END_OF_EXCLUSIVE = 0b1111_0111 # also ESCAPE
TRACK_EVENT_TYPE_TIMING_CLOCK = 0b1111_1000
TRACK_EVENT_TYPE_START = 0b1111_1010
TRACK_EVENT_TYPE_CONTINUE = 0b1111_1011
TRACK_EVENT_TYPE_STOP = 0b1111_1100
TRACK_EVENT_TYPE_ACTIVE_SENSING = 0b1111_1110
TRACK_EVENT_TYPE_META_RESET = 0b1111_1111 # meta-data
TRACK_EVENT_LENGTH = {
    TRACK_EVENT_TYPE_NOTE_OFF: 2,
    TRACK_EVENT_TYPE_NOTE_ON: 2,
    TRACK_EVENT_TYPE_POLYPHONIC_KEY_PRESSURE: 2,
    TRACK_EVENT_TYPE_CONTROL_CHANGE: 2,
    TRACK_EVENT_TYPE_PROGRAM_CHANGE: 1,
    TRACK_EVENT_TYPE_CHANNEL_PRESSURE: 1,
    TRACK_EVENT_TYPE_PITCH_WHEEL_CHANGE: 2,
    # TRACK_EVENT_TYPE_SYSTEM: see below
}
TRACK_SYSTEM_EVENT_LENGTH = {
    TRACK_EVENT_TYPE_SYSTEM_EXCLUSIVE: -1,
    TRACK_EVENT_TYPE_SONG_POSITION_POINTER: 2,
    TRACK_EVENT_TYPE_SONG_SELECT: 1,
    TRACK_EVENT_TYPE_END_OF_EXCLUSIVE: -1,
    TRACK_EVENT_TYPE_META_RESET: -1,
    # else 0
}
META_TYPE_END_OF_TRACK = 0x2F
META_TYPE_SET_TEMPO = 0x51

def _read_until(stream, ending, read_block_size = 1):
    data = b''
    block = stream.read(read_block_size)
    readed = read_block_size
    while len(block) > 0:
        data += block
        if data.endswith(ending):
            return data
        block = stream.read(read_block_size)
        readed += read_block_size
    return readed, data

def _read_dyn_uint(stream):
    num = 0
    byt = stream.read(1)[0]
    readed = 1
    while byt & 0x80:
        num |= (byt & 0x7F)
        num <<= 7
        byt = stream.read(1)[0]
        readed += 1
    num |= byt
    return readed, num

def _get_midi_track_event_length(event_type):
    if (event_type & TRACK_EVENT_TYPE_MASK1) in TRACK_EVENT_LENGTH:
        return TRACK_EVENT_LENGTH[event_type & TRACK_EVENT_TYPE_MASK1]
    if event_type in TRACK_SYSTEM_EVENT_LENGTH:
        return TRACK_SYSTEM_EVENT_LENGTH[event_type]
    return 0

def _parse_event_block(event_type, meta_type, delta, event_data):
    ''' (event_type, meta_type, delta, event_data) -> bytes '''
    byts = bytearray([event_type, meta_type])
    byts.extend(int.to_bytes(delta, 2, 'big'))
    byts.extend(event_data)
    return bytes(byts)

def _read_midi_track_event(stream):
    ''' return (readed_size, event_block_bytes '''
    readed, delta = _read_dyn_uint(stream)
    event_type = stream.read(1)[0]
    readed += 1
    event_length = _get_midi_track_event_length(event_type)
    if event_length >= 0:
        return readed + event_length, _parse_event_block(event_type, 0, delta, stream.read(event_length))
    elif event_type == TRACK_EVENT_TYPE_SYSTEM_EXCLUSIVE:
        size, data = _read_until(stream, bytes([TRACK_EVENT_TYPE_END_OF_EXCLUSIVE]), 1)
        return readed + size, _parse_event_block(event_type, 0, delta, data[:-1])
    elif event_type == TRACK_EVENT_TYPE_END_OF_EXCLUSIVE:
        readed2, size = _read_dyn_uint(stream)
        readed += readed2
        return readed + size, _parse_event_block(event_type, 0, delta, stream.read(size))
    else: # meta
        meta_type = stream.read(1)[0]
        readed += 1
        readed2, size = _read_dyn_uint(stream)
        readed += readed2
        return readed + size, _parse_event_block(event_type, meta_type, delta, stream.read(size))

def _read_midi_header(stream, check_id=True):
    ''' return (readed_size, track_type, track_count, division) '''
    if check_id:
        assert stream.read(4) == b'MThd'
    assert stream.read(4) == b'\x00\x00\x00\x06'
    track_type = int.from_bytes(stream.read(2), 'big')
    track_count = int.from_bytes(stream.read(2), 'big')
    division = int.from_bytes(stream.read(2), 'big')
    # division_type = note_ticks >> 15 # 0:每个四分音符的ticks 1:每秒中SMTPE帧的数量
    # division = note_ticks & 0x7FFF
    return 14 if check_id else 10, track_type, track_count, division

def _read_midi_track(stream, check_id=True):
    ''' return (readed_size, track_event_list:[event_block_bytes]) '''
    readed = 0
    if check_id:
        assert stream.read(4) == b'MTrk'
        readed += 4
    track_data_size = int.from_bytes(stream.read(4), 'big')
    content_count = 0
    event_list = []
    readed2, event = _read_midi_track_event(stream)
    while True:
        event_list.append(event)
        readed += readed2
        content_count += readed2
        if content_count < track_data_size:
            readed2, event = _read_midi_track_event(stream)
        else:
            break
    return readed, MIDITrack(event_list)

class MIDITrack():
    def __init__(self, events):
        self.events = events # MIDITrackEvent: [event_block_bytes:b'u8_event_type|u8_meta_type|u16_delta|u8array_data']
        self.meta = {
            META_TYPE_SET_TEMPO: b'\x07\xA1\x20' # 500_000us
        }
        start_event_index = 0 # first no-meta event index
        for event in events:
            if event[0] == TRACK_EVENT_TYPE_META_RESET:
                self.meta[event[1]] = event[4:]
                start_event_index += 1
            else:
                break
        for _ in range(start_event_index):
            del self.events[0]
        self.us_per_beat = int.from_bytes(self.meta[META_TYPE_SET_TEMPO], 'big')
    
    def __repr__(self):
        return '<MIDITrack events="{}" us_per_beat="{}" />'.format(len(self.events), self.us_per_beat)

class MIDIFile():
    def __init__(self, stream):
        _, self.__track_type, self.__track_count, self.__division = _read_midi_header(stream)
        self.tracks = []
        for _ in range(self.__track_count):
            _, track = _read_midi_track(stream)
            self.tracks.append(track)
    @property
    def track_type(self):
        return self.__track_type
    @property
    def track_count(self):
        return self.__track_count
    @property
    def division(self):
        return self.__division

    def __repr__(self):
        return '<MIDIFile tracks="{}" division="{}" />'.format(self.__track_count, self.__division)

class MIDIPlayer():
    def __init__(self, stream):
        self.__midobj = MIDIFile(stream)
        self.__pointer = [0] * self.__midobj.track_count
        self.__ups = []
        for track in self.__midobj.tracks:
            self.__ups.append(track.us_per_beat)
    
    def next_event(self, track_id):
        ''' return next_us, track_event_bytes '''
        pos = self.__pointer[track_id]
        event = self.__midobj.tracks[track_id].events[pos]
        if event[0] == TRACK_EVENT_TYPE_META_RESET:
            if event[1] == META_TYPE_SET_TEMPO:
                self.__ups[track_id] = int.from_bytes(event[4:], 'big')
            elif event[1] == META_TYPE_END_OF_TRACK:
                return 0, event
        pos += 1
        self.__pointer[track_id] = pos
        if event[0] & TRACK_EVENT_TYPE_MASK1 == TRACK_EVENT_TYPE_NOTE_OFF or event[0] & TRACK_EVENT_TYPE_MASK1 == TRACK_EVENT_TYPE_NOTE_ON:
            next_event = self.__midobj.tracks[track_id].events[pos]
            next_us = int.from_bytes(next_event[2:4], 'big') * self.__ups[track_id] // self.__midobj.division
            return next_us, event
        else:
            return self.next_event(track_id) # ignore other event

    def reset(self, track_id):
        self.__pointer[track_id] = 0
        self.__ups[track_id] = self.__midobj.tracks[track_id].us_per_beat
