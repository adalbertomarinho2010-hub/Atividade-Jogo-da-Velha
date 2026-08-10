from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

IMAGENS = Path(__file__).parent

VERDE = "#0f766e"
VERDE_ESCURO = "#115e59"
CINZA = "#e2e8f0"
TEXTO = "#0f172a"
TEXTO_FRACO = "#64748b"

QSS = f"""
QWidget {{ background: #ffffff; color: {TEXTO}; font-size: 14px; }}
QLabel {{ background: transparent; }}
QTabWidget::pane {{ border: 1px solid {CINZA}; border-radius: 10px; }}
QTabBar::tab {{
background: #f1f5f9; color: {TEXTO_FRACO};
padding: 12px 26px; margin-right: 4px;
border-top-left-radius: 10px; border-top-right-radius: 10px;
font-weight: 600;
}}
QTabBar::tab:selected {{ background: {VERDE}; color: #ffffff; }}
QTabBar::tab:disabled {{ color: #cbd5e1; }}

QLabel#titulo   {{ font-size: 24px; font-weight: 700; }}
QLabel#subtitulo{{ color: {TEXTO_FRACO}; }}
QLabel#rotulo   {{ font-weight: 600; font-size: 13px; }}
QLabel#erro     {{ color: #dc2626; font-size: 12px; }}
QLabel#saldo    {{ color: {VERDE}; font-size: 34px; font-weight: 700; }}

QLineEdit {{
    background: #f8fafc; border: 1.5px solid {CINZA}; border-radius: 8px;
    padding: 0 12px; min-height: 42px;
}}
QLineEdit:focus {{ background: #ffffff; border-color: {VERDE}; }}

QPushButton {{
    background: {VERDE}; color: #ffffff; border: none;
    border-radius: 8px; min-height: 44px; font-weight: 600; padding: 0 18px;
}}
QPushButton:hover {{ background: {VERDE_ESCURO}; }}
QPushButton#secundario {{
    background: #ffffff; color: {VERDE}; border: 1.5px solid {VERDE};
}}
QPushButton#secundario:hover {{ background: #f0fdfa; }}
QPushButton#perigo {{
    background: #ffffff; color: #dc2626; border: 1.5px solid #dc2626;
}}
QPushButton#perigo:hover {{ background: #fef2f2; }}

QPushButton#casa_velha {{
    font-size: 36px; font-weight: bold; background: #f8fafc;
    border: 2px solid {CINZA}; border-radius: 12px;
}}
QPushButton#casa_velha:hover {{ background: #f1f5f9; border-color: {VERDE}; }}
QListWidget {{ background: #f8fafc; border: 1px solid {CINZA}; border-radius: 8px; padding: 6px; }}
"""

def icone(nome, tamanho=40, cor=VERDE):
    caminho = IMAGENS / nome
    if not caminho.exists():
        pixmap = QPixmap(tamanho, tamanho)
        pixmap.fill(Qt.transparent)
        return pixmap
    
    pixmap = QPixmap(str(caminho)).scaled(
        tamanho, tamanho, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    if cor:
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(cor))
        painter.end()
    return pixmap


def cabecalho(layout, arquivo, titulo, subtitulo):
    linha = QHBoxLayout()
    linha.setSpacing(14)
    imagem = QLabel()
    imagem.setPixmap(icone(arquivo, 44))

    textos = QVBoxLayout()
    textos.setSpacing(2)

    rotulo = QLabel(titulo)
    rotulo.setObjectName("titulo")

    ajuda = QLabel(subtitulo)
    ajuda.setObjectName("subtitulo")

    textos.addWidget(rotulo)
    textos.addWidget(ajuda)

    linha.addWidget(imagem)
    linha.addLayout(textos)
    linha.addStretch(1)

    layout.addLayout(linha)
    layout.addSpacing(24)


def campo(layout, rotulo, placeholder, senha=False):
    titulo = QLabel(rotulo)
    titulo.setObjectName("rotulo")

    entrada = QLineEdit()
    entrada.setPlaceholderText(placeholder)

    if senha:
        entrada.setEchoMode(QLineEdit.Password)

    layout.addWidget(titulo)
    layout.addSpacing(6)
    layout.addWidget(entrada)
    layout.addSpacing(16)

    return entrada


def rotulo_erro(layout):
    erro = QLabel()
    erro.setObjectName("erro")
    erro.setMinimumHeight(18)
    erro.setWordWrap(True)

    layout.addWidget(erro)
    layout.addSpacing(8)

    return erro


def botao(texto, ao_clicar, secundario=False, perigo=False):
    elemento_botao = QPushButton(texto)
    elemento_botao.setCursor(Qt.PointingHandCursor)
    elemento_botao.clicked.connect(ao_clicar)

    if secundario:
        elemento_botao.setObjectName("secundario")
    elif perigo:
        elemento_botao.setObjectName("perigo")

    return elemento_botao


@contextmanager
def aguardando():
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


def moeda(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "*").replace(".", ",").replace("*", ".")
