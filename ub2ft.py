from tkinter import filedialog # file dialogue
from json import loads # read input file
from os import system # pause when exiting code

base = '''# FamiTracker text export 0.4.2

# Song information
TITLE           ""
AUTHOR          ""
COPYRIGHT       ""

# Song comment
COMMENT ""

# Global settings
MACHINE         0
FRAMERATE       0
EXPANSION       0
VIBRATO         1
SPLIT           32

# Macros
MACRO       4   1  -1  -1   0 : 1
MACRO       4   2  -1  -1   0 : 2
[MACROS]
# DPCM samples

# Instruments
[INSTRUMENTS]
# Tracks

TRACK  32   3 [BPM] "New song"
COLUMNS :[EFFECTS_COUNT]
[SEQUENCES]

[PATTERNS]# End of export
'''

base_notes = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
channel_types = ["pitch1","pitch2","triangle1","noise1"]
pulse_type = {'square': 2, '1/4 pulse': 1, '1/8 pulse': 0}

AGRESSIVE_EFFECT_RESET = "y" == input("Use aggressive effect reset? [y/n]\n- This will prevent arpeggio and fade in/out effects from persisting trough another pattern, this can however break the transition of the detune effect and will increase the amount of effects considerably. Use this option if the transition between pattern isn't done correctly.\n").lower()

input_path = filedialog.askopenfilename(title="Ultrabox input file", filetypes=[("*.json", "Ultrabox JSON export file")])
if input_path == "":
    quit()

print(f"\nConverting: {input_path}\nAggressive effect reset: {AGRESSIVE_EFFECT_RESET}\n")

ub_data = {}
with open(input_path, 'r', encoding="utf-8") as f:
    ub_data = loads(f.read())
    f.close()

tick_offset = 8 / ub_data['ticksPerBeat']
bpm = ub_data['beatsPerMinute']
highest_volume = 0

key_offset = 0
for n in range(len(base_notes)):
    if base_notes[n].replace('-', '') == ub_data['key'].replace('♯', '#'):
        key_offset = n
        break
key_offset += (12 * ub_data['keyOctave'])

def index_to_hex(i: int) -> str:
    return str(hex(i))[2:].upper().zfill(2)

custom_macros = []
class Macro:
    global_volume_index = 0
    global_blip_index = 0
    
    def __init__(self, volume, pitch_blip):
        self.volume = volume
        self.pitch_blip = pitch_blip

        # volume index
        if self.volume != 0:
            self.volume_index = Macro.global_volume_index
            Macro.global_volume_index += 1
        else:
            self.volume_index = -1
        
        # blip index
        if pitch_blip:
            self.blip_index = Macro.global_blip_index
            Macro.global_blip_index += 1
        else:
            self.blip_index = -1
                
        self.display = ""

    # Macro
    # volume = 0
    # arpeggio = 1
    # MACRO       TYPE   ID  -1  -1   0 : VALUE
    def update_display(self):
        self.display = ""

        if self.volume != 0:
            true_volume = (self.volume - highest_volume) + 15
            if true_volume < 1:
                true_volume = 1
            if true_volume > 15:
                true_volume = 15
            self.display += f"MACRO       0   {self.volume_index}  -1  -1   0 : {true_volume}\n"
        
        if self.pitch_blip:
            self.display += f"MACRO       1   {self.blip_index}  -1  -1   0 : 17 0\n"


instruments = []
class Instrument:
    global_index = 0
    
    def __init__(self, channel_type, pulse, pitch_blip, detune, volume):
        self.index = Instrument.global_index
        Instrument.global_index += 1

        if channel_type == 3:
            volume += 2

        self.pulse = pulse
        self.channel_type = channel_type
        self.pitch_blip = pitch_blip
        self.detune = detune
        self.volume = volume
        self.display = ""
        self.macro = Macro(volume, pitch_blip)
        custom_macros.append(self.macro)

    # Instruments
    # -1 = disabled
    # INST2A03   ID     VOL   0  PITCH  -1   WAVE "NAME"
    def update_display(self):
        self.display = f'INST2A03   {index_to_hex(self.index)}     {self.macro.volume_index}   {self.macro.blip_index}  -1  -1   {self.pulse} "{channel_types[self.channel_type]}{self.index}"\n'

sequences = []
class Sequence:
    def __init__(self, index):
        self.index = index
        self.channels = [0, 0, 0, 0, 0] # pulse1, pulse2, triangle, noise, DPCM
        self.display = ""

    def update_display(self):
        true_index = index_to_hex(self.index)
        self.display = f"\nORDER {true_index} :"
        for c in self.channels:
            true_pat_index = str(c).zfill(2)
            self.display += f" {true_pat_index}"

patterns = []
class Pattern:    
    def __init__(self, index):
        self.index = index + 1
        self.rows = []
        self.display = ""
        
        for r in range(32):
            self.rows.append(Row(r))

    def update_display(self):
        for r in self.rows:
            r.update_display()
            
        true_index = index_to_hex(self.index)
        self.display = f"PATTERN {true_index}\n"
        for r in self.rows:
            self.display += f"{r.display}\n"
        self.display += "\n"

class Empty:
    def __init__(self, channel):
        self.channel = channel
        self.display = ""

    def update_display(self):
        effects_count = effects_per_channels[self.channel]
        self.display = "... .. ." + (" ..." * effects_count)


class Row:
    def __init__(self, index):
        self.index = index
        self.channels = [Empty(0), Empty(1), Empty(2), Empty(3), Empty(4)] # pulse1, pulse2, triangle, noise, DPCM
        self.display = ""
    
    def update_display(self):
        for c in self.channels:
            c.update_display()
        true_index = index_to_hex(self.index)
        self.display = f"ROW {true_index} : "
        for c in self.channels:
            self.display += f"{c.display} : "
        self.display = self.display[:-3]

class Note:
    def __init__(self, pitch, volume, effects, isDrum, instrument, channel):
        self.pitch = pitch
        self.volume = volume
        self.effects = effects
        self.isDrum = isDrum
        self.instrument = instrument
        self.channel = channel
        self.display = ""
    
    def update_display(self):
        key = base_notes[self.pitch%len(base_notes)]
        octave = self.pitch // 12

        true_volume = 'F' if self.volume >= 100 else int(self.volume // 10)
        if true_volume == 0: true_volume = 1

        if self.isDrum:
            self.display = f"{self.pitch-2-key_offset}-# {index_to_hex(self.instrument.index)} {true_volume}"
        else:
            self.display = f"{key}{octave} {index_to_hex(self.instrument.index)} {true_volume}"

        # effects
        effects_count = effects_per_channels[self.channel]
        for effect in self.effects[:effects_count]:
            self.display += f" {effect}"

class Stop:
    def __init__(self, channel):
        self.channel = channel
        self.display = ""

    def update_display(self):
        effects_count = effects_per_channels[self.channel]
        self.display = "--- .. ." + (" ..." * effects_count)

class Slide:
    def __init__(self, to, channel, arpeggio = None):
        self.channel = channel
        self.to = to
        self.arpeggio = arpeggio
    
    def update_display(self):
        if self.to > 15: self.to = 15
        if self.to < -15: self.to = -15
        effects_count = effects_per_channels[self.channel]

        self.display = f"... .. . {'Q' if self.to > 0 else 'R'}9{index_to_hex(abs(self.to))[1]}"
        if self.arpeggio != None:
            self.display += f" {self.arpeggio}"
            if effects_count != 0: effects_count -= 1
        self.display += (" ..." * (effects_count-1))


# get patterns/sequences amount
best_pat_len = 0
best_seq_len = 0
for ub_channel in ub_data['channels']:

    if best_pat_len < len(ub_channel['patterns']):
        best_pat_len = len(ub_channel['patterns'])
        
    if best_seq_len < len(ub_channel['sequence']):
        best_seq_len = len(ub_channel['sequence'])

# generate patterns lenght
for i in range(best_pat_len):
    patterns.append(Pattern(i))

# generate sequence lenght
for i in range(best_seq_len):
    sequences.append(Sequence(i))

# remove mod channel
if ub_data['channels'][-1]['type'] == 'mod':
    del ub_data['channels'][-1]

# generate patterns/rows/notes
# channels
effects_per_channels = [1, 1, 1, 1, 1] # pulse1, pulse2, triangle, noise, DPCM
for ub_channel_index in range(len(ub_data['channels'][-4:])): # 4 last channels
    current_channel = ub_data['channels'][-4:][ub_channel_index]

    last_arpeggio = 0
    last_fade = 0
    last_detune = 128

    # instruments
    current_instruments = []
    for instrument in current_channel['instruments']:
        pulse = pulse_type[instrument['wave']] if instrument['wave'] in pulse_type else 0
        effects = instrument['effects']
        volume = instrument['volume'] - (5 if ub_channel_index < 2 else 0) #+ (5 if ub_channel_index == 3 else 0)
        if volume * 2 > highest_volume:
            highest_volume = volume // 2

        # detune
        if instrument['unison'] == 'detune':
            detune = 25
        elif 'detune' in effects:
            detune = instrument['detuneCents']
        else:
            detune = 0

        # pitch blip
        pitch_blip = False
        if 'pitch shift' in effects:
            for e in instrument['envelopes']:
                if e['target'] == 'pitchShift':
                    pitch_blip = True
            
        new_inst = Instrument(ub_channel_index, pulse, pitch_blip, detune, volume)
        instruments.append(new_inst)
        current_instruments.append(new_inst)

    # sequences
    for ub_sequence_index in range(len(current_channel['sequence'])):
        current_sequence = current_channel['sequence'][ub_sequence_index]
        sequences[ub_sequence_index].channels[ub_channel_index] = index_to_hex(current_sequence)

    # patterns
    for ub_patterns_index in range(len(current_channel['patterns'])):
        current_pattern = current_channel['patterns'][ub_patterns_index]

        # notes
        reset_effect = AGRESSIVE_EFFECT_RESET
        for note in current_pattern['notes']:

            # get note info
            start_pos = int(note['points'][0]['tick'] * tick_offset)
            end_pos = int(note['points'][-1]['tick'] * tick_offset)
            note_lenght = end_pos - start_pos
            note_volume = note['points'][0]['volume']
            if note_volume < 1: note_volume = 1

            # get note pitch
            offset = key_offset - (12 if ub_channel_index < 2 else 0)# - ((12 * ub_data['keyOctave']) if ub_channel_index == 2 else 0)
            note_pitch = note['pitches'][0]

            # fade
            fade = 0
            if note['points'][1]['volume'] != note['points'][0]['volume']:
                fade = 1 if note['points'][0]['volume'] > note['points'][1]['volume'] else -1
                if note_lenght > 2:
                    fade *= 2

            # arpeggio
            arpeggio = 0
            if len(note['pitches']) > 1:
                note_arpeggio = note['pitches'][1]
                arpeggio = abs(note_pitch - note_arpeggio)
                if note_pitch > note_arpeggio:
                    note_pitch = note_arpeggio

            note_pitch += offset

            # get slide
            slide_to = note['points'][1]['pitchBend']
            #slide_timing = int(note['points'][1]['tick'] * tick_offset)
            slide_timing = start_pos + 1

            # place note
            if start_pos < len(patterns[ub_patterns_index].rows):
                instrument_index = current_pattern['instruments'][0] - 1 if 'instruments' in current_pattern else 0

                # effects 
                note_effects = []

                # fade in/out
                if fade != last_fade or reset_effect:
                    last_fade = fade
                    if fade != 0:
                        fade_speed = index_to_hex(10 // fade)[1]
                        note_effects.append(f"A0{fade_speed}" if fade >= 1 else f"A{fade_speed}0")
                    # disable fade
                    elif fade == 0:
                        note_effects.append("A00")

                # arpeggio
                arpeggio_effect = ""
                if arpeggio != last_arpeggio or reset_effect:
                    last_arpeggio = arpeggio
                    if arpeggio != 0:
                        if arpeggio > 15:
                            arpeggio = 15
                        arpeggio_effect = f"0{index_to_hex(arpeggio)[1]}0"
                        note_effects.append(arpeggio_effect)
                    # disable arpeggio
                    elif arpeggio == 0:
                        note_effects.append("000")

                # detune
                true_detune = (current_instruments[instrument_index].detune // 10) + 128
                if last_detune != true_detune or reset_effect:
                    last_detune = true_detune
                    note_effects.append(f"P{index_to_hex(true_detune)}")

                # effects count
                if effects_per_channels[ub_channel_index] < len(note_effects):
                    effects_per_channels[ub_channel_index] = len(note_effects)
                
                note_effects += ['...', '...', '...'] # fill empty

                new_note = Note(note_pitch, note_volume, note_effects, current_channel['type'] == "drum", current_instruments[instrument_index], ub_channel_index)
                patterns[ub_patterns_index].rows[start_pos].channels[ub_channel_index] = new_note

            if slide_to != 0:
                new_slide = Slide(slide_to, ub_channel_index, arpeggio_effect if arpeggio_effect != "" else None)
                if slide_timing >= len(patterns[ub_patterns_index].rows):
                    slide_timing -= 1
                patterns[ub_patterns_index].rows[slide_timing].channels[ub_channel_index] = new_slide
                if effects_per_channels[ub_channel_index] < 2 and arpeggio_effect != "":
                    effects_per_channels[ub_channel_index] = 2

            # place stop note
            stop_timing = start_pos + note_lenght
            if stop_timing < 32:
                patterns[ub_patterns_index].rows[stop_timing].channels[ub_channel_index] = Stop(ub_channel_index)
            
            reset_effect = False

    print(f"{ub_channel_index+1}/4 channels completed.")

# create silent/empty pattern
empty_pat = Pattern(-1)
empty_row = Row(0)
empty_row.channels = [Stop(0), Stop(1), Stop(2), Stop(3), Empty(4)]
empty_pat.rows[0] = empty_row
patterns.insert(0, empty_pat)

# create macro result
macro_result = ""
for m in custom_macros:
    m.update_display()
    macro_result += m.display

# create macro result
instruments_result = ""
for i in instruments:
    i.update_display()
    instruments_result += i.display

# create patterns result
patterns_result = ""
for p in patterns:
    p.update_display()
    patterns_result += p.display

# create sequences result 
sequences_result = ""
for s in sequences:
    s.update_display()
    sequences_result += s.display

effects_count_result = ""
for e in effects_per_channels:
    effects_count_result += f" {e}"

result = base.replace(
    '[PATTERNS]', patterns_result).replace(
    '[SEQUENCES]', sequences_result).replace(
    '[MACROS]', macro_result).replace(
    '[INSTRUMENTS]', instruments_result).replace(
    '[EFFECTS_COUNT]', effects_count_result).replace(
    '[BPM]', str(bpm))

print('\nDone!')

file_name = input_path.split('/')[-1].split('.')[0] + "_tracker"
init_dir = ""
for i in __file__.split('\\')[:-1]: init_dir += i + "/"

output_path = filedialog.asksaveasfilename(title="Output path", initialdir=init_dir, initialfile=file_name, defaultextension=".txt", filetypes=[("*.txt", "Famitracker text format")])
if output_path != "":
    with open(output_path, 'w') as f:
        f.write(result)
        f.close()
    #print(f'Output path: {output_path}\n')
else:
    print('Output path incorrect...\n')

system('pause')