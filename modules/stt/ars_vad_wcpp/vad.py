import numpy as np
import onnxruntime as ort

SAMPLE_RATE = 16000
WINDOW_SIZE_SAMPLES = 512
NEG_THRESHOLD = 0.35
THRESHOLD = 0.5
MIN_SPEECH_DURATION_MS = 250
MIN_SILENCE_DURATION_MS = 2000


class VAD:
    _initial_h = np.zeros((2, 1, 64)).astype("float32")
    _initial_c = np.zeros((2, 1, 64)).astype("float32")

    def __init__(self, model_path, window_size_samples: int = int(SAMPLE_RATE / 10)):
        self.ort_sess = ort.InferenceSession(model_path)
        self.window_size_samples = window_size_samples
        self.sr = SAMPLE_RATE
        self._h = self._initial_h
        self._c = self._initial_c
        self.triggered = False
        self.speeches = []
        self.current_speech = {}

    def _reset_state(self):
        self._h = self._initial_h
        self._c = self._initial_c
        self.triggered = False
        self.speeches = []
        self.current_speech = {}

    def process_chunk(self, chunk: np.ndarray) -> float:
        # Garantir que o chunk tenha o tamanho correto
        if len(chunk) < WINDOW_SIZE_SAMPLES:
            chunk = np.pad(chunk, (0, WINDOW_SIZE_SAMPLES - len(chunk)))  # Pad to required size

        # Reshape para 2D
        chunk = chunk.reshape(1, -1)  # Shape: (1, WINDOW_SIZE_SAMPLES)

        # Ajustar h e c para ter a forma correta
        h = self._h  # Deve ter forma [2, 1, 64]
        c = self._c  # Deve ter forma [2, 1, 64]

        # Criar ort_inputs com as formas corretas
        ort_inputs = {
            "input": chunk,  # Agora deve ter forma [1, WINDOW_SIZE_SAMPLES]
            "h": h,  # Forma [2, 1, 64]
            "c": c,  # Forma [2, 1, 64]
            "sr": np.array(self.sr, dtype="int64"),  # Taxa de amostragem
        }

        # Executar o modelo
        out, new_h, new_c = self.ort_sess.run(None, ort_inputs)

        # Atualizar estados ocultos e de célula
        self._h = new_h  # Certifique-se de que new_h tem a forma correta
        self._c = new_c  # Certifique-se de que new_c tem a forma correta

        # Retornar a probabilidade de fala
        return np.squeeze(out)  # Remove entradas de dimensões únicas

    def detect_speech(self, audio: np.ndarray):
        # Divide o áudio em chunks e processa cada chunk
        self._reset_state()
        speech_probs = []
        for i in range(0, len(audio), WINDOW_SIZE_SAMPLES):
            chunk = audio[i: i + WINDOW_SIZE_SAMPLES]
            speech_prob = self.process_chunk(chunk)
            speech_probs.append(speech_prob)
            self._update_speech_status(speech_prob, i)

        return self.speeches

    def _update_speech_status(self, speech_prob, sample_idx):
        neg_threshold = THRESHOLD - 0.15
        if (speech_prob >= THRESHOLD) and not self.triggered:
            # Detecta início da fala
            self.triggered = True
            self.current_speech["start"] = sample_idx
        elif (speech_prob < neg_threshold) and self.triggered:
            # Detecta fim da fala baseado no silêncio
            if sample_idx - self.current_speech.get("start", 0) > MIN_SPEECH_DURATION_MS:
                self.current_speech["end"] = sample_idx
                self.speeches.append(self.current_speech)
            self.current_speech = {}
            self.triggered = False

        # Checa o timeout de silêncio
        if self.triggered and sample_idx - self.current_speech.get("start", 0) > MIN_SILENCE_DURATION_MS:
            self.current_speech["end"] = sample_idx
            self.speeches.append(self.current_speech)
            self.current_speech = {}
            self.triggered = False
