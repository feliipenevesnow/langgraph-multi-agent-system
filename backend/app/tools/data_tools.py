import pandas as pd
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLIENTES_PATH = os.path.join(DATA_DIR, "clientes.csv")
SCORE_LIMITE_PATH = os.path.join(DATA_DIR, "score_limite.csv")
SOLICITACOES_PATH = os.path.join(DATA_DIR, "solicitacoes_aumento_limite.csv")

def authenticate_user(cpf: str, data_nascimento: str):
    """
    Autentica um usuário por CPF e Data de Nascimento.
    Retorna o dicionário do usuário se encontrado, caso contrário None.
    """
    try:
        df = pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})
        
        cpf = cpf.replace(".", "").replace("-", "").strip()
        
        user = df[(df["cpf"] == cpf) & (df["data_nascimento"] == data_nascimento)]
        
        if not user.empty:
            return user.iloc[0].to_dict()
        return None

    except Exception as e:

        print(f"Error authenticating user: {e}")

        return None

def get_user_data(cpf: str):
    """Recupera dados do usuário por CPF."""
    try:

        df = pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})

        cpf = cpf.replace(".", "").replace("-", "").strip()

        user = df[df["cpf"] == cpf]

        if not user.empty:
            return user.iloc[0].to_dict()

        return None

    except Exception as e:

        print(f"Error getting user data: {e}")

        return None

def check_credit_limit(cpf: str):
    """Retorna o limite de crédito atual para um usuário."""

    user = get_user_data(cpf)

    if user:
        return user.get("limite_atual")

    return None

def request_limit_increase(cpf: str, new_limit: float):
    """
    Processa uma solicitação de aumento de limite.
    Retorna um dict com status e mensagem.
    """

    try:
        user = get_user_data(cpf)

        if not user:
            return {"status": "error", "message": "User not found"}
        
        current_score = user["score"]
        current_limit = user["limite_atual"]
        
        score_df = pd.read_csv(SCORE_LIMITE_PATH)
        
        rule = score_df[(score_df["score_min"] <= current_score) & (score_df["score_max"] >= current_score)]
        
        status = "rejeitado"

        if not rule.empty:
            max_allowed = rule.iloc[0]["limite_max"]

            if new_limit <= max_allowed:
                status = "aprovado"
             
        new_request = {
            "cpf_cliente": cpf,
            "data_hora_solicitacao": datetime.now().isoformat(),
            "limite_atual": current_limit,
            "novo_limite_solicitado": new_limit,
            "status_pedido": status
        }
        
        
        requests_df = pd.DataFrame([new_request])

        if os.path.exists(SOLICITACOES_PATH) and os.path.getsize(SOLICITACOES_PATH) > 0:
            requests_df.to_csv(SOLICITACOES_PATH, mode='a', header=False, index=False)

        else:
            requests_df.to_csv(SOLICITACOES_PATH, mode='w', header=True, index=False)
            
        if status == "aprovado":
            update_user_limit(cpf, new_limit)
            
        return {
            "status": status, 
            "message": f"Request {status}",
            "current_score": int(current_score),
            "max_allowed": float(max_allowed),
            "limit_requested": float(new_limit)
        }
        
    except Exception as e:
        
        print(f"Error processing limit request: {e}")

        return {"status": "error", "message": str(e)}

def update_user_limit(cpf: str, new_limit: float):
    """Atualiza o limite do usuário no CSV."""

    try:
        df = pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})
        cpf = cpf.replace(".", "").replace("-", "").strip()
        
        if cpf in df["cpf"].values:
            df.loc[df["cpf"] == cpf, "limite_atual"] = new_limit
            df.to_csv(CLIENTES_PATH, index=False)
            return True

        return False

    except Exception as e:

        print(f"Error updating limit: {e}")

        return False

def update_user_score(cpf: str, new_score: int):
    """Atualiza o score do usuário no CSV."""

    try:
        df = pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})
        cpf = cpf.replace(".", "").replace("-", "").strip()
        
        if cpf in df["cpf"].values:
            df.loc[df["cpf"] == cpf, "score"] = new_score
            df.to_csv(CLIENTES_PATH, index=False)
            return True

        return False

    except Exception as e:

        print(f"Error updating score: {e}")
        
        return False
