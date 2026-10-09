// Autenticação de Login via Python
async function realizarLogin(e) {
    e.preventDefault();
    const user = document.getElementById("user-input").value;
    const pass = document.getElementById("pass-input").value;
    const statusDiv = document.getElementById("login-status");

    statusDiv.innerText = "Autenticando no Servidor Mãe...";
    statusDiv.style.color = "#D4AF37";

    const resultado = await eel.autenticar_usuario_py(user, pass)();

    if (resultado.sucesso) {
        document.getElementById("login-screen").classList.add("hidden");
        document.getElementById("app-screen").classList.remove("hidden");
        document.getElementById("user-info").innerText = `Usuário: ${resultado.user.toUpperCase()} | Plano: ${resultado.plano}`;
    } else {
        statusDiv.innerText = resultado.mensagem;
        statusDiv.style.color = "#FF4D4D";
    }
}

// Troca de Abas
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
}

// Selecionar Pasta
async function selecionarPasta() {
    const caminho = await eel.selecionar_pasta_py()();
    if (caminho) {
        document.getElementById("folder-path-display").innerText = caminho;
    }
}

// Executar Triagem
async function executarTriagem() {
    const acao = document.getElementById("tipo-processo").value;
    const log = document.getElementById("log-triagem");
    log.innerHTML += `<br>> Iniciando análise jurídica para: ${acao}...`;
    await eel.processar_arquivos_py(acao)();
}

// Recebe Logs do Python em Tempo Real
eel.expose(atualizarLogJS);
function atualizarLogJS(mensagem) {
    const log = document.getElementById("log-triagem");
    log.innerHTML += `<br>${mensagem}`;
    log.scrollTop = log.scrollHeight;
}

// Gerar Minuta
async function gerarMinuta() {
    const acao = document.getElementById("tipo-processo").value;
    const textTextArea = document.getElementById("text-minuta");
    
    textTextArea.value = "🤖 Lendo arquivos organizados e gerando minuta...";
    
    const textoGerado = await eel.gerar_minuta_py(acao)();
    textTextArea.value = textoGerado;
}

// Validar Admissibilidade
async function validarAdmissibilidade() {
    const checkDiv = document.getElementById("val-check");
    const scoreDiv = document.getElementById("val-score");

    checkDiv.innerText = "🔍 Diagnosticando requisitos e documentos...";
    scoreDiv.innerText = "Aguarde...";

    const res = await eel.validar_admissibilidade_py()();

    if (res) {
        checkDiv.innerText = res.checklist;
        scoreDiv.innerText = `${res.score}\n\n${res.parecer}`;
    } else {
        checkDiv.innerText = "❌ Erro ao processar admissibilidade.";
        scoreDiv.innerText = "Tente novamente.";
    }
}