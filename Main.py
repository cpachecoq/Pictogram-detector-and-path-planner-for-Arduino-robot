import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QGridLayout, QFrame, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize

from calculoCentroides import IntegratedApp  # tu clase actual

EMOJI_BY_CATEGORY = {
    "Chakana": "🧩", "Maiz": "🌽", "Condor": "🦅",
    "Llama": "🦙", "Cuy": "🐹", "Tinaja": "🏺", "Zampoña": "🎶",
}

ICON_BY_CATEGORY = {
    "Chakana": "assets/icons/Chakana.png",
    "Maiz": "assets/icons/Maiz.png",
    "Condor": "assets/icons/Condor.png",
    "Llama": "assets/icons/Llama.png",
    "Cuy": "assets/icons/Cuy.png",
    "Tinaja": "assets/icons/Tinaja.png",
    "Zampoña": "assets/icons/Zampona.png",
}

LIGHT_QSS = """
/* === Fondo exterior celeste infantil === */
QWidget {
    background-color: #B5E5FF;  /* celeste suave */
    color: #123;
}

/* === Tarjeta interior (blanca) === */
QFrame#Card {
    background: #FFFFFF;
    border: 2px solid rgba(0,0,0,0.06);
    border-radius: 20px;
}

/* === Textos === */
QLabel#Title {
    color: #1B3A57;
    font-size: 22px;
    font-weight: 800;
}
QLabel#Subtitle {
    color: #2A5676;
    font-size: 14px;
    font-weight: 600;
}

/* === Botones generales === */
QPushButton.Category {
    background: #FDFDFE;
    border: 3px solid #D8EAFE;
    border-radius: 18px;
    padding: 18px 22px;
    font-size: 18px;
    font-weight: 700;
    text-align: left;
}
QPushButton.Category:hover {
    background: #F2F8FF;
    border-color: #A8D0FF;
}
QPushButton.Category:pressed {
    background: #E6F0FF;
    border-color: #7FB8FF;
}

/* === Botón de ayuda (naranja) === */
QPushButton#HelpBtn {
    background: #FFD580;
    border: 3px solid #FFB347;
    border-radius: 18px;
    padding: 18px 22px;
    font-size: 18px;
    font-weight: 700;
    text-align: left;
}
QPushButton#HelpBtn:hover {
    background: #FFC266;
    border-color: #FFA500;
}
QPushButton#HelpBtn:pressed {
    background: #FFB84D;
    border-color: #FF9100;
}

/* === Botón de pantalla completa grande (abajo) === */
QPushButton#FullBtn {
    background: #A8E6CF;            /* verde menta suave */
    border: 3px solid #81D4AF;
    border-radius: 22px;
    padding: 20px 30px;
    font-size: 20px;
    font-weight: 800;
    min-height: 80px;
    min-width: 260px;
    color: #064E3B;
}
QPushButton#FullBtn:hover {
    background: #96E0C1;
    border-color: #6FC7A3;
}
QPushButton#FullBtn:pressed {
    background: #8BD8B3;
    border-color: #52B788;
}
"""

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cavia – Explorador de Figuras")
        self.setGeometry(200, 100, 560, 720)
        self.detector = None

        self.setStyleSheet(LIGHT_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # ===== Encabezado =====
        header = QVBoxLayout()
        title = QLabel("🐹 Cavia – Explorador de Figuras")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Black))

        subtitle = QLabel("Toca una tarjeta para comenzar la aventura")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        # ===== Tarjeta blanca (contenedor de los botones) =====
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # ===== Grid de 8 botones (4 filas × 2 columnas) =====
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        categories = ["Chakana", "Maiz", "Condor", "Llama", "Cuy", "Tinaja", "Zampoña"]
        font_button = QFont("Arial", 16, QFont.Weight.Bold)

        # Crear los 7 botones de figuras
        for idx, name in enumerate(categories):
            btn = QPushButton(f"{EMOJI_BY_CATEGORY.get(name,'✨')}  {name}")
            btn.setFont(font_button)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName(f"btn_{name}")
            btn.setMinimumHeight(84)
            btn.setProperty("class", "Category")
            btn.setStyleSheet("QPushButton { text-align: left; }")
            btn.clicked.connect(lambda checked=False, n=name: self.launch_camera(n))
            r, c = divmod(idx, 2)
            grid.addWidget(btn, r, c)

        # Botón de ayuda (octavo)
        help_btn = QPushButton("❓ Ayuda")
        help_btn.setFont(font_button)
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setObjectName("HelpBtn")
        help_btn.setMinimumHeight(84)
        help_btn.setStyleSheet("QPushButton { text-align: left; }")
        help_btn.clicked.connect(self.show_help)
        grid.addWidget(help_btn, 3, 1)

        card_layout.addLayout(grid)
        root.addWidget(card)

        # ===== Botón de pantalla completa (grande, abajo) =====
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full_btn = QPushButton("⛶ Pantalla completa")
        full_btn.setObjectName("FullBtn")
        full_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        full_btn.clicked.connect(self.toggle_fullscreen)
        bottom_layout.addWidget(full_btn)
        root.addLayout(bottom_layout)

        root.addStretch()

    # ======= Funciones =======
    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Cómo jugar")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            "👋 ¡Hola! Elige una tarjeta para explorar.\n\n"
            "• La cámara buscará la figura seleccionada.\n"
            "• Mantén la figura frente a la cámara y ¡observa qué pasa!\n"
            "• Si quieres cambiar de figura, cierra la ventana y vuelve aquí.\n\n"
            "Consejo: ilumina bien la escena y mantén la figura centrada."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def toggle_fullscreen(self):
        if self.windowState() & Qt.WindowState.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

    def launch_camera(self, name: str):
        if self.detector is not None and self.detector.isVisible():
            try:
                self.detector.close()
            except Exception as e:
                print(f"Error al cerrar instancia previa: {e}")

        print(f"Lanzando módulo para: {name}")
        self.detector = IntegratedApp()
        self.detector.setWindowTitle(f"Detección: {name}")

        if hasattr(self.detector, "setCategory") and callable(getattr(self.detector, "setCategory")):
            self.detector.setCategory(name)
        elif hasattr(self.detector, "category"):
            try:
                self.detector.category = name
            except Exception:
                pass

        self.detector.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
