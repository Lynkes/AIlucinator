import subprocess
import os

class Piper:
    def __init__(self, piper_exe_path, model_path):
        self.piper_exe_path = piper_exe_path
        self.model_path = model_path

    def generate_speech(self, text, output_file):
        """
        Generate speech from the provided text and save it to the specified output file.
        
        :param text: Text to be synthesized.
        :param output_file: Path to the output WAV file.
        """
        # Create a temporary text file to hold the text
        temp_text_file = 'temp_text.txt'
        with open(temp_text_file, 'w') as f:
            f.write(text)

        # Build the command to run piper.exe
        command = [
            self.piper_exe_path,
            '-m', self.model_path,
            '-f', output_file
        ]
        
        # Run the command using subprocess
        try:
            result = subprocess.run(
                command,
                input=open(temp_text_file, 'r').read(),
                text=True,
                capture_output=True,
                check=True
            )
            print(f"Speech synthesis successful. Output saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.stderr}")

        # Clean up temporary text file
        os.remove(temp_text_file)

# Usage example:
if __name__ == '__main__':
    piper_exe_path = 'piper\piper.exe'  # Path to piper.exe
    model_path = 'conversations\GLaDOS\pipermodel\glados.onnx'    # Path to the model file
    output_file = 'conversations\GLaDOS\pipermodel\\voices\\test1.wav'       # Output WAV file

    piper = Piper(piper_exe_path, model_path)
    text = 'Welcome to the world of speech synthesis!'
    piper.generate_speech(text, output_file)

'''
echo 'Welcome to the world of speech synthesis!' | .\piper.exe -m .\glados.onnx -f test1.wav
'''