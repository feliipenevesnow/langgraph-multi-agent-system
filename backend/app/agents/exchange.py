from langchain_core.messages import SystemMessage
from app.tools.search_tools import get_exchange_rate
from app.models.schemas import CurrencyExtraction
from app.core.llm import llm
from langchain_core.prompts import ChatPromptTemplate
from app.core.agent_utils import check_exit_intent
from app.core.error_handler import generate_error_response

def exchange_node(state):
    """
    Agente de Câmbio:
    Retorna cotações de moedas.
    """

    try:
        messages = state.get("messages", [])
        last_message = messages[-1].content.upper()

        if check_exit_intent(last_message):
            return {
                "messages": [SystemMessage(content="Atendimento finalizado com sucesso. Foi um prazer te ajudar! Se precisar de mais alguma coisa, é só mandar uma nova mensagem que eu volto a te atender. Até logo!")],
                "next_node": "end",
                "active_agent": "triage"
            }

        structured_llm = llm.with_structured_output(CurrencyExtraction)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um especialista em câmbio. Extraia o código da moeda que o usuário quer consultar (USD, EUR, GBP). Se não for claro, assuma USD."),
            ("user", "{input}")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"input": last_message})
        currency = result.currency_code

        rate = get_exchange_rate(currency)

        return {
            "messages": [SystemMessage(content=f"A cotação atual do {currency} é R$ {rate:.2f}.\n\nDeseja consultar outra moeda? Se preferir, também posso te ajudar com serviços de crédito ou finalizar nosso atendimento.")],
            "next_node": "end",
            "active_agent": "triage"
        }

    except Exception as e:

        print(f"Error in exchange agent: {e}")
        error_msg = generate_error_response(str(e))
        
        return {
            "messages": [SystemMessage(content=error_msg)],
            "next_node": "end",
            "active_agent": "triage"
        }
