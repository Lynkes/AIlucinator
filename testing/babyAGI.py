import datetime
import os
import json
import cv2  # Biblioteca OpenCV para captura de webcam
from transitions import Machine
from ollama import generate

class BabyAGI:
    """
    Classe que representa um agente AGI (Inteligência Artificial Geral) usando uma Máquina de Estados Finitos (FSM).
    Esse agente interage com o ambiente visualmente, gera hipóteses, executa planos e adapta seu comportamento baseado em feedback.
    """

    def __init__(self):
        """
        Inicializa o agente AGI e define os estados e transições da FSM.
        """
        # Define os estados da FSM
        states = ['understand_task', 'analyze_visual_input', 'generate_hypothesis', 'execute_plan', 'evaluate_result', 'learn_and_adapt']

        # Inicializa a máquina de estados
        self.machine = Machine(model=self, states=states, initial='understand_task')

        # Define as transições entre os estados
        self.machine.add_transition(trigger='task_identified', source='understand_task', dest='analyze_visual_input', before='process_visual_input')
        self.machine.add_transition(trigger='visual_processed', source='analyze_visual_input', dest='generate_hypothesis', before='generate_new_hypothesis')
        self.machine.add_transition(trigger='hypothesis_ready', source='generate_hypothesis', dest='execute_plan', before='execute_chosen_plan')
        self.machine.add_transition(trigger='plan_executed', source='execute_plan', dest='evaluate_result', before='evaluate_execution')
        self.machine.add_transition(trigger='result_evaluated', source='evaluate_result', dest='learn_and_adapt', before='learn_from_feedback')
        self.machine.add_transition(trigger='adapt_complete', source='learn_and_adapt', dest='understand_task')

        # Base de conhecimento e rastreamento de estado interno
        self.knowledge_base = {}
        self.current_task = "o que o usuário está fazendo"
        self.current_hypothesis = None
        self.execution_result = None
        self.reward = 0  # Recompensa para aprendizado por reforço
        self.save_snapshots = False

    # Métodos de estado

    def understand_task(self):
        """
        Estado: understand_task.
        Compreende a tarefa atual e transita para o estado de análise de entrada visual.
        """
        print("Compreendendo a tarefa atual...")
        self.task_identified()  # Transita para 'analyze_visual_input'

    def process_visual_input(self):
        """
        Estado: analyze_visual_input.
        Captura entrada visual da webcam e analisa a cena usando um modelo multimodal.
        """
        print("Capturando entrada visual da webcam...")

        cap = cv2.VideoCapture(0)  # Abre a webcam
        
        if not cap.isOpened():
            print("Erro: Não foi possível abrir a webcam.")
            return
        
        ret, frame = cap.read()  # Captura uma única imagem
        if not ret:
            print("Erro: Falha ao capturar imagem da webcam.")
            cap.release()
            return
        
        # Salva o quadro capturado em um arquivo
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'camsaps/{timestamp}.jpg'
        cv2.imwrite(filename, frame)
        
        # Converte a imagem para bytes
        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()
        
        cap.release()  # Libera a webcam
        cv2.destroyAllWindows()

        # Usa o modelo LLAVA para analisar a imagem
        try:
            for response in generate('llava-llama3', 'explique esta cena:', images=[image_bytes], stream=True):
                print(response['response'], end='', flush=True)

            # Armazena a descrição visual na base de conhecimento
            self.knowledge_base['visual_description'] = response['response']
            self.visual_processed()  # Transita para 'generate_hypothesis'
        except Exception as e:
            print(f"Erro durante a análise visual: {e}")

        if self.save_snapshots is False:
            os.remove(filename)  # Exclui a imagem capturada, caso não seja salva

    def generate_new_hypothesis(self):
        """
        Estado: generate_hypothesis.
        Gera uma nova hipótese com base na tarefa e na entrada visual.
        """
        print("Gerando hipótese com base na entrada visual...")

        prompt = f"""
        Você é um modelo de IA resolvendo a tarefa: {self.current_task}.
        Considere a seguinte informação visual: {self.knowledge_base.get('visual_description', 'Sem entrada visual disponível')}.
        Gere uma hipótese no seguinte formato:
        {{
          "hypothesis": "sua hipótese aqui",
          "confidence": "nível de confiança (0 a 100)",
          "details": "informações adicionais"
        }}
        """
        response = self.query_ollama(prompt)  # Consulta o modelo Ollama
        self.current_hypothesis = self.parse_response(response, "generate_hypothesis")
        if self.current_hypothesis:
            print(f"Hipótese gerada: {self.current_hypothesis}")
            self.hypothesis_ready()  # Transita para 'execute_plan'
        else:
            print("Falha ao gerar uma hipótese válida.")

    def execute_chosen_plan(self):
        """
        Estado: execute_plan.
        Executa o plano gerado com base na hipótese.
        """
        print("Executando o plano escolhido...")
        if not self.current_hypothesis:
            print("Nenhuma hipótese disponível para executar.")
            return

        prompt = f"Execute o seguinte plano: {self.current_hypothesis.get('hypothesis')}"
        response = self.query_ollama(prompt)
        self.execution_result = self.parse_response(response, "execute_plan")
        if self.execution_result:
            print(f"Plano executado com sucesso: {self.execution_result}")
            self.plan_executed()  # Transita para 'evaluate_result'
        else:
            print("Falha ao executar o plano.")

    def evaluate_execution(self):
        """
        Estado: evaluate_result.
        Avalia o resultado da execução do plano.
        """
        print("Avaliando o resultado da execução...")

        prompt = f"Avalie o seguinte resultado: {self.execution_result.get('execution_result')}"
        response = self.query_ollama(prompt)
        parsed_response = self.parse_response(response, "evaluate_result")
        if parsed_response:
            self.reward = parsed_response.get('reward', 0)
            print(f"Resultado avaliado com recompensa: {self.reward}")
            self.result_evaluated()  # Transita para 'learn_and_adapt'
        else:
            print("Falha ao avaliar o resultado.")

    def learn_from_feedback(self):
        """
        Estado: learn_and_adapt.
        Aprende com o feedback da avaliação e adapta as estratégias.
        """
        print("Aprendendo com o feedback e adaptando...")

        if self.reward > 75:
            print("Bom desempenho. Alta recompensa.")
            self.knowledge_base['feedback'] = 'positivo'
        elif self.reward > 50:
            print("Desempenho moderado.")
            self.knowledge_base['feedback'] = 'neutro'
        else:
            print("Desempenho ruim. Ajustes necessários.")
            self.knowledge_base['feedback'] = 'negativo'
            self.current_task = "Tarefa revisada com base no feedback"
            print(f"Tarefa revisada: {self.current_task}")

        self.save_feedback_to_log()
        self.adapt_strategies_based_on_feedback()
        self.adapt_complete()  # Completa a adaptação e volta ao estado inicial

    def save_feedback_to_log(self):
        """
        Salva o feedback em um log ou banco de dados para referência futura.
        """
        try:
            with open('feedback_log.json', 'a') as f:
                json.dump({
                    'task': self.current_task,
                    'reward': self.reward,
                    'feedback': self.knowledge_base.get('feedback'),
                    'timestamp': datetime.datetime.now().isoformat()
                }, f)
                f.write('\n')
            print("Feedback salvo no log.")
        except IOError as e:
            print(f"Erro ao salvar o feedback no log: {e}")

    def adapt_strategies_based_on_feedback(self):
        """
        Ajusta estratégias ou parâmetros com base no feedback.
        """
        if self.knowledge_base.get('feedback') == 'negativo':
            print("Adaptação de estratégias com base no feedback negativo.")
            self.adjust_parameters()

    def adjust_parameters(self):
        """
        Ajusta os parâmetros do modelo com base no feedback.
        """
        print("Ajustando parâmetros do modelo...")

    def query_ollama(self, prompt):
        """
        Consulta a API Ollama com o prompt fornecido.
        """
        try:
            response = generate('llava', prompt, stream=False)
            return response['response']
        except Exception as e:
            print(f"Erro ao consultar a API Ollama: {e}")
            return None

    def parse_response(self, response, state):
        """
        Analisa a resposta do LLM (Large Language Model) e verifica se está no formato esperado.
        """
        try:
            parsed_output = json.loads(response)
            if state == "generate_hypothesis":
                assert "hypothesis" in parsed_output and "confidence" in parsed_output
                return parsed_output
            elif state == "execute_plan":
                assert "execution_result" in parsed_output
                return parsed_output
            elif state == "evaluate_result":
                assert "reward" in parsed_output
                return parsed_output
            elif state == "analyze_visual_input":
                assert "description" in parsed_output and "context" in parsed_output
                return parsed_output
        except (json.JSONDecodeError, AssertionError) as e:
            print(f"Erro ao analisar a resposta em {state}: {e}")
            return None

if __name__ == "__main__":
    # Inicializa o agente AGI e inicia o processo de FSM compreendendo a tarefa
    agi = BabyAGI()
    agi.understand_task()  # Inicia o processo FSM começando pelo entendimento da tarefa
