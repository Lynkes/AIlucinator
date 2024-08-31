import speech_recognition as sr

class GoogleSTT:
    
    def recognize_speech(self, audio):
        if audio:
            return self.recognizer.recognize_google_cloud(audio)
        else:
            raise ValueError("Empty audio input")

        