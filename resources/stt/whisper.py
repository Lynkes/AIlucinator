from stt.stt_base import STTBase
from faster_whisper import WhisperModel
import io

class WhisperSTT(STTBase):
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16"):
        self.model = WhisperModel(model_size=model_size, device=device, compute_type=compute_type)

    def recognize_speech(self, audio):
        response = ""
        audio_data = io.BytesIO(audio.get_wav_data())
        segments, info = self.model.transcribe(audio_data, vad_filter=True, beam_size=5)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        for segment in segments:
            response += segment.text
        return response, info.language, info.language_probability
