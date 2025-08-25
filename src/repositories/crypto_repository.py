"""
Repositório para dados de criptomoedas
Responsável por queries e acesso aos dados
"""
from typing import Dict, Optional
from datetime import datetime
from ..models.crypto_data import CryptoPrice, CryptoSymbol, SystemStatus


class CryptoRepository:
    """Repositório para gerenciar dados de criptomoedas"""
    
    def __init__(self):
        self._crypto_data: Dict[str, CryptoPrice] = {}
        self._system_status = SystemStatus()
        self._initialize_crypto_data()
    
    def _initialize_crypto_data(self):
        """Inicializa dados das criptomoedas"""
        crypto_configs = {
            "btc": (CryptoSymbol.BTC, "Bitcoin"),
            "eth": (CryptoSymbol.ETH, "Ethereum"),
            "xrp": (CryptoSymbol.XRP, "Ripple"),
            "bnb": (CryptoSymbol.BNB, "BNB"),
            "ada": (CryptoSymbol.ADA, "Cardano"),
            "sol": (CryptoSymbol.SOL, "Solana"),
            "doge": (CryptoSymbol.DOGE, "Dogecoin"),
            "dot": (CryptoSymbol.DOT, "Polkadot"),
            "matic": (CryptoSymbol.MATIC, "Polygon"),
            "ltc": (CryptoSymbol.LTC, "Litecoin"),
            "avax": (CryptoSymbol.AVAX, "Avalanche"),
            "shib": (CryptoSymbol.SHIB, "Shiba Inu")
        }
        
        for key, (symbol, name) in crypto_configs.items():
            self._crypto_data[key] = CryptoPrice(symbol=symbol, name=name)
    
    def get_crypto_by_symbol(self, symbol: str) -> Optional[CryptoPrice]:
        """Busca criptomoeda por símbolo"""
        return self._crypto_data.get(symbol.lower())
    
    def get_all_cryptos(self) -> Dict[str, CryptoPrice]:
        """Retorna todas as criptomoedas"""
        return self._crypto_data.copy()
    
    def update_crypto_price(self, symbol: str, price: float) -> bool:
        """Atualiza preço de uma criptomoeda"""
        crypto = self.get_crypto_by_symbol(symbol)
        if crypto:
            crypto.update_price(price)
            self._update_system_status()
            return True
        return False
    
    def get_system_status(self) -> SystemStatus:
        """Retorna status do sistema"""
        return self._system_status
    
    def _update_system_status(self):
        """Atualiza status do sistema baseado nos preços"""
        btc_price = self._crypto_data["btc"].price
        eth_price = self._crypto_data["eth"].price
        self._system_status.update_connection_status(btc_price, eth_price)
    
    def get_prices_summary(self) -> dict:
        """Retorna resumo dos preços para API"""
        btc = self._crypto_data["btc"]
        eth = self._crypto_data["eth"]
        
        return {
            "btc_brl": btc.price,
            "eth_brl": eth.price,
            "btc_formatted": btc.formatted_price,
            "eth_formatted": eth.formatted_price,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_full_data(self) -> dict:
        """Retorna dados completos para API"""
        return {
            "data": {
                "btc": {
                    "price": self._crypto_data["btc"].price,
                    "formatted_price": self._crypto_data["btc"].formatted_price,
                    "last_update": self._crypto_data["btc"].last_update.isoformat() if self._crypto_data["btc"].last_update else None,
                    "symbol": self._crypto_data["btc"].symbol.value,
                    "name": self._crypto_data["btc"].name,
                    "alert_status": self._crypto_data["btc"].alert_status.value
                },
                "eth": {
                    "price": self._crypto_data["eth"].price,
                    "formatted_price": self._crypto_data["eth"].formatted_price,
                    "last_update": self._crypto_data["eth"].last_update.isoformat() if self._crypto_data["eth"].last_update else None,
                    "symbol": self._crypto_data["eth"].symbol.value,
                    "name": self._crypto_data["eth"].name,
                    "alert_status": self._crypto_data["eth"].alert_status.value
                },
                "status": self._system_status.status
            },
            "timestamp": datetime.now().isoformat()
        }
