import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QEventLoop, QTimer
from typing import Optional

class BoardWidget(QWidget):
    """Widget personnalisé qui dessine le plateau."""
    cell_cliquee = pyqtSignal(int, int)  # On envoie (row, col)

    def __init__(self, board_ref):
        super().__init__()
        self.board = board_ref
        self.setMinimumSize(400, 350)

    def paintEvent(self, event):
        if self.board is None: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calcul dimensions
        w, h = self.width(), self.height()
        rows, cols = self.board.shape
        size = min(w / cols, h / rows)
        radius = size * 0.8
        off_x = (w - cols * size) / 2
        off_y = (h - rows * size) / 2

        # Fond Bleu
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
            # Conversion Pixel -> Colonne ET Ligne
            w, h = self.width(), self.height()
            rows, cols = self.board.shape
            size = min(w / cols, h / rows)
            
            off_x = (w - cols * size) / 2
            off_y = (h - rows * size) / 2

            x_click = event.position().x() - off_x
            y_click = event.position().y() - off_y  # Ajout calcul Y

            col = int(x_click // size)
            row = int(y_click // size)      # Ajout calcul Row

            # Vérifier que le clic est bien dans la grille
            if 0 <= col < cols and 0 <= row < rows:
                # On émet maintenant (row, col)
                self.cell_cliquee.emit(row, col)


class Interface:
    """Gère la fenêtre et la synchronisation avec le Contrôleur."""
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

        # Outils de pause
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
        """Bloque le contrôleur mais laisse l'UI active."""
        if not self._running: return None
        self.loop.exec()
        return self.result

    def _resume(self, value: object) -> None:
        """Débloque le contrôleur."""
        self.result = value
        self.loop.quit()

    def _clean_ui(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def send_menu(self, title: str, options: list[str]) -> Optional[int]:
        """Affiche un menu."""
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
        if not self._running: return None
        self._clean_ui()

        # On utilise la nouvelle méthode
        nom, code_couleur = self._get_player_info(player)

        lbl = QLabel(f"Au tour de : {nom}")
        lbl.setStyleSheet(f"color: {code_couleur}; font-size: 24px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)

        board_widget = BoardWidget(board)
    
        # CORRECTION ICI : On récupère r et c directement du signal
        # Avant c'était : lambda c: self._resume((0, c))
        board_widget.cell_cliquee.connect(lambda r, c: self._resume((r, c)))
        
        self.layout.addWidget(board_widget)

        btn = QPushButton("Retour Menu")
        btn.setStyleSheet("background-color: #95a5a6; color: white;")
        btn.clicked.connect(lambda: self._resume(None))
        self.layout.addWidget(btn)

        return self._wait()

    def refresh_only(self, player: int, board: np.ndarray, message: str = None) -> None:
        if not self._running: return
        self._clean_ui()
       
        # On utilise la nouvelle méthode
        nom, code_couleur = self._get_player_info(player)

        if message:
            texte = message
        else:
            texte = f"Au tour de : {nom}"

        lbl = QLabel(texte)
        lbl.setStyleSheet(f"color: {code_couleur}; font-size: 24px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl)
        # ----------------------

        board_widget = BoardWidget(board)
        self.layout.addWidget(board_widget)

        QApplication.processEvents()

    def notify_victory(self, player: int) -> None:
        # player est le gagnant (-1 ou 1)
        nom = "ROUGE" if player == -1 else "JAUNE" # <-- Correction ici
        QMessageBox.information(self.window, "Victoire !", f"Le joueur {nom} a gagné !")

    def notify_message(self, message: str)->None:
        QMessageBox.information(self.window, "", message)

    def notify_draw(self) -> None:
        QMessageBox.information(self.window, "Égalité", "Match nul !")

    # Ajoute ceci dans la classe Interface
    def set_title(self, title: str) -> None:
        self.window.setWindowTitle(title)
    
    def pause(self, milliseconds: int) -> None:
        """Met le programme en pause sans geler la fenêtre."""
        if not self._running: return
        
        # On crée une petite boucle d'attente locale
        loop = QEventLoop()
        # On dit au Timer : "Dans X ms, arrête la boucle"
        QTimer.singleShot(milliseconds, loop.quit)
        # On lance la boucle (ça bloque le code ici, mais l'interface reste vivante)
        loop.exec()
    
    # Ajoute ce bloc DANS la classe Interface (attention à l'indentation)
    def _get_player_info(self, player_code: int):
        """Retourne le nom et la couleur selon le code joueur (-1 ou 1)."""
        if player_code == -1: 
            # C'est le Joueur 1 (ROUGE)
            return "Joueur 1 (ROUGE)", "#e74c3c"
        else:                 
            # C'est le Joueur 2 (JAUNE / IA)
            return "Joueur 2 (JAUNE)", "#f1c40f"
