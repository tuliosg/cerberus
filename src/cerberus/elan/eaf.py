import os
import tempfile
from typing import Optional, Tuple, Union

import pympi


def abre_eaf(arquivo: Union[str, bytes], nome_arquivo: Optional[str] = None) -> Tuple[str, pympi.Elan.Eaf]:
    """
    Abre um arquivo .eaf usando a biblioteca pympi.Elan.
    Se o arquivo for 'bytes', salva em um arquivo temporário para leitura,
    pois o pympi não lida corretamente com streams em memória.
    """
    
    eaf_obj = None
    nome_final = None
    temp_file_path = None # Para armazenar o caminho do arquivo temporário

    try:
        if isinstance(arquivo, bytes):
            # 1. INPUT É BYTES (vindo do upload do Streamlit)
            if nome_arquivo is None:
                raise ValueError("O 'nome_arquivo' é obrigatório quando o 'arquivo' é fornecido como bytes.")
            
            nome_final = nome_arquivo
            
            # Cria um arquivo temporário com o sufixo .eaf
            # delete=False é crucial para que o pympi possa abri-lo pelo nome
            with tempfile.NamedTemporaryFile(suffix='.eaf', delete=False) as temp_f:
                temp_f.write(arquivo) # Escreve os bytes no arquivo temp
                temp_file_path = temp_f.name # Salva o caminho do arquivo temp
            
            # Agora passamos o CAMINHO do arquivo temp para o pympi
            eaf_obj = pympi.Elan.Eaf(temp_file_path)

        elif isinstance(arquivo, str):
            # 2. INPUT É STRING (tratamos como um caminho de arquivo)
            nome_final = nome_arquivo if nome_arquivo else os.path.basename(arquivo)
            
            eaf_obj = pympi.Elan.Eaf(arquivo)
        
        else:
            raise TypeError(f"Tipo de 'arquivo' não suportado: {type(arquivo)}")

        return nome_final, eaf_obj

    except Exception as e:
        # Relança o erro para o Streamlit capturar
        raise RuntimeError(f"Erro ao processar o arquivo {nome_final}: {e}")
        
    finally:
        # 3. Limpeza: Sempre apaga o arquivo temporário se ele foi criado
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)