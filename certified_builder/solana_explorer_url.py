def extract_solana_explorer_url(solana_response: dict) -> str:
    # alteração: função isolada para extrair a URL do explorer da resposta do serviço
    explorer_url = solana_response.get("explorer_url", "")
    return explorer_url


