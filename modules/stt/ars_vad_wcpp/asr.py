import subprocess
import tempfile
import numpy as np
import wave
from loguru import logger
from typing import Optional, List
from contextlib import AbstractContextManager
import os

# Configurações
SILENCE_DURATION_MS = 500
SAMPLE_RATE = 16000
WORD_LEVEL_TIMINGS = False
BEAM_SEARCH = True

class ASR(AbstractContextManager):
    """
    Classe ASR que utiliza whisper.cpp (whisper-cli.exe) externamente.
    """

    def __init__(self, model: str, whisper_cli_path: str):
        """
        Inicializa o ASR com o caminho do modelo e do executável whisper-cli.
        """
        if not os.path.exists(whisper_cli_path):
            raise FileNotFoundError(f"whisper-cli.exe não encontrado em: {whisper_cli_path}")
        if not os.path.exists(model):
            raise FileNotFoundError(f"Modelo não encontrado em: {model}")

        self.model = model
        self.whisper_cli_path = whisper_cli_path
        self.last_detected_language: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _add_silence(self, audio: np.ndarray) -> np.ndarray:
        silence_samples = int((SILENCE_DURATION_MS / 1000) * SAMPLE_RATE)
        silence = np.zeros(silence_samples, dtype=audio.dtype)
        return np.concatenate((silence, audio, silence))

    def _save_wav(self, audio: np.ndarray) -> str:
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(tmp_wav.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        return tmp_wav.name

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> str:
        """
        Transcreve o áudio usando whisper-cli.exe
        """
        if not isinstance(audio, np.ndarray):
            raise TypeError("O áudio deve ser um np.ndarray (float32).")

        logger.info(f"Comprimento do áudio original: {len(audio)} amostras")
        audio = self._add_silence(audio)
        logger.info(f"Comprimento do áudio após adicionar silêncio: {len(audio)} amostras")

        wav_path = self._save_wav(audio)

        cmd = [
            self.whisper_cli_path,
            "--model", self.model,
            "--file", wav_path,
            "--output-txt",  # salva a saída em texto
        ]

        if language:
            cmd += ["--language", language]
        else:
            cmd += ["--detect-language"]

        if BEAM_SEARCH:
            cmd += ["--beam-size", "5"]

        logger.debug(f"Executando comando: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(wav_path)  # remove o arquivo temporário

        if result.returncode != 0:
            logger.error(f"Erro ao executar whisper-cli: {result.stderr}")
            raise RuntimeError(f"Erro do whisper-cli (código {result.returncode})")

        # A saída principal pode vir em stdout
        output_text = result.stdout.strip()

        # Se o whisper-cli gerou um arquivo de saída, tente ler também
        txt_file = wav_path.replace(".wav", ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                output_text = f.read().strip()
            os.remove(txt_file)

        logger.info(f"Texto transcrito: {output_text}")

        return output_text


# Exemplo de uso
if __name__ == "__main__":
    import sys

    whisper_cli = r"submodules\whisper.cpp\whisper-cli.exe"
    model = r"C:\_git_\AIlucinator\models\ggml-large-v3-q5_0.bin"

    # Exemplo: áudio de 5s de silêncio
    audio_data = np.zeros(int(SAMPLE_RATE * 5), dtype=np.float32)

    try:
        with ASR(model, whisper_cli) as asr:
            text = asr.transcribe(audio_data)
            print(f"\n>>> Texto transcrito:\n{text}")
    except Exception as e:
        logger.exception(e)
