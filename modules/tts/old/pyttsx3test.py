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
voice = rep(engine, 
            '''
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
            , clean_queue=True)

voice = rep(engine, "Isso é outro texto que será reproduzido.", clean_queue=True)

voice = rep(engine, "Isso é um terceiro texto.", clean_queue=True)