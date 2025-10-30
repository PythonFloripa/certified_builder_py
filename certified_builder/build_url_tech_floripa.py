from config import config

def build_url_tech_floripa(url_service_solona: str, validation_code: str, order_id: str) -> str:
    try:
        txid_solana = url_service_solona.split('/')[-1]
        full_url = f"{config.TECH_FLORIPA_CERTIFICATE_VALIDATE_URL}?validate_code={validation_code}&hash={txid_solana}&order_id={order_id}"
        return full_url
    except Exception as e:
        raise ValueError(f"Error building Tech Floripa URL: {str(e)}")