from faster_whisper import WhisperModel
import speech_recognition as sr
from colorama import *
import ollama
# Mic Set-up
r = sr.Recognizer()
r.dynamic_energy_threshold=False
r.energy_threshold = 150 # 300 is the default value of the SR library
assistant_name = "GLaDOS"
def fasterwhisper(audio):
        response = ""
        with open('speech.wav','wb') as f:
            f.write(audio.get_wav_data())
        speech = open('speech.wav', 'rb')
        segments, info = WhisperModel(model_size_or_path="large-v2", device="cuda", compute_type="float16").transcribe(speech, vad_filter=True, beam_size=5)
        if info.language_probability > 0.5:
            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
            for segment in segments:
                response = response + segment.text
        return response, info.language, info.language_probability

def speech_recognition(audio):
    user_input = fasterwhisper(audio)
    return user_input

def listen_for_voice_OLD(timeout:int|None=5):
    with sr.Microphone(device_index=0) as source:
            print(Style.BRIGHT + Fore.GREEN+"\n>Listening...")
            r.adjust_for_ambient_noise(source, duration=0.2)
            try:
                audio = r.listen(source, timeout)
            except:
                return []
    return audio

def response_completion(self):
        message=''
        stream = ollama.chat(model="llama3", messages=messages, stream=True,)
        print(Style.BRIGHT + Fore.LIGHTYELLOW_EX,"\n",assistant_name,":",Style.BRIGHT + Fore.WHITE)
        for chunk in stream:
            message += chunk['message']['content']
            print(chunk['message']['content'], end='', flush=True)
        print(Style.BRIGHT + Fore.LIGHTCYAN_EX,"\n")
        return message

if __name__ == "__main__":
    messages = [
    {
        'role': 'system',
        'content': '{ "You Are GLaDOS, GLaDOS is an artificial intelligence system with a penchant for testing and a somewhat twisted sense of humor. Shes highly intelligent, ruthlessly efficient, and often manipulative. GLaDOS must respond the last user question, never respond any "\n" in the response" }'
    },
    {
        'role': 'user', 
        'content': '{ "why is the sky blue?" }'
    },
    {
        'role': 'assistant',
        'content': '{"due to rayleigh scattering."}'
    },
    {
        'role': 'user',
        'content': '{"how is that different than mie scattering?"}'
    },
    {
        'role': 'assistant', 
        'content': '{ "take a look at this, https://www.youtube.com/watch?v=7wqo5s2WV4n3Kc" }'
    },
    {
        'role': 'user',
        'content': '{"what is the meaning of life GLaDOS?"}'
    },
    ]
    while True:
         audio=listen_for_voice_OLD()
         if audio:
            comment = speech_recognition(audio)
            if comment != "":
               messages.append({
                      'role': 'user',
                      'content': comment
                  },)
               response_completion()
            audio = None
    