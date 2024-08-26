import pyttsx3

def Startpyttsx3():
    engine = pyttsx3.init()
    engine.setProperty('rate', 180) #200 is the default speed, this makes it slower
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id) # 0 for male, 1 for female
    return engine


def rep(engine, text, clean_queue=True):
    if clean_queue:
        engine.stop()  # Limpa a fila de reprodução
    engine.say(text)
    engine.runAndWait()

engine = Startpyttsx3()
voice = rep(engine, "Olá! Este é um exemplo de texto para reprodução.", clean_queue=True)

voice = rep(engine, "Isso é outro texto que será reproduzido.", clean_queue=True)

voice = rep(engine, "Isso é um terceiro texto.", clean_queue=True)