"""
Serviço Firestore para gerenciar configurações dinâmicas
Permite alterar níveis de alerta sem reiniciar a aplicação
"""
import json
import requests
import jwt
import time
from typing import Dict, Any, Optional
from datetime import datetime

class FirestoreService:
    """Serviço para gerenciar configurações no Firestore"""
    
    def __init__(self):
        # Importação tardia para evitar dependência circular
        from ..config.settings import settings
        self.collection_name = settings.firebase.firestore_collection
        self._load_service_account()
        self._setup_firestore_url()
    
    def _load_service_account(self):
        """Carrega credenciais do service account"""
        from ..config.settings import settings
        with open(settings.firebase.service_account_path, 'r') as f:
            self.service_account = json.load(f)
        
        self.project_id = self.service_account["project_id"]
        self.private_key = self.service_account["private_key"]
        self.client_email = self.service_account["client_email"]
    
    def _setup_firestore_url(self):
        """Configura URL do Firestore"""
        self.firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"
    
    def _get_access_token(self) -> Optional[str]:
        """Obtém access token para Firestore com escopo correto"""
        try:
            now = int(time.time())

            payload = {
                "iss": self.client_email,
                "scope": "https://www.googleapis.com/auth/datastore https://www.googleapis.com/auth/firebase",
                "aud": "https://oauth2.googleapis.com/token",
                "iat": now,
                "exp": now + 3600  # 1 hora
            }
            
            jwt_token = jwt.encode(payload, self.private_key, algorithm="RS256")
            
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
            
            response = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                return access_token
            else:
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            return None
    
    def _build_headers(self, access_token: str) -> Dict[str, str]:
        """Constrói headers para requisições Firestore"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_all_coins(self) -> Optional[Dict[str, Any]]:
        """Busca todos os documentos da coleção coins"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                print("Não foi possível obter token para Firestore")
                return None
            
            headers = self._build_headers(access_token)
            
            url = f"{self.firestore_url}/{self.collection_name}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'documents' in data:
                    coins_data = {}
                    for doc in data['documents']:
                        doc_id = doc['name'].split('/')[-1]
                        if 'fields' in doc:
                            coin_config = self._convert_firestore_to_dict(doc['fields'])
                            coins_data[doc_id] = coin_config
                    return coins_data
                else:
                    print("Coleção existe mas não tem documentos")
                    return None
            elif response.status_code == 404:
                print("Coleção não encontrada no Firestore")
                return None
            else:
                print(f"Erro ao buscar coleção: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao buscar coleção do Firestore: {e}")
            return None
    
    def get_alert_config(self) -> Optional[Dict[str, Any]]:
        """Busca configurações de alerta percorrendo toda a coleção"""
        coins_data = self.get_all_coins()
        if not coins_data:
            return None

        btc_config = None
        eth_config = None
        
        for doc_id, coin_data in coins_data.items():
            moeda = coin_data.get('moeda', '').upper()
            
            if moeda == 'BTC':
                btc_config = {
                    'btc_lowest': coin_data.get('btc_lowest'),
                    'btc_high': coin_data.get('btc_high')
                }
            elif moeda == 'ETH':
                eth_config = {
                    'eth_lowest': coin_data.get('eth_lowest'),
                    'eth_high': coin_data.get('eth_high')
                }
        
        if btc_config or eth_config:
            combined_config = {
                'btc_lowest': btc_config.get('btc_lowest') if btc_config else None,
                'btc_high': btc_config.get('btc_high') if btc_config else None,
                'eth_lowest': eth_config.get('eth_lowest') if eth_config else None,
                'eth_high': eth_config.get('eth_high') if eth_config else None,
                'notification_interval': self._get_default_notification_interval()
            }
            return combined_config
        return None
    
    def save_alert_config(self, config: Dict[str, Any]) -> bool:
        """Salva configurações de alerta no Firestore"""
        try:
            coins_data = self.get_all_coins()
            target_doc_id = None
            
            if coins_data:
                for doc_id, coin_data in coins_data.items():
                    if coin_data.get('btc_lowest') is not None or coin_data.get('btc_high') is not None:
                        target_doc_id = doc_id
                        break
            
            if not target_doc_id:
                target_doc_id = f"btc_config_{int(time.time())}"
            
            access_token = self._get_access_token()
            if not access_token:
                return False
            
            headers = self._build_headers(access_token)
            url = f"{self.firestore_url}/{self.collection_name}/{target_doc_id}"
            
            firestore_data = {
                "fields": self._convert_dict_to_firestore(config)
            }
            
            response = requests.patch(url, headers=headers, json=firestore_data, timeout=10)
            
            if response.status_code == 200:
                print(f"Configurações salvas no documento '{target_doc_id}': {config}")
                return True
            else:
                print(f"Erro ao salvar configurações: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Erro ao salvar configurações no Firestore: {e}")
            return False
    
    def _convert_firestore_to_dict(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Converte formato Firestore para dict normal e mapeia campos"""
        raw_data = {}
        for key, value in fields.items():
            if 'doubleValue' in value:
                raw_data[key] = float(value['doubleValue'])
            elif 'integerValue' in value:
                raw_data[key] = int(value['integerValue'])
            elif 'stringValue' in value:
                str_val = value['stringValue']
                try:
                    if '_' in str_val:
                        raw_data[key] = float(str_val.replace('_', ''))
                    else:
                        raw_data[key] = str_val
                except ValueError:
                    raw_data[key] = str_val
            elif 'booleanValue' in value:
                raw_data[key] = value['booleanValue']
            elif 'timestampValue' in value:
                raw_data[key] = value['timestampValue']
        
        result = {}
        
        moeda = raw_data.get('Moeda', '').upper()
        
        if 'Lowest' in raw_data and isinstance(raw_data['Lowest'], (int, float)):
            lowest_val = float(raw_data['Lowest'])
            if moeda == 'BTC':
                result['btc_lowest'] = lowest_val
            elif moeda == 'ETH':
                result['eth_lowest'] = lowest_val
                
        if 'Highest' in raw_data and isinstance(raw_data['Highest'], (int, float)):
            highest_val = float(raw_data['Highest'])
            if moeda == 'BTC':
                result['btc_high'] = highest_val
            elif moeda == 'ETH':
                result['eth_high'] = highest_val
        
        if 'Moeda' in raw_data:
            result['moeda'] = raw_data['Moeda']
        
        result['notification_interval'] = self._get_default_notification_interval()
        
        return result
    
    def _get_default_notification_interval(self) -> int:
        """Obtém o intervalo padrão de notificação das configurações"""
        from ..config.settings import settings
        return settings.notifications.notification_interval
    
    def _convert_dict_to_firestore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte dict normal para formato Firestore usando sua estrutura"""
        result = {}
        
        if 'btc_lowest' in data:
            result["Lowest"] = {"stringValue": f"{data['btc_lowest']:,.0f}".replace(',', '_')}
        if 'btc_high' in data:
            result["Highest"] = {"stringValue": f"{data['btc_high']:,.0f}".replace(',', '_')}
        
        result["Moeda"] = {"stringValue": "BTC"}
        
        if 'eth_lowest' in data:
            result["eth_lowest"] = {"doubleValue": data['eth_lowest']}
        if 'eth_high' in data:
            result["eth_high"] = {"doubleValue": data['eth_high']}
        if 'notification_interval' in data:
            result["notification_interval"] = {"integerValue": data['notification_interval']}
        
        result["last_updated"] = {"timestampValue": datetime.now().isoformat() + "Z"}
        
        return result
    
    def create_default_config(self) -> bool:
        """Cria configuração padrão no Firestore se não existir"""
        try:
            existing_config = self.get_alert_config()
            if existing_config:
                print("Configuração já existe no Firestore")
                return True            
            return False
            
        except Exception as e:
            print(f"Erro ao verificar configuração: {e}")
            return False
    
    def get_notify_coins(self) -> Optional[list]:
        """Busca lista de moedas da coleção 'notify'"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                print("Não foi possível obter token para buscar notify")
                return None
            
            headers = self._build_headers(access_token)
            url = f"{self.firestore_url}/notify"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'documents' in data:
                    coins = []
                    for doc in data['documents']:
                        if 'fields' in doc and 'name' in doc['fields']:
                            name_field = doc['fields']['name']
                            if 'stringValue' in name_field:
                                coin_name = name_field['stringValue'].lower()
                                coins.append(coin_name)
                    print(f"Moedas para notificação: {coins}")
                    return coins
                else:
                    print("Coleção notify existe mas não tem documentos")
                    return []
            elif response.status_code == 404:
                print("Coleção notify não encontrada")
                return []
            else:
                print(f"Erro ao buscar notify: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao buscar notify: {e}")
            return None
    
    def get_current_prices_for_storage(self, btc_price: float, eth_price: float) -> bool:
        """Salva preços atuais no Firestore para histórico"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return False
            
            headers = self._build_headers(access_token)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url = f"{self.firestore_url}/crypto_prices/{timestamp}"
            
            price_data = {
                "btc_price": btc_price,
                "eth_price": eth_price,
                "timestamp": datetime.now().isoformat()
            }
            
            firestore_data = {
                "fields": self._convert_dict_to_firestore(price_data)
            }
            
            response = requests.patch(url, headers=headers, json=firestore_data, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Erro ao salvar preços no Firestore: {e}")
            return False

# Instância global será criada quando necessária
_firestore_service = None

def get_firestore_service():
    """Retorna instância do FirestoreService (lazy loading)"""
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreService()
    return _firestore_service
