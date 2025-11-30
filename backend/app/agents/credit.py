from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.tools.data_tools import check_credit_limit, request_limit_increase
from pydantic import BaseModel, Field
from app.core.llm import llm
from app.models.schemas import CreditIntent, InterviewOfferIntent
from app.core.agent_utils import check_exit_intent
from app.core.error_handler import generate_error_response

def credit_node(state):
    """
    Agente de Crédito:
    Lida com consultas sobre limite atual e solicitações de aumento.
    """

    messages = state.get("messages", [])
    user_data = state.get("user_data")
    last_message = messages[-1].content

    if check_exit_intent(last_message):
        return {
            "messages": [SystemMessage(content="Atendimento finalizado com sucesso. Foi um prazer te ajudar! Se precisar de mais alguma coisa, é só mandar uma nova mensagem que eu volto a te atender. Até logo!")],
            "next_node": "end",
            "active_agent": "triage" 
        }

    structured_llm = llm.with_structured_output(CreditIntent)

    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente de crédito. Classifique a intenção do usuário.\n"
                   "- 'CHECK_LIMIT': Perguntas sobre 'qual meu limite', 'quanto tenho'.\n"
                   "- 'REQUEST_INCREASE': Pedidos de aumento, ou apenas um número/valor solto (ex: '3000', 'quero 5000').\n"
                   "- 'OTHER': Qualquer outra coisa.\n"),
        ("user", "{input}")
    ])
    
    try:
        chain = classify_prompt | structured_llm
        result = chain.invoke({"input": last_message})
        intent = result.intent
        value = result.value

        if intent == "CHECK_LIMIT":
            limit = check_credit_limit(user_data["cpf"])
            return {
                "messages": [SystemMessage(content=f"Seu limite de crédito atual é de R$ {limit:.2f}.\n\nPosso te ajudar com mais alguma coisa? Se quiser, podemos ver um aumento de limite, consultar taxas de câmbio ou encerrar o atendimento por aqui.")],
                "next_node": "end", 
                "active_agent": "triage" 
            }

        elif intent == "REQUEST_INCREASE":
            if value:
                result = request_limit_increase(user_data["cpf"], float(value))

                if result["status"] == "aprovado":
                    return {
                        "messages": [SystemMessage(content=f"Parabéns! Seu aumento para R$ {value:.2f} foi aprovado!\n\nPosso ajudar em algo mais? Fique à vontade para pedir cotações de moedas ou qualquer outra informação.")],
                        "next_node": "end",
                        "active_agent": "triage"
                    }

                else:
                    current_score = result.get("current_score")
                    max_allowed = result.get("max_allowed")
                    msg = (f"Infelizmente seu pedido foi negado. Seu score atual é {current_score}, "
                           f"o que permite um limite máximo de R$ {max_allowed:.2f}.\n\n"
                           "Gostaria de realizar uma entrevista para atualizar seu perfil e tentar melhorar seu score?")
                           
                    return {
                        "messages": [SystemMessage(content=msg)],
                        "next_node": "end", 
                        "active_agent": "interview_offer" 
                    }
            else:
                return {
                    "messages": [SystemMessage(content="Qual o valor do novo limite que você deseja?")],
                    "next_node": "end", 
                    "active_agent": "credit_agent" 
                }
        else:
             return {
                "messages": [SystemMessage(content="Posso consultar seu limite atual ou dar entrada em um pedido de aumento. O que você prefere fazer agora?")],
                "next_node": "end",
                "active_agent": "credit_agent"
            }

    except Exception as e:

        print(f"Error in credit agent: {e}")
        error_msg = generate_error_response(str(e))

        return {
            "messages": [SystemMessage(content=error_msg)],
            "next_node": "end",
            "active_agent": "triage"
        }

def interview_offer_node(state):
    """
    Lida com a resposta do usuário à oferta de entrevista.
    """

    messages = state.get("messages", [])
    last_message = messages[-1].content.lower()

    structured_llm = llm.with_structured_output(InterviewOfferIntent)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente bancário. O usuário recebeu uma oferta para fazer uma entrevista e aumentar o score.\n"
                   "Analise a resposta dele e classifique como:\n"
                   "- 'ACCEPT': Se ele concordou, disse sim, bora, ok, pode ser.\n"
                   "- 'DECLINE': Se ele recusou, disse não, agora não, deixa pra lá.\n"
                   "- 'UNCLEAR': Se não dá para saber."),
        ("user", "{input}")
    ])

    try:
        chain = prompt | structured_llm
        result = chain.invoke({"input": last_message})
        decision = result.decision
    except:
        decision = "UNCLEAR"

    if decision == "ACCEPT":
        return {
            "messages": [SystemMessage(content="Ótimo! Vamos começar a entrevista. Vou te fazer algumas perguntas.")],
            "next_node": "interview_agent", 
            "active_agent": "interview_agent"
        }

    elif decision == "DECLINE":
        return {
            "messages": [SystemMessage(content="Sem problemas. Se precisar de mais alguma coisa, como consultar seu limite atual ou ver taxas de câmbio, é só pedir.")],
            "next_node": "end",
            "active_agent": "triage"
        }
    
    else:
        return {
            "messages": [SystemMessage(content="Desculpe, não entendi. Você gostaria de fazer a entrevista para tentar aumentar seu limite? (Sim/Não)")],
            "next_node": "end",
            "active_agent": "interview_offer"
        }
