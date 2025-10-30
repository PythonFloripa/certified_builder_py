import pytest
from unittest.mock import patch, MagicMock
from certified_builder.certificates_on_solana import CertificatesOnSolana, CertificatesOnSolanaException
from certified_builder import certificates_on_solana as module_under_test


@pytest.fixture
def sample_payload():
    return {
        "name": "User Test",
        "event": "Evento X",
        "email": "user@example.com",
        "certificate_code": "ABC-123-XYZ",
    }


def test_register_certificate_success(sample_payload, monkeypatch):
    # Configura URLs/chaves do módulo
    monkeypatch.setattr(module_under_test.config, "SERVICE_URL_REGISTRATION_API_SOLANA", "https://api.test/solana")
    monkeypatch.setattr(module_under_test.config, "SERVICE_API_KEY_REGISTRATION_API_SOLANA", "secret-key")

    # Mock do client httpx
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "blockchain": {"verificacao_url": "https://verify"}}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.__exit__.return_value = False

    with patch("certified_builder.certificates_on_solana.httpx.Client", return_value=mock_client_instance) as mock_client_cls:
        result = CertificatesOnSolana.register_certificate_on_solana(sample_payload)

        # Retorno
        assert result["ok"] is True
        assert result["blockchain"]["verificacao_url"] == "https://verify"

        # Chamada correta
        mock_client_cls.assert_called_once()
        mock_client_instance.post.assert_called_once()
        call_kwargs = mock_client_instance.post.call_args.kwargs
        assert call_kwargs["url"] == "https://api.test/solana"
        assert call_kwargs["headers"]["x-api-key"] == "secret-key"
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        assert call_kwargs["json"] == sample_payload


def test_register_certificate_http_error_raises(sample_payload, monkeypatch):
    monkeypatch.setattr(module_under_test.config, "SERVICE_URL_REGISTRATION_API_SOLANA", "https://api.test/solana")
    monkeypatch.setattr(module_under_test.config, "SERVICE_API_KEY_REGISTRATION_API_SOLANA", "secret-key")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"ok": False}

    # raise_for_status levanta erro
    def _raise():
        raise Exception("boom")
    mock_response.raise_for_status.side_effect = _raise

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.__exit__.return_value = False

    with patch("certified_builder.certificates_on_solana.httpx.Client", return_value=mock_client_instance):
        with pytest.raises(CertificatesOnSolanaException) as exc:
            CertificatesOnSolana.register_certificate_on_solana(sample_payload)

        assert "boom" in str(exc.value.details)


