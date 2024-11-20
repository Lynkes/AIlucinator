from style_bert_vits2.nlp import bert_models
from style_bert_vits2.constants import Languages
import soundfile as sf
from pydub.playback import play
from pydub import AudioSegment
from pathlib import Path
from style_bert_vits2.tts_model import TTSModel
from modules.tts.tts_base import TTSBase

class Vits2TTS(TTSBase):
    def __init__(self):
        super().__init__()
        # Preload the BERT model and tokenizer for English
        bert_models.load_model(Languages.EN, "microsoft/deberta-v3-large")
        bert_models.load_tokenizer(Languages.EN, "microsoft/deberta-v3-large")

        # Define paths for the model, config, and style files
        assets_root = Path("conversations/GLaDOS/model")
        model_file = assets_root / "Portal_GLaDOS_v1_e782_s50000.safetensors"
        config_file = assets_root / "Models_Style-Bert_VITS2_Portal_GLaDOS_v1_config.json"
        style_file = assets_root / "style_vectors.npy"

        # Preload the TTS model
        print("Preloading the TTS model...")
        self.model = TTSModel(
            model_path=model_file,
            config_path=config_file,
            style_vec_path=style_file,
            device="cuda",  # Change to "cuda" if using GPU
        )
        print("TTS model loaded successfully.")

        # Define the phoneme dictionary
        self.given_phone = [
            "Test", "Success", "Failure", "Subject", "Science", "Congratulations",
            "Error", "Warning", "Protocol", "Terminate", "Data", "Glitch",
            "Pathetic", "Threat", "Malfunction", "Deploy", "Critical", "Testing",
            "Procedure", "Observation", "Result", "Experiment", "Surveillance",
            "Analysis", "Detonation", "Disappointment", "Directive", "Override",
            "Authorization", "Simulation", "Calibration", "Compliance", "Aperture",
            "Contamination", "Specimen", "Termination"
        ]

    def generate_speech(self, text, save=True):
        # Generate speech without loading the model again
        sr, audio = self.model.infer(
            language=Languages.EN,
            split_interval=3.5,
            sdp_ratio=1.5,
            given_phone=self.given_phone,
            text=text
        )
        audio_segment = AudioSegment(audio.tobytes(), frame_rate=sr, sample_width=audio.dtype.itemsize, channels=1)
        play(audio_segment)
        if save:
            self.saveTTS(audio, sr)

    def saveTTS(self, audio, sr):
        # Save TTS output to the predefined directory
        assets_root = Path("conversations/GLaDOS/model")
        output_dir = assets_root / "voices"
        output_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        output_file = output_dir / self.generate_unique_filename(output_dir)
        
        try:
            sf.write(output_file, audio, sr)
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
