import os
import json
import re
import mimetypes
import base64
from groq import Groq
from pypdf import PdfWriter, PdfReader

# Sua Chave de API do Groq
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

PASTA_ENTRADA = "./PARA_PROCESSAR"
PASTA_SAIDA = "./PROCESSADOS_PRONTOS"

def limpar_nome_arquivo(nome):
    """Remove caracteres proibidos no Windows"""
    nome = re.sub(r'[/\\:*?"<>|]', '_', nome)
    nome = re.sub(r'\s+', '_', nome)
    return nome.strip('_')

def converter_para_base64(caminho_arquivo):
    with open(caminho_arquivo, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def classificar_com_groq(caminho_arquivo):
    """Analisa o documento detalhadamente com foco no nome do titular/casal e data"""
    nome_arquivo = os.path.basename(caminho_arquivo)
    nome_upper = nome_arquivo.upper()

    anos = re.findall(r'\b(19\d\d|20\d\d)\b', nome_upper)
    ano_detectado = int(anos[0]) if anos else 0

    mime_type, _ = mimetypes.guess_type(caminho_arquivo)
    
    # Classificação local por nome para não juntar pessoas diferentes
    if not mime_type or not mime_type.startswith('image/'):
        titular_especifico = "REQUERENTE"
        if "FALECIDO" in nome_upper or "ESPOSO" in nome_upper:
            titular_especifico = "FALECIDO"
        elif "FILHO" in nome_upper or "FILHA" in nome_upper:
            titular_especifico = "FILHO"

        # Extrai o nome da pessoa no arquivo para separar individualmente
        match_nome = re.search(r'(FILH[AO]|REQUERENTE|FALECIDO)\s+([A-Z\s]+)', nome_upper)
        detalhe_pessoa = match_nome.group(0).strip() if match_nome else titular_especifico

        e_rural = "SIM" if any(r in nome_upper for r in ["LAVRADOR", "RURAL", "AGRICULTOR", "BOLETIM", "ELEITORAL"]) else "NAO"

        categoria = "DOCUMENTO_GERAL"
        if "CASAMENTO" in nome_upper: categoria = "CERTIDAO_CASAMENTO"
        elif "NASC" in nome_upper: categoria = "CERTIDAO_NASCIMENTO"
        elif "OBITO" in nome_upper: categoria = "CERTIDAO_OBITO"
        elif "RESIDENCIA" in nome_upper: categoria = "COMPROVANTE_RESIDENCIA"
        elif "TRABALHO" in nome_upper or "CTPS" in nome_upper: categoria = "CARTEIRA_TRABALHO"
        elif "RG" in nome_upper or "CPF" in nome_upper: categoria = "DOCUMENTO_IDENTIFICACAO"
        elif "CNIS" in nome_upper: categoria = "CNIS"
        elif "PROCURACAO" in nome_upper: categoria = "PROCURACAO"

        return {
            "categoria": categoria,
            "titular_id": detalhe_pessoa,
            "ano": ano_detectado,
            "e_prova_material": e_rural,
            "detalhe": "Extraído da estrutura do arquivo"
        }

    try:
        base64_image = converter_para_base64(caminho_arquivo)
        prompt = """
        Analise o documento e retorne APENAS um JSON:
        {
            "categoria": "CERTIDAO_CASAMENTO" | "CERTIDAO_NASCIMENTO" | "CERTIDAO_OBITO" | "COMPROVANTE_RESIDENCIA" | "DOCUMENTO_IDENTIFICACAO" | "OUTROS",
            "titular_id": "Nome do Titular ou Casal constante no documento",
            "ano": 1997,
            "e_prova_material": "SIM" ou "NAO",
            "detalhe": "Profissão ou fato comprovado"
        }
        """

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception:
        return {
            "categoria": "DOCUMENTO_GERAL",
            "titular_id": nome_arquivo,
            "ano": ano_detectado,
            "e_prova_material": "NAO",
            "detalhe": "Não classificado via visão"
        }

def processar_cliente():
    os.makedirs(PASTA_ENTRADA, exist_ok=True)
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    clientes = [d for d in os.listdir(PASTA_ENTRADA) if os.path.isdir(os.path.join(PASTA_ENTRADA, d))]

    if not clientes:
        print(f"⚠️ Nenhuma pasta em '{PASTA_ENTRADA}'.")
        return

    for cliente in clientes:
        caminho_cliente = os.path.join(PASTA_ENTRADA, cliente)
        pasta_destino_cliente = os.path.join(PASTA_SAIDA, cliente)
        os.makedirs(pasta_destino_cliente, exist_ok=True)

        print("\n==========================================")
        print(f"🚀 PROCESSANDO CLIENTE: {cliente}")
        print("==========================================")

        agrupados = {}

        for raiz, _, arquivos in os.walk(caminho_cliente):
            for arq in sorted(arquivos):
                if arq.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    caminho_arq = os.path.join(raiz, arq)
                    info = classificar_com_groq(caminho_arq)

                    # CHAVE DE AGRUPAMENTO ÚNICA: Garante que cada pessoa/certidão fique em arquivo próprio
                    chave_grupo = f"{info['categoria']}_{info['titular_id']}"

                    if chave_grupo not in agrupados:
                        agrupados[chave_grupo] = {
                            "arquivos": [],
                            "ano": info.get("ano", 0),
                            "categoria": info["categoria"],
                            "titular_id": info["titular_id"],
                            "e_prova_material": info.get("e_prova_material", "NAO"),
                            "detalhe": info.get("detalhe", "")
                        }

                    agrupados[chave_grupo]["arquivos"].append(caminho_arq)

        # Separa provas ordenáveis dos documentos gerais
        provas = [g for g in agrupados.values() if g["e_prova_material"] == "SIM" or g["ano"] > 0]
        gerais = [g for g in agrupados.values() if g not in provas]

        # Ordena provas da mais antiga para a mais recente
        provas_ordenadas = sorted(provas, key=lambda x: (x["ano"] if x["ano"] > 0 else 9999, x["categoria"]))

        print("\n🧩 Gerando arquivos com numeração discreta...")
        
        # 1. Salva Provas Numeradas estilo "01_", "02_"
        contador = 1
        for grupo in provas_ordenadas:
            writer = PdfWriter()
            str_ano = f"ANO_{grupo['ano']}" if grupo['ano'] > 0 else "S_DATA"
            
            nome_base = f"{contador:02d}_{grupo['categoria']}_{grupo['titular_id']}_{str_ano}"
            nome_limpo = limpar_nome_arquivo(nome_base) + ".pdf"
            caminho_final = os.path.join(pasta_destino_cliente, nome_limpo)

            for arq in grupo["arquivos"]:
                if arq.lower().endswith('.pdf'):
                    try:
                        reader = PdfReader(arq)
                        for page in reader.pages:
                            writer.add_page(page)
                    except Exception as e_pdf:
                        print(f"Erro ao ler PDF {arq}: {e_pdf}")

            with open(caminho_final, "wb") as f_saida:
                writer.write(f_saida)

            print(f"✅ Arquivo {contador:02d}: {nome_limpo} (Uniu {len(grupo['arquivos'])} folha(s))")
            contador += 1

        # 2. Salva Documentos Gerais sem numeração
        for grupo in gerais:
            writer = PdfWriter()
            str_ano = f"ANO_{grupo['ano']}" if grupo['ano'] > 0 else "S_DATA"

            nome_base = f"{grupo['categoria']}_{grupo['titular_id']}_{str_ano}"
            nome_limpo = limpar_nome_arquivo(nome_base) + ".pdf"
            caminho_final = os.path.join(pasta_destino_cliente, nome_limpo)

            for arq in grupo["arquivos"]:
                if arq.lower().endswith('.pdf'):
                    try:
                        reader = PdfReader(arq)
                        for page in reader.pages:
                            writer.add_page(page)
                    except Exception as e_pdf:
                        print(f"Erro ao ler PDF {arq}: {e_pdf}")

            with open(caminho_final, "wb") as f_saida:
                writer.write(f_saida)

            print(f"📄 Documento Geral: {nome_limpo}")

        print(f"\n🎉 Organização concluída com sucesso em: {pasta_destino_cliente}")

if __name__ == "__main__":
    processar_cliente()