# from contextlib import contextmanager
# from pathlib import Path

# from PySide6.QtCore import Qt
# from PySide6.QtGui import QColor, QPainter, QPixmap
# from PySide6.QtWidgets import (
#     QApplication,
#     QHBoxLayout,
#     QLabel,
#     QLineEdit,
#     QPushButton,
#     QVBoxLayout,
# )
# def cabecalho(layout, arquivo, titulo, subtitulo):
#     linha = QHBoxLayout()
#     linha.setSpacing(14)
#     imagem = QLabel()
#     # imagem.setPixmap(icone(arquivo, 44))

#     textos = QVBoxLayout()
#     textos.setSpacing(2)

#     rotulo = QLabel(titulo)
#     rotulo.setObjectName("titulo")

#     ajuda = QLabel(subtitulo)
#     ajuda.setObjectName("subtitulo")

#     textos.addWidget(rotulo)
#     textos.addWidget(ajuda)

#     linha.addWidget(imagem)
#     linha.addLayout(textos)
#     linha.addStretch(1)

#     layout.addLayout(linha)
#     layout.addSpacing(24)


# def campo(layout, rotulo, placeholder, senha=False):
#     titulo = QLabel(rotulo)
#     titulo.setObjectName("rotulo")

#     entrada = QLineEdit()
#     entrada.setPlaceholderText(placeholder)

#     if senha:
#         entrada.setEchoMode(QLineEdit.Password)

#     layout.addWidget(titulo)
#     layout.addSpacing(6)
#     layout.addWidget(entrada)
#     layout.addSpacing(16)

#     return entrada


# def rotulo_erro(layout):
#     erro = QLabel()
#     erro.setObjectName("erro")
#     erro.setMinimumHeight(18)
#     erro.setWordWrap(True)

#     layout.addWidget(erro)
#     layout.addSpacing(8)

#     return erro


# def botao(texto, ao_clicar, secundario=False):
#     b = QPushButton(texto)
#     b.setCursor(Qt.PointingHandCursor)
#     b.clicked.connect(ao_clicar)

#     if secundario:
#         b.setObjectName("secundario")

#     return b


# @contextmanager
# def aguardando():
#     QApplication.setOverrideCursor(Qt.WaitCursor)
#     try:
#         yield
#     finally:
#         QApplication.restoreOverrideCursor()