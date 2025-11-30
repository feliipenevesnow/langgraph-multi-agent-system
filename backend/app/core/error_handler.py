from langchain_core.prompts import ChatPromptTemplate
from app.core.llm import llm

def generate_error_response(error_details: str) -> str:
    """
    Gera uma mensagem de erro amigável usando LLM para manter a persona do atendente.
    """

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um assistente bancário virtual prestativo e educado. Ocorreu um erro interno no sistema: {error_details}.\n"
                       "Seu objetivo é explicar ao usuário, de forma humana e não técnica, que algo deu errado do nosso lado.\n"
                       "Peça desculpas pelo inconveniente e sugira que ele aguarde um momento ou tente atualizar a página para reiniciar o atendimento.\n"
                       "IMPORTANTE: Avise que ao reiniciar, será necessário passar pelo processo de autenticação novamente.\n"
                       "Não mencione códigos de erro ou detalhes técnicos. Mantenha a calma e a empatia."),
            ("user", "Gere a mensagem de erro.")
        ])

        chain = prompt | llm
        response = chain.invoke({"error_details": error_details})

        return response.content

    except Exception as e:

        print(f"Error generating error response: {e}")
        
        return "Desculpe, estamos enfrentando dificuldades técnicas no momento. Por favor, tente novamente mais tarde."
