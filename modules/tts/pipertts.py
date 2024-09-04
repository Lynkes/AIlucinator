import subprocess
import os
import soundfile as sf
import wave
from pathlib import Path
from modules.tts.tts_base import TTSBase

class PiperTTS(TTSBase):
    def __init__(self, piper_exe_path, model_path):
        super().__init__()
        self.piper_exe_path = piper_exe_path
        self.model_path = model_path

    def generate_speech(self, text, save=True):
        output_file = 'temp_output.wav'
        self._generate_speech_from_text(text, output_file)
        if save:
            self.save_tts(output_file)
        self.play_audio(output_file)
    
    def _generate_speech_from_text(self, text, output_file):
        # Create a temporary text file to hold the text
        temp_text_file = 'temp_text.txt'
        with open(temp_text_file, 'w') as f:
            f.write(text)

        # Build the command to run piper.exe
        command = [
            self.piper_exe_path,
            '-m', self.model_path,
            '-f', output_file
        ]
        
        # Run the command using subprocess
        try:
            result = subprocess.run(
                command,
                input=open(temp_text_file, 'r').read(),
                text=True,
                capture_output=True,
                check=True
            )
            print(f"Speech synthesis successful. Output saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.stderr}")

        # Clean up temporary text file
        os.remove(temp_text_file)

    def play_audio(self, audio_file):
        # Play audio using wave and ffplay
        try:
            with wave.open(audio_file, 'rb') as wf:
                print(f"Playing audio: {audio_file}")
                os.system(f'ffplay -nodisp -autoexit {audio_file}')
        except Exception as e:
            print(f"Failed to play audio: {e}")
        finally:
            os.remove(audio_file)  # Clean up the temp file

    def save_tts(self, audio_file):
        # Save TTS output to a predefined directory
        assets_root = Path("conversations/GLaDOS/model")
        output_dir = assets_root / "voices"
        output_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        output_file = output_dir / self.generate_unique_filename(output_dir)
        
        try:
            sf.copy(audio_file, output_file)  # Copy the audio file to the output directory
            print(f"Audio saved as {output_file}")
        except Exception as e:
            print(f"Failed to save audio: {e}")

    @staticmethod
    def generate_unique_filename(output_dir):
        # Generate a unique filename based on existing files
        counter = 1
        while (output_dir / f"output_{counter}.wav").exists():
            counter += 1
        return f"output_{counter}.wav"
