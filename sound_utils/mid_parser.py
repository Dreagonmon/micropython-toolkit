''' convert .mid file to bee_note_sound format.
.bns format:
['bns': 3] # magic number
[padding: 1]
[ticks_per_beat: 2] # ticks_per_beat
[frames_count: 4] # frames_count
[
    [time: 2] # time before next event, in ticks.
    [type: 1] # frame type, [on, off, set_tempo, event]
    [padding: 1] # padding, but can store what you want
    [data: 4] # depends on 'type'.
] ... # sound frames (total 'frames_count' frames)
ALL NUMBER ARE UNSIGNED BIG-ENDIAN.
tempo = 500_000 # DEFAULT_TEMPO
time_in_ns = (tempo / ticks_per_beat) * ticks
time_in_ms = time_in_ns // 1000
'''
import os, sys, re
current_path = os.path.abspath(os.path.dirname(__file__))

import mido
from mido import merge_tracks
TYPE_EMIT_EVENT = 0X00
TYPE_SET_TEMPO = 0X01
TYPE_NOTE_ON = 0X02
TYPE_NOTE_OFF = 0X03

class BeeNoteSoundFrame():
    def __init__(self, time=0, frame_type=TYPE_EMIT_EVENT, padding=0, data=bytearray(4)):
        self.time = time
        self.type = frame_type
        self.padding = padding
        self.data = data

    def __repr__(self):
        return '<BeeNoteSoundFrame time={} type={} data={}>'.format(self.time, self.type, str(self.data))

    def get_bytes(self):
        output = bytearray()
        output.extend(int.to_bytes(self.time, 2, 'big', signed=False))
        output.append(self.type)
        output.append(self.padding)
        output.extend(self.data)
        return bytes(output)
    
    @staticmethod
    def from_bytes(data):
        assert len(data) == 8
        time = int.from_bytes(data[:2], 'big', signed=False)
        frame_type = data[2]
        padding = data[3]
        frame_data = data[4:]
        return BeeNoteSoundFrame(time, frame_type, padding, frame_data)

    @staticmethod
    def emit_event(time=0, event_data=b'\x00\x00\x00\x00'):
        assert time >= 0 and time < 2**16
        assert len(event_data) == 4
        return BeeNoteSoundFrame(time, TYPE_EMIT_EVENT, 0, event_data)
    
    @staticmethod
    def set_tempo(time=0, tempo=500_000):
        assert time >= 0 and time < 2**16
        assert tempo >= 0 and tempo < 2**32
        tempo_data = int.to_bytes(tempo, 4, 'big', signed=False)
        return BeeNoteSoundFrame(time, TYPE_SET_TEMPO, 0, tempo_data)
    
    @staticmethod
    def note_on(time=0, note=0, velocity=64):
        assert time >= 0 and time < 2**16
        assert note >= 0 and note < 128
        assert velocity >= 0 and velocity < 128
        data = bytes([note, velocity, 0, 0])
        return BeeNoteSoundFrame(time, TYPE_NOTE_ON, 0, data)
    
    @staticmethod
    def note_off(time=0):
        assert time >= 0 and time < 2**16
        data = bytes(4)
        return BeeNoteSoundFrame(time, TYPE_NOTE_OFF, 0, data)

class BeeNoteSound():
    def __init__(self, ticks_per_beat=480, frames=[]):
        self.ticks_per_beat = ticks_per_beat
        self.frames = frames
    
    def append(self, frame):
        self.frames.append(frame)

    def get_bytes(self):
        output = bytearray(b'bns\x00')
        output.extend(int.to_bytes(self.ticks_per_beat, 2, 'big', signed=False))
        output.extend(int.to_bytes(len(self.frames), 4, 'big', signed=False))
        for frame in self.frames:
            output.extend(frame.get_bytes())
        return bytes(output)
    
    @staticmethod
    def from_bytes(data):
        assert tuple(data[:3]) == tuple(b'bns')
        ticks_per_beat = int.from_bytes(data[4:6], 'big', signed=False)
        frame_count = int.from_bytes(data[6:10], 'big', signed=False)
        frames = []
        for i in range(frame_count):
            offset = 10 + i * 8
            frame_data = data[offset: offset + 8]
            frames.append(BeeNoteSoundFrame.from_bytes(frame_data))
        return BeeNoteSound(ticks_per_beat, frames)

def convert_to_bee_note_sound(midfile):
    # midfile must be a single note one.
    bns = BeeNoteSound(midfile.ticks_per_beat)
    last_frame = None
    def commit_last_frame(msg):
        if msg.time == 0 and last_frame and (last_frame.type in [TYPE_NOTE_ON, TYPE_NOTE_OFF]):
            # override last_frame
            pass
        elif last_frame:
            last_frame.time = int(msg.time)
            bns.frames.append(last_frame)
    for msg in merge_tracks(midfile.tracks):
        commit_last_frame(msg)
        if msg.type == 'note_on':
            if msg.velocity > 0 and msg.note >= 0:
                last_frame = BeeNoteSoundFrame.note_on(0, msg.note, msg.velocity)
            else:
                last_frame = BeeNoteSoundFrame.note_off(0)
        elif msg.type == 'note_off':
            last_frame = BeeNoteSoundFrame.note_off(0)
        elif msg.type == 'set_tempo':
            last_frame = BeeNoteSoundFrame.set_tempo(0, msg.tempo)
        elif msg.type == 'end_of_track':
            commit_last_frame(msg)
            bns.frames.append(BeeNoteSoundFrame.note_off(0))
        else:
            last_frame = None
        # no event frame.
    return bns

def convert_to_single_note_midi(midfile):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    mid.ticks_per_beat = midfile.ticks_per_beat
    time_offset = 0
    playing_note = -1
    for msg in merge_tracks(midfile.tracks):
        if msg.type == 'note_on':
            if playing_note > 0:
                if msg.time > 0:
                    # turn off last
                    track.append(mido.Message(type='note_off', note=playing_note, velocity=0, channel=0, time=msg.time+time_offset))
                    track.append(msg.copy(channel=0, time=0))
                else:
                    # replace last note_on
                    meta = []
                    last_msg = track.pop()
                    while last_msg.type != 'note_on':
                        meta.append(last_msg)
                        last_msg = track.pop()
                    track.append(msg.copy(channel=0, time=last_msg.time+time_offset))
                    track.extend(meta)
            else:
                track.append(msg.copy(channel=0, time=msg.time+time_offset))
            playing_note = msg.note
            time_offset = 0
        elif msg.type == 'note_off':
            if msg.note == playing_note:
                track.append(msg.copy(channel=0, time=msg.time+time_offset))
                playing_note = -1
                time_offset = 0
        elif msg.type == 'set_tempo':
            track.append(msg.copy(time=msg.time+time_offset))
            time_offset = 0
        elif msg.time > 0:
            time_offset += msg.time
    return mid

def convert_midi_to_bns(file_name):
    mid_file = mido.MidiFile(file_name)
    mid_file.tracks = mid_file.tracks[0:2]
    mid = convert_to_single_note_midi(mid_file)
    bns = convert_to_bee_note_sound(mid)
    return bns

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        output_name = re.sub(r"\.mid$", ".bns", file_name, flags=re.IGNORECASE)
        bns = convert_midi_to_bns(file_name)
        with open(output_name, "wb") as f:
            f.write(bns.get_bytes())
