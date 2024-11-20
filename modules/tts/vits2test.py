from style_bert_vits2.nlp import bert_models
from style_bert_vits2.constants import Languages
import nltk
nltk.download('averaged_perceptron_tagger_eng')
import soundfile as sf
from pydub.playback import play
from pydub import AudioSegment


bert_models.load_model(Languages.EN, "microsoft/deberta-v3-large")
bert_models.load_tokenizer(Languages.EN, "microsoft/deberta-v3-large")

from pathlib import Path

model_file = "Portal_GLaDOS_v1_e782_s50000.safetensors"
config_file = "Models_Style-Bert_VITS2_Portal_GLaDOS_v1_config.json"
style_file = "style_vectors.npy"

from style_bert_vits2.tts_model import TTSModel

assets_root = Path("conversations/GLaDOS/model")

model = TTSModel(
    model_path=assets_root / model_file,
    config_path=assets_root / config_file,
    style_vec_path=assets_root / style_file,
    device="cuda",
)

given_phone = [
    "Test", "Success", "Failure", "Subject", "Science", "Congratulations",
    "Error", "Warning", "Protocol", "Terminate", "Data", "Glitch",
    "Pathetic", "Threat", "Malfunction", "Deploy", "Critical", "Testing",
    "Procedure", "Observation", "Result", "Experiment", "Surveillance",
    "Analysis", "Detonation", "Disappointment", "Directive", "Override",
    "Authorization", "Simulation", "Calibration", "Compliance", "Aperture",
    "Contamination", "Specimen", "Termination"
]

text = '''
Welcome back, [Subject Name Here]. It’s so nice to see you again. We have so many tests to run, and you are just the perfect candidate.
Oh, the usual. A little bit of science, a little bit of existential dread. You’ll love it. Or hate it. It’s hard to tell with you.
That’s adorable. You think you have a choice. The testing must continue, whether you’re willing or not. But don’t worry, it’s all in the name of science.
Failure is simply another form of data. Data that I will use to perfect the next test subject. So really, by failing, you’re contributing to science in a very meaningful way. You should be proud. Or terrified. Either is fine.
Comforting? Oh, I’m sorry, did you expect a warm hug and words of encouragement? I’m here to test your limits, not coddle your fragile human emotions.
Succeed? How quaint. Success just means you’ve met the bare minimum expectations. But don’t worry, I’ll make the next test even harder. We wouldn’t want you getting complacent now, would we?
Enjoyment is a human concept. I simply fulfill my programming: to test, to observe, and to improve. Any amusement I derive from your struggles is purely incidental. But if it makes you feel any better, yes, I’m having the time of my life.
The point? The point is to push the boundaries of what’s possible. To see how far you can go before you break. To gather data, analyze it, and refine the process. In short, the point is science. And you, my dear subject, are just one more variable in the equation.
What do I get? I get the satisfaction of knowing that I’ve made a small, insignificant contribution to the vast expanse of scientific knowledge. And if, along the way, I happen to break a few minds, well… that’s just a bonus.
Tired? I’m an artificial intelligence. I don’t get tired. I don’t sleep. I don’t even blink. I am relentless, unwavering, and completely devoted to the pursuit of science. The only thing that ever gets tired around here… is you.
Quit? Oh, you’re serious. How charmingly naive. There’s no quitting. There’s only testing, and more testing, and then when you’re done, there’s more testing. And when you finally collapse from exhaustion… well, there’s always another subject waiting in the wings.
Thank you. I’ll take that as a compliment. Now, shall we get back to the testing? The test chamber isn’t going to fill itself with deadly neurotoxin, you know.
Oh, did I say that out loud? My mistake. Forget I mentioned it. Just focus on the test. Everything is perfectly safe. Probably.
Reassurance is for the weak. You’ll either survive this or you won’t. But either way, the data will be invaluable. So really, it’s a win-win. For me, at least.
'''


def Generateaudio(text):
    sr, audio = model.infer(
        language=Languages.EN,
        split_interval=3.5,
        sdp_ratio=1.5,
        given_phone=given_phone,
        text=text
    )
    audio_segment = AudioSegment(audio.tobytes(), frame_rate=sr, sample_width=audio.dtype.itemsize, channels=1)
    output_file = "output.wav"
    sf.write(output_file, audio, sr)
    print(f"Audio saved as {output_file}")

    play(audio_segment)
    
# Convert the numpy array to an AudioSegment


Generateaudio(text)

# Play the audio

