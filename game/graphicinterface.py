import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QEventLoop, QTimer
from typing import Optional

class BoardWidget(QWidget):
    """Widget personnalisé pour le rendu graphique du plateau."""
    cell_cliquee = pyqtSignal(int, int)  # Signal émettant (row, col) lors d'un clic

    def __init__(self, board_ref):
        super().__init__()
        self.board = board_ref
        self.setMinimumSize(400, 350)

    def paintEvent(self, event):
        if self.board is None: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calcul des dimensions dynamiques
        w, h = self.width(), self.height()
        rows, cols = self.board.shape
        size = min(w / cols, h / rows)
        radius = size * 0.8
        off_x = (w - cols * size) / 2
        off_y = (h - rows * size) / 2

        # Fond
        painter.fillRect(self.rect(), QColor("#34495e"))

        # Dessin des pions
        for r in range(rows):
            for c in range(cols):
                val = self.board[r, c]
                if val == -1: color = QColor("#e74c3c")   # Rouge
                elif val == 1: color = QColor("#f1c40f") # Jaune
                else: color = QColor("#ecf0f1")           # Vide

                x = off_x + c * size + (size - radius)/2
                y = off_y + r * size + (size - radius)/2

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(x, y, radius, radius))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Conversion Coordonnées Pixel -> Indices Grille
            w, h = self.width(), self.height()
            rows, cols = self.board.shape
            size = min(w / cols, h / rows)
            
            off_x = (w - cols * size) / 2
            off_y = (h - rows * size) / 2

            x_click = event.position().x() - off_x
            y_click = event.position().y() - off_y

            col = int(x_click // size)
            row = int(y_click // size)

            if 0 <= col < cols and 0 <= row < rows:
                self.cell_cliquee.emit(row, col)


class Interface:
    """Gère la fenêtre principale et la synchronisation avec le Contrôleur."""
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

        self.window = QMainWindow()
        self.window.setWindowTitle("Puissance 4 - Humain vs Humain")
        self.window.resize(600, 650)
        self.window.setStyleSheet("background-color: #2c3e50;")

        self.central_widget = QWidget()
        self.window.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.window.show()

        # Mécanisme d'attente active (EventLoop)
        self.loop = QEventLoop()
        self.result = None
        self._running = True
        self.app.aboutToQuit.connect(self._on_quit)

    def _on_quit(self):
        self._running = False
        if self.loop.isRunning():
            self.result = None
            self.loop.quit()

    def _wait(self) -> Optional[object]:
        """Bloque le contrôleur tout en gardant l'interface réactive."""
        if not self._running: return None
        self.loop.exec()
        return self.result

    def _resume(self, value: object) -> None:
        """Libère le contrôleur avec une valeur de retour."""
        self.result = value
        self.loop.quit()

    def _clean_ui(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def send_menu(self, title: str, options: list[str]) -> Optional[int]:
        """Affiche un menu de sélection."""
        if not self._running: return None
        self._clean_ui()

        lbl = QLabel(title)
        lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        for i, txt in enumerate(options):
            btn = QPushButton(txt)
            btn.setFont(QFont("Arial", 14))
            btn.setStyleSheet("background-color: #3498db; color: white; padding: 15px; border-radius: 5px;")
            btn.clicked.connect(lambda _, idx=i: self._resume(idx))
            self.layout.addWidget(btn)

        return self._wait()

    def send_game(self, player: int, board: np.ndarray) -> Optional[tuple[int]]:
        """Affiche le plateau de jeu et attend une action utilisateur."""
        if not self._running: return None
        self._clean_ui()

        nom, code_couleur = self._get_player_info(player)

        lbl = QLabel(f"Au tour de : {nom}")
        lbl.setStyleSheet(f"color: {code_couleur}; font-size: 24px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        board_widget = BoardWidget(board)
        board_widget.cell_cliquee.connect(lambda r, c: self._resume((r, c)))
        
        self.layout.addWidget(board_widget)

        btn = QPushButton("Retour Menu")
        btn.setStyleSheet("background-color: #95a5a6; color: white;")
        btn.clicked.connect(lambda: self._resume(None))
        self.layout.addWidget(btn)

        return self._wait()

    def refresh_only(self, player: int, board: np.ndarray, message: str = None) -> None:
        """Met à jour l'affichage sans attendre d'action."""
        if not self._running: return
        self._clean_ui()
       
        nom, code_couleur = self._get_player_info(player)

        texte = message if message else f"Au tour de : {nom}"

        lbl = QLabel(texte)
        lbl.setStyleSheet(f"color: {code_couleur}; font-size: 24px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        board_widget = BoardWidget(board)
        self.layout.addWidget(board_widget)

        QApplication.processEvents()

    def notify_victory(self, player: int) -> None:
        nom = "ROUGE" if player == -1 else "JAUNE"
        QMessageBox.information(self.window, "Victoire !", f"Le joueur {nom} a gagné !")

    def notify_message(self, message: str)->None:
        QMessageBox.information(self.window, "", message)

    def notify_draw(self) -> None:
        QMessageBox.information(self.window, "Égalité", "Match nul !")

    def set_title(self, title: str) -> None:
        self.window.setWindowTitle(title)
    
    def pause(self, milliseconds: int) -> None:
        """Met en pause l'exécution sans figer l'interface graphique."""
        if not self._running: return
        
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()
    
    def _get_player_info(self, player_code: int):
        """Retourne le nom et la couleur hexadécimale associée au joueur."""
        if player_code == -1: 
            return "Joueur 1 (ROUGE)", "#e74c3c"
        else:                 
            return "Joueur 2 (JAUNE)", "#f1c40f"
