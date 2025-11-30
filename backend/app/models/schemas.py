from pydantic import BaseModel, Field
from typing import Literal, Optional

class TriageIntent(BaseModel):
    category: Literal["CREDITO", "CAMBIO", "OUTROS"] = Field(description="A categoria do serviço bancário solicitado.")

class CreditIntent(BaseModel):
    intent: Literal["CHECK_LIMIT", "REQUEST_INCREASE", "OTHER"] = Field(description="A intenção do usuário.")
    value: Optional[float] = Field(description="O valor monetário solicitado, se houver (ex: 3000.00).")

class ValidationResult(BaseModel):
    valid: bool = Field(description="Se a resposta faz sentido para a pergunta.")
    feedback: Optional[str] = Field(description="Mensagem curta e educada pedindo correção se inválido. Vazio se válido.")
    cleaned_value: Optional[str] = Field(description="O valor extraído e limpo da resposta (ex: '5000' para 'ganho 5k').")

class ExitIntent(BaseModel):
    is_exit: bool = Field(description="Verdadeiro se o usuário quiser sair, finalizar ou parar a conversa. Falso caso contrário.")

class UserMessage(BaseModel):
    message: str = Field(description="A mensagem enviada pelo usuário.")
    session_id: str = Field(default="default", description="O ID da sessão do usuário.")

class InterviewOfferIntent(BaseModel):
    decision: Literal["ACCEPT", "DECLINE", "UNCLEAR"] = Field(description="Se o usuário aceitou ou recusou a oferta de entrevista.")

class CurrencyExtraction(BaseModel):
    currency_code: Literal["USD", "EUR", "GBP", "OTHER"] = Field(description="O código da moeda que o usuário quer consultar. Default para USD se não especificado.")

class GreetingIntent(BaseModel):
    is_greeting: bool = Field(description="Verdadeiro se a mensagem for apenas uma saudação (ex: 'Oi', 'Bom dia'). Falso se contiver uma solicitação ou informação.")

class CPFExtraction(BaseModel):
    cpf: Optional[str] = Field(description="O CPF extraído da mensagem, contendo apenas números (11 dígitos). Retorne None ou string vazia se não encontrar um CPF válido.")

class DateExtraction(BaseModel):
    date: Optional[str] = Field(description="A data extraída formatada como YYYY-MM-DD. Retorne None ou 'INVALID' se não encontrar uma data válida.")

class InterviewNormalization(BaseModel):
    income: float = Field(description="Renda mensal numérica.")
    job_type: Literal["formal", "autônomo", "desempregado"] = Field(description="Tipo de emprego normalizado.")
    expenses: float = Field(description="Despesas mensais numéricas.")
    dependents: int = Field(description="Número total de dependentes.")
    has_debts: bool = Field(description="Se possui dívidas ativas.")
