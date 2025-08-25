# Crypto Analyser - Monitor de Preços e Notificações

Sistema refatorado seguindo melhores práticas para monitorar preços de Bitcoin e Ethereum em tempo real com sistema de notificações automáticas.

## 🚀 Funcionalidades

### 📊 Consulta de Preços
- Preços em tempo real via API REST Binance
- Bitcoin (BTC) e Ethereum (ETH) em BRL
- API REST para integração
- Interface visual ASCII

### 📱 Sistema de Notificações
- **Firebase FCM**: Push notifications profissionais
- Alertas automáticos baseados em níveis configurados

## 🏗️ Arquitetura Refatorada

### Estrutura do Projeto
```
crypto_analyser/
├── app.py                          # Aplicação principal
├── src/
│   ├── config/
│   │   └── settings.py            # Configurações centralizadas
│   ├── models/
│   │   └── crypto_data.py         # Modelos de dados
│   ├── repositories/
│   │   └── crypto_repository.py   # Camada de dados (queries)
│   ├── services/
│   │   ├── crypto_service.py      # Regras de negócio
│   │   ├── notification_service.py # Lógica de notificações
│   │   └── fcm_service.py         # Firebase FCM
│   ├── controllers/
│   │   ├── crypto_controller.py   # Gatilhos HTTP
│   │   └── notification_controller.py
│   └── utils/
│       └── (utilitários removidos)

├── service-account.json           # Credenciais Firebase
└── google-services.json          # Configuração Firebase
```

### Princípios Aplicados
- **Separação de Responsabilidades**: Cada camada tem uma função específica
- **Inversão de Dependência**: Services dependem de abstrações
- **Single Responsibility**: Cada classe tem uma única responsabilidade
- **Clean Architecture**: Camadas bem definidas
- **Configuration Management**: Configurações centralizadas

## 🔧 Configuração

### Dependências
```bash
pip install -r requirements.txt
```

### Execução
```bash
python app.py
```

## 📡 Endpoints da API

- `GET /` - Informações da API
- `GET /prices` - Todos os preços
- `GET /prices/btc` - Preço do Bitcoin
- `GET /prices/eth` - Preço do Ethereum  
- `GET /prices/simple` - Preços simplificados
- `GET /display` - Visualização ASCII
- `GET /alerts` - Configuração dos alertas
- `POST /fcm/send-to-topic` - Enviar FCM para tópico

- `GET /status` - Status da conexão

## 📱 Configuração de Notificações

### Firebase FCM (Avançado)
1. Configure `service-account.json` com suas credenciais
2. Subscreva no tópico `crypto_alerts` no seu app
3. Receba push notifications profissionais

## ⚡ Níveis de Alerta (Configuráveis no código)

- **BTC**: Alerta abaixo de R$ 610.000 ou acima de R$ 630.000
- **ETH**: Alerta abaixo de R$ 15.000 ou acima de R$ 20.000

## 🎯 Uso

O sistema inicia automaticamente e:
1. Conecta à API REST da Binance
2. Monitora preços em tempo real
3. Envia notificações formatadas a cada 10 minutos (configurável)
4. Disponibiliza API REST em `http://localhost:5000`

**Sistema limpo, focado e funcional!** 🎉
