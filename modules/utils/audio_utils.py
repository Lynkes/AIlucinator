import subprocess, os, winsound
import sounddevice as sd
import soundfile as sf
from typing import Any, List, Optional, Sequence, Tuple
import time
import globals
PAUSE_TIME = 0.05 

def play_audio(audio_file):
    ffplay = 'python-embedded/ffplay.exe'
    # Play audio using ffplay with suppressed output
    try:
        print(f"Playing audio: {audio_file}")
        
        # Build the ffplay command
        command = [ffplay, '-nodisp', '-autoexit', audio_file]
        
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


def clip_interrupted_sentence(
        generated_text: str, percentage_played: float
    ) -> str:
        """
        Clips the generated text if the TTS was interrupted.

        Args:

            generated_text (str): The generated text from the LLM model.
            percentage_played (float): The percentage of the audio played before the TTS was interrupted.

            Returns:

            str: The clipped text.

        """
        tokens = generated_text.split()
        words_to_print = round((percentage_played / 100) * len(tokens))
        text = " ".join(tokens[:words_to_print])

        # If the TTS was cut off, make that clear
        if words_to_print < len(tokens):
            text = text + "<INTERRUPTED>"
        return text

def percentage_played_audio(total_samples: int, rate) -> Tuple[bool, int]:
        globals.interrupted = False
        start_time = time.time()
        played_samples = 0.0

        while sd.get_stream().active:
            time.sleep(PAUSE_TIME)  # Should the TTS stream should still be active?
            if globals.processing is False:
                sd.stop()  # Stop the audio stream
                #self.tts_generation_queue = queue.Queue()  # Clear the TTS queue
                globals.interrupted = True
                break

        elapsed_time = (
            time.time() - start_time + 0.12
        )  # slight delay to ensure all audio timing is correct
        played_samples = elapsed_time * rate

        # Calculate percentage of audio played
        percentage_played = min(int((played_samples / total_samples * 100)), 100)
        return percentage_played