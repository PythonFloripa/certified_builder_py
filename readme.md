# Certified Builder Py

Sistema de geração automática de certificados para eventos usando AWS Lambda e Docker. O projeto gera certificados personalizados para participantes de eventos, processando mensagens do SQS e utilizando templates predefinidos. Os certificados incluem QR code para validação com logo [Tech Floripa](https://tech.floripa.br/) no centro e são registrados na blockchain Solana para autenticação.

## Funcionalidades

- Geração de certificados personalizados com:
  - Nome do participante em fonte estilizada
  - Código de validação único
  - Logo do evento
  - Detalhes do evento em três linhas centralizadas
  - QR Code para validação com logo Tech Floripa no centro
  - Registro na blockchain Solana para autenticação
- Processamento de mensagens SQS
- Execução em container Docker
- Deploy automatizado para AWS Lambda
- Integração com AWS ECR
- Envio de mensagens para fila de notificação com dados do certificado

## Estrutura do Projeto

```plaintext
project_root/
├── certified_builder/
│   ├── certified_builder.py    # Classe principal de geração de certificados
│   ├── make_qrcode.py          # Geração de QR codes com logo
│   ├── certificates_on_solana.py  # Integração com blockchain Solana
│   ├── solana_explorer_url.py  # Extração de URL do Solana Explorer
│   └── utils/
│       └── fetch_file_certificate.py  # Utilitário para download de imagens
├── models/
│   ├── participant.py          # Modelo de dados do participante
│   ├── certificate.py          # Modelo de dados do certificado
│   └── event.py               # Modelo de dados do evento
├── aws/
│   ├── sqs_service.py         # Serviço para envio de mensagens SQS
│   ├── s3_service.py          # Serviço para upload no S3
│   └── boto_aws.py            # Configuração do cliente AWS
├── fonts/
│   ├── PinyonScript/          # Fonte para o nome do participante
│   └── ChakraPetch/           # Fonte para detalhes e código de validação
├── tests/                     # Testes automatizados
├── lambda_function.py         # Handler da função Lambda
├── config.py                  # Configurações do projeto
├── Dockerfile                 # Configuração do container
└── requirements.txt           # Dependências do projeto
```

## Tecnologias Utilizadas

- Python 3.13
- Pillow (Processamento de imagens)
- httpx (Requisições HTTP)
- Pydantic (Validação de dados)
- qrcode (Geração de QR codes)
- Docker
- AWS Lambda
- AWS ECR
- AWS SQS
- [Solana Blockchain (Registro de certificados)](https://github.com/p4ndabk/certificates-on-solana)

## Formato da Mensagem SQS (Entrada)

A Lambda recebe mensagens do SQS com os dados dos participantes para gerar os certificados:

```json
{
  "participants": [
    {
      "first_name": "Nome",
      "last_name": "Sobrenome",
      "email": "email@exemplo.com",
      "phone": "(00) 00000-0000",
      "cpf": "000.000.000-00",
      "order_id": 123,
      "product_id": 456,
      "product_name": "Nome do Evento",
      "certificate_details": "Descrição do certificado em três linhas",
      "certificate_logo": "URL do logo",
      "certificate_background": "URL do template",
      "order_date": "2025-03-26 20:55:25",
      "checkin_latitude": "-27.5460492",
      "checkin_longitude": "-48.6227075",
      "time_checkin": "2025-03-26 20:55:44"
    }
  ]
}
```

## Formato da Mensagem SQS (Saída - Fila de Notificação)

Após a geração dos certificados, uma mensagem é enviada para outra fila SQS com os dados do certificado gerado:

```json
[
  {
    "order_id": 123,
    "validation_code": "ABC-DEF-GHI",
    "authenticity_verification_url": "https://explorer.solana.com/tx/...?cluster=devnet",
    "product_id": 456,
    "product_name": "Nome do Evento",
    "email": "email@exemplo.com",
    "certificate_key": "certificates/456/123/Nome_Sobrenome_Nome_do_Evento_ABC-DEF-GHI.png",
    "success": true
  }
]
```

### Campos da Mensagem de Saída

- **`order_id`**: ID do pedido/ordem
- **`validation_code`**: Código de validação do certificado (formato: XXX-XXX-XXX)
- **`authenticity_verification_url`**: URL do Solana Explorer para verificação na blockchain
- **`product_id`**: ID do produto/evento
- **`product_name`**: Nome do produto/evento
- **`email`**: Email do participante
- **`certificate_key`**: Chave do certificado no S3 (formato: `certificates/{product_id}/{order_id}/{nome_certificado}.png`)
- **`success`**: Indica se a geração foi bem-sucedida (true/false)

**Nota**: A mensagem é enviada como um array, podendo conter múltiplos certificados quando processados em lote.

## Desenvolvimento Local

### Pré-requisitos

- Docker
- Python 3.13+
- AWS CLI configurado

### Executando Localmente

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/certified_builder_py.git
cd certified_builder_py
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute com Docker:
```bash
docker build -t certified-builder . && docker run -p 9000:8080 certified-builder
```

4. Teste localmente:
```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test/mock.json
```

## Deploy

O deploy é automatizado através do GitHub Actions:

1. Push para a branch main dispara o workflow
2. Imagem Docker é construída
3. Upload para AWS ECR
4. Atualização da função Lambda

## Estrutura do Certificado Gerado

- **Logo do Evento**: Canto superior esquerdo (150x150 pixels máximo, redimensionado automaticamente)
- **Nome**: Centro do certificado (fonte Pinyon Script)
- **Detalhes**: Três linhas centralizadas abaixo do nome (fonte Chakra Petch)
- **QR Code**: Posicionado abaixo do logo (150x150 pixels) com logo Tech Floripa centralizado
  - Contém URL de validação com código único: `https://tech.floripa.br/certificate-validate/?validate_code=XXX-XXX-XXX`
  - Usa correção de erros nível H (30% redundância) para garantir leitura mesmo com logo
- **Texto "Scan to Validate"**: Abaixo do QR code, centralizado
- **Código de Validação**: Canto inferior direito (fonte Chakra Petch)

## Contribuindo

1. Fork o projeto
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

