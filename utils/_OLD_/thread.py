#https://realpython.com/intro-to-python-threading/#starting-a-thread
import threading
import time

def funcao_da_thread(nome):
    print("Sou o a thread ",nome, " e vou dormir")
    time.sleep(500)
    print("Sou a thread ", nome, " e terminei")


if __name__ == "__main__": #função principal
    c = 0
    while c<600:
        t = threading.Thread(target=funcao_da_thread, args=("minha thread "+str(c), ))
        t.start()
        c+=1