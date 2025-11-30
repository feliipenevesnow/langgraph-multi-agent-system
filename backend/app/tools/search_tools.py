import requests

def get_exchange_rate(currency: str) -> float:
    """
    Busca a taxa de câmbio atual para a moeda dada em BRL usando AwesomeAPI.
    
    Args:
        currency (str): O código da moeda (ex: 'USD', 'EUR', 'GBP').
        
    Returns:
        float: A taxa de câmbio atual (preço de compra).
    """

    currency = currency.upper()
    
    if currency == "DÓLAR" or currency == "DOLAR":
        currency = "USD"
    
    try:
        url = f"https://economia.awesomeapi.com.br/last/{currency}-BRL"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        key = f"{currency}BRL"
        
        if key in data:
            return float(data[key]["bid"])

        else:

            print(f"Currency pair not found in response: {data}")
            
            return 0.0
            
    except Exception as e:

        print(f"Error fetching exchange rate for {currency}: {e}")

        return 0.0
