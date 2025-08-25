"""
Serviço para integração com CoinGecko API
Busca preços de criptomoedas em BRL
"""
import requests
from typing import Dict, Optional


class CoinGeckoApiService:
    """Serviço para buscar preços via CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3/simple/price"
        # Mapeamento dos nossos símbolos internos para IDs do CoinGecko
        self.coin_ids = {
            "btc": "bitcoin",
            "eth": "ethereum", 
            "xrp": "ripple",
            "bnb": "binancecoin",
            "ada": "cardano",
            "sol": "solana",
            "doge": "dogecoin",
            "dot": "polkadot",
            "matic": "polygon",
            "ltc": "litecoin",
            "avax": "avalanche-2",
            "shib": "shiba-inu"
        }
        
        # Mapeamento reverso para converter resposta da API
        self.id_to_symbol = {v: k for k, v in self.coin_ids.items()}
    
    def _format_price_for_display(self, price: float) -> str:
        """Formata preço para exibição com decimais inteligentes"""
        if price < 0.01:
            # Para preços muito baixos (como SHIB), mostra 8 decimais
            return f"{price:,.8f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elif price < 1.0:
            # Para preços baixos, mostra 4 decimais
            return f"{price:,.4f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            # Para preços normais, mostra 2 decimais
            return f"{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, Optional[float]]:
        """
        Busca preços de múltiplas moedas
        Args:
            symbols: Lista de símbolos internos (ex: ['btc', 'eth', 'xrp'])
        Returns:
            Dict com preços: {'btc': 615576.0, 'eth': 25807.0, ...}
        """
        try:
            # Converte símbolos internos para IDs do CoinGecko
            coin_ids = []
            valid_symbols = []
            
            for symbol in symbols:
                if symbol in self.coin_ids:
                    coin_ids.append(self.coin_ids[symbol])
                    valid_symbols.append(symbol)
                else:
                    print(f"Símbolo desconhecido ignorado: {symbol}")
            
            if not coin_ids:
                print("Nenhum símbolo válido encontrado")
                return {}
            
            # Monta URL com todos os IDs
            ids_param = ",".join(coin_ids)
            url = f"{self.base_url}?ids={ids_param}&vs_currencies=brl"
            
            print(f"Consultando CoinGecko: {len(coin_ids)} moedas...")
            
            # Faz requisição
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = {}
            
            # Processa resposta e converte IDs de volta para símbolos
            for coin_id, price_data in data.items():
                if coin_id in self.id_to_symbol:
                    symbol = self.id_to_symbol[coin_id]
                    price = price_data.get("brl")
                    
                    if price is not None:
                        prices[symbol] = float(price)
                        formatted_price = self._format_price_for_display(price)
                        print(f"Preço {symbol.upper()}: R$ {formatted_price}")
                    else:
                        print(f"Preço não encontrado para {symbol.upper()}")
                        prices[symbol] = None
            
            # Adiciona None para símbolos que não retornaram dados
            for symbol in valid_symbols:
                if symbol not in prices:
                    prices[symbol] = None
                    print(f"Dados não retornados para {symbol.upper()}")
            
            print(f"CoinGecko: {len(prices)} preços processados")
            return prices
            
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição CoinGecko: {e}")
            return {}
        except Exception as e:
            print(f"Erro ao processar resposta CoinGecko: {e}")
            return {}
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Busca preço de uma moeda específica
        Args:
            symbol: Símbolo interno (ex: 'btc')
        Returns:
            Preço em float ou None se não encontrado
        """
        prices = self.get_multiple_prices([symbol])
        return prices.get(symbol)


# Instância singleton
coingecko_api_service = CoinGeckoApiService()
