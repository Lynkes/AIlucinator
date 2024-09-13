import json

def criar_json_do_texto(arquivo_txt, arquivo_json):
    dados = []

    # Lendo o arquivo de texto
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        for linha in f:
            # Verifica se a linha começa com aspas
            if linha.startswith("\""):
                # Remove aspas no início e no final da linha
                linha_sem_aspas = linha.strip().strip("\"")
                entrada = {
                    "role": "assistant",
                    "content": linha_sem_aspas
                }
                dados.append(entrada)

    # Salvando em formato JSON
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Executando a função para diferentes arquivos de texto
criar_json_do_texto('conversations/GLaDOS/PDFs/GLaDOS_voice_lines_(Portal).txt', 'conversations/GLaDOS/GLaDOS_voice_lines_(Portal).json')
criar_json_do_texto('conversations/GLaDOS/PDFs/GLaDOS_voice_lines_(Portal 2).txt', 'conversations/GLaDOS/GLaDOS_voice_lines_(Portal 2).json')
criar_json_do_texto('conversations/GLaDOS/PDFs/GLaDOS_voice_lines_(Cooperative).txt', 'conversations/GLaDOS/GLaDOS_voice_lines_(Cooperative).json')
criar_json_do_texto('conversations/GLaDOS/PDFs/GLaDOS_voice_lines_(Other).txt', 'conversations/GLaDOS/GLaDOS_voice_lines_(Other).json')
