import subprocess, os, winsound
import sounddevice as sd
import soundfile as sf

def play_audio(audio_file):
    # Play audio using ffplay with suppressed output
    try:
        print(f"Playing audio: {audio_file}")
        
        # Build the ffplay command
        command = ['ffplay', '-nodisp', '-autoexit', audio_file]
        
        # Suppress output by redirecting stdout and stderr to os.devnull
        with open(os.devnull, 'w') as devnull:
            subprocess.run(command, stdout=devnull, stderr=devnull)
    except Exception as e:
        print(f"Failed to play audio: {e}")
    finally:
        os.remove(audio_file)  # Clean up the temp file

def async_play_audio(audio_path):
    data, sample_rate = sf.read(audio_path)
    channels = data.shape[1] if len(data.shape) > 1 else 1
    data = data.astype('float32')  # Convert the data to float32
    with sd.OutputStream(samplerate=sample_rate, channels=channels) as stream:
        stream.write(data)

    # os.remove(audio_path)

def play_audioSD(audio_path):
    try:
        data, samplerate = sf.read(audio_path)
        sd.play(data, samplerate)
        sd.wait()
    except:
        return "FIN"
    # os.remove(audio_path)

def beep():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        beep_path = os.path.join(script_dir, "resources", "beep.mp3")
        data, samplerate = sf.read(beep_path)
        sd.play(data, samplerate)
    except:
        # If `soundfile` fails, play a system beep instead
        duration = 500
        frequency = 500
        winsound.Beep(frequency, duration)