import numpy as np
from abc import ABC, abstractmethod
from game.calculateur import AIModel


class InvalidMove(Exception):
    """Exception levée lorsqu'un coup n'est pas valide."""
    pass

class Gestionnaire(ABC):
    """Classe abstraite du jeu gérant l'état du plateau et les règles communes."""
    name: str = "Jeu"

    def __init__(self, mode_solo=False, difficulty=4):
        self._width = 7
        self._height = 6
        self._board = np.zeros((self._height, self._width), dtype=int)
        self._current_player = -1  # 1 = Rouge, -1 = Jaune
        self._victory = False
        self._draw = False
        self._event = False
        self._message_event = ""

        self.mode_solo = mode_solo
        self.difficulty = difficulty # Profondeur de recherche du Minimax
        self.ai_engine = None
        
        if self.mode_solo:
            print(f"Initialisation du mode SOLO (Difficulté {difficulty})")
            try:
                self.ai_engine = AIModel() # Chargement de la librairie C++
            except Exception as e:
                print(f"Erreur critique : Impossible de charger l'IA C++. {e}")

    def check_victory(self, move: tuple[int, int], player: int, n : int) -> bool:
        """Vérifie si le coup joué complète un alignement de taille n."""
        r, c = move
        # Directions : Horizontal, Vertical, Diagonale \, Diagonale /
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1 # On compte le pion que l'on vient de poser

            # Sens positif
            for i in range(1, n):
                nr, nc = r + dr*i, c + dc*i
                if 0 <= nr < self.height and 0 <= nc < self.width and self.board[nr, nc] == player:
                    count += 1
                else: break

            # Sens négatif
            for i in range(1, n):
                nr, nc = r - dr*i, c - dc*i
                if 0 <= nr < self.height and 0 <= nc < self.width and self.board[nr, nc] == player:
                    count += 1
                else: break

            if count >= n:
                return True
        return False
    
    def get_ai_move(self):
        """
        Demande au moteur C++ la meilleure colonne à jouer.
        Ne joue pas le coup directement, renvoie uniquement l'index de la colonne.
        """
        if not self.ai_engine:
            return None
        
        print("L'IA réfléchit...")
        col = self.ai_engine.get_best_move(self.board, depth=self.difficulty)
        print(f"L'IA a choisi la colonne {col}")
        return col

    @abstractmethod
    def play(self, move: tuple[int, int]) -> None:
        pass

    @property
    def board(self): return self._board

    @property
    def width(self): return self._width

    @property
    def height(self): return self._height

    @property
    def current_player(self): return self._current_player

    @property
    def victory(self): return self._victory

    @property
    def draw(self): return self._draw

    @property
    def event(self): return self._event

    @property
    def message_event(self): return self._message_event


class ClassicGame(Gestionnaire):
    """Implémentation des règles du Puissance 4 classique."""
    name = "Puissance 4 Classique"

    def __init__(self, mode_solo=False, difficulty=4):
        super().__init__(mode_solo=mode_solo, difficulty=difficulty)
    
    def play(self, move: tuple[int, int]) -> None:
        _, col = move

        # 1. Validation du coup
        if col < 0 or col >= self.width or self.board[0, col] != 0:
            raise InvalidMove("Colonne pleine ou invalide.")

        # 2. Application de la gravité
        r_found = -1
        for r in range(self.height - 1, -1, -1):
            if self.board[r, col] == 0:
                self.board[r, col] = self._current_player
                r_found = r
                break

        # 3. Vérification de la victoire
        if self.check_victory((r_found, col), self._current_player, 4):
            self._victory = True

        # 4. Vérification de l'égalité (grille pleine)
        elif np.all(self.board != 0):
            self._draw = True

        # 5. Changement de tour
        else:
            self._current_player *= -1
    
    def play_ai_turn(self):
        """
        Gère le tour de l'IA : calcul du meilleur coup et exécution.
        """
        if not self.mode_solo or not self.ai_engine:
            return

        # On vérifie que c'est bien au tour de l'IA (Joueur 1)
        if self._current_player != 1:
            return

        # Appel au moteur C++
        # Conversion du plateau en tableau 1D d'entiers 32 bits
        board_c = self.board.flatten().astype(np.int32)
        
        # Mode 0 correspond au jeu classique
        best_col = self.ai_engine.get_best_move(board_c, depth=self.difficulty, mode=0)
        
        # On exécute le coup
        self.play((0, best_col))

    

class Variante_1(Gestionnaire):
    """Variante '1 pour 3' : Aligner 3 pions permet de supprimer un pion adverse."""
    name = "1 pour 3"

    def __init__(self, mode_solo=False, difficulty=4):
        super().__init__(mode_solo=mode_solo, difficulty=difficulty)
        self._message_event = "Vous pouvez retirer un pion de votre adversaire"
        self._event = False

    def get_best_victim(self, opponent_player):
        """Détermine le meilleur pion adverse à supprimer (stratégie IA)."""
        # Priorité : Centre du plateau, du bas vers le haut
        priority_cols = [3, 2, 4, 1, 5, 0, 6]
        for col in priority_cols:
            for row in range(self.height - 1, -1, -1):
                if self.board[row, col] == opponent_player:
                    return (row, col)
        return None

    def play_ai_turn(self):
        """Logique spécifique de l'IA pour la variante (pose et suppression)."""
        if not self.mode_solo or not self.ai_engine or self._current_player != 1:
            return

        # 1. Calcul du meilleur coup (Mode 1 = Variante)
        board_c = self.board.flatten().astype(np.int32)
        best_col = self.ai_engine.get_best_move(board_c, depth=self.difficulty, mode=1)

        # 2. L'IA joue le coup (Phase de pose)
        try:
            self.play((0, best_col))
        except InvalidMove:
            return

        # 3. Gestion de l'événement (Si l'IA a aligné 3 pions)
        if self._event:
            target = self.get_best_victim(-1) # Cible l'humain (-1)
            
            if target:
                print(f"L'IA supprime le pion en {target}")
                self.play(target) # Déclenche la phase de suppression
            else:
                self._event = False
                self._current_player *= -1

    def play(self, move: tuple[int, int]) -> None:
        """Gestion du tour : soit pose de pion, soit suppression selon l'état de l'événement."""
        
        #  CAS 1 : TOUR NORMAL (POSER UN PION) 
        if not self._event:
            _, col = move

            if col < 0 or col >= self.width or self.board[0, col] != 0:
                raise InvalidMove("Colonne pleine ou invalide.")

            # Application de la gravité
            r_found = -1
            for r in range(self.height - 1, -1, -1):
                if self.board[r, col] == 0:
                    self.board[r, col] = self._current_player
                    r_found = r
                    break
            
            #  PRIORITÉS DES RÈGLES 

            # 1. Victoire (4 alignés) -> Fin de partie
            if self.check_victory((r_found, col), self._current_player, 4):
                self._victory = True

            # 2. Événement (3 alignés) -> Action bonus (Suppression)
            elif self.check_victory((r_found, col), self._current_player, 3):
                self._event = True 
                # On ne change pas de joueur pour permettre l'action de suppression

            # 3. Égalité
            elif np.all(self.board != 0):
                self._draw = True

            # 4. Tour suivant standard
            else:
                self._current_player *= -1
        
        #  CAS 2 : ÉVÉNEMENT (SUPPRIMER UN PION) 
        else:
            row, col = move
            # Détermination de la cible (Si je suis 1, je vise -1)
            other_player = -1 if self.current_player == 1 else 1
            
            if (row < 0 or row >= self.height or 
                col < 0 or col >= self.width or 
                self.board[row, col] != other_player):
                raise InvalidMove("Vous devez cliquer sur un pion adverse !")

            # Suppression du pion
            self._board[row, col] = 0

            # Gravité après suppression (Chute des pions du dessus)
            for r in range(row, 0, -1):
                self._board[r, col] = self._board[r-1, col]
            self._board[0, col] = 0

            # Vérification des conditions de victoire après la chute
            victoire_moi = False
            victoire_autre = False

            # On scanne la colonne modifiée
            for r in range(self.height):
                pion = self.board[r, col]
                if pion != 0:
                    if self.check_victory((r, col), pion, 4):
                        if pion == self.current_player:
                            victoire_moi = True
                        else:
                            victoire_autre = True

            # Résolution des conflits de victoire post-gravité
            if victoire_moi and victoire_autre:
                self._draw = True
            elif victoire_moi:
                self._victory = True
            elif victoire_autre:
                self._victory = True 
                self._current_player = other_player # L'adversaire gagne suite à notre action
            else:
                self._current_player *= -1

            self._event = False


# Liste des variantes disponibles
variantes = [ClassicGame, Variante_1]
