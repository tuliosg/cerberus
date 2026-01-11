regras_entrevista = {
    "num_trilhas": 3, 
    "maiusculas": True,
    "regras_trilhas": [
        {"type": "exato", "value": "DISF", "content_type": "DISF"},
        {"type": "comeca", "value": "DOC", "content_type": "DOC"},
        {"type": "regex", "value": r"^[A-Z]+\d?[A-Z]+$", "content_type": "INF"}
    ]
}

regras_nomeacao = {
    "num_trilhas": 2,
    "maiusculas": False,
    "regras_trilhas": [
        {"type": "regex", "value": r"^[A-Z]+\d?[A-Z]+$", "content_type": "INF"},
        {"type": "regex", "value": r"^[A-Z]+\d{1}[A-Z]+$", "content_type": "INF"}
    ]
}