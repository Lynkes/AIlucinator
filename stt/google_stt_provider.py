import speech_recognition as sr

class google_stt_provider:
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def recognize_speech(self, audio):
        if audio:
            return self.recognizer.recognize_google_cloud(audio)
        else:
            raise ValueError("Empty audio input")

        