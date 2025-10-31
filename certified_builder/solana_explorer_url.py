def extract_solana_explorer_url(solana_response: dict) -> str:
    # alteração: extrai a URL do explorer do bloco "blockchain" conforme contrato oficial
    explorer_url = solana_response.get("blockchain", {}).get("explorer_url", "")
    return explorer_url


