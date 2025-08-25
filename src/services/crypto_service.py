"""
Serviço de criptomoedas
Contém as regras de negócio
"""
from typing import Optional, Tuple
from datetime import datetime
from ..models.crypto_data import CryptoPrice, AlertStatus, NotificationData
from ..repositories.crypto_repository import CryptoRepository
from ..config.settings import settings
from .binance_api_service import binance_api_service


class CryptoService:
    """Serviço para regras de negócio de criptomoedas"""
    
    def __init__(self, repository: CryptoRepository):
        self.repository = repository
        self.alert_config = settings.alerts
    
    def update_crypto_price(self, symbol: str, price: float) -> bool:
        """Atualiza preço e verifica alertas"""
        success = self.repository.update_crypto_price(symbol, price)
        if success:
            self._check_and_update_alert_status(symbol, price)
        return success
    
    def update_prices_from_api(self):
        """Atualiza preços via API REST da Binance"""
        try:
            # Busca todas as moedas suportadas
            all_coins = list(binance_api_service.symbols.keys())
            prices = binance_api_service.get_multiple_prices(all_coins)
            
            for symbol, price in prices.items():
                if price is not None:
                    self.update_crypto_price(symbol, price)
                    
        except Exception as e:
            print(f"Erro ao atualizar preços via API: {e}")
    
    def _check_and_update_alert_status(self, symbol: str, price: float):
        """Verifica e atualiza status de alerta"""
        crypto = self.repository.get_crypto_by_symbol(symbol)
        if not crypto:
            return
        
        if symbol.lower() == "btc":
            crypto.alert_status = self._get_btc_alert_status(price)
        elif symbol.lower() == "eth":
            crypto.alert_status = self._get_eth_alert_status(price)
    
    def _get_btc_alert_status(self, price: float) -> AlertStatus:
        """Determina status de alerta para BTC"""
        if self.alert_config.btc_lowest is not None and price <= self.alert_config.btc_lowest:
            return AlertStatus.BAIXA
        elif self.alert_config.btc_high is not None and price >= self.alert_config.btc_high:
            return AlertStatus.ALTA
        return AlertStatus.NORMAL
    
    def _get_eth_alert_status(self, price: float) -> AlertStatus:
        """Determina status de alerta para ETH"""
        if self.alert_config.eth_lowest is not None and price <= self.alert_config.eth_lowest:
            return AlertStatus.BAIXA
        elif self.alert_config.eth_high is not None and price >= self.alert_config.eth_high:
            return AlertStatus.ALTA
        return AlertStatus.NORMAL
    
    def should_send_alert(self, symbol: str, current_status: AlertStatus, last_status: Optional[AlertStatus]) -> bool:
        """Determina se deve enviar alerta (evita spam)"""
        if current_status == AlertStatus.NORMAL:
            return False
        return current_status != last_status
    
    def get_notification_data(self, notify_coins: Optional[list] = None) -> Optional[NotificationData]:
        """Prepara dados para notificação usando apenas moedas da coleção notify"""
        if not notify_coins:
            # Fallback para BTC e ETH se não houver lista
            notify_coins = ["btc", "eth"]
        
        crypto_prices = {}
        valid_prices = 0
        
        for coin in notify_coins:
            crypto = self.repository.get_crypto_by_symbol(coin)
            if crypto and crypto.price is not None:
                crypto_prices[coin] = crypto
                valid_prices += 1
        
        # Só retorna dados se houver pelo menos uma moeda com preço
        if valid_prices == 0:
            return None
        
        return NotificationData(
            crypto_prices=crypto_prices,
            timestamp=datetime.now()
        )
    
    def get_alert_levels_info(self) -> dict:
        """Retorna informações dos níveis de alerta"""
        btc = self.repository.get_crypto_by_symbol("btc")
        eth = self.repository.get_crypto_by_symbol("eth")
        
        return {
            "alert_levels": {
                "btc": {
                    "lowest": self.alert_config.btc_lowest,
                    "high": self.alert_config.btc_high,
                    "current": btc.price if btc else None,
                    "formatted_lowest": self._format_brl(self.alert_config.btc_lowest),
                    "formatted_high": self._format_brl(self.alert_config.btc_high),
                    "formatted_current": btc.formatted_price if btc else "N/A",
                    "status": btc.alert_status.value if btc else "N/A"
                },
                "eth": {
                    "lowest": self.alert_config.eth_lowest,
                    "high": self.alert_config.eth_high,
                    "current": eth.price if eth else None,
                    "formatted_lowest": self._format_brl(self.alert_config.eth_lowest),
                    "formatted_high": self._format_brl(self.alert_config.eth_high),
                    "formatted_current": eth.formatted_price if eth else "N/A",
                    "status": eth.alert_status.value if eth else "N/A"
                }
            },
            "alert_status": f"Sistema ativo - notificações a cada {settings.notifications.notification_interval // 60} minutos",
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_brl(self, price: Optional[float]) -> str:
        """Formata preço para BRL com casas decimais inteligentes"""
        if price is None:
            return "N/A"
        
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
    
    def create_display_text(self) -> str:
        """Cria texto formatado para display ASCII com todas as moedas"""
        all_cryptos = self.repository.get_all_cryptos()
        
        # Filtra apenas moedas com preço disponível
        available_cryptos = {k: v for k, v in all_cryptos.items() if v.price is not None}
        
        if not available_cryptos:
            return "Dados não disponíveis"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        width = 80  # Aumentado para acomodar mais moedas
        
        display_text = ""
        display_text += "╔" + "═" * width + "╗\n"
        display_text += "║" + " CRYPTO ANALYSER".center(width) + "║\n"
        display_text += "╠" + "═" * width + "╣\n"
        display_text += f"║ Última atualização: {timestamp}{' ' * (width - len(f' Última atualização: {timestamp}'))}║\n"
        display_text += "╠" + "═" * width + "╣\n"
        
        # Coleta alertas de todas as moedas
        alerts_active = []
        for symbol, crypto in available_cryptos.items():
            if crypto.alert_status == AlertStatus.BAIXA:
                alerts_active.append(f"{symbol.upper()} ALERTA DE BAIXA")
            elif crypto.alert_status == AlertStatus.ALTA:
                alerts_active.append(f"{symbol.upper()} ALERTA DE ALTA")
        
        if alerts_active:
            for alert in alerts_active:
                display_text += f"║ {alert}{' ' * (width - len(f' {alert}'))}║\n"
            display_text += "╠" + "═" * width + "╣\n"
        
        # Exibe preços de todas as moedas em ordem
        crypto_order = ["btc", "eth", "xrp", "ada", "bnb", "sol", "doge", "dot", "matic", "ltc", "avax", "shib"]
        
        for symbol in crypto_order:
            if symbol in available_cryptos:
                crypto = available_cryptos[symbol]
                name = crypto.name
                price_text = crypto.formatted_price
                
                # Formato simples e alinhado: Nome (SYMBOL): preço
                line = f"║ {name:<12} ({symbol.upper():<4}): R$ {price_text}"
                
                # Calcula espaços necessários para completar a largura
                spaces_needed = width - len(line) + 1  # +1 porque queremos chegar até a borda
                
                if spaces_needed > 0:
                    display_text += line + " " * spaces_needed + "║\n"
                else:
                    # Trunca se necessário
                    max_content = width - 3  # 3 = "║" + espaço + "║"
                    content = f" {name:<12} ({symbol.upper():<4}): R$ {price_text}"
                    if len(content) > max_content:
                        content = content[:max_content-3] + "..."
                    display_text += f"║{content:<{max_content}}║\n"
        
        # Seção de níveis de alerta (apenas BTC e ETH por espaço)
        btc = available_cryptos.get("btc")
        eth = available_cryptos.get("eth")
        
        if btc or eth:
            display_text += "╠" + "═" * width + "╣\n"
            
            if btc:
                btc_line = f"║ Níveis BTC: L={self._format_brl(self.alert_config.btc_lowest)} H={self._format_brl(self.alert_config.btc_high)}"
                spaces_needed = width - len(btc_line) + 1
                if spaces_needed > 0:
                    display_text += btc_line + " " * spaces_needed + "║\n"
                else:
                    max_content = width - 2
                    content = f" Níveis BTC: L={self._format_brl(self.alert_config.btc_lowest)} H={self._format_brl(self.alert_config.btc_high)}"
                    if len(content) > max_content:
                        content = content[:max_content-3] + "..."
                    display_text += f"║{content:<{max_content}}║\n"
                
            if eth:
                eth_line = f"║ Níveis ETH: L={self._format_brl(self.alert_config.eth_lowest)} H={self._format_brl(self.alert_config.eth_high)}"
                spaces_needed = width - len(eth_line) + 1
                if spaces_needed > 0:
                    display_text += eth_line + " " * spaces_needed + "║\n"
                else:
                    max_content = width - 2
                    content = f" Níveis ETH: L={self._format_brl(self.alert_config.eth_lowest)} H={self._format_brl(self.alert_config.eth_high)}"
                    if len(content) > max_content:
                        content = content[:max_content-3] + "..."
                    display_text += f"║{content:<{max_content}}║\n"
        
        display_text += "╚" + "═" * width + "╝\n"
        
        return display_text
