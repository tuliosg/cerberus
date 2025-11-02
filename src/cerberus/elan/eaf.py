import os
from typing import Optional, Union

import pympi


def abre_eaf(arquivo: Union[str, bytes], nome_arquivo: Optional[str] = None):
    """
    Abre um arquivo .eaf usando a biblioteca pympi.Elan. Se o arquivo for fornecido como bytes, decodifica-o para uma string UTF-8.

    Args:
        arquivo (Union[str, bytes]): O caminho para o arquivo .eaf ou o conteúdo do arquivo em bytes.
        nome_arquivo (Optional[str]): O nome do arquivo, se fornecido.

    Returns:
        pympi.Elan.Eaf: O objeto Eaf carregado.
        nome_arquivo (str): O nome do arquivo, se fornecido ou extraído do caminho.
    """
    if isinstance(arquivo, bytes):
        arquivo = arquivo.decode('utf-8')
    nome_arquivo = nome_arquivo if nome_arquivo else os.path.basename(arquivo)

    return nome_arquivo, pympi.Elan.Eaf(arquivo)