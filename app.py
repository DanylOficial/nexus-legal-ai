import eel
import os
import re
import json
import urllib.request
import customtkinter as ctk
from tkinter import filedialog
from groq import Groq
from pypdf import PdfWriter, PdfReader
import docx
from datetime import datetime

VERSAO_ATUAL = "3.0.0"

# CONFIGURAÇÃO DO JSONBIN.IO (PROTEGIDO)
BIN_ID = "6ac88e47ffd5d160535b5554"
# COLA A TUA MASTER KEY DO JSONBIN.IO ABAIXO:
API_KEY_JSONBIN = "$2a$10$JJqyhVKyW.87HvGUBz9xy.sk3tuIeqyuY8oio2G9tldfvPH05K7S6"

# Variáveis Globais de Sessão
pasta_selecionada = ""
api_key_injetada = ""
usuario_logado = ""
plano_usuario = ""

# Inicializa o Eel a apontar para a pasta web
eel.init('web')


# --- 1. AUTENTICAÇÃO REMOTA (JSONBIN.IO) ---
@eel.expose
def autenticar_usuario_py(user, password):
    global api_key_injetada, usuario_logado, plano_usuario
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
        req = urllib.request.Request(
            url, 
            headers={
                'X-Master-Key': API_KEY_JSONBIN,
                'User-Agent': 'Mozilla/5.0'
            }
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            resposta = json.loads(response.read().decode('utf-8'))
            dados = resposta.get("record", {})
            
            api_key_injetada = dados.get("groq_api_key_global", "")
            usuarios = dados.get("usuarios", [])

            usuario_encontrado = None
            for u in usuarios:
                if u["login"] == user and u["senha"] == password:
                    usuario_encontrado = u
                    break

            if not usuario_encontrado:
                return {"sucesso": False, "mensagem": "Usuário ou senha incorretos."}

            if not usuario_encontrado.get("ativo", False):
                return {"sucesso": False, "mensagem": "Acesso suspenso. Contate o administrador."}

            exp_str = usuario_encontrado.get("expiracao", "2000-01-01")
            data_exp = datetime.strptime(exp_str, "%Y-%m-%d")
            if datetime.now() > data_exp:
                return {"sucesso": False, "mensagem": f"Plano expirado em {exp_str}."}

            usuario_logado = usuario_encontrado["login"]
            plano_usuario = usuario_encontrado.get("plano", "Padrão")

            return {
                "sucesso": True, 
                "user": usuario_logado, 
                "plano": plano_usuario,
                "expiracao": exp_str
            }

    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro de conexão: {e}"}


# --- 2. SELEÇÃO DE PASTA DO CLIENTE ---
@eel.expose
def selecionar_pasta_py():
    global pasta_selecionada
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    pasta = filedialog.askdirectory(master=root)
    root.destroy()
    if pasta:
        pasta_selecionada = pasta
        return pasta
    return ""


# --- 3. MOTOR DE TRIAGEM JURÍDICA E AGRUPAMENTO PJe ---
@eel.expose
def processar_arquivos_py(acao):
    global pasta_selecionada, api_key_injetada
    try:
        if not pasta_selecionada:
            eel.atualizarLogJS("❌ Erro: Selecione a pasta do cliente primeiro!")()
            return

        if not api_key_injetada:
            eel.atualizarLogJS("❌ Erro de Autenticação: Chave da API não carregada.")()
            return

        client = Groq(api_key=api_key_injetada)
        nome_cliente = os.path.basename(pasta_selecionada)
        pasta_destino = os.path.join(os.path.dirname(pasta_selecionada), f"{nome_cliente}_ORGANIZADO")
        os.makedirs(pasta_destino, exist_ok=True)

        eel.atualizarLogJS(f"⚖️ Análise Jurídica para Ação de '{acao}' ({nome_cliente})...")()
        
        arquivos_pdf = []
        for raiz, _, arquivos in os.walk(pasta_selecionada):
            for arq in arquivos:
                if arq.lower().endswith('.pdf'):
                    arquivos_pdf.append(os.path.join(raiz, arq))

        if not arquivos_pdf:
            eel.atualizarLogJS("❌ Nenhum arquivo PDF encontrado na pasta.")()
            return

        classificacoes = {}
        total = len(arquivos_pdf)

        TERMOS_PROVA_RURAL = [
            "ELEITORAL", "CASAMENTO", "BOLETIM", "SINDICAL", "SINDICATO", 
            "PARCERIA", "DECLARACAO_RURAL", "ALISTAMENTO", "BATISMO", "CONTRATO",
            "FICHA", "CADASTRO", "PRONTUARIO", "CREDIARIO", "LOJA", "LEOLAR",
            "CNIS", "EXTRATO_CNIS", "TERRA", "ITR", "CCIR", "CAR", "ESCRITURA",
            "PRONAF", "COMODATO", "MATRICULA", "MATRICULA_ESCOLAR", "POSTINHO", "SAUDE"
        ]

        TERMOS_DOCUMENTO_FORMAL = [
            "PROTOCOLO", "COMPROVANTE DE REQUERIMENTO", "PROCURACAO", "PROCURAÇÃO",
            "HIPOSSUFICIENCIA", "INDEFERIMENTO", "COMUNICADO DE DECISAO",
            "RESIDENCIA", "RG", "CPF", "IDENTIDADE", "DOCS_TESTEMUNHO"
        ]

        for idx, caminho in enumerate(sorted(arquivos_pdf), 1):
            nome_arq_orig = os.path.basename(caminho)
            nome_sem_ext = os.path.splitext(nome_arq_orig)[0].upper()
            nome_limpo_base = re.sub(r'(\bANO\b\s*\d{4}\s*[-_]*)+', '', nome_sem_ext, flags=re.IGNORECASE).strip()
            nome_limpo_base = re.sub(r'[:\\/*?\"<>|]', '', nome_limpo_base).strip()

            eel.atualizarLogJS(f"📖 [{idx}/{total}] Examinando: {nome_arq_orig}...")()

            texto_extraido = ""
            try:
                reader = PdfReader(caminho)
                for i, page in enumerate(reader.pages[:3]):
                    t = page.extract_text()
                    if t:
                        texto_extraido += f"\n--- PÁGINA {i+1} ---\n" + t
            except Exception:
                texto_extraido = ""

            anos_encontrados = re.findall(r'\b(19\d\d|20\d\d)\b', nome_sem_ext + " " + texto_extraido)
            ano_historico = int(anos_encontrados[0]) if anos_encontrados else None

            eh_formal_obrigatorio = any(term in nome_limpo_base for term in TERMOS_DOCUMENTO_FORMAL)
            eh_prova_confirmada = any(term in nome_limpo_base for term in TERMOS_PROVA_RURAL)

            prompt = f"""
            Atue como um Advogado Previdenciarista especialista no PJe.
            Classifique o documento abaixo para a Ação de '{acao}'.

            NOME DO ARQUIVO: {nome_arq_orig}
            CONTEÚDO DO PDF:
            {texto_extraido[:2000]}

            INSTRUÇÕES:
            1. "is_prova_rural": true -> Início de Prova Material Rural.
            2. "is_prova_rural": false -> Documentos formais (Procuração, RG/CPF, Comprovante Residência, Indeferimento, Protocolos).

            FORMATO DE RESPOSTA APENAS EM JSON:
            {{
              "titulo": "TITULO LIMPO EM CAIXA ALTA",
              "is_prova_rural": true_ou_false
            }}
            """

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                resultado = json.loads(response.choices[0].message.content)
                titulo = resultado.get("titulo", nome_limpo_base)
                is_prova = bool(resultado.get("is_prova_rural", False))
            except Exception:
                titulo = nome_limpo_base
                is_prova = eh_prova_confirmada

            if eh_formal_obrigatorio:
                is_prova = False
            elif eh_prova_confirmada:
                is_prova = True

            titulo_final = re.sub(r'[:\\/*?\"<>|]', '', str(titulo)).strip()
            titulo_final = re.sub(r'(\bANO\b\s*\d{4}\s*[-_]*)+', '', titulo_final, flags=re.IGNORECASE).strip()

            chave_grupo = f"{titulo_final}_{ano_historico if (ano_historico and is_prova) else 'FORMAL'}"
            if chave_grupo not in classificacoes:
                classificacoes[chave_grupo] = {
                    "arquivos": [],
                    "titulo": titulo_final,
                    "ano": ano_historico if is_prova else None,
                    "is_prova": is_prova
                }
            classificacoes[chave_grupo]["arquivos"].append(caminho)

            tag = "🌾 [PROVA MATERIAL RURAL]" if is_prova else "📄 [DOC IDENTIFICAÇÃO/FORMAL]"
            str_ano_log = f" (ANO {ano_historico})" if (ano_historico and is_prova) else ""
            eel.atualizarLogJS(f"   ➔ {tag} {titulo_final}{str_ano_log}")()

        formais = [g for g in classificacoes.values() if not g["is_prova"]]
        provas = sorted([g for g in classificacoes.values() if g["is_prova"]], key=lambda x: (x["ano"] if x["ano"] is not None else 9999, x["titulo"]))

        for g in formais:
            writer = PdfWriter()
            nome_arquivo_pje = f"{g['titulo']}.pdf"
            caminho_final = os.path.join(pasta_destino, nome_arquivo_pje)

            for arq in g["arquivos"]:
                try:
                    reader = PdfReader(arq)
                    for page in reader.pages:
                        writer.add_page(page)
                except Exception:
                    pass

            with open(caminho_final, "wb") as f_out:
                writer.write(f_out)

            eel.atualizarLogJS(f"✅ Doc Formal Gerado: {nome_arquivo_pje}")()

        contador_provas = 1
        for g in provas:
            writer = PdfWriter()
            str_ano = f" - ANO {g['ano']}" if g['ano'] is not None else ""
            nome_arquivo_pje = f"{contador_provas:02d}.{g['titulo']}{str_ano}.pdf"
            caminho_final = os.path.join(pasta_destino, nome_arquivo_pje)

            for arq in g["arquivos"]:
                try:
                    reader = PdfReader(arq)
                    for page in reader.pages:
                        writer.add_page(page)
                except Exception:
                    pass

            with open(caminho_final, "wb") as f_out:
                writer.write(f_out)

            eel.atualizarLogJS(f"🌾 Prova Rural Gerada: {nome_arquivo_pje}")()
            contador_provas += 1

        eel.atualizarLogJS(f"\n🎉 TRIAGEM JURÍDICA CONCLUÍDA!\nArquivos salvos em: {pasta_destino}")()

    except Exception as e:
        eel.atualizarLogJS(f"❌ Erro na triagem: {e}")()


# --- 4. GERADOR DE MINUTA .DOCX (TEXTO FIEL DO ESCRITÓRIO) ---
@eel.expose
def gerar_minuta_py(opcao_selecionada):
    global pasta_selecionada, api_key_injetada
    try:
        if not pasta_selecionada or not api_key_injetada:
            return "Erro: Selecione a pasta do cliente e verifique a autenticação."

        nome_cliente = os.path.basename(pasta_selecionada)
        pasta_organizada = os.path.join(os.path.dirname(pasta_selecionada), f"{nome_cliente}_ORGANIZADO")

        if not os.path.exists(pasta_organizada):
            return f"Atenção: Execute primeiro a Triagem da pasta para gerar os documentos organizados."

        client = Groq(api_key=api_key_injetada)
        todos_arquivos = os.listdir(pasta_organizada)
        provas_rurais_ordenadas = sorted([
            f for f in todos_arquivos 
            if f.lower().endswith('.pdf') and re.match(r'^\d{2}\.', f)
        ])

        if not provas_rurais_ordenadas:
            provas_rurais_ordenadas = sorted([f for f in todos_arquivos if f.lower().endswith('.pdf')])

        if opcao_selecionada == "Pensão por Morte Rural":
            texto_historia_base = f"""DOS FATOS

Excelência, a Requerente faz jus ao benefício de Pensão por Morte Rural em razão do falecimento de seu(sua) (PARENTESCO/VÍNCULO: CÔNJUGE / COMPANHEIRO / GENITOR), o(a) Sr.(a) (NOME DO FALECIDO/SEGURADO ESPECIAL), ocorrido no dia (DATA DO ÓBITO), conforme certidão de óbito em anexo.

A Requerente dirigiu-se ao INSS e fez seu pedido administrativo no dia (COLOCAR DATA), contudo o benefício foi indevidamente indeferido.

Inconformada com a negativa do INSS, a Autora faz uso da presente tutela jurisdicional a fim de ter o seu direito garantido.

A verdade é que tanto a Requerente quanto o(a) falecido(a) exerceram a profissão de lavrador(a)/agricultor(a) desde a juventude, tendo nascido, se criado e sempre residido em meio rural.

Em todas as localidades onde residiram, o casal sempre exerceu trabalhos tipicamente rurais, como o plantio de milho, mandioca, feijão, abóbora, cultivo de hortaliças e criação de animais, sem qualquer tipo de remuneração ou compensação financeira, praticando as atividades apenas para a subsistência de sua família.

Portanto, cumpre ressaltar que o(a) de cujos esteve filiado(a) à Previdência Social na qualidade de segurado(a) especial (trabalhador(a) rural) até a data de seu falecimento.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural e da qualidade de segurado especial:"""

        elif opcao_selecionada == "Salário-Maternidade Rural":
            texto_historia_base = f"""DOS FATOS

Excelência, a Requerente faz jus à concessão do benefício de Salário-Maternidade Rural em razão do nascimento/adoção de seu(sua) filho(a), ocorrido no dia (DATA DE NASCIMENTO DA CRIANÇA), conforme certidão em anexo.

A Requerente dirigiu-se ao INSS e efetuou o requerimento administrativo no dia (COLOCAR DATA), contudo o pedido foi indeferido sob a alegação de não comprovação da qualidade de segurada especial.

Inconformada com a negativa do INSS, a Autora faz uso da presente tutela jurisdicional a fim de ter o seu direito garantido.

A verdade é que a Autora exerce a profissão de lavradora/agricultora desde a juventude, tendo nascido, se criado e sempre residido em meio rural.

Durante todo o período de carência que antecedeu o parto, a Requerente sempre exerceu trabalhos tipicamente rurais, como o plantio de milho, mandioca, feijão, abóbora, cultivo de hortaliças e criação de animais, sem qualquer tipo de remuneração ou compensação financeira, praticando as atividades apenas para a subsistência de sua família.

Portanto, resta plenamente comprovada a qualidade de segurada especial (trabalhadora rural) da Requerente no período exigido por lei.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural:"""

        else:
            # TEXTO EXATO DA APOSENTADORIA RURAL POR IDADE
            texto_historia_base = f"""DOS FATOS

Excelência, ao completar os requisitos para a concessão do benefício de Aposentadoria Rural por idade, a Autora se dirigiu ao INSS e fez seu pedido administrativo no dia (COLOCAR DATA), contudo foi indeferido.

Inconformada com a negativa do INSS, a Autora faz uso da presente tutela jurisdicional a fim de ter o seu direito garantido.

A verdade é que a Autora exerce a profissão de lavradora/agricultora desde a juventude, tendo nascido, se criado e sempre residido em meio rural.

Em todas as localidades onde residiu, a Requerente sempre exerceu trabalhos tipicamente rurais, como o plantio de milho, mandioca, feijão, abóbora, cultivo de hortaliças e criação de animais, sem qualquer tipo de remuneração ou compensação financeira, praticando as atividades apenas para a subsistência de sua família.

Portanto, cumpre ressaltar que a Autora esteve filiada à Previdência Social na qualidade de segurado especial (trabalhadora rural) durante todo o seu histórico laboral, visto que nasceu e se criou na roça.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural:"""

        prompt = f"""
        Examine a lista de arquivos de PROVAS RURAIS ORGANIZADAS abaixo e monte APENAS a lista numerada em ORDEM CRONOLÓGICA.

        ARQUIVOS ORGANIZADOS:
        {json.dumps(provas_rurais_ordenadas, ensure_ascii=False)}

        FORMATO DE RESPOSTA EXATO (Apenas a lista numerada, sem saudações):
        1. [NOME LIMPO DO DOCUMENTO] - ANO [XXXX]: [Qualificação objetiva do indício de prova rural].
        2. [NOME LIMPO DO DOCUMENTO] - ANO [XXXX]: [Qualificação objetiva do indício de prova rural].
        """

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            lista_provas_gerada = response.choices[0].message.content.strip()
        except Exception:
            lista_provas_gerada = "\n".join([f"{idx+1}. {doc}" for idx, doc in enumerate(provas_rurais_ordenadas)])

        texto_completo = f"{texto_historia_base}\n\n{lista_provas_gerada}"

        caminho_docx = os.path.join(pasta_organizada, f"_DOS_FATOS_{nome_cliente}.docx")
        doc = docx.Document()
        doc.add_heading(f"DOS FATOS - CLIENTE: {nome_cliente}", level=1)
        for linha in texto_completo.split("\n"):
            if linha.strip():
                doc.add_paragraph(linha.strip())
        doc.save(caminho_docx)

        return texto_completo

    except Exception as e:
        return f"Erro ao gerar minuta: {e}"

# --- 5. DIAGNÓSTICO DE ADMISSIBILIDADE ---
@eel.expose
def validar_admissibilidade_py():
    global pasta_selecionada
    try:
        if not pasta_selecionada:
            return {
                "sucesso": False,
                "checklist": "🔴 Selecione a pasta do cliente primeiro!",
                "score": "0%",
                "parecer": "Selecione uma pasta para avaliar os requisitos."
            }

        nome_cliente = os.path.basename(pasta_selecionada)
        pasta_organizada = os.path.join(os.path.dirname(pasta_selecionada), f"{nome_cliente}_ORGANIZADO")
        
        arquivos = [f.upper() for f in os.listdir(pasta_selecionada)]
        if os.path.exists(pasta_organizada):
            arquivos += [f.upper() for f in os.listdir(pasta_organizada)]

        texto_arquivos_juntos = " ".join(arquivos)

        requisitos = {
            "PROCURAÇÃO E DECLARAÇÃO": any(k in texto_arquivos_juntos for k in ["PROCURACAO", "PROCURAÇÃO", "DECLARACAO", "HIPOSSUFICIENCIA"]),
            "INDEFERIMENTO ADMINISTRATIVO (INSS)": any(k in texto_arquivos_juntos for k in ["INDEFERIMENTO", "DECISAO", "COMUNICADO", "DESPACHO", "INSS", "NEGATIVA"]),
            "RG E CPF DA REQUERENTE": any(k in texto_arquivos_juntos for k in ["RG", "CPF", "IDENTIFICACAO", "IDENTIDADE", "DOC"]),
            "COMPROVANTE DE RESIDÊNCIA RURAL": any(k in texto_arquivos_juntos for k in ["RESIDENCIA", "ENDERECO", "COMPROVANTE", "LUZ", "TALÃO"]),
            "INÍCIO DE PROVA MATERIAL RURAL": any(k in texto_arquivos_juntos for k in ["CASAMENTO", "NASCIMENTO", "ELEITORAL", "BOLETIM", "SINDICAL", "CARTEIRA", "CTPS", "RURAL", "ANO"])
        }

        chk_str = ""
        itens_presentes = 0

        for doc, presente in requisitos.items():
            if presente:
                chk_str += f"🟢 [ OK ] {doc}\n"
                itens_presentes += 1
            else:
                chk_str += f"🔴 [PENDENTE] {doc}\n"

        score_val = int((itens_presentes / len(requisitos)) * 100)

        if score_val == 100:
            parecer_txt = "✅ PROCESSO APTO PARA PROTOCOLO!\n\nTodos os requisitos formais foram identificados."
        elif score_val >= 70:
            parecer_txt = "⚠️ PROTOCOLO COM RESSALVAS\n\nPossui conjunto probatório, mas anexe os itens faltantes para evitar emendas."
        else:
            parecer_txt = "🚫 PROCESSO INAPTO\n\nFaltam documentos indispensáveis para o protocolo."

        return {
            "sucesso": True,
            "checklist": chk_str,
            "score": f"📊 Score: {score_val}%",
            "parecer": parecer_txt
        }

    except Exception as e:
        return {
            "sucesso": False,
            "checklist": f"Erro: {e}",
            "score": "0%",
            "parecer": "Não foi possível validar."
        }

# --- INICIALIZAÇÃO DO APLICATIVO WEB DESKTOP ---
if __name__ == '__main__':
    # Abre a janela do aplicativo com a interface HTML5/CSS3
    eel.start('index.html', size=(1080, 820), port=0)