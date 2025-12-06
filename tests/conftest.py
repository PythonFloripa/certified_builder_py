import sys
import types
import pytest


def _install_config_mock() -> None:
    """
    Instala um módulo falso chamado `config` antes dos imports dos testes.
    - Evita que `config.Config()` leia variáveis de ambiente no import.
    - Disponibiliza `config.config` com os campos usados no código.
    """

    # comentário: cria um módulo dinâmico chamado 'config'
    mock_module = types.ModuleType("config")

    class MockConfig:
        # comentário: valores estáveis para o ambiente de testes (sem dependências externas)
        REGION = "us-east-1"
        BUCKET_NAME = "test-bucket"
        QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/000000000000/test"
        SERVICE_URL_REGISTRATION_API_SOLANA = "https://example.test/solana/register"
        SERVICE_API_KEY_REGISTRATION_API_SOLANA = "test-api-key"
        # comentário: URL de validação mockada para o Tech Floripa usada nos testes
        TECH_FLORIPA_CERTIFICATE_VALIDATE_URL = (
            "https://example.test/certificate-validate/"
        )
        TECH_FLORIPA_LOGO_URL = "https://example.test/logo.png"

    # comentário: expõe tanto a classe quanto a instância, como o módulo real faria
    mock_module.Config = MockConfig
    mock_module.config = MockConfig()

    # comentário: injeta o módulo mock no sys.modules antes de qualquer import nos testes
    sys.modules["config"] = mock_module

    # debug estratégico para validar no log do CI
    print("[tests] Módulo 'config' mockado instalado para o ambiente de testes")


# comentário: instala o mock assim que o pytest carrega o conftest (antes dos testes)
_install_config_mock()


@pytest.fixture(autouse=True)
def _mock_solana_registration(monkeypatch, request):
    """
    Mocka a integração com o serviço de registro na Solana para todos os testes.
    - Evita chamadas HTTP reais.
    - Garante que o fluxo avance e permita assertivas como `save_certificate` ter sido chamada.
    """

    # comentário: não mockar no teste específico que valida o módulo certificates_on_solana
    try:
        test_file = str(request.node.fspath)
        if test_file.endswith("test_certificates_on_solana.py"):
            return
    except Exception:
        pass

    # comentário: resposta estável usada nos demais testes
    fake_response = {
        "blockchain": {"verificacao_url": "https://example.test/verify/abc123"}
    }

    # comentário: função fake substitui o método estático
    def _fake_register_certificate_on_solana(certificate_data: dict) -> dict:
        # debug estratégico para CI
        print("[tests] Mock CertificatesOnSolana.register_certificate_on_solana called")
        return fake_response

    # comentário: injeta o mock no alvo correto
    from certified_builder.certificates_on_solana import CertificatesOnSolana

    monkeypatch.setattr(
        CertificatesOnSolana,
        "register_certificate_on_solana",
        staticmethod(_fake_register_certificate_on_solana),
        raising=False,
    )
