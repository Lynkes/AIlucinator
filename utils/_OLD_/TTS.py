import os
import torch

device = torch.device('cpu')
torch.set_num_threads(8)
local_file = 'model.pt'

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt',
                                   local_file)  

model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

example_text = 'In this version, Ive updated the colors and styling to create a Dark IDE-style appearance. The background color of the main window and buttons has been changed, and the text colors have been adjusted to fit the dark theme. Ive also added a color tag for the mode output to distinguish it visually from the input.'
sample_rate = 48000
speaker='random'

audio_paths = model.save_wav(text=example_text,
                             speaker=speaker,
                             sample_rate=sample_rate)