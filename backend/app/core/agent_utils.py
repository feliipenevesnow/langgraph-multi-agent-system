from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import llm
from app.models.schemas import ExitIntent

def check_exit_intent(message: str) -> bool:
    """
    Usa LLM para determinar se o usuário deseja sair da conversa.
    """

    try:
        structured_llm = llm.with_structured_output(ExitIntent)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um classificador de intenção. Analise a mensagem do usuário e determine se ele deseja ENCERRAR, FINALIZAR, SAIR ou PARAR a conversa.\n"
                       "Frases como 'não obrigado', 'deixa pra lá', 'já resolvi', 'não quero nada', 'tchau', 'fim', 'sair', 'finalizar' devem ser consideradas SAÍDA (True).\n"
                       "Frases de continuação, dúvidas ou respostas a perguntas devem ser consideradas CONTINUAÇÃO (False)."),
            ("user", "{input}")
        ])

        chain = prompt | structured_llm
        result = chain.invoke({"input": message})

        return result.is_exit
        
    except Exception as e:

        print(f"Error checking exit intent: {e}")
        
        return False
