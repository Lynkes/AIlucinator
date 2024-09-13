import json
import ollama
import asyncio

def get_flight_times(departure: str, arrival: str) -> str:
    """
    Simula uma chamada de API para obter os horários de voos entre duas cidades.

    Parâmetros:
    -----------
    departure (str): O código do aeroporto de partida (ex: 'NYC').
    arrival (str): O código do aeroporto de chegada (ex: 'LAX').

    Retorna:
    --------
    str: Um JSON contendo os detalhes do voo (horário de partida, chegada e duração).
    Caso o voo não seja encontrado, retorna um JSON com uma mensagem de erro.
    """
    flights = {
        'NYC-LAX': {'departure': '08:00 AM', 'arrival': '11:30 AM', 'duration': '5h 30m'},
        'LAX-NYC': {'departure': '02:00 PM', 'arrival': '10:30 PM', 'duration': '5h 30m'},
        'LHR-JFK': {'departure': '10:00 AM', 'arrival': '01:00 PM', 'duration': '8h 00m'},
        'JFK-LHR': {'departure': '09:00 PM', 'arrival': '09:00 AM', 'duration': '7h 00m'},
        'CDG-DXB': {'departure': '11:00 AM', 'arrival': '08:00 PM', 'duration': '6h 00m'},
        'DXB-CDG': {'departure': '03:00 AM', 'arrival': '07:30 AM', 'duration': '7h 30m'},
    }

    key = f'{departure}-{arrival}'.upper()
    return json.dumps(flights.get(key, {'error': 'Flight not found'}))

async def run(model: str):
    """
    Função principal que executa uma conversa com o modelo LLM e simula uma interação que envolve
    a obtenção de horários de voo.

    Parâmetros:
    -----------
    model (str): O nome do modelo de LLM a ser utilizado.

    O fluxo da função é o seguinte:
    1. Envia uma consulta inicial ao modelo.
    2. Aguarda a resposta do modelo, que pode solicitar o uso de uma função para obter dados de voos.
    3. Se a função for solicitada, a função `get_flight_times` é executada.
    4. O resultado da função é adicionado ao histórico da conversa.
    5. Uma nova consulta é enviada ao modelo para obter a resposta final.
    """
    client = ollama.AsyncClient()

    # Inicializa a conversa com uma consulta do usuário
    messages = [{'role': 'user', 'content': 'What is the flight time from New York (NYC) to Los Angeles (LAX)?'}]

    # Primeira chamada de API: Envia a consulta e descrição da função ao modelo
    response = await client.chat(
        model=model,
        messages=messages,
        tools=[
            {
                'type': 'function',
                'function': {
                    'name': 'get_flight_times',
                    'description': 'Get the flight times between two cities',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'departure': {
                                'type': 'string',
                                'description': 'The departure city (airport code)',
                            },
                            'arrival': {
                                'type': 'string',
                                'description': 'The arrival city (airport code)',
                            },
                        },
                        'required': ['departure', 'arrival'],
                    },
                },
            },
        ],
    )

    # Adiciona a resposta do modelo ao histórico da conversa
    messages.append(response['message'])

    # Verifica se o modelo decidiu usar a função fornecida
    if not response['message'].get('tool_calls'):
        print("The model didn't use the function. Its response was:")
        print(response['message']['content'])
        return

    # Processa as chamadas de função feitas pelo modelo
    if response['message'].get('tool_calls'):
        available_functions = {
            'get_flight_times': get_flight_times,
        }
        for tool in response['message']['tool_calls']:
            function_to_call = available_functions[tool['function']['name']]
            function_response = function_to_call(tool['function']['arguments']['departure'], tool['function']['arguments']['arrival'])
            # Adiciona a resposta da função à conversa
            messages.append(
                {
                    'role': 'tool',
                    'content': function_response,
                }
            )

    # Segunda chamada de API: Obter a resposta final do modelo
    final_response = await client.chat(model=model, messages=messages)
    print(final_response['message']['content'])


# Executa a função assíncrona
asyncio.run(run('mistral'))
