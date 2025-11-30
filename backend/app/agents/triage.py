from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.tools.data_tools import authenticate_user
import re
from pydantic import BaseModel, Field
from app.models.schemas import TriageIntent, GreetingIntent, CPFExtraction, DateExtraction
from app.core.llm import llm
from app.core.agent_utils import check_exit_intent
from app.core.error_handler import generate_error_response

def handle_greeting(last_message: str):
    """
    1. Saudação
    Lida com a saudação inicial e solicita o CPF.
    """

    structured_llm = llm.with_structured_output(GreetingIntent)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analise se a mensagem do usuário é apenas uma saudação inicial (ex: 'Oi', 'Olá', 'Bom dia', 'Start') ou se já contém alguma solicitação específica.\n"
                   "Se for só saudação, retorne True. Se tiver conteúdo, retorne False."),
        ("user", "{input}")
    ])
    
    is_greeting = False
    try:
        chain = prompt | structured_llm
        result = chain.invoke({"input": last_message})
        is_greeting = result.is_greeting
    except:
        is_greeting = True 

    if is_greeting:
         return {
            "messages": [SystemMessage(content="Olá! Para que eu possa te ajudar, preciso confirmar seus dados. Por favor, me informe seu CPF para começarmos.")],
            "triage_step": "collect_cpf",
            "next_node": "end",
            "active_agent": "triage"
        }

    greeting_prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um atendente bancário virtual. Seu objetivo agora é APENAS pedir o CPF do usuário para iniciar o atendimento.\n"
                   "Instruções:\n"
                   "1. Se o usuário disse 'Olá', 'Bom dia', etc., responda a saudação brevemente.\n"
                   "2. Se o usuário perguntou algo, diga que precisa identificar o cliente primeiro.\n"
                   "3. FINALIZE A MENSAGEM PEDINDO O CPF (ex: 'Por favor, me informe seu CPF para começarmos').\n"
                   "Não invente dados, não simule conversas longas. Seja direto e educado."),
        ("user", "{input}")
    ])

    chain = greeting_prompt | llm
    response_content = chain.invoke({"input": last_message}).content

    return {
        "messages": [SystemMessage(content=response_content)],
        "triage_step": "collect_cpf",
        "next_node": "end",
        "active_agent": "triage"
    }

def handle_cpf_collection(last_message: str):
    """
    2. Coleta CPF
    Extrai e valida o CPF da mensagem do usuário.
    """

    cpf_clean = re.sub(r'\D', '', last_message)

    if len(cpf_clean) == 11 and len(last_message.strip()) < 20:
         cpf_input = cpf_clean

    else:
        structured_llm = llm.with_structured_output(CPFExtraction)
        extract_cpf_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extraia o CPF da mensagem do usuário. Retorne APENAS os números. Se não encontrar um CPF válido (11 dígitos), retorne vazio."),
            ("user", "{input}")
        ])

        chain = extract_cpf_prompt | structured_llm
        result = chain.invoke({"input": last_message})
        cpf_input = result.cpf

        if cpf_input:
             cpf_input = re.sub(r'\D', '', cpf_input)

    if not cpf_input or len(cpf_input) != 11:

        return {
            "messages": [SystemMessage(content="Não consegui identificar um CPF válido. Por favor, digite apenas os 11 números do seu CPF.")],
            "next_node": "end",
            "active_agent": "triage"
        }

    return {
        "messages": [SystemMessage(content="Obrigado.\n\nQual é a sua data de nascimento?")],
        "triage_step": "collect_dob",
        "temp_cpf": cpf_input,
        "next_node": "end",
        "active_agent": "triage"
    }

def handle_dob_collection(last_message: str, temp_cpf: str, auth_attempts: int):
    """
    3. Coleta Data de Nascimento
    4. Validação
    5. Se autenticado -> Redireciona
    6. Se falha -> Retenta ou Encerra
    """

    dob_regex = r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"

    match = re.search(dob_regex, last_message)

    if match:
        dob_input = match.group(0)

    else:
        structured_llm = llm.with_structured_output(DateExtraction)
        extract_dob_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extraia a data de nascimento da mensagem do usuário e formate EXATAMENTE como YYYY-MM-DD.\n"
                       "Aceite formatos como:\n"
                       "- '20/10/2000' -> '2000-10-20'\n"
                       "- '2000-10-20' -> '2000-10-20' (já está correto)\n"
                       "- '20 de outubro de 2000' -> '2000-10-20'\n"
                       "- '10-05-90' -> '1990-05-10'\n"
                       "Se não encontrar uma data válida, retorne 'INVALID'."),
            ("user", "{input}")
        ])

        chain = extract_dob_prompt | structured_llm
        result = chain.invoke({"input": last_message})
        dob_input = result.date or "INVALID"

    if dob_input == "INVALID":
         return {
            "messages": [SystemMessage(content="Não consegui entender a data. Poderia informar novamente? (Ex: dia, mês e ano)")],
            "next_node": "end",
            "active_agent": "triage"
        }

    user = authenticate_user(temp_cpf, dob_input)

    if user:

        return {
            "messages": [SystemMessage(content=f"Olá {user['nome']}, autenticação realizada com sucesso!\n\nComo posso ajudar hoje? Posso verificar seu limite de crédito, solicitar um aumento ou, se precisar, consultar a cotação de moedas estrangeiras.")],
            "user_data": user,
            "auth_attempts": 0,
            "triage_step": "authenticated",
            "next_node": "end",
            "active_agent": "triage"
        }

    else:

        new_attempts = auth_attempts + 1

        if new_attempts >= 3:

            return {
                "messages": [SystemMessage(content="Não foi possível autenticar seus dados após 3 tentativas. Por favor, entre em contato com o suporte.\n\nEncerrando o atendimento.")],
                "next_node": "end",
                "active_agent": "triage", 
                "triage_step": "failed"
            }

        else:

            return {
                "messages": [SystemMessage(content=f"Dados incorretos. Tentativa {new_attempts}/3.\nPor favor, informe seu CPF novamente.")],
                "auth_attempts": new_attempts,
                "triage_step": "collect_cpf", 
                "temp_cpf": None,
                "next_node": "end",
                "active_agent": "triage"
            }

def handle_authenticated(last_message: str):
    """
    Roteia o usuário autenticado para o agente correto.
    """

    structured_llm = llm.with_structured_output(TriageIntent)

    route_prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um classificador de intenções bancárias. "
                   "As categorias são: 'CREDITO' (limite, aumento de limite), 'CAMBIO' (cotação de moedas), 'OUTROS' (saudação, ajuda geral). "),
        ("user", "{input}")
    ])

    chain = route_prompt | structured_llm
    result = chain.invoke({"input": last_message})
    intent = result.category

    if intent == "CREDITO":

        return {
            "next_node": "credit_agent",
            "active_agent": "credit_agent"
        }

    elif intent == "CAMBIO":

        return {
            "next_node": "exchange_agent",
            "active_agent": "exchange_agent"
        }

    else:

        return {
            "messages": [SystemMessage(content="Entendi. Posso te ajudar com serviços de crédito ou com cotações de câmbio. Qual dessas opções você prefere?")],
            "next_node": "end",
            "active_agent": "triage"
        }

def triage_node(state):
    """
    Agente de Triagem:
    Fluxo estrito:
    1. Saudação
    2. Coleta CPF
    3. Coleta Data de Nascimento
    4. Validação
    5. Se autenticado -> Redireciona
    6. Se falha -> Retenta ou Encerra
    """
    messages = state.get("messages", [])

    user_data = state.get("user_data", None)

    auth_attempts = state.get("auth_attempts", 0)

    active_agent = state.get("active_agent", None)

    triage_step = state.get("triage_step", "greeting") 

    temp_cpf = state.get("temp_cpf", None)

    if user_data and active_agent and active_agent != "triage":
        return {"next_node": active_agent}

    last_message = messages[-1].content if messages else ""

    if check_exit_intent(last_message):

        return {
            "messages": [SystemMessage(content="Atendimento finalizado com sucesso. Foi um prazer te ajudar! Se precisar de mais alguma coisa, é só mandar uma nova mensagem que eu volto a te atender. Até logo!")],
            "next_node": "end",
            "active_agent": "triage", 
            "triage_step": "greeting", 
            "temp_cpf": None
        }
    
    try:
        if triage_step == "greeting":
            return handle_greeting(last_message)

        elif triage_step == "collect_cpf":
            return handle_cpf_collection(last_message)

        elif triage_step == "collect_dob":
            return handle_dob_collection(last_message, temp_cpf, auth_attempts)

        elif triage_step == "authenticated":
            return handle_authenticated(last_message)
        
        return {
            "messages": [SystemMessage(content="Desculpe, me perdi. Vamos começar de novo? Digite seu CPF.")],
            "triage_step": "collect_cpf",
            "next_node": "end",
            "active_agent": "triage"
        }
        
    except Exception as e:

        print(f"Error in triage agent: {e}")
        error_msg = generate_error_response(str(e))
        
        return {
            "messages": [SystemMessage(content=error_msg)],
            "next_node": "end",
            "active_agent": "triage"
        }
