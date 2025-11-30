from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.tools.data_tools import update_user_score
from pydantic import BaseModel, Field
from app.core.llm import llm
from app.core.agent_utils import check_exit_intent
from app.core.error_handler import generate_error_response
from app.models.schemas import ValidationResult, InterviewNormalization

QUESTIONS = [
    "Qual é a sua renda mensal aproximada?",
    "Qual seu tipo de emprego? (formal, autônomo, desempregado)",
    "Qual o valor das suas despesas fixas mensais?",
    "Quantos dependentes você tem?",
    "Você possui dívidas ativas? (sim/não)"
]

def validate_answer(question: str, answer: str) -> dict:
    """
    Usa LLM para validar se a resposta é apropriada para a pergunta.
    Retorna dict com chaves correspondentes a ValidationResult.
    """

    structured_llm = llm.with_structured_output(ValidationResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um validador de dados bancários. Analise se a RESPOSTA do usuário faz sentido para a PERGUNTA feita.\n"
                   "Se fizer sentido, extraia o valor limpo/formatado em 'cleaned_value'.\n"
                   "Se NÃO fizer sentido (ex: risadas, texto aleatório, fugiu do assunto), marque 'valid' como False e gere um 'feedback'."),
        ("user", "PERGUNTA: {question}\nRESPOSTA: {answer}")
    ])

    try:

        chain = prompt | structured_llm
        result = chain.invoke({"question": question, "answer": answer})

        return result.dict()
        
    except Exception as e:

        print(f"Validation error: {e}")

        return {"valid": True, "cleaned_value": answer, "feedback": ""}

def normalize_data(answers: list) -> InterviewNormalization:
    """
    Usa LLM para normalizar as respostas soltas em um objeto estruturado para cálculo.
    """
    structured_llm = llm.with_structured_output(InterviewNormalization)
    
    context = ""
    for q, a in zip(QUESTIONS, answers):
        context += f"P: {q}\nR: {a}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um analista de crédito. Seu objetivo é extrair e normalizar os dados financeiros de uma entrevista.\n"
                   "Converta valores monetários para float (ex: '5k' -> 5000.0).\n"
                   "Classifique o emprego em: 'formal' (CLT, funcionário público), 'autônomo' (PJ, freelancer, empresário) ou 'desempregado'.\n"
                   "Conte o número total de dependentes.\n"
                   "Identifique se há dívidas (Sim/Não)."),
        ("user", "Dados da entrevista:\n{input}")
    ])

    chain = prompt | structured_llm
    return chain.invoke({"input": context})

def calculate_score(data: InterviewNormalization):
    """
    Calcula o score com base nos dados JÁ NORMALIZADOS.
    """
    try:
        renda = data.income
        emprego = data.job_type
        despesas = data.expenses
        num_dep = data.dependents
        tem_dividas = data.has_debts
        
        peso_renda = 30
        
        peso_emprego = {
            "formal": 300,
            "autônomo": 200,
            "desempregado": 0
        }

        peso_dependentes = {
            0: 100,
            1: 80,
            2: 60,
            "3+": 30
        }

        peso_dividas = {
            True: -100,
            False: 100
        }

        p_emp = peso_emprego.get(emprego, 0)

        if num_dep >= 3:
            p_dep = peso_dependentes["3+"]
        elif num_dep in peso_dependentes:
            p_dep = peso_dependentes[num_dep]
        else:
            p_dep = 30 

        p_div = peso_dividas[tem_dividas]

        
        score = (renda / (despesas + 1)) * peso_renda + p_emp + p_dep + p_div

        return min(1000, max(0, int(score))) 

    except Exception as e:
        print(f"Error calculating score: {e}")
        return 500 

def interview_node(state):
    """
    Agente de Entrevista:
    Faz perguntas sequencialmente e atualiza o score no final.
    Inclui loop de validação inteligente.
    """

    messages = state.get("messages", [])
    interview_step = state.get("interview_step", 0)
    interview_answers = state.get("interview_answers", [])
    user_data = state.get("user_data")

    try:
        if messages and interview_step > 0:
            last_message = messages[-1].content

            if check_exit_intent(last_message):

                 return {
                    "messages": [SystemMessage(content="Atendimento finalizado com sucesso. Foi um prazer te ajudar! Se precisar de mais alguma coisa, é só mandar uma nova mensagem que eu volto a te atender. Até logo!")],
                    "interview_step": 0,
                    "interview_answers": [],
                    "next_node": "end",
                    "active_agent": "triage"
                }

        if interview_step == 0:

            return {
                "messages": [SystemMessage(content=QUESTIONS[0])],
                "interview_step": 1,
                "interview_answers": [],
                "next_node": "end", 
                "active_agent": "interview_agent"
            }

        last_answer = messages[-1].content
        question_asked = QUESTIONS[interview_step - 1]
        validation = validate_answer(question_asked, last_answer)

        if not validation.get("valid", False):

            feedback = validation.get("feedback", "Resposta inválida.")

            return {
                "messages": [SystemMessage(content=f"{feedback}\n\n{question_asked}")],
                "interview_step": interview_step, 
                "interview_answers": interview_answers, 
                "next_node": "end",
                "active_agent": "interview_agent"
            }

        cleaned_value = validation.get("cleaned_value", last_answer)
        new_answers = interview_answers + [cleaned_value]

        if interview_step < len(QUESTIONS):

            return {
                "messages": [SystemMessage(content=QUESTIONS[interview_step])],
                "interview_step": interview_step + 1,
                "interview_answers": new_answers,
                "next_node": "end",
                "active_agent": "interview_agent"
            }

        normalized_data = normalize_data(new_answers)
        new_score = calculate_score(normalized_data)
        update_user_score(user_data["cpf"], new_score)

        return {
            "messages": [SystemMessage(content=f"Obrigado! Suas informações foram atualizadas e seu novo score é {new_score}.\n\n"
                                               "Pronto! Atualizei suas informações e seu score. Agora, por favor, me diga novamente qual o valor de limite que você gostaria de solicitar para que eu possa fazer uma nova análise.")],
            "interview_step": 0, 
            "interview_answers": [],
            "next_node": "end", 
            "active_agent": "credit_agent" 
        }

    except Exception as e:

        print(f"Error in interview agent: {e}")
        error_msg = generate_error_response(str(e))
        
        return {
            "messages": [SystemMessage(content=error_msg)],
            "next_node": "end",
            "active_agent": "triage"
        }
