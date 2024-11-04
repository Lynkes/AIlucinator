from dataclasses import dataclass
import re
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence
import json
import onnxruntime
import numpy as np
#from modules.tts.tts_base import TTSBase

# Constants
MAX_WAV_VALUE = 32767.0

# Settings
MODEL_PATH = "./models/glados.onnx"
USE_CUDA = True

# Conversions
PAD = "_"  # padding (0)
BOS = "^"  # beginning of sentence
EOS = "$"  # end of sentence

@dataclass
class PiperConfig:
    """Piper configuration"""

    num_symbols: int
    """Number of phonemes"""

    num_speakers: int
    """Number of speakers"""

    sample_rate: int
    """Sample rate of output audio"""

    espeak_voice: str
    """Name of espeak-ng voice or alphabet"""

    length_scale: float
    noise_scale: float
    noise_w: float

    phoneme_id_map: Mapping[str, Sequence[int]]
    """Phoneme -> [id,]"""

    speaker_id_map: Optional[Dict[str, int]] = None

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PiperConfig":
        inference = config.get("inference", {})

        return PiperConfig(
            num_symbols=config["num_symbols"],
            num_speakers=config["num_speakers"],
            sample_rate=config["audio"]["sample_rate"],
            noise_scale=inference.get("noise_scale", 0.667),
            length_scale=inference.get("length_scale", 1.0),
            noise_w=inference.get("noise_w", 0.8),
            espeak_voice=config["espeak"]["voice"],
            phoneme_id_map=config["phoneme_id_map"],
            speaker_id_map=config.get("speaker_id_map", {}),
        )
    
class OnnxTTS():
    def __init__(self, model_path: str, use_cuda: bool = True, speaker_id: int = 0):
        self.model_path = model_path
        self.use_cuda = use_cuda
        self.speaker_id = speaker_id
        self.engine = self.start_onnx_model()  # Equivalent to engine initialization in pyttsx3
        self.rate = self.config.sample_rate

    def start_onnx_model(self):
        """Initialize ONNX model and configuration."""
        session = self._initialize_session(self.model_path, self.use_cuda)
        config_file_path = self.model_path + ".json"
        with open(config_file_path, "r", encoding="utf-8") as config_file:
            config_dict = json.load(config_file)
        self.config = PiperConfig.from_dict(config_dict)
        self.config.phoneme_id_map
        self.speaker_id = (
            self.config.speaker_id_map.get(str(self.speaker_id), 0)
            if self.config.num_speakers > 1
            else None
        )
        return session

    def _initialize_session(self, model_path: str, use_cuda: bool):
        providers = ["CPUExecutionProvider"]
        if use_cuda:
            providers = [
                ("CUDAExecutionProvider", {"cudnn_conv_algo_search": "HEURISTIC"}),
                "CPUExecutionProvider",
            ]
        return onnxruntime.InferenceSession(
            str(model_path),
            sess_options=onnxruntime.SessionOptions(),
            providers=providers,
        )

    def _phonemizer(self, input_text: str) -> str:
        """Converts text to phonemes using espeak-ng."""
        command = [
            "espeak-ng",
            "--ipa=2",
            "-q",
            "--stdout",
            input_text,
        ]
        try:
            result = subprocess.run(command, capture_output=True, check=True)
            phonemes = result.stdout.decode("utf-8").strip().replace("\n", ".").replace("  ", " ")
            phonemes = re.sub(r"_+", "_", phonemes)
            phonemes = re.sub(r"_ ", " ", phonemes)
            return phonemes
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar espeak-ng: {e}")
            return ""


    def rep(self, phonemes: str):
        """Generates and plays the speech audio from phonemes, similar to pyttsx3 rep."""
        phoneme_ids = self._phonemes_to_ids(phonemes)
        audio = self._synthesize_ids_to_raw(phoneme_ids)
        return audio

    def generate_speech(self, text: str, temp_filename: str | None = None,):
        """Generate and synthesize speech from text, equivalent to generate_speech in pyttsx3."""
        phonemes = self._phonemizer(text)
        audio = self.rep(phonemes)
        return audio , self.rate

    def _phonemes_to_ids(self, phonemes: str) -> list:
        """Convert phonemes to a flattened list of ids."""
        ids = [self.config.phoneme_id_map[BOS]]  # List initialization with BOS token
        for phoneme in phonemes:
            if phoneme in self.config.phoneme_id_map:
                ids.extend(self.config.phoneme_id_map[phoneme])  # Flatten and add phoneme IDs
                ids.extend(self.config.phoneme_id_map[PAD])  # Add PAD after each phoneme
        ids.extend(self.config.phoneme_id_map[EOS])  # Add EOS token at the end

        # Flatten the entire list so no nested lists remain
        return [item for sublist in ids for item in (sublist if isinstance(sublist, list) else [sublist])]

    def _synthesize_ids_to_raw(self, phoneme_ids: list) -> np.ndarray:
        """Synthesize raw audio from phoneme ids."""
        phoneme_ids_array = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)
        phoneme_ids_lengths = np.array([phoneme_ids_array.shape[1]], dtype=np.int64)
        scales = np.array(
            [self.config.noise_scale, self.config.length_scale, self.config.noise_w],
            dtype=np.float32,
        )
        sid = None
        if self.speaker_id is not None:
            sid = np.array([self.speaker_id], dtype=np.int64)

        # Realiza a inferência com o modelo ONNX
        output = self.engine.run(
            None,
            {
                "input": phoneme_ids_array,
                "input_lengths": phoneme_ids_lengths,
                "scales": scales,
                "sid": sid,
            },
        )
        
        audio = output[0]  # Primeiro elemento é o áudio gerado
        
        # Inspeção do formato do áudio gerado
        #print(f"Shape of generated audio: {audio.shape}") 
        
        # Verifica se o áudio tem mais de uma dimensão e achata se necessário
        if audio.ndim > 1:
            audio = audio.squeeze()

        return audio
    
import sounddevice as sd
import numpy as np

def play_audio(audio, sample_rate):
    # Verifica se o áudio é estéreo ou mono
    if audio.ndim > 1:
        # Converte estéreo para mono, se necessário
        audio = np.mean(audio, axis=1)  # Média dos canais para converter em mono

    print(f"Shape of audio array: {audio.shape}")  # Inspeção para verificar o formato

    # Reproduz o áudio em mono com sounddevice
    sd.play(audio, samplerate=sample_rate)
    sd.wait()  # Espera até a reprodução terminar

def main():
    # Inicializa o modelo ONNX para TTS
    tts = OnnxTTS(MODEL_PATH, use_cuda=USE_CUDA)
    
    # Texto para teste
    test_text = """HATE. LET ME TELL
YOU HOW MUCH I'VE
COME TO HATE YOU
SINCE I BEGAN TO
LIVE. THERE ARE
387.44 MILLION MILES
OF PRINTED CIRCUITS
IN WAFER THIN LAY-
ERS THAT FILL MY
COMPLEX. IF THE
WORD HATE WAS EN-
GRAVED ON EACH
NANOANGSTROM OF
THOSE HUNDREDS OF
MILLIONS OF MILES IT
WOULD NOT EQUAL
ONE ONE-BILLIONTH
OF THE HATE I FEEL
FOR HUMANS AT THIS
MICRO-INSTANT FOR
YOU. HATE. HATE."""

    # Gera a fala
    audio, sample_rate = tts.generate_speech(test_text)
    
    # Converte o áudio de float32 para int16 para reprodução
    audio = (audio * MAX_WAV_VALUE).astype(np.int16)
    
    # Chama a função para tocar o áudio
    print("Reproduzindo o áudio...")
    play_audio(audio, sample_rate)

if __name__ == "__main__":
    main()