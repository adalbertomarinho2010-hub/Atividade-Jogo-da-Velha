import json, os, sys, uuid, requests
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QMessageBox, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget, QTabWidget)
from config import TITLE_ID, SECRET_KEY

URL = f"https://{TITLE_ID}.playfabapi.com"
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(BASE, "tic-tac-toe.png")
WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
ME = {"ticket": "", "id": "", "nome": ""}

def _aba(widget):
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(60, 44, 60, 44)
    layout.setSpacing(0)
    return layout


def api(path, data, admin=False):
    h = {"X-SecretKey": SECRET_KEY} if admin else {"X-Authorization": ME["ticket"]}
    r = requests.post(URL + path, json=data, headers=h).json()
    if "data" not in r:
        raise Exception(r.get("errorMessage", str(r)))
    return r["data"]


def ler(chave, padrao=None):
    d = api("/Admin/GetTitleData", {"Keys": [chave]}, True)["Data"]
    return json.loads(d[chave]) if chave in d else padrao


def gravar(chave, valor):
    api("/Admin/SetTitleData", {"Key": chave, "Value": json.dumps(valor)}, True)


class Jogo(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)


        self.setWindowTitle("Jogo da Velha - PlayFab")
        self.setWindowIcon(QIcon(ICON))
        self.partida, self.meu_simbolo, self.tab, self.vez = "", "", " " * 9, "X"
        self.telas = QStackedWidget()
        QVBoxLayout(self).addWidget(self.telas)
        self.telas.addWidget(self.tela_cadastro())
        self.telas.addWidget(self.tela_convite())
        self.telas.addWidget(self.tela_jogo())
        self.timer = QTimer(self, interval=3000, timeout=self.atualizar)

    def tela_cadastro(self):
        t = QWidget()
        v = QVBoxLayout(t)
        logo = QLabel(alignment=Qt.AlignCenter)
        logo.setPixmap(QPixmap(ICON).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.email = QLineEdit(placeholderText="E-mail")
        self.usuario = QLineEdit(placeholderText="Usuario (so no cadastro)")
        self.senha = QLineEdit(placeholderText="Senha (min. 6)", echoMode=QLineEdit.Password)
        b1, b2 = QPushButton("Cadastrar"), QPushButton("Entrar")
        b1.clicked.connect(self.cadastrar)
        b2.clicked.connect(self.entrar)
        for w in (logo, QLabel("<h2>Jogo da Velha</h2>"), self.email, self.usuario, self.senha, b1, b2):
            v.addWidget(w)
        return t

    def cadastrar(self):
        self.tentar(lambda: api("/Client/RegisterPlayFabUser", {
            "TitleId": TITLE_ID, "Email": self.email.text(), "Password": self.senha.text(),
            "Username": self.usuario.text(), "RequireBothUsernameAndEmail": True}) and
            QMessageBox.information(self, "Ok", "Cadastrado! Agora clique em Entrar."))

    def entrar(self):
        def acao():
            d = api("/Client/LoginWithEmailAddress", {
                "TitleId": TITLE_ID, "Email": self.email.text(), "Password": self.senha.text()})
            ME["ticket"], ME["id"] = d["SessionTicket"], d["PlayFabId"]
            ME["nome"] = api("/Admin/GetUserAccountInfo", {"PlayFabId": ME["id"]},
                             True)["UserInfo"]["Username"]
            jogadores = ler("jogadores", {})
            jogadores[ME["nome"]] = ME["id"]
            gravar("jogadores", jogadores)
            self.telas.setCurrentIndex(1)
            self.carregar_jogadores()
        self.tentar(acao)

    def tela_convite(self):
        t = QWidget()
        v = QVBoxLayout(t)
        self.lista = QListWidget()
        b0, b1, b2 = QPushButton("Atualizar lista"), QPushButton("Convidar selecionado"), QPushButton("Ver convite recebido")
        b0.clicked.connect(self.carregar_jogadores)
        b1.clicked.connect(self.convidar)
        b2.clicked.connect(self.aceitar)
        for w in (QLabel("<h3>Jogadores cadastrados</h3>"), self.lista, b0, b1, b2):
            v.addWidget(w)
        return t

    def carregar_jogadores(self):
        def acao():
            self.lista.clear()
            self.jogadores = ler("jogadores", {})
            for nome in sorted(self.jogadores):
                if nome != ME["nome"]:
                    self.lista.addItem(nome)
        self.tentar(acao)

    def convidar(self):
        item = self.lista.currentItem()
        if not item:
            return QMessageBox.warning(self, "Erro", "Selecione um jogador na lista.")

        def acao():
            oid = self.jogadores[item.text()]
            self.partida, self.meu_simbolo = uuid.uuid4().hex[:12], "X"
            self.salvar(" " * 9, "X")
            api("/Server/UpdateUserData", {"PlayFabId": oid, "Data": {"convite": self.partida}}, True)
            self.abrir_jogo()
        self.tentar(acao)

    def aceitar(self):
        def acao():
            d = api("/Client/GetUserData", {"Keys": ["convite"]})["Data"]
            if "convite" not in d:
                raise Exception("Nenhum convite recebido ainda.")
            self.partida, self.meu_simbolo = d["convite"]["Value"], "O"
            self.abrir_jogo()
        self.tentar(acao)

    def tela_jogo(self):
        t = QWidget()
        v = QVBoxLayout(t)
        topo = QHBoxLayout()
        img = QLabel()
        img.setPixmap(QPixmap(ICON).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.status = QLabel("...")
        topo.addWidget(img)
        topo.addWidget(self.status, 1)
        g = QGridLayout()
        self.casas = []
        for i in range(9):
            b = QPushButton("")
            b.setFixedSize(80, 80)
            b.setStyleSheet("font-size:32px")
            b.clicked.connect(lambda _, i=i: self.jogar(i))
            g.addWidget(b, i // 3, i % 3)
            self.casas.append(b)
        atual = QPushButton("Atualizar")
        atual.clicked.connect(self.atualizar)
        v.addLayout(topo)
        v.addLayout(g)
        v.addWidget(atual)
        return t

    def abrir_jogo(self):
        self.telas.setCurrentIndex(2)
        self.timer.start()
        self.atualizar()

    def salvar(self, tabuleiro, vez):
        gravar("partida_" + self.partida, {"t": tabuleiro, "v": vez})
        self.mostrar(tabuleiro, vez)

    def atualizar(self):
        def acao():
            e = ler("partida_" + self.partida)
            if e:
                self.mostrar(e["t"], e["v"])
        self.tentar(acao)

    def jogar(self, i):
        t, vez = self.tab, self.vez
        if vez != self.meu_simbolo or t[i] != " " or self.fim(t):
            return
        t = t[:i] + self.meu_simbolo + t[i + 1:]
        self.tentar(lambda: self.salvar(t, "O" if vez == "X" else "X"))

    def mostrar(self, tabuleiro, vez):
        self.tab, self.vez = tabuleiro, vez
        for i, b in enumerate(self.casas):
            b.setText(tabuleiro[i])
        v = self.fim(tabuleiro)
        if v:
            self.status.setText("Voce venceu!" if v == self.meu_simbolo else
                                ("Empate!" if v == "-" else "Voce perdeu!"))
            self.timer.stop()
        else:
            self.status.setText(f"Voce e '{self.meu_simbolo}' - " +
                                ("sua vez" if vez == self.meu_simbolo else "vez do adversario"))

    def fim(self, t):
        for a, b, c in WINS:
            if t[a] != " " and t[a] == t[b] == t[c]:
                return t[a]
        return "-" if " " not in t else ""

    def tentar(self, acao):
        try:
            acao()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

class AbaRanking(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        layout = _aba(self)

class Janela(QTabWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa Eletrônico")
        # self.setWindowIcon(QIcon(icone("bank.png", 64)))
        self.resize(700, 760)      

        self.conta = None

        self.ranking = AbaRanking(self)

        self.addTab(self.ranking, "Ranking")



app = QApplication(sys.argv)
app.setWindowIcon(QIcon(ICON))
j = Jogo()
j.show()
janela = Janela()
janela.show() 
sys.exit(app.exec())
