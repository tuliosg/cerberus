import collections
import re
from itertools import permutations, combinations
from typing import Any, Dict, List, Tuple, Optional

import pympi

def _valida_regra(nome_trilha: str, regra: Dict[str, Any]) -> bool:
    """
    Função auxiliar para checar um nome de trilha contra uma regra específica.

    :param nome_trilha: O nome da trilha a ser validada.
    :type nome_trilha: str
    :param regra: Dicionário contendo o tipo ('type') e o valor ('value') da regra.
    :type regra: Dict[str, Any]
    :return: True se a trilha satisfaz a regra, False caso contrário.
    :rtype: bool
    """
    tipo_regra = regra.get("type")
    regra_valor = regra.get("value")

    if tipo_regra == "exato":
        return nome_trilha == regra_valor
    if tipo_regra == "comeca":
        return nome_trilha.startswith(regra_valor)
    if tipo_regra == "termina":
        return nome_trilha.endswith(regra_valor)
    if tipo_regra == "contem":
        return regra_valor in nome_trilha
    if tipo_regra == "regex":
        return re.fullmatch(regra_valor, nome_trilha) is not None
    
    return False

def valida_id_trilhas(eaf: pympi.Elan.Eaf, regras: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Dict[str, str]]]:
    """
    Valida as trilhas (tiers) de um objeto Eaf contra um conjunto de regras estruturais.

    Verifica a quantidade de trilhas, formatação (maiúsculas) e aplica regras de correspondência 
    permitindo trilhas opcionais e intervalos de quantidade.

    :param eaf: Objeto Eaf carregado via pympi.
    :type eaf: pympi.Elan.Eaf
    :param regras: Dicionário contendo configurações como 'num_trilhas', 'maiusculas' e 'regras_trilhas'.
    :type regras: Dict[str, Any]
    :return: Uma tupla contendo (Sucesso, ListaDeErros, MapeamentoDeConteudo).
    :rtype: Tuple[bool, List[str], Optional[Dict[str, str]]]
    """
    trilhas_presentes = list(eaf.get_tier_names())
    erros = []
    mapeamento_conteudo = None

    num_trilhas_esperado = regras.get("num_trilhas")
    num_trilhas_encontrado = len(trilhas_presentes)
    
    # Lógica de validação de quantidade flexível
    qtd_valida = True
    if num_trilhas_esperado is not None:
        if isinstance(num_trilhas_esperado, int):
            if num_trilhas_encontrado != num_trilhas_esperado:
                qtd_valida = False
        elif isinstance(num_trilhas_esperado, str):
            # Parser simples para operadores: >1, >=2, <5, etc.
            match = re.match(r'([<>]=?|==)?\s*(\d+)', num_trilhas_esperado)
            if match:
                op, val = match.groups()
                val = int(val)
                if op == '>' and not (num_trilhas_encontrado > val): qtd_valida = False
                elif op == '>=' and not (num_trilhas_encontrado >= val): qtd_valida = False
                elif op == '<' and not (num_trilhas_encontrado < val): qtd_valida = False
                elif op == '<=' and not (num_trilhas_encontrado <= val): qtd_valida = False
                elif (op == '==' or op is None) and not (num_trilhas_encontrado == val): qtd_valida = False
            else:
                erros.append(f"Formato de regra 'num_trilhas' inválido: {num_trilhas_esperado}")

    if not qtd_valida:
        erros.append(f"Número incorreto de trilhas. Esperado: {num_trilhas_esperado}, Encontrado: {num_trilhas_encontrado}.")
        erros.append(f"   Trilhas presentes: {trilhas_presentes}")
        
    if regras.get("maiusculas", False):
        for trilha in trilhas_presentes:
            if not trilha.isupper():
                erros.append(f"A trilha '{trilha}' não está em maiúsculas.")
    
    regras_trilhas = regras.get("regras_trilhas", [])
    if not regras_trilhas:
        return (not erros, erros, None)

    # Validar se há trilhas suficientes para cobrir as regras obrigatórias
    num_mandatorias = sum(1 for r in regras_trilhas if r.get("mandatory", True))
    if num_trilhas_encontrado < num_mandatorias:
        erros.append(f"Número de trilhas encontradas ({num_trilhas_encontrado}) é menor que o número de regras obrigatórias ({num_mandatorias}).")
        return (False, erros, None)

    # Lógica de Combinação + Permutação para suportar regras opcionais
    # Se temos 2 trilhas e 3 regras (1 opcional), precisamos achar qual subconjunto de 2 regras satisfaz as trilhas.
    
    permutacao_valida = False
    indices_regras = range(len(regras_trilhas))
    
    # Itera sobre todas as combinações de regras que tenham o mesmo tamanho das trilhas encontradas
    # Ex: Se achei 2 trilhas, testo todas as combinações de 2 regras disponíveis.
    for subset_indices in combinations(indices_regras, num_trilhas_encontrado):
        
        # Verifica se as regras que NÃO foram escolhidas são todas opcionais
        indices_ignorados = set(indices_regras) - set(subset_indices)
        regras_ignoradas_sao_opcionais = all(
            not regras_trilhas[idx].get("mandatory", True) for idx in indices_ignorados
        )
        
        if not regras_ignoradas_sao_opcionais:
            continue # Essa combinação ignorou uma regra obrigatória, então é inválida
            
        # Pega o subconjunto de regras para testar contra as trilhas
        subset_regras = [regras_trilhas[i] for i in subset_indices]
        
        # Aqui entra a lógica original de permutação para alinhar trilhas com as regras escolhidas
        for perm in permutations(trilhas_presentes):
            status_permutacao = True
            mapeamento_temp = {}
            
            for i, nome_trilha in enumerate(perm):
                rule = subset_regras[i]
                if not _valida_regra(nome_trilha, rule):
                    status_permutacao = False
                    break 
                
                content_type = rule.get("content_type")
                if content_type:
                    mapeamento_temp[nome_trilha] = content_type
            
            if status_permutacao:
                permutacao_valida = True
                mapeamento_conteudo = mapeamento_temp
                break 
        
        if permutacao_valida:
            break

    if not permutacao_valida:
        erros.append("Não foi encontrada uma combinação válida que satisfaça todas as regras de trilha (considerando obrigatórias/opcionais).")
        erros.append(f"   Trilhas Encontradas: {trilhas_presentes}")
        
    # Limpa erros se a permutação foi válida, mas erros de qtd/maiuscula podem persistir
    sucesso = permutacao_valida and not any(e for e in erros if "Número incorreto" in e or "maiúsculas" in e)
    
    # Se a permutação falhou, mantemos todos os erros. Se passou, limpamos erros espúrios de lógica anterior se houver.
    if permutacao_valida:
         # Filtra apenas erros que não sejam sobre a combinação
         erros = [e for e in erros if "combinação válida" not in e]

    return (sucesso, erros, mapeamento_conteudo if sucesso else None)
   
def _valida_conteudo_disf(valor: str) -> List[str]:
    """
    Valida o conteúdo de uma anotação de uma trilha DISF.

    :param valor: O texto da anotação.
    :type valor: str
    :return: Lista de códigos de erro encontrados.
    :rtype: List[str]
    """
    erros = []
    
    if valor == '(EST)' or valor == '(HES)':
        return [] 
        
    if re.fullmatch(r'\(\([A-Z\s]+\)\)', valor):
        return [] 
    
    if valor.upper() == '(EST)' or valor.upper() == '(HES)':
        erros.append("ERRO_DISF") # Disfluência fora do padrão
    
    elif re.fullmatch(r'\(\(.*\)\)', valor):
        erros.append("ERRO_DISF") # Disfluência fora do padrão
    
    else:
        erros.append("DISF_INVALIDA") # Conteúdo inválido
        
    return erros

def _valida_conteudo_inf_doc(valor: str) -> List[str]:
    """
    Valida o conteúdo de uma anotação do tipo INF ou DOC.

    Verifica presença de dígitos, disfluências mal posicionadas e caracteres inválidos.

    :param valor: O texto da anotação.
    :type valor: str
    :return: Lista de códigos de erro encontrados.
    :rtype: List[str]
    """
    erros = []
    
    if re.search(r'\d', valor):
        erros.append("DIGITO_PRESENTE") # Número encontrado
        
    if '(EST)' in valor or '(HES)' in valor or '((' in valor:
        erros.append("DISF_PRESENTE") # Disfluência em trilha errada
        
    hipoteses = re.findall(r'\((?!\s*\))([^)]+)\)', valor)
    for h in hipoteses:
        if h.upper() == 'EST' or h.upper() == 'HES':
            continue
            
        if h.strip() == '?':
            continue
            
        padrao_caracteres_invalidos = r'[^a-zA-Zá-úÁ-Ú\s\(\)\?\/\-"çÇàÀ-]'
        caracteres_invalidos = re.findall(padrao_caracteres_invalidos, valor)
    
    # Nota: o código original verificava caracteres_invalidos fora do loop, mantive a lógica
    padrao_caracteres_invalidos = r'[^a-zA-Zá-úÁ-Ú\s\(\)\?\/\-"çÇàÀ-]'
    caracteres_invalidos = re.findall(padrao_caracteres_invalidos, valor)
    
    if caracteres_invalidos:
        erros.append(f"CARACTERE_INVALIDO:{sorted(list(set(caracteres_invalidos)))}")
        
    return erros


def valida_conteudo_trilhas(eaf: pympi.Elan.Eaf, regras_mapeamento: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Valida o CONTEÚDO das anotações em um EAF com base em um mapeamento de regras.

    :param eaf: Objeto Eaf carregado.
    :type eaf: pympi.Elan.Eaf
    :param regras_mapeamento: Dicionário mapeando {nome_da_trilha: tipo_de_conteudo}.
                              Ex: {'Trilha1': 'INF', 'Trilha2': 'DISF'}
    :type regras_mapeamento: Dict[str, str]
    :return: Tupla contendo (Sucesso, ListaDeRelatorio).
    :rtype: Tuple[bool, List[str]]
    """
    
    erros_agrupados = collections.defaultdict(list)
    erros_globais = []
    
    trilhas_para_validar = regras_mapeamento.keys()
    
    for nome_trilha in trilhas_para_validar:
        tipo_regra = regras_mapeamento.get(nome_trilha)
        
        if nome_trilha not in eaf.get_tier_names():
            erros_globais.append(f"[Global] A trilha obrigatória '{nome_trilha}' não foi encontrada no arquivo.")
            continue 
            
        try:
            anotacoes = eaf.get_annotation_data_for_tier(nome_trilha)
        except KeyError:
            erros_globais.append(f"[Global] Erro ao tentar ler anotações da trilha '{nome_trilha}'.")
            continue

        for (inicio, fim, valor) in anotacoes: 
            if not valor or not valor.strip():
                continue
                
            valor_limpo = valor.strip()
            codigos_erro_anotacao = []
            
            loc_exemplo = f"[Tempo: {inicio/1000:.3f}s]"

            if tipo_regra == "INF" or tipo_regra == "DOC":
                codigos_erro_anotacao = _valida_conteudo_inf_doc(valor_limpo)
            
            elif tipo_regra == "DISF":
                codigos_erro_anotacao = _valida_conteudo_disf(valor_limpo)
            
            else:
                erros_globais.append(f"[Global] Tipo de regra desconhecido '{tipo_regra}' para a trilha '{nome_trilha}'.")
                break 

            if codigos_erro_anotacao:
                for codigo_erro in codigos_erro_anotacao:
                    chave_agrupamento = (codigo_erro, nome_trilha)
                    erros_agrupados[chave_agrupamento].append(loc_exemplo)

    relatorio_final = []
    relatorio_final.extend(erros_globais)
    
    for chave_agrupamento, exemplos in erros_agrupados.items():
        codigo_erro, nome_trilha = chave_agrupamento
        msg_final = ""

        # Mapeia códigos de erro para as mensagens formatadas
        if codigo_erro == "DIGITO_PRESENTE":
            msg_final = f"[Trilha: {nome_trilha}] [Erro: Número (dígito) encontrado na trilha]"

        elif codigo_erro == "DISF_PRESENTE":
            msg_final = f"[Trilha: {nome_trilha}] [Erro: Anotação de disfluência fora da trilha DISF]"

        elif codigo_erro == "DISF_INVALIDA":
            msg_final = f"[Trilha: {nome_trilha}] [Erro: Conteúdo inválido]"

        elif codigo_erro == "ERRO_DISF":
            msg_final = f"[Trilha: {nome_trilha}] [Erro: Disfluência fora do padrão]"

        elif codigo_erro.startswith("CARACTERE_INVALIDO:"):
            detalhes = codigo_erro.split(':', 1)[1]
            msg_final = f"[Trilha: {nome_trilha}] [Erro: Caracteres inválidos {detalhes}]"
        else:
            msg_final = f"[{codigo_erro} na trilha {nome_trilha}]" 

        exemplos_str = ", ".join(exemplos[:3])
        if len(exemplos) > 3:
            exemplos_str += f", e mais {len(exemplos) - 3}"
            
        relatorio_final.append(f"{msg_final} {exemplos_str}")
        
    return (not relatorio_final, relatorio_final)
