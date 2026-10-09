import os
import re
import json
import urllib.request
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from groq import Groq
from pypdf import PdfWriter, PdfReader
import docx
from datetime import datetime

VERSAO_ATUAL = "2.0.0"
URL_CHECAR_VERSAO = "https://raw.githubusercontent.com/DanylOficial/nexus-legal-ai/main/version.json"

# CONFIGURAÇÃO DO TEU JSONBIN.IO (PROTEGIDO E PRIVADO)
BIN_ID = "6ac88e47ffd5d160535b5554"
# COLA A TUA MASTER KEY DO JSONBIN.IO ABAIXO:
API_KEY_JSONBIN = "$2a$10$JJqyhVKyW.87HvGUBz9xy.sk3tuIeqyuY8oio2G9tldfvPH05K7S6" 

ctk.set_appearance_mode("Dark")

# PALETA LUXURY GOLD & BLACK
COLOR_BG = "#0B0C10"
COLOR_CARD = "#12141C"
COLOR_CARD_BORDER = "#2A2E3D"
COLOR_GOLD = "#D4AF37"
COLOR_GOLD_HOVER = "#AA8A2E"
COLOR_WHITE = "#FFFFFF"
COLOR_TEXT_MUTED = "#A0A5B5"
COLOR_SUCCESS = "#28A745"
COLOR_DANGER = "#DC3545"

class AppAdvocacia(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"👑 NEXUS LEGAL AI v{VERSAO_ATUAL} • Executive Gold Edition")
        self.geometry("1020x820")
        self.configure(fg_color=COLOR_BG)

        self.pasta_selecionada = ""
        self.tipo_processo = ctk.StringVar(value="Aposentadoria Rural por Idade")
        self.api_key_injetada = ""
        self.usuario_logado = ""
        self.plano_usuario = ""
        self.expiracao_usuario = ""

        # INICIA NA TELA DE LOGIN VIP
        self.setup_tela_login()

    # --- TELA DE LOGIN VIP ---
    def setup_tela_login(self):
        self.frame_login = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=20, border_width=2, border_color=COLOR_GOLD)
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center", width=420, height=520)

        lbl_logo = ctk.CTkLabel(self.frame_login, text="⚡ NEXUS LEGAL AI", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLOR_GOLD)
        lbl_logo.pack(pady=(35, 5))

        lbl_sub = ctk.CTkLabel(self.frame_login, text="Painel Executivo de Autenticação", font=ctk.CTkFont(size=13), text_color=COLOR_TEXT_MUTED)
        lbl_sub.pack(pady=(0, 25))

        self.ent_user = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário corporativo", width=320, height=45, fg_color="#1A1D28", border_color=COLOR_CARD_BORDER, text_color=COLOR_WHITE)
        self.ent_user.pack(pady=10)

        self.ent_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Senha de acesso", show="*", width=320, height=45, fg_color="#1A1D28", border_color=COLOR_CARD_BORDER, text_color=COLOR_WHITE)
        self.ent_pass.pack(pady=10)

        btn_login = ctk.CTkButton(self.frame_login, text="ENTRAR NO SISTEMA", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", height=48, font=ctk.CTkFont(size=14, weight="bold"), command=self.autenticar_usuario)
        btn_login.pack(pady=(25, 10), fill="x", padx=50)

        self.lbl_status_login = ctk.CTkLabel(self.frame_login, text="", font=ctk.CTkFont(size=12), text_color=COLOR_DANGER)
        self.lbl_status_login.pack(pady=5)

    def autenticar_usuario(self):
        user_input = self.ent_user.get().strip()
        pass_input = self.ent_pass.get().strip()

        if not user_input or not pass_input:
            self.lbl_status_login.configure(text="Preencha o usuário e a senha.")
            return

        self.lbl_status_login.configure(text="Autenticando no Servidor Mãe...", text_color=COLOR_GOLD)
        
        def validar_remoto():
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
                    
                    self.api_key_injetada = dados.get("groq_api_key_global", "")
                    usuarios = dados.get("usuarios", [])

                    usuario_encontrado = None
                    for u in usuarios:
                        if u["login"] == user_input and u["senha"] == pass_input:
                            usuario_encontrado = u
                            break

                    if not usuario_encontrado:
                        self.lbl_status_login.configure(text="Usuário ou senha incorretos.", text_color=COLOR_DANGER)
                        return

                    if not usuario_encontrado.get("ativo", False):
                        self.lbl_status_login.configure(text="Acesso suspenso. Contate o administrador.", text_color=COLOR_DANGER)
                        return

                    exp_str = usuario_encontrado.get("expiracao", "2000-01-01")
                    data_exp = datetime.strptime(exp_str, "%Y-%m-%d")
                    data_hoje = datetime.now()

                    if data_hoje > data_exp:
                        self.lbl_status_login.configure(text=f"Plano expirado em {exp_str}. Renove a licença.", text_color=COLOR_DANGER)
                        return

                    # AUTENTICAÇÃO BEM-SUCEDIDA
                    self.usuario_logado = usuario_encontrado["login"]
                    self.plano_usuario = usuario_encontrado.get("plano", "Padrão")
                    self.expiracao_usuario = exp_str

                    self.frame_login.destroy()
                    self.setup_interface_principal()

            except Exception as e:
                self.lbl_status_login.configure(text=f"Erro de conexão com o servidor: {e}", text_color=COLOR_DANGER)

        threading.Thread(target=validar_remoto, daemon=True).start()

    # --- INTERFACE PRINCIPAL DOURADA & LUXO ---
    def setup_interface_principal(self):
        self.setup_header()

        self.tabview = ctk.CTkTabview(
            self, width=980, height=680, 
            fg_color=COLOR_CARD, 
            segmented_button_selected_color=COLOR_GOLD, 
            segmented_button_selected_hover_color=COLOR_GOLD_HOVER,
            text_color=COLOR_WHITE
        )
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_organizador = self.tabview.add("🧠 1. Triagem Jurídica por Ação")
        self.tab_fatos = self.tabview.add("✍️ 2. Minuta de Fatos & Provas")
        self.tab_validador = self.tabview.add("🛡️ 3. Verificador de Admissibilidade")
        self.tab_central = self.tabview.add("⚙️ 4. Central de Licenças")

        self.setup_aba_organizador()
        self.setup_aba_fatos()
        self.setup_aba_validador()
        self.setup_aba_central()

    def setup_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=15, border_width=1, border_color=COLOR_GOLD)
        header_frame.pack(padx=20, pady=(15, 5), fill="x")

        lbl_logo = ctk.CTkLabel(header_frame, text="⚡ NEXUS LEGAL AI", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_GOLD)
        lbl_logo.pack(side="left", padx=20, pady=12)

        lbl_sub = ctk.CTkLabel(header_frame, text=f"Usuário: {self.usuario_logado.upper()} | Plano: {self.plano_usuario} (Validade: {self.expiracao_usuario})", font=ctk.CTkFont(size=12), text_color=COLOR_WHITE)
        lbl_sub.pack(side="left", padx=10, pady=12)

        self.lbl_status_badge = ctk.CTkLabel(header_frame, text="● LICENÇA ATIVA", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SUCCESS)
        self.lbl_status_badge.pack(side="right", padx=20, pady=12)

    def setup_aba_organizador(self):
        frame = ctk.CTkFrame(self.tab_organizador, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_proc = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        card_proc.pack(fill="x", pady=5, padx=5)

        lbl_proc = ctk.CTkLabel(card_proc, text="⚖️ Ação Previdenciária Alvo:", text_color=COLOR_WHITE, font=ctk.CTkFont(size=12, weight="bold"))
        lbl_proc.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        cb_proc = ctk.CTkOptionMenu(
            card_proc, 
            values=["Aposentadoria Rural por Idade", "Pensão por Morte Rural", "Salário-Maternidade Rural"], 
            variable=self.tipo_processo,
            fg_color=COLOR_CARD,
            button_color=COLOR_GOLD,
            button_hover_color=COLOR_GOLD_HOVER,
            text_color="#000000",
            width=320
        )
        cb_proc.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        card_pasta = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        card_pasta.pack(fill="x", pady=5, padx=5)

        btn_sel = ctk.CTkButton(card_pasta, text="📁 Selecionar Pasta do Cliente", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", font=ctk.CTkFont(weight="bold"), command=self.selecionar_pasta)
        btn_sel.grid(row=0, column=0, padx=15, pady=12)

        self.lbl_pasta = ctk.CTkLabel(card_pasta, text="Nenhuma pasta selecionada", text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(size=12))
        self.lbl_pasta.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(frame, progress_color=COLOR_GOLD, fg_color=COLOR_CARD_BORDER, height=8)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(5, 10), padx=5)

        btn_run = ctk.CTkButton(frame, text="⚖️ EXECUTAR ANÁLISE JURÍDICA E FILTRAGEM DE PROVAS (PJe)", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", height=48, font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.executar_thread(self.processar_arquivos_com_ia))
        btn_run.pack(fill="x", pady=5, padx=5)

        self.txt_log_org = ctk.CTkTextbox(frame, height=280, fg_color=COLOR_BG, text_color=COLOR_GOLD, font=ctk.CTkFont(family="Consolas", size=12), border_width=1, border_color=COLOR_CARD_BORDER)
        self.txt_log_org.pack(fill="both", expand=True, pady=5, padx=5)

    def setup_aba_fatos(self):
        frame = ctk.CTkFrame(self.tab_fatos, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_proc = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        card_proc.pack(fill="x", pady=5, padx=5)

        lbl_proc = ctk.CTkLabel(card_proc, text="⚖️ Tipo de Ação Selecionado:", text_color=COLOR_WHITE, font=ctk.CTkFont(size=13, weight="bold"))
        lbl_proc.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        lbl_tipo_atual = ctk.CTkLabel(card_proc, textvariable=self.tipo_processo, text_color=COLOR_GOLD, font=ctk.CTkFont(size=13, weight="bold"))
        lbl_tipo_atual.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        btn_gerar_fatos = ctk.CTkButton(frame, text="✍️ GERAR HISTÓRICO DOS FATOS E LISTA DE PROVAS (.DOCX)", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", height=45, font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.executar_thread(self.gerar_historia_fatos))
        btn_gerar_fatos.pack(fill="x", pady=10, padx=5)

        self.txt_fatos = ctk.CTkTextbox(frame, height=380, fg_color=COLOR_BG, text_color=COLOR_WHITE, font=ctk.CTkFont(size=13), border_width=1, border_color=COLOR_CARD_BORDER)
        self.txt_fatos.pack(fill="both", expand=True, pady=5, padx=5)

    def setup_aba_validador(self):
        frame = ctk.CTkFrame(self.tab_validador, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_btn = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        card_btn.pack(fill="x", pady=5, padx=5)

        btn_validar = ctk.CTkButton(card_btn, text="🔍 DIAGNOSTICAR REQUISITOS DE PROTOCOLO JURÍDICO", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", height=45, font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.executar_thread(self.validar_requisitos_protocolo))
        btn_validar.pack(fill="x", padx=15, pady=12)

        panel_grid = ctk.CTkFrame(frame, fg_color="transparent")
        panel_grid.pack(fill="both", expand=True, pady=10)

        self.card_check = ctk.CTkFrame(panel_grid, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        self.card_check.pack(side="left", fill="both", expand=True, padx=5)

        lbl_chk_title = ctk.CTkLabel(self.card_check, text="📋 Checklist de Documentos Indispensáveis", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_GOLD)
        lbl_chk_title.pack(pady=10, padx=10, anchor="w")

        self.txt_check_results = ctk.CTkTextbox(self.card_check, fg_color="transparent", text_color=COLOR_WHITE, font=ctk.CTkFont(size=13))
        self.txt_check_results.pack(fill="both", expand=True, padx=10, pady=5)

        self.card_parecer = ctk.CTkFrame(panel_grid, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        self.card_parecer.pack(side="right", fill="both", expand=True, padx=5)

        lbl_par_title = ctk.CTkLabel(self.card_parecer, text="🛡️ Diagnóstico de Competência & Viabilidade", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_GOLD)
        lbl_par_title.pack(pady=10, padx=10, anchor="w")

        self.txt_parecer = ctk.CTkTextbox(self.card_parecer, fg_color="transparent", text_color=COLOR_WHITE, font=ctk.CTkFont(size=13))
        self.txt_parecer.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_aba_central(self):
        frame = ctk.CTkFrame(self.tab_central, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        card_update = ctk.CTkFrame(frame, fg_color=COLOR_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        card_update.pack(fill="x", pady=10, padx=5)

        lbl_info = ctk.CTkLabel(card_update, text="🌐 Central de Gerenciamento & Atualizações do Sistema Mãe", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_GOLD)
        lbl_info.pack(pady=12, padx=15, anchor="w")

        lbl_status_ver = ctk.CTkLabel(card_update, text=f"Versão Local Instalada: v{VERSAO_ATUAL}", font=ctk.CTkFont(size=12), text_color=COLOR_WHITE)
        lbl_status_ver.pack(pady=5, padx=15, anchor="w")

        btn_checar_update = ctk.CTkButton(card_update, text="🔄 VERIFICAR ATUALIZAÇÕES NO SERVIDOR MÃE", fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER, text_color="#000000", height=40, font=ctk.CTkFont(weight="bold"), command=lambda: self.executar_thread(self.verificar_atualizacoes_servidor))
        btn_checar_update.pack(fill="x", padx=15, pady=15)

        self.txt_log_central = ctk.CTkTextbox(frame, height=280, fg_color=COLOR_BG, text_color=COLOR_WHITE, font=ctk.CTkFont(size=12), border_width=1, border_color=COLOR_CARD_BORDER)
        self.txt_log_central.pack(fill="both", expand=True, pady=5, padx=5)
        self.log(self.txt_log_central, f"Usuário Logado: {self.usuario_logado} | Licença Válida até: {self.expiracao_usuario}")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_selecionada = pasta
            self.lbl_pasta.configure(text=pasta, text_color=COLOR_WHITE)

    def log(self, caixa, msg):
        caixa.insert("end", msg + "\n")
        caixa.see("end")

    def executar_thread(self, funcao):
        if not self.pasta_selecionada and funcao != self.verificar_atualizacoes_servidor:
            messagebox.showwarning("Atenção", "Selecione a pasta do cliente primeiro!")
            return
        threading.Thread(target=funcao, daemon=True).start()

    # --- MOTOR DE TRIAGEM JURÍDICA COM CHAVE INJETADA ---
    def processar_arquivos_com_ia(self):
        try:
            if not self.api_key_injetada:
                messagebox.showerror("Erro de Autenticação", "Chave da API não carregada pelo Servidor Mãe.")
                return

            client = Groq(api_key=self.api_key_injetada)
            pasta_origem = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_origem)
            pasta_destino = os.path.join(os.path.dirname(pasta_origem), f"{nome_cliente}_ORGANIZADO")
            os.makedirs(pasta_destino, exist_ok=True)

            acao = self.tipo_processo.get()
            self.log(self.txt_log_org, f"⚖️ Análise Jurídica Cirúrgica para Ação de '{acao}' ({nome_cliente})...")
            
            arquivos_pdf = []
            for raiz, _, arquivos in os.walk(pasta_origem):
                for arq in arquivos:
                    if arq.lower().endswith('.pdf'):
                        arquivos_pdf.append(os.path.join(raiz, arq))

            if not arquivos_pdf:
                self.log(self.txt_log_org, "❌ Nenhum arquivo PDF encontrado na pasta.")
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
                self.progress_bar.set(idx / total)
                nome_arq_orig = os.path.basename(caminho)
                
                nome_sem_ext = os.path.splitext(nome_arq_orig)[0].upper()
                nome_limpo_base = re.sub(r'(\bANO\b\s*\d{4}\s*[-_]*)+', '', nome_sem_ext, flags=re.IGNORECASE).strip()
                nome_limpo_base = re.sub(r'[:\\/*?\"<>|]', '', nome_limpo_base).strip()

                self.log(self.txt_log_org, f"\n📖 [{idx}/{total}] Examinando: {nome_arq_orig}...")

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
                1. "is_prova_rural": true -> Início de Prova Material Rural (Certidões rurais, Ficha Cadastral, CNIS com tempo rural, Documento de Terra, PRONAF, Comodato, Matrícula Escolar, Prontuário de Saúde, Carteira de Sindicato, Eleitoral).
                2. "is_prova_rural": false -> Documentos formais (Procuração, Hipossuficiência, RG/CPF, Comprovante de Residência Atual, Indeferimento e PROTOCOLOS DE REQUERIMENTO).

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
                self.log(self.txt_log_org, f"   ➔ {tag} {titulo_final}{str_ano_log}")

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

                self.log(self.txt_log_org, f"✅ Doc Formal Gerado: {nome_arquivo_pje}")

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

                self.log(self.txt_log_org, f"🌾 Prova Rural Gerada: {nome_arquivo_pje}")
                contador_provas += 1

            self.progress_bar.set(1.0)
            self.log(self.txt_log_org, f"\n🎉 TRIAGEM JURÍDICA CONCLUÍDA!\nArquivos salvos em: {pasta_destino}")
            messagebox.showinfo("Sucesso", f"Triagem Concluída!\nSalvo em: {pasta_destino}")

        except Exception as e:
            self.log(self.txt_log_org, f"❌ Erro na triagem: {e}")

    # --- MINUTA DOS FATOS EXATA DO ESCRITÓRIO ---
    def gerar_historia_fatos(self):
        try:
            if not self.pasta_selecionada:
                messagebox.showwarning("Pasta Não Selecionada", "Selecione a pasta do cliente na Aba 1 primeiro!")
                return

            if not self.api_key_injetada:
                messagebox.showerror("Erro de Autenticação", "Chave da API não carregada pelo Servidor Mãe.")
                return

            pasta_origem = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_origem)
            pasta_organizada = os.path.join(os.path.dirname(pasta_origem), f"{nome_cliente}_ORGANIZADO")

            if not os.path.exists(pasta_organizada):
                messagebox.showwarning(
                    "Triagem Pendente", 
                    f"A pasta organizada '{nome_cliente}_ORGANIZADO' ainda não foi criada!\n\nExecute primeiro o botão da Aba 1 (Triagem) antes de gerar a minuta."
                )
                return

            client = Groq(api_key=self.api_key_injetada)
            self.log(self.txt_fatos, f"🤖 Lendo arquivos da pasta organizada: '{os.path.basename(pasta_organizada)}'...")

            todos_arquivos = os.listdir(pasta_organizada)
            provas_rurais_ordenadas = sorted([
                f for f in todos_arquivos 
                if f.lower().endswith('.pdf') and re.match(r'^\d{2}\.', f)
            ])

            if not provas_rurais_ordenadas:
                provas_rurais_ordenadas = sorted([f for f in todos_arquivos if f.lower().endswith('.pdf')])

            opcao_selecionada = self.tipo_processo.get()

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
                texto_historia_base = f"""DOS FATOS

Excelência, ao completar os requisitos para a concessão do benefício de Aposentadoria Rural por idade, a Autora se dirigiu ao INSS e fez seu pedido administrativo no dia (COLOCAR DATA), contudo foi indeferido.

Inconformada com a negativa do INSS, a Autora faz uso da presente tutela jurisdicional a fim de ter o seu direito garantido.

A verdade é que a Autora exerce a profissão de lavradora/agricultora desde a juventude, tendo nascido, se criado e sempre residido em meio rural.

Em todas as localidades onde residiu, a Requerente sempre exerceu trabalhos tipicamente rurais, como o plantio de milho, mandioca, feijão, abóbora, cultivo de hortaliças e criação de animais, sem qualquer tipo de remuneração ou compensação financeira, praticando as atividades apenas para a subsistência de sua família.

Portanto, cumpre ressaltar que a Autora esteve filiada à Previdência Social na qualidade de segurada especial (trabalhadora rural) durante todo o seu histórico laboral, visto que nasceu e se criou na roça.

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

            self.txt_fatos.delete("1.0", "end")
            self.txt_fatos.insert("1.0", texto_completo)

            caminho_docx = os.path.join(pasta_organizada, f"_DOS_FATOS_{nome_cliente}.docx")
            
            try:
                doc = docx.Document()
                doc.add_heading(f"DOS FATOS - CLIENTE: {nome_cliente}", level=1)
                for linha in texto_completo.split("\n"):
                    if linha.strip():
                        doc.add_paragraph(linha.strip())
                doc.save(caminho_docx)
                self.log(self.txt_fatos, f"\n\n✅ Minuta Word salva na pasta organizada: {caminho_docx}")
                messagebox.showinfo("Sucesso", f"Histórico dos Fatos ({opcao_selecionada}) gerado com sucesso!\nSalvo em: {caminho_docx}")
            except PermissionError:
                messagebox.showwarning("Arquivo Aberto", "O arquivo Word está aberto! Feche-o e tente novamente.")

        except Exception as e:
            self.log(self.txt_fatos, f"❌ Erro ao gerar os fatos: {e}")

    # --- VERIFICADOR DE ADMISSIBILIDADE ---
    def validar_requisitos_protocolo(self):
        try:
            pasta_target = self.pasta_selecionada
            nome_cliente = os.path.basename(pasta_target)
            pasta_organizada = os.path.join(os.path.dirname(pasta_target), f"{nome_cliente}_ORGANIZADO")
            
            arquivos = [f.upper() for f in os.listdir(pasta_target)]
            if os.path.exists(pasta_organizada):
                arquivos += [f.upper() for f in os.listdir(pasta_organizada)]

            texto_arquivos_juntos = " ".join(arquivos)

            requisitos = {
                "PROCURAÇÃO E DECLARAÇÃO": any(k in texto_arquivos_juntos for k in ["PROCURACAO", "PROCURAÇÃO", "DECLARACAO", "HIPOSSUFICIENCIA"]),
                "INDEFERIMENTO ADMINISTRATIVO (INSS)": any(k in texto_arquivos_juntos for k in ["INDEFERIMENTO", "DECISAO", "COMUNICADO", "DESPACHO", "INSS", "NEGATIVA", "CUMP"]),
                "RG E CPF DA REQUERENTE": any(k in texto_arquivos_juntos for k in ["RG", "CPF", "IDENTIFICACAO", "IDENTIDADE", "DOC"]),
                "COMPROVANTE DE RESIDÊNCIA RURAL": any(k in texto_arquivos_juntos for k in ["RESIDENCIA", "ENDERECO", "COMPROVANTE", "LUZ", "TALÃO"]),
                "INÍCIO DE PROVA MATERIAL RURAL": any(k in texto_arquivos_juntos for k in ["CASAMENTO", "NASCIMENTO", "ELEITORAL", "BOLETIM", "SINDICAL", "CARTEIRA", "CTPS", "RURAL", "ANO"])
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
                self.txt_parecer.insert("end", "Todos os requisitos formais de admissibilidade foram identificados.")
            elif score >= 70:
                self.txt_parecer.insert("end", "⚠️ PROTOCOLO COM RESSALVAS\n\n")
                self.txt_parecer.insert("end", "Ação possui conjunto probatório rural, mas certifique-se de anexar os itens em vermelho no PJe para evitar despacho de emenda.")
            else:
                self.txt_parecer.insert("end", "🚫 PROCESSO INAPTO\n\n")
                self.txt_parecer.insert("end", "Faltam documentos indispensáveis. O protocolo imediato pode causar o indeferimento da petição inicial.")

        except Exception as e:
            messagebox.showerror("Erro na Validação", f"Não foi possível validar a pasta: {e}")

    # --- AUTO-UPDATER MÃE ---
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