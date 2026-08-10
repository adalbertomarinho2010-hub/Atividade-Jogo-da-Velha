import sys
import uuid
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget
)

import banco
from config import TITLE_ID, SALDO_INICIAL
from estilo import (
    QSS,
    aguardando,
    botao,
    cabecalho,
    campo,
    icone,
    moeda,
    rotulo_erro
)

COMBINACOES_VITORIA = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], 
    [0, 3, 6], [1, 4, 7], [2, 5, 8], 
    [0, 4, 8], [2, 4, 6]
]

def _aba(widget):
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(60, 44, 60, 44)
    layout.setSpacing(0)
    return layout


class AbaCadastroLogin(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

        cabecalho(layout, "tic-tac-toe.png", "Jogo da Velha", "Cadastre-se ou faça login para jogar")

        self.email = campo(layout, "E-mail", "voce@email.com")
        self.usuario = campo(layout, "Usuário (apenas no cadastro)", "seu apelido")
        self.senha = campo(layout, "Senha", "mínimo 6 caracteres", senha=True)

        self.erro = rotulo_erro(layout)
        
        botoes = QHBoxLayout()
        botoes.addWidget(botao("Entrar", self.entrar))
        botoes.addWidget(botao("Cadastrar", self.cadastrar, secundario=True))
        
        layout.addLayout(botoes)
        layout.addStretch(1)

    def cadastrar(self):
        email = self.email.text().strip()
        usuario = self.usuario.text().strip()
        senha = self.senha.text()

        if email == "" or usuario == "" or senha == "":
            self.erro.setText("Preencha todos os campos para se cadastrar.")
            return

        try:
            with aguardando():
                banco.api("/Client/RegisterPlayFabUser", {
                    "TitleId": TITLE_ID, 
                    "Email": email, 
                    "Password": senha,
                    "Username": usuario, 
                    "RequireBothUsernameAndEmail": True
                })
                
                resposta_login = banco.api("/Client/LoginWithEmailAddress", {
                    "TitleId": TITLE_ID, 
                    "Email": email, 
                    "Password": senha
                })
                
                novo_id = resposta_login["PlayFabId"]
                banco.gravar_user(novo_id, "saldo", SALDO_INICIAL)
                banco.gravar_user(novo_id, "vitorias", 0)
                
                self.erro.clear()
                QMessageBox.information(self, "Sucesso", "Cadastro realizado com sucesso! Clique no botão Entrar.")
                
        except Exception as erro:
            self.erro.setText(str(erro))

    def entrar(self):
        email = self.email.text().strip()
        senha = self.senha.text()

        if email == "" or senha == "":
            self.erro.setText("Informe seu e-mail e senha.")
            return

        try:
            with aguardando():
                resposta_login = banco.api("/Client/LoginWithEmailAddress", {
                    "TitleId": TITLE_ID, 
                    "Email": email, 
                    "Password": senha
                })
                
                banco.ME["ticket"] = resposta_login["SessionTicket"]
                banco.ME["id"] = resposta_login["PlayFabId"]
                
                info_usuario = banco.api("/Admin/GetUserAccountInfo", {"PlayFabId": banco.ME["id"]}, admin=True)
                banco.ME["nome"] = info_usuario["UserInfo"]["Username"]
                
                jogadores = banco.ler("jogadores", {})
                jogadores[banco.ME["nome"]] = banco.ME["id"]
                banco.gravar("jogadores", jogadores)
                
                self.erro.clear()
                self.janela.liberar_acesso()
                
        except Exception as erro:
            self.erro.setText(str(erro))


class AbaBanco(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

        cabecalho(layout, "piggy-bank.png", "Seu Banco", "Administre o saldo de apostas")

        self.lbl_saldo = QLabel("R$ 0,00")
        self.lbl_saldo.setObjectName("saldo")
        layout.addWidget(self.lbl_saldo)
        layout.addSpacing(24)
        
        self.input_deposito = campo(layout, "Depositar valor (R$)", "0.00")
        self.erro = rotulo_erro(layout)

        layout.addWidget(botao("Depositar Dinheiro", self.depositar))
        layout.addSpacing(10)
        layout.addWidget(botao("Deslogar", self.deslogar, perigo=True))
        layout.addStretch(1)

    def atualizar(self):
        try:
            with aguardando():
                saldo_atual = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                self.lbl_saldo.setText(moeda(saldo_atual))
        except Exception as erro:
            self.erro.setText(str(erro))

    def depositar(self):
        try:
            with aguardando():
                texto_valor = self.input_deposito.text().strip().replace(",", ".")
                
                if texto_valor == "":
                    self.erro.setText("Digite um valor para depositar.")
                    return
                
                valor = float(texto_valor)
                if valor <= 0:
                    self.erro.setText("O valor deve ser maior que zero.")
                    return
                
                saldo_atual = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                novo_saldo = saldo_atual + valor
                banco.gravar_user(banco.ME["id"], "saldo", novo_saldo)
                
                self.input_deposito.clear()
                self.erro.clear()
                self.atualizar()
                QMessageBox.information(self, "Sucesso", "Depósito realizado.")
                
        except Exception as erro:
            self.erro.setText(str(erro))

    def deslogar(self):
        banco.ME["ticket"] = ""
        banco.ME["id"] = ""
        banco.ME["nome"] = ""
        self.janela.bloquear_acesso()


class AbaLobby(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

        cabecalho(layout, "banking.png", "Lobby", "Convide outros jogadores e defina o valor da aposta")

        self.lista = QListWidget()
        layout.addWidget(self.lista)
        layout.addSpacing(10)
        
        self.valor_aposta = campo(layout, "Valor da Aposta (R$)", "50.00")
        self.erro = rotulo_erro(layout)

        layout.addWidget(botao("Atualizar lista de jogadores", self.carregar_jogadores, secundario=True))
        layout.addSpacing(6)
        layout.addWidget(botao("Convidar selecionado", self.convidar))
        layout.addSpacing(6)
        layout.addWidget(botao("Ver convite recebido", self.aceitar))
        layout.addStretch(1)

    def carregar_jogadores(self):
        try:
            with aguardando():
                self.lista.clear()
                self.jogadores = banco.ler("jogadores", {})
                for nome in self.jogadores:
                    if nome != banco.ME["nome"]:
                        self.lista.addItem(nome)
        except Exception as erro:
            self.erro.setText(str(erro))

    def convidar(self):
        try:
            with aguardando():
                item_selecionado = self.lista.currentItem()
                if not item_selecionado:
                    self.erro.setText("Selecione um jogador na lista.")
                    return
                
                texto_aposta = self.valor_aposta.text().strip().replace(",", ".")
                if texto_aposta == "":
                    self.erro.setText("Informe o valor da aposta.")
                    return
                
                aposta = float(texto_aposta)
                if aposta <= 0:
                    self.erro.setText("A aposta deve ser maior que zero.")
                    return

                meu_saldo = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                if aposta > meu_saldo:
                    self.erro.setText("Você não possui saldo suficiente para essa aposta.")
                    return

                nome_oponente = item_selecionado.text()
                id_oponente = self.jogadores[nome_oponente]
                
                id_partida = uuid.uuid4().hex[:12]
                self.janela.aba_jogo.partida = id_partida
                self.janela.aba_jogo.meu_simbolo = "X"
                self.janela.aba_jogo.aposta = aposta
                self.janela.aba_jogo.oponente = nome_oponente
                
                self.janela.aba_jogo.salvar("         ", "X")
                
                texto_convite = id_partida + "-" + str(aposta) + "-" + banco.ME["nome"]
                banco.api("/Server/UpdateUserData", {
                    "PlayFabId": id_oponente, 
                    "Data": {"convite": texto_convite}
                }, admin=True)
                
                self.erro.clear()
                self.janela.aba_jogo.abrir_jogo()
                
        except Exception as erro:
            self.erro.setText(str(erro))

    def aceitar(self):
        try:
            with aguardando():
                resposta = banco.api("/Client/GetUserData", {"Keys": ["convite"]})["Data"]
                
                if "convite" not in resposta or resposta["convite"]["Value"] == "":
                    self.erro.setText("Nenhum convite recebido no momento.")
                    return
                
                dados_convite = resposta["convite"]["Value"].split("-")
                id_partida = dados_convite[0]
                aposta = float(dados_convite[1])
                nome_oponente = dados_convite[2]
                
                meu_saldo = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                if aposta > meu_saldo:
                    self.erro.setText("Você não tem saldo suficiente para aceitar este convite.")
                    return

                banco.api("/Server/UpdateUserData", {
                    "PlayFabId": banco.ME["id"], 
                    "Data": {"convite": ""}
                }, admin=True)

                self.janela.aba_jogo.partida = id_partida
                self.janela.aba_jogo.meu_simbolo = "O"
                self.janela.aba_jogo.aposta = aposta
                self.janela.aba_jogo.oponente = nome_oponente
                self.erro.clear()
                self.janela.aba_jogo.abrir_jogo()
                
        except Exception as erro:
            self.erro.setText(str(erro))


class AbaJogo(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

        self.partida = ""
        self.meu_simbolo = ""
        self.tabuleiro = "         "
        self.vez = "X"
        self.aposta = 0.0
        self.oponente = ""
        self.finalizado = False

        cabecalho(layout, "tic-tac-toe.png", "Partida", "Acompanhe as jogadas")

        self.info = QLabel("...")
        self.info.setObjectName("subtitulo")
        layout.addWidget(self.info)

        grade = QGridLayout()
        self.casas = []
        
        for posicao in range(9):
            botao_casa = QPushButton("")
            botao_casa.setObjectName("casa_velha")
            botao_casa.setFixedSize(80, 80)
            botao_casa.clicked.connect(lambda _, pos=posicao: self.jogar(pos))
            grade.addWidget(botao_casa, posicao // 3, posicao % 3)
            self.casas.append(botao_casa)
            
        container = QHBoxLayout()
        container.addStretch(1)
        container.addLayout(grade)
        container.addStretch(1)
        layout.addLayout(container)

        self.status = QLabel("...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setObjectName("rotulo")
        layout.addWidget(self.status)
        layout.addSpacing(16)
        
        layout.addWidget(botao("Sair da partida", self.sair_jogo, perigo=True))
        layout.addStretch(1)

        self.timer = QTimer(self, interval=3000, timeout=self.atualizar)

    def abrir_jogo(self):
        self.finalizado = False
        self.info.setText("Adversário: " + self.oponente + " | Valendo: " + moeda(self.aposta))
        for botao_casa in self.casas:
            botao_casa.setEnabled(True)
        self.janela.setCurrentIndex(3)
        self.timer.start()
        self.atualizar()

    def salvar(self, tabuleiro, vez):
        banco.gravar("partida_" + self.partida, {"t": tabuleiro, "v": vez})
        self.mostrar(tabuleiro, vez)

    def atualizar(self):
        if self.partida != "":
            dados_partida = banco.ler("partida_" + self.partida)
            if dados_partida:
                self.mostrar(dados_partida["t"], dados_partida["v"])

    def jogar(self, posicao):
        tabuleiro = self.tabuleiro
        vez = self.vez
        
        if self.finalizado == True or vez != self.meu_simbolo or tabuleiro[posicao] != " " or self.fim(tabuleiro) != "":
            return
            
        parte_1 = tabuleiro[:posicao]
        parte_2 = tabuleiro[posicao + 1:]
        
        if vez == "X":
            proxima_vez = "O" 
        else:
            proxima_vez = "X"
            
        novo_tabuleiro = parte_1 + self.meu_simbolo + parte_2
        
        self.salvar(novo_tabuleiro, proxima_vez)

    def mostrar(self, tabuleiro, vez):
        self.tabuleiro = tabuleiro
        self.vez = vez
        
        for indice in range(9):
            self.casas[indice].setText(tabuleiro[indice])
            
        vencedor = self.fim(tabuleiro)
        
        if vencedor != "" and self.finalizado == False:
            self.finalizado = True
            self.timer.stop()
            
            for botao_casa in self.casas:
                botao_casa.setEnabled(False)
                
            if vencedor == "-":
                self.status.setText("Empate! O dinheiro não foi mexido.")
                QMessageBox.information(self, "Fim de Jogo", "A partida empatou!")
            elif vencedor == self.meu_simbolo:
                self.status.setText("Você venceu!")
                
                saldo_atual = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                banco.gravar_user(banco.ME["id"], "saldo", saldo_atual + self.aposta)
                
                vitorias_atuais = banco.ler_user(banco.ME["id"], "vitorias", 0)
                banco.gravar_user(banco.ME["id"], "vitorias", int(vitorias_atuais) + 1)
                
                QMessageBox.information(self, "Vitória", "Você venceu e faturou " + moeda(self.aposta) + "!")
            else:
                self.status.setText("Você perdeu!")
                saldo_atual = banco.ler_user(banco.ME["id"], "saldo", 0.0)
                banco.gravar_user(banco.ME["id"], "saldo", saldo_atual - self.aposta)
                
                QMessageBox.information(self, "Derrota", "Você perdeu " + moeda(self.aposta) + ".")
                
            self.janela.aba_banco.atualizar()
        else:
            if self.finalizado == False:
                if vez == self.meu_simbolo:
                    self.status.setText("Sua peça: '" + self.meu_simbolo + "' (Sua vez de jogar)")
                else:
                    self.status.setText("Sua peça: '" + self.meu_simbolo + "' (Aguardando oponente)")

    def fim(self, tabuleiro):
        for combinacao in COMBINACOES_VITORIA:
            pos_1 = combinacao[0]
            pos_2 = combinacao[1]
            pos_3 = combinacao[2]
            
            if tabuleiro[pos_1] != " " and tabuleiro[pos_1] == tabuleiro[pos_2] and tabuleiro[pos_1] == tabuleiro[pos_3]:
                return tabuleiro[pos_1]
                
        tem_espaco_vazio = False
        for espaco in tabuleiro:
            if espaco == " ":
                tem_espaco_vazio = True
                
        if tem_espaco_vazio == False:
            return "-"
            
        return ""
        
    def sair_jogo(self):
        self.timer.stop()
        self.partida = ""
        self.status.setText("...")
        self.janela.setCurrentIndex(2)


class AbaRanking(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

        cabecalho(layout, "regulation.png", "Ranking", "Lista global dos jogadores")

        self.lista_ranking = QListWidget()
        layout.addWidget(self.lista_ranking)
        layout.addSpacing(16)

        layout.addWidget(botao("Atualizar Ranking", self.atualizar))
        layout.addStretch(1)

    def atualizar(self):
        try:
            with aguardando():
                self.lista_ranking.clear()
                jogadores = banco.ler("jogadores", {})
                dados_ranking = []
                
                for nome in jogadores:
                    playfab_id = jogadores[nome]
                    vitorias = banco.ler_user(playfab_id, "vitorias", 0)
                    saldo = banco.ler_user(playfab_id, "saldo", 0.0)
                    dados_ranking.append([nome, int(vitorias), float(saldo)])
                    
                tamanho = len(dados_ranking)
                for i in range(tamanho):
                    for j in range(tamanho - 1):
                        if dados_ranking[j][1] < dados_ranking[j + 1][1]:
                            temporario = dados_ranking[j]
                            dados_ranking[j] = dados_ranking[j + 1]
                            dados_ranking[j + 1] = temporario
                
                for item in dados_ranking:
                    nome = item[0]
                    vitorias = item[1]
                    saldo = item[2]
                    texto_linha = nome + " | Vitórias: " + str(vitorias) + " | Saldo: " + moeda(saldo)
                    self.lista_ranking.addItem(texto_linha)
                    
        except Exception as erro:
            QMessageBox.warning(self, "Erro", str(erro))


class Janela(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jogo da Velha Apostado")
        self.setWindowIcon(QIcon(icone("tic-tac-toe.png", 64)))
        self.resize(700, 760)      
        self.setStyleSheet(QSS)

        self.aba_login = AbaCadastroLogin(self)
        self.aba_banco = AbaBanco(self)
        self.aba_lobby = AbaLobby(self)
        self.aba_jogo = AbaJogo(self)
        self.aba_ranking = AbaRanking(self)

        self.addTab(self.aba_login, "Início")
        self.addTab(self.aba_banco, "Banco")
        self.addTab(self.aba_lobby, "Lobby")
        self.addTab(self.aba_jogo, "Partida")
        self.addTab(self.aba_ranking, "Ranking")

        self.bloquear_acesso()          

    def bloquear_acesso(self):
        self.setTabEnabled(1, False)
        self.setTabEnabled(2, False)
        self.setTabEnabled(3, False)
        self.setTabEnabled(4, False)
        self.setCurrentIndex(0)

    def liberar_acesso(self):
        self.setTabEnabled(1, True)
        self.setTabEnabled(2, True)
        self.setTabEnabled(3, True)
        self.setTabEnabled(4, True)
        self.aba_banco.atualizar()
        self.aba_lobby.carregar_jogadores()
        self.setCurrentIndex(1)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Jogo da Velha Apostado")
    app.setFont(QFont("Segoe UI", 10))  

    janela = Janela()
    janela.show()    

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

