import io
from faster_whisper import WhisperModel

def transcribe_audio(audio, model: WhisperModel) -> tuple[str, str, float]:
    """
    Transcribes speech from audio using the Faster Whisper model.
    
    :param audio: The audio input to transcribe.
    :param model: The Whisper model used for transcription.
    :return: A tuple containing the transcribed text, detected language, and language probability.
    """
    response = ""
    audio_data = io.BytesIO(audio.get_wav_data())
    segments, info = model.transcribe(audio_data, vad_filter=True, beam_size=5)
    for segment in segments:
        response += segment.text
    return response, info.language, info.language_probability
