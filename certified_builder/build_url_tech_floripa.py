from config import config


def build_url_tech_floripa(solana_response: dict, validation_code: str, order_id: str) -> str:
    try:
        base_url = config.TECH_FLORIPA_CERTIFICATE_VALIDATE_URL

        url_service_solona = solana_response.get("blockchain", {}).get("verificacao_url", "")
        registered_time = solana_response.get("certificado", {}).get("time", "")
        registered_uuid = solana_response.get("certificado", {}).get("uuid", "")
        registered_name = solana_response.get("certificado", {}).get("name", "")

        txid_solana = url_service_solona.rsplit("/", 1)[-1] if url_service_solona else ""

        full_url = (
            f"{base_url}?validate_code={validation_code}"
            f"&hash={txid_solana}"
            f"&order_id={order_id}"
            f"&registered_time={registered_time}"
            f"&registered_uuid={registered_uuid}"
            f"&registered_name={registered_name}"
        )
        return full_url
    except Exception as e:
        raise ValueError(f"Error building Tech Floripa URL: {str(e)}")