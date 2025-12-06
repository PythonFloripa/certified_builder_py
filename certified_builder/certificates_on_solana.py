import logging
import httpx
from retry import retry
from pydantic import BaseModel
from config import config

logger = logging.getLogger(__name__)


class CertificatesOnSolanaException(Exception):
    """Custom exception for CertificatesOnSolana errors."""

    def __init__(
        self,
        message: str = "Error registering certificate on Solana",
        details: str = "",
        cause: Exception = None,
    ):
        super().__init__(message)
        self.details = details
        self.cause = cause


class CertificatesOnSolana:
    """
    A class to manage certificates on the Solana blockchain Service."""

    @staticmethod
    @retry(
        tries=3,
        delay=3,
        backoff=2,
        exceptions=(httpx.RequestError, CertificatesOnSolanaException, Exception),
        logger=logger,
    )
    def register_certificate_on_solana(certificate_data: dict) -> dict:
        logger.info(
            "Registering certificate on Solana blockchain with data: %s",
            certificate_data,
        )
        """
        Registers a certificate on the Solana blockchain.

        Args:
            certificate_data (dict): A dictionary containing certificate details.

        Returns:
            dict: A dictionary with the registration result.
        """
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    url=config.SERVICE_URL_REGISTRATION_API_SOLANA,
                    headers={
                        "x-api-key": config.SERVICE_API_KEY_REGISTRATION_API_SOLANA,
                        "Content-Type": "application/json",
                    },
                    json=certificate_data,
                )
                logger.info(f"Solana response status code: {response.status_code}")
                response.raise_for_status()
                solana_response = response.json()
                return solana_response
        except Exception as e:
            logger.error(f"Error registering certificate on Solana: {str(e)}")
            raise CertificatesOnSolanaException(details=str(e), cause=e)
