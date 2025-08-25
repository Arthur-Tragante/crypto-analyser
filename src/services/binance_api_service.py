"""
Serviço para consultar preços via API REST da Binance
Consulta preços via HTTP para compatibilidade com GCP
"""
import requests
import time
from typing import Dict, Optional
from datetime import datetime


class BinanceApiService:
    """Serviço para consultar preços via API REST da Binance"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/ticker/price"
        self.symbols = {
            "btc": "BTCBRL",
            "eth": "ETHBRL", 
            "xrp": "XRPBRL",
            "bnb": "BNBBRL",
            "ada": "ADABRL",
            "sol": "SOLBRL",
            "doge": "DOGEBRL",
            "dot": "DOTBRL",
            "matic": "MATICBRL",
            "ltc": "LTCBRL",
            "avax": "AVAXBRL",
            "shib": "SHIBBRL"
        }
        self.last_update = None
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Obtém preço de uma criptomoeda específica"""
        try:
            binance_symbol = self.symbols.get(symbol.lower())
            if not binance_symbol:
                print(f"Símbolo não suportado: {symbol}")
                return None
            
            url = f"{self.base_url}?symbol={binance_symbol}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                formatted_price = self._format_price_for_display(price)
                print(f"Preço {symbol.upper()}: R$ {formatted_price}")
                return price
            else:
                print(f"Erro ao consultar {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro na consulta {symbol}: {e}")
            return None
    
    def _format_price_for_display(self, price: float) -> str:
        """Formata preço para exibição nos logs com casas decimais inteligentes"""
        if price < 0.01:
            # Para preços muito baixos, usa até 8 casas decimais
            formatted = f"{price:.8f}".rstrip('0').rstrip('.')
            # Se ainda for 0, usa formatação científica
            if float(formatted) == 0:
                return f"{price:.2e}"
        elif price < 1.0:
            # Para preços baixos, usa 4 casas decimais
            formatted = f"{price:.4f}".rstrip('0').rstrip('.')
        else:
            # Para preços normais, usa 2 casas decimais
            formatted = f"{price:,.2f}"
        
        # Aplica formatação brasileira (ponto para milhares, vírgula para decimais)
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    
    def get_all_prices(self) -> Dict[str, Optional[float]]:
        """Obtém preços de todas as criptomoedas configuradas"""
        prices = {}
        
        for symbol in self.symbols.keys():
            prices[symbol] = self.get_price(symbol)
            time.sleep(0.1)  # Pequeno delay entre requests
        
        self.last_update = datetime.now()
        return prices
    
    def get_multiple_prices(self, symbols_list: list) -> Dict[str, Optional[float]]:
        """Obtém preços de múltiplas criptomoedas usando uma única requisição"""
        try:
            # Monta lista de símbolos da Binance
            binance_symbols = []
            symbol_map = {}
            
            for symbol in symbols_list:
                binance_symbol = self.symbols.get(symbol.lower())
                if binance_symbol:
                    binance_symbols.append(binance_symbol)
                    symbol_map[binance_symbol] = symbol.lower()
            
            if not binance_symbols:
                return {}
            
            # Faz requisição para múltiplos símbolos
            symbols_param = '["' + '","'.join(binance_symbols) + '"]'
            url = f"{self.base_url}?symbols={symbols_param}"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for item in data:
                    binance_symbol = item['symbol']
                    our_symbol = symbol_map.get(binance_symbol)
                    if our_symbol:
                        price = float(item['price'])
                        prices[our_symbol] = price
                        formatted_price = self._format_price_for_display(price)
                        print(f"Preço {our_symbol.upper()}: R$ {formatted_price}")
                
                self.last_update = datetime.now()
                return prices
            else:
                print(f"Erro ao consultar preços múltiplos: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Erro na consulta múltipla: {e}")
            # Fallback para consultas individuais
            return self.get_all_prices()
    
    def is_api_available(self) -> bool:
        """Verifica se a API da Binance está disponível"""
        try:
            response = requests.get(self.base_url + "?symbol=BTCBRL", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_last_update_info(self) -> dict:
        """Retorna informações sobre a última atualização"""
        return {
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "api_available": self.is_api_available(),
            "supported_symbols": list(self.symbols.keys())
        }


# Instância global
binance_api_service = BinanceApiService()
