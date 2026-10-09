import os
import re
import json
import urllib.request
import mimetypes
import base64
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from groq import Groq
from pypdf import PdfWriter, PdfReader
import docx

# Versão do seu sistema local
VERSAO_ATUAL = "1.1.0"
# URL onde você hospedará o JSON de controle de versão (ex: GitHub Gist ou servidor)
URL_CHECAR_VERSAO = "https://raw.githubusercontent.com/DanylOficial/nexus-legal-ai/refs/heads/main/version.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_BG = "#0D1117"
COLOR_CARD = "#161B22"
COLOR_ACCENT_BLUE = "#1F6FE5"
COLOR_ACCENT_CYAN = "#00F2FE"
COLOR_SUCCESS = "#2EA043"
COLOR_DANGER = "#DA3633"
COLOR_WARNING = "#D29922"
COLOR_TEXT_MAIN = "#F0F6FC"
COLOR_TEXT_MUTED = "#8B949E"

class AppAdvocacia(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"NEXUS LEGAL AI - v{VERSAO_ATUAL} (Sistema Mãe & Automação Prev)")
        self.geometry("1000x780")
        self.configure(fg_color=COLOR_BG)

        self.pasta_selecionada = ""
        self.api_key = ctk.StringVar(value="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")
        self.tipo_processo = ctk.StringVar(value="Aposentadoria Rural por Idade")

        self.setup_header()

        self.tabview = ctk.CTkTabview(
            self, width=960, height=650, 
            fg_color=COLOR_CARD, 
            segmented_button_selected_color=COLOR_ACCENT_BLUE, 
            segmented_button_selected_hover_color="#1158C7"
        )
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_organizador = self.tabview.add("📁 1. Triagem & Unificação")
        self.tab_fatos = self.tabview.add("✍️ 2. Minuta de Fatos & Provas")
        self.tab_validador = self.tabview.add("🛡️ 3. Verificador de Admissibilidade")
        self.tab_central = self.tabview.add("⚙️ 4. Central de Atualizações")

        self.setup_aba_organizador()
        self.setup_aba_fatos()
        self.setup_aba_validador()
        self.setup_aba_central()

    def setup_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12)
        header_frame.pack(padx=20, pady=(15, 5), fill="x")

        lbl_logo = ctk.CTkLabel(header_frame, text="⚡ NEXUS LEGAL AI", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        lbl_logo.pack(side="left", padx=20, pady=12)

        lbl_sub = ctk.CTkLabel(header_frame, text=f"Engine Prev360 • v{VERSAO_ATUAL} • Módulo Central Ativo", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED)
        lbl_sub.pack(side="left", padx=10, pady=12)

        self.lbl_status_badge = ctk.CTkLabel(header_frame, text="● CONECTADO AO SISTEMA MÃE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SUCCESS)
        self.lbl_status_badge.pack(side="right", padx=20, pady=12)

    def setup_aba_organizador(self):
        frame = ctk.CTkFrame(self.tab_organizador, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_cfg = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=10)
        card_cfg.pack(fill="x", pady=5, padx=5)

        lbl_api = ctk.CTkLabel(card_cfg, text="🔑 Chave API Groq:", text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=12, weight="bold"))
        lbl_api.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        ent_api = ctk.CTkEntry(card_cfg, textvariable=self.api_key, width=540, show="*", fg_color=COLOR_CARD, border_color="#30363D")
        ent_api.grid(row=0, column=1, padx=10, pady=12)

        card_pasta = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=10)
        card_pasta.pack(fill="x", pady=10, padx=5)

        btn_sel = ctk.CTkButton(card_pasta, text="📁 Selecionar Pasta do Cliente", fg_color=COLOR_ACCENT_BLUE, hover_color="#1158C7", font=ctk.CTkFont(weight="bold"), command=self.selecionar_pasta)
        btn_sel.grid(row=0, column=0, padx=15, pady=12)

        self.lbl_pasta = ctk.CTkLabel(card_pasta, text="Nenhuma pasta selecionada", text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(size=12))
        self.lbl_pasta.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        btn_run = ctk.CTkButton(frame, text="🚀 EXECUTAR TRIAGEM E UNIFICAÇÃO DE PDFS", fg_color=COLOR_SUCCESS, hover_color="#238636", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.executar_thread(self.processar_arquivos))
        btn_run.pack(fill="x", pady=10, padx=5)

        self.txt_log_org = ctk.CTkTextbox(frame, height=270, fg_color=COLOR_BG, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_log_org.pack(fill="both", expand=True, pady=5, padx=5)

    def setup_aba_fatos(self):
        frame = ctk.CTkFrame(self.tab_fatos, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_proc = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=10)
        card_proc.pack(fill="x", pady=5, padx=5)

        lbl_proc = ctk.CTkLabel(card_proc, text="⚖️ Tipo de Ação Previdenciária:", text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=13, weight="bold"))
        lbl_proc.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        cb_proc = ctk.CTkOptionMenu(
            card_proc, 
            values=["Aposentadoria Rural por Idade", "Pensão por Morte Rural", "Salário-Maternidade Rural"], 
            variable=self.tipo_processo,
            fg_color=COLOR_CARD,
            button_color=COLOR_ACCENT_BLUE,
            button_hover_color="#1158C7",
            width=280
        )
        cb_proc.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        btn_gerar_fatos = ctk.CTkButton(frame, text="✍️ GERAR HISTÓRICO DOS FATOS E LISTA DE PROVAS (.DOCX)", fg_color=COLOR_ACCENT_BLUE, hover_color="#1158C7", height=45, font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.executar_thread(self.gerar_historia_fatos))
        btn_gerar_fatos.pack(fill="x", pady=10, padx=5)

        self.txt_fatos = ctk.CTkTextbox(frame, height=360, fg_color=COLOR_BG, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=13))
        self.txt_fatos.pack(fill="both", expand=True, pady=5, padx=5)

    def setup_aba_validador(self):
        frame = ctk.CTkFrame(self.tab_validador, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_btn = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=10)
        card_btn.pack(fill="x", pady=5, padx=5)

        btn_validar = ctk.CTkButton(card_btn, text="🔍 DIAGNOSTICAR REQUISITOS DE PROTOCOLO", fg_color=COLOR_ACCENT_CYAN, text_color="#000000", hover_color="#00D8E4", height=45, font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.executar_thread(self.validar_requisitos_protocolo))
        btn_validar.pack(fill="x", padx=15, pady=12)

        panel_grid = ctk.CTkFrame(frame, fg_color="transparent")
        panel_grid.pack(fill="both", expand=True, pady=10)

        self.card_check = ctk.CTkFrame(panel_grid, fg_color=COLOR_BG, corner_radius=10)
        self.card_check.pack(side="left", fill="both", expand=True, padx=5)

        lbl_chk_title = ctk.CTkLabel(self.card_check, text="📋 Checklist de Documentos Indispensáveis", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        lbl_chk_title.pack(pady=10, padx=10, anchor="w")

        self.txt_check_results = ctk.CTkTextbox(self.card_check, fg_color="transparent", text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=13))
        self.txt_check_results.pack(fill="both", expand=True, padx=10, pady=5)

        self.card_parecer = ctk.CTkFrame(panel_grid, fg_color=COLOR_BG, corner_radius=10)
        self.card_parecer.pack(side="right", fill="both", expand=True, padx=5)

        lbl_par_title = ctk.CTkLabel(self.card_parecer, text="🛡️ Diagnóstico de Competência & Viabilidade", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        lbl_par_title.pack(pady=10, padx=10, anchor="w")

        self.txt_parecer = ctk.CTkTextbox(self.card_parecer, fg_color="transparent", text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=13))
        self.txt_parecer.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_aba_central(self):
        frame = ctk.CTkFrame(self.tab_central, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_update = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=10)
        card_update.pack(fill="x", pady=10, padx=5)

        lbl_info = ctk.CTkLabel(card_update, text="🌐 Central de Gerenciamento & Atualizações do Sistema Mãe", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        lbl_info.pack(pady=12, padx=15, anchor="w")

        lbl_status_ver = ctk.CTkLabel(card_update, text=f"Versão Local Instalada: v{VERSAO_ATUAL}", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MAIN)
        lbl_status_ver.pack(pady=5, padx=15, anchor="w")

        btn_checar_update = ctk.CTkButton(card_update, text="🔄 VERIFICAR ATUALIZAÇÕES NO SERVIDOR MÃE", fg_color=COLOR_ACCENT_BLUE, hover_color="#1158C7", height=40, font=ctk.CTkFont(weight="bold"), command=lambda: self.executar_thread(self.verificar_atualizacoes_servidor))
        btn_checar_update.pack(fill="x", padx=15, pady=15)

        self.txt_log_central = ctk.CTkTextbox(frame, height=280, fg_color=COLOR_BG, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=12))
        self.txt_log_central.pack(fill="both", expand=True, pady=5, padx=5)
        self.log(self.txt_log_central, "Sistema Pronto. Clique no botão acima para sincronizar correções com a central.")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_selecionada = pasta
            self.lbl_pasta.configure(text=pasta, text_color=COLOR_TEXT_MAIN)

    def log(self, caixa, msg):
        caixa.insert("end", msg + "\n")
        caixa.see("end")

    def executar_thread(self, funcao):
        if not self.pasta_selecionada and funcao != self.verificar_atualizacoes_servidor:
            messagebox.showwarning("Atenção", "Selecione a pasta do cliente primeiro!")
            return
        threading.Thread(target=funcao, daemon=True).start()

    def processar_arquivos(self):
        try:
            client = Groq(api_key=self.api_key.get().strip())
            pasta_origem = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_origem)
            pasta_destino = os.path.join(os.path.dirname(pasta_origem), f"{nome_cliente}_ORGANIZADO")
            os.makedirs(pasta_destino, exist_ok=True)

            self.log(self.txt_log_org, f"⚡ Iniciando motor de triagem para: {nome_cliente}...")
            agrupados = {}

            for raiz, _, arquivos in os.walk(pasta_origem):
                for arq in sorted(arquivos):
                    if arq.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                        caminho_arq = os.path.join(raiz, arq)
                        nome_upper = arq.upper()
                        anos = re.findall(r'\b(19\d\d|20\d\d)\b', nome_upper)
                        ano = int(anos[0]) if anos else 0

                        match_nome = re.search(r'(FILH[AO]|REQUERENTE|FALECIDO)\s+([A-Z\s]+)', nome_upper)
                        pessoa = match_nome.group(0).strip() if match_nome else "REQUERENTE"

                        categoria = "DOCUMENTO_GERAL"
                        if any(k in nome_upper for k in ["PROCURACAO", "PROCURAÇÃO"]): categoria = "PROCURACAO"
                        elif any(k in nome_upper for k in ["HIPOSSUFICIENCIA", "DECLARACAO", "JUSTICA_GRATUITA"]): categoria = "DECLARACAO_HIPOSSUFICIENCIA"
                        elif any(k in nome_upper for k in ["INDEFERIMENTO", "DECISAO", "COMUNICADO", "DESPACHO", "INSS"]): categoria = "INDEFERIMENTO_INSS"
                        elif "CASAMENTO" in nome_upper: categoria = "CERTIDAO_CASAMENTO"
                        elif "NASC" in nome_upper: categoria = "CERTIDAO_NASCIMENTO"
                        elif "OBITO" in nome_upper: categoria = "CERTIDAO_OBITO"
                        elif "RESIDENCIA" in nome_upper: categoria = "COMPROVANTE_RESIDENCIA"
                        elif "TRABALHO" in nome_upper or "CTPS" in nome_upper: categoria = "CARTEIRA_TRABALHO"
                        elif any(k in nome_upper for k in ["RG", "CPF", "IDENTIDADE", "DOC"]): categoria = "DOCUMENTO_IDENTIFICACAO"

                        chave = f"{categoria}_{pessoa}"
                        if chave not in agrupados:
                            agrupados[chave] = {"arquivos": [], "ano": ano, "categoria": categoria, "pessoa": pessoa}
                        agrupados[chave]["arquivos"].append(caminho_arq)

            grupos_ordenados = sorted(agrupados.values(), key=lambda x: (x["ano"] if x["ano"] > 0 else 9999, x["categoria"]))

            contador = 1
            for g in grupos_ordenados:
                writer = PdfWriter()
                str_ano = f"ANO_{g['ano']}" if g['ano'] > 0 else "S_DATA"
                nome_limpo = re.sub(r'[/\\:*?"<>|]', '_', f"{contador:02d}_{g['categoria']}_{g['pessoa']}_{str_ano}") + ".pdf"
                caminho_final = os.path.join(pasta_destino, nome_limpo)

                for arq in g["arquivos"]:
                    if arq.lower().endswith('.pdf'):
                        try:
                            reader = PdfReader(arq)
                            for page in reader.pages:
                                writer.add_page(page)
                        except Exception:
                            pass

                with open(caminho_final, "wb") as f_out:
                    writer.write(f_out)

                self.log(self.txt_log_org, f"✔ Unificado com sucesso: {nome_limpo}")
                contador += 1

            self.log(self.txt_log_org, f"\n🎉 Triagem concluída em: {pasta_destino}")
            messagebox.showinfo("Sucesso", f"PDFs unificados e organizados!\nSalvo em: {pasta_destino}")
        except Exception as e:
            self.log(self.txt_log_org, f"❌ Erro: {e}")

    def gerar_historia_fatos(self):
        try:
            client = Groq(api_key=self.api_key.get().strip())
            pasta_target = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_target)
            pasta_organizada = os.path.join(os.path.dirname(pasta_target), f"{nome_cliente}_ORGANIZADO")
            pasta_leitura = pasta_organizada if os.path.exists(pasta_organizada) else pasta_target

            self.log(self.txt_fatos, f"🤖 Gerando minuta de Fatos para '{os.path.basename(pasta_leitura)}'...")
            lista_documentos = os.listdir(pasta_leitura)
            opcao_selecionada = self.tipo_processo.get()

            if opcao_selecionada == "Pensão por Morte Rural":
                texto_historia_base = f"""DOS FATOS

Excelência, a Requerente faz jus ao benefício de Pensão por Morte Rural em razão do falecimento de seu(sua) (PARENTESCO/VÍNCULO: CÔNJUGE / COMPANHEIRO / GENITOR), o(a) Sr.(a) (NOME DO FALECIDO/SEGURADO ESPECIAL), ocorrido em (DATA DO ÓBITO), conforme certidão de óbito em anexo.

A Requerente dirigiu-se ao INSS e fez seu pedido administrativo no dia (colocar data DER), contudo o benefício foi indevidamente indeferido.

A Requerente é nascida e criada no meio rural, tendo desde a infância se dedicado às atividades do campo. Inicialmente, residiu na zona rural exercendo o labor agrícola em regime de economia familiar, auxiliando sua família na lida com a terra para garantir o sustento do lar.

Posteriormente, juntamente com o(a) de cujos Sr.(a) (NOME DO FALECIDO/SEGURADO ESPECIAL), passou a residir e trabalhar em fazendas e propriedades rurais da região, prestando serviços agrícolas contínuos na produção de culturas de subsistência e criação de pequenos animais.

Cumpre destacar que o(a) de cujos exerceu a profissão de lavrador/agricultor durante toda a sua vida laboral, mantendo a condição de segurado especial da Previdência Social até a data do seu falecimento.

Toda a trajetória da Requerente e do(a) falecido(a) foi dedicada ao labor rural em regime de economia familiar, circunstância que demonstra de forma clara e inequívoca a condição de segurado especial, fazendo jus à concessão da Pensão por Morte Rural pleiteada.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural e da qualidade de segurado especial:"""

            elif opcao_selecionada == "Salário-Maternidade Rural":
                texto_historia_base = f"""DOS FATOS

Excelência, a Requerente faz jus à concessão do benefício de Salário-Maternidade Rural em razão do nascimento/adoção de seu(sua) filho(a), ocorrido em (DATA DE NASCIMENTO DA CRIANÇA), conforme certidão em anexo.

A Requerente dirigiu-se ao INSS e efetuou o requerimento administrativo no dia (colocar data DER), contudo o pedido foi indeferido sob a alegação de não comprovação da qualidade de segurada especial.

A verdade é que a Autora exerce a profissão de lavradora/agricultora desde a juventude, trabalhando em regime de economia familiar na zona rural do município.

Durante todo o período de carência que antecedeu o parto, a Requerente manteve o exercício contínuo de atividades rurais agrícolas (cultivo de milho, mandioca, feijão, hortaliças e criação de pequenos animais) para a subsistência de sua família.

Portanto, resta plenamente comprovada a qualidade de segurada especial (trabalhadora rural) da Requerente no período exigido por lei.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural:"""

            else:
                texto_historia_base = f"""DOS FATOS

Excelência, ao completar os requisitos para a concessão do benefício de Aposentadoria Rural por Idade, a Autora se dirigiu ao INSS e fez seu pedido administrativo no dia (colocar data DER), contudo foi indeferido.

Inconformada com a negativa do INSS, a Autora faz uso da presente tutela jurisdicional a fim de ter o seu direito garantido.

A verdade é que a Autora exerce a profissão de lavradora/agricultora desde a juventude, tendo nascido e se criado na roça como filha de lavradores.

A Requerente morou na propriedade de seus genitores até a juventude, época em que constituiu união estável/matrimônio, relacionamento do qual resultaram seus filhos.

Em seguida, a Requerente passou a residir e trabalhar em propriedades rurais do município, exercendo continuamente atividades do campo para a subsistência de sua família.

Em todos os seus endereços a Requerente sempre exerceu trabalhos tipicamente rurais, como o plantio de milho, mandioca, feijão, abóbora, cultivo de hortaliças e a criação de pequenos animais (galinhas e porcos), sem qualquer tipo de remuneração ou compensação financeira, os praticando apenas para sua própria subsistência e de sua família.

Portanto, cumpre ressaltar que a Autora esteve filiada à Previdência Social na qualidade de segurada especial (trabalhadora rural) durante todo o seu histórico laboral, contando com o tempo de contribuição rural necessário para o deferimento do pleito.

Segue em ordem conforme a Instrução Normativa nº 77, art. 54 os documentos necessários, que constituem indícios de provas materiais para fins de comprovação do exercício de atividade rural:"""

            prompt = f"""
            Examine a lista de documentos em PDF abaixo para uma ação previdenciária e gere APENAS a lista numerada em ORDEM CRONOLÓGICA (do ano mais antigo para o mais novo).

            ARQUIVOS DISPONÍVEIS:
            {json.dumps(lista_documentos, ensure_ascii=False)}

            FORMATO EXATO DE RESPOSTA (Apenas a lista numerada, sem introduções):
            1. [NOME DO DOCUMENTO] - ANO [XXXX]: [Qualificação objetiva. Ex: A profissão da Requerente/Falecido é mencionada como LAVRADOR(A).]
            2. [NOME DO DOCUMENTO] - ANO [XXXX]: [Qualificação objetiva. Ex: O endereço rural é mencionado na Zona Rural.]
            """

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                lista_provas_gerada = response.choices[0].message.content.strip()
            except Exception:
                lista_provas_gerada = "1. (Verifique a pasta de arquivos para preencher a lista de provas)"

            texto_completo = f"{texto_historia_base}\n\n{lista_provas_gerada}"

            self.txt_fatos.delete("1.0", "end")
            self.txt_fatos.insert("1.0", texto_completo)

            caminho_docx = os.path.join(pasta_target, f"_DOS_FATOS_{nome_cliente}.docx")
            
            try:
                doc = docx.Document()
                doc.add_heading(f"DOS FATOS - CLIENTE: {nome_cliente}", level=1)
                for linha in texto_completo.split("\n"):
                    if linha.strip():
                        doc.add_paragraph(linha.strip())
                doc.save(caminho_docx)
                self.log(self.txt_fatos, f"\n\n✅ Minuta Word salva em: {caminho_docx}")
                messagebox.showinfo("Sucesso", f"Histórico dos Fatos ({opcao_selecionada}) gerado com sucesso!\nSalvo em: {caminho_docx}")
            except PermissionError:
                messagebox.showwarning("Arquivo Aberto", "O arquivo Word está aberto! Feche-o e tente novamente.")

        except Exception as e:
            self.log(self.txt_fatos, f"❌ Erro ao gerar os fatos: {e}")

    # --- VERIFICADOR CORRIGIDO E AMPLIADO ---
    def validar_requisitos_protocolo(self):
        try:
            pasta_target = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_target)
            pasta_organizada = os.path.join(os.path.dirname(pasta_target), f"{nome_cliente}_ORGANIZADO")
            
            # Lê tanto a pasta original quanto a pasta organizada se ela existir
            arquivos = [f.upper() for f in os.listdir(pasta_target)]
            if os.path.exists(pasta_organizada):
                arquivos += [f.upper() for f in os.listdir(pasta_organizada)]

            texto_arquivos_juntos = " ".join(arquivos)

            # Lógica flexível e abrangente de palavras-chave
            requisitos = {
                "PROCURAÇÃO": any(k in texto_arquivos_juntos for k in ["PROCURACAO", "PROCURAÇÃO", "PROC"]),
                "DECLARAÇÃO DE HIPOSSUFICIÊNCIA": any(k in texto_arquivos_juntos for k in ["HIPOSSUFICIENCIA", "DECLARACAO", "JUSTICA_GRATUITA", "HIPO"]),
                "INDEFERIMENTO ADMINISTRATIVO (INSS)": any(k in texto_arquivos_juntos for k in ["INDEFERIMENTO", "DECISAO", "COMUNICADO", "DESPACHO", "INSS", "NEGATIVA", "CUMP"]),
                "RG / CPF / DOC. IDENTIFICAÇÃO": any(k in texto_arquivos_juntos for k in ["RG", "CPF", "IDENTIFICACAO", "IDENTIDADE", "DOC"]),
                "COMPROVANTE DE RESIDÊNCIA RURAL": any(k in texto_arquivos_juntos for k in ["RESIDENCIA", "ENDERECO", "COMPROVANTE", "LUZ", "TALÃO"]),
                "INÍCIO DE PROVA MATERIAL RURAL": any(k in texto_arquivos_juntos for k in ["CASAMENTO", "NASCIMENTO", "ELEITORAL", "BOLETIM", "SINDICAL", "CARTEIRA", "CTPS", "RURAL"])
            }

            self.txt_check_results.delete("1.0", "end")
            itens_presentes = 0

            for doc, presente in requisitos.items():
                if presente:
                    self.txt_check_results.insert("end", f"🟢 [ OK ] {doc}\n")
                    itens_presentes += 1
                else:
                    self.txt_check_results.insert("end", f"🔴 [PENDENTE] {doc}\n")

            score = int((itens_presentes / len(requisitos)) * 100)

            self.txt_parecer.delete("1.0", "end")
            self.txt_parecer.insert("end", f"📊 Score de Admissibilidade: {score}%\n")
            self.txt_parecer.insert("end", "----------------------------------------\n\n")

            if score == 100:
                self.txt_parecer.insert("end", "✅ PROCESSO APTO PARA PROTOCOLO!\n\n")
                self.txt_parecer.insert("end", "Todos os requisitos formais e documentais essenciais foram identificados.")
            elif score >= 70:
                self.txt_parecer.insert("end", "⚠️ PROTOCOLO COM RESSALVAS\n\n")
                self.txt_parecer.insert("end", "Há provas rurais presentes, mas certifique-se de anexar os itens em vermelho no PJe para evitar despacho de emenda.")
            else:
                self.txt_parecer.insert("end", "🚫 PROCESSO INAPTO\n\n")
                self.txt_parecer.insert("end", "Faltam documentos indispensáveis. O protocolo imediato pode causar o indeferimento da petição inicial.")

        except Exception as e:
            messagebox.showerror("Erro na Validação", f"Não foi possível validar a pasta: {e}")

    # --- MÓDULO AUTO-UPDATER MÃE ---
    def verificar_atualizacoes_servidor(self):
        self.log(self.txt_log_central, "🔍 Conectando ao Servidor Mãe para verificar atualizações...")
        try:
            req = urllib.request.Request(URL_CHECAR_VERSAO, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                dados = json.loads(response.read().decode('utf-8'))
                versao_remota = dados.get("version", VERSAO_ATUAL)
                changelog = dados.get("changelog", "Melhorias de desempenho e correções de erros.")

                if versao_remota > VERSAO_ATUAL:
                    self.log(self.txt_log_central, f"🚀 NOVA VERSÃO ENCONTRADA: v{versao_remota}")
                    self.log(self.txt_log_central, f"📝 Novidades: {changelog}")
                    messagebox.showinfo("Nova Atualização Disponível", f"A versão v{versao_remota} está disponível!\nNovidades: {changelog}")
                else:
                    self.log(self.txt_log_central, f"✅ O seu sistema já está na versão mais recente (v{VERSAO_ATUAL}).")
                    messagebox.showinfo("Sistema Atualizado", "Você já está rodando a versão mais recente do Sistema Mãe!")
        except Exception as err:
            self.log(self.txt_log_central, f"⚠️ Não foi possível conectar ao Servidor Mãe no momento. (Modo Offline). Erro: {err}")

if __name__ == "__main__":
    app = AppAdvocacia()
    app.mainloop()