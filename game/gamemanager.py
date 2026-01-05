import numpy as np
from abc import ABC, abstractmethod
from calculateur import AIModel


class InvalidMove(Exception):
    """Exception levée lorsqu'un coup n'est pas valide."""
    pass

class Gestionnaire(ABC):
    """Classe abstraite du jeu."""
    name: str = "Jeu"

    def __init__(self,mode_solo=False, difficulty=4):
        self._width = 7
        self._height = 6
        self._board = np.zeros((self._height, self._width), dtype=int)
        self._current_player = -1  # 1 = Rouge, -1 = Jaune
        self._victory = False
        self._draw = False
        self._event = False
        self._message_event = ""

        self.mode_solo = mode_solo
        self.difficulty = difficulty # Profondeur du Minimax
        self.ai_engine = None
        
        if self.mode_solo:
            print(f"Initialisation du mode SOLO (Difficulté {difficulty})")
            try:
                self.ai_engine = AIModel() # Charge le C++
            except Exception as e:
                print(f"Erreur critique : Impossible de charger l'IA C++. {e}")

    def check_victory(self, move: tuple[int, int], player: int, n : int) -> bool:
        """Vérifie si le coup joué complète un alignement de n."""
        r, c = move
        # Directions : Horizontal, Vertical, Diag \, Diag /
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1 # Le pion qu'on vient de poser

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
        Demande au C++ quelle colonne jouer.
        Ne joue pas le coup directement, renvoie juste la colonne.
        """
        if not self.ai_engine:
            return None
        
        # Le C++ attend le plateau et la profondeur
        # Attention : Ton C++ considère que l'IA est le joueur 'AI_PIECE' (souvent défini à 1 ou 2).
        # Il faut s'assurer que le tableau envoyé correspond à ce que le C++ attend.
        # Si ton C++ attend 1 pour l'IA et -1 pour l'Humain, c'est bon si self.current_player est l'IA.
        
        print("🤖 L'IA réfléchit...")
        col = self.ai_engine.get_best_move(self.grid, depth=self.difficulty)
        print(f"🤖 L'IA a choisi la colonne {col}")
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
    """Variante classique du puissance 4."""
    name = "Puissance 4 Classique"

    def __init__(self, mode_solo=False, difficulty=4):
        # On passe les paramètre au parent pour qu'il charge l'IA
        super().__init__(mode_solo=mode_solo, difficulty=difficulty)
    
    def play(self, move: tuple[int, int]) -> None:
        _, col = move

        # 1. Validation
        if col < 0 or col >= self.width or self.board[0, col] != 0:
            raise InvalidMove("Colonne pleine ou invalide.")

        # 2. Gravité : Trouver la ligne
        r_found = -1
        for r in range(self.height - 1, -1, -1):
            if self.board[r, col] == 0:
                self.board[r, col] = self._current_player
                r_found = r
                break

        # 3. Vérification Victoire
        # Si le joueur actuel gagne, on active le flag et ON NE CHANGE PAS de joueur.
        # Ainsi, self.current_player désignera le gagnant.
        if self.check_victory((r_found, col), self._current_player, 4):
            self._victory = True

        # 4. Vérification Égalité
        elif np.all(self.board != 0):
            self._draw = True

        # 5. Sinon, tour suivant
        else:
            self._current_player *= -1
    
    def play_ai_turn(self):
        """
        1. Demande au C++ la meilleure colonne.
        2. Construit le move.
        3. Appelle play().
        """
        if not self.mode_solo or not self.ai_engine:
            return

        # On vérifie que c'est bien à l'IA de jouer (Joueur -1)
        if self._current_player != 1:
            return

        
        # APPEL AU C++ (C'est ici que la magie opère)
        # On envoie la grille numpy et la profondeur
        best_col = self.ai_engine.get_best_move(self.board, depth=self.difficulty)
        

        # On exécute le coup comme si c'était un humain
        # On passe (0, best_col) car ta méthode play attend un tuple, 
        # même si le 0 ne sert à rien grâce à la gravité.
        self.play((0, best_col))

    

class Variante_1(Gestionnaire):
    name = "1 pour 3"
    def __init__(self):
        super().__init__()
        self._message_event = "Vous pouvez retirer un pion de votre adversaire"
        self._event = False

 

    def play(self, move: tuple[int, int]) -> None:

        ### COUP CLASSIQUE ###
        if not self._event:
            _, col = move

            # 1. Validation
            if col < 0 or col >= self.width or self.board[0, col] != 0:
                raise InvalidMove("Colonne pleine ou invalide.")

            # 2. Gravité : Trouver la ligne
            r_found = -1
            for r in range(self.height - 1, -1, -1):
                if self.board[r, col] == 0:
                    self.board[r, col] = self._current_player
                    r_found = r
                    break
            
            # --- CORRECTION DE L'ORDRE DES VÉRIFICATIONS ---

            # 3. PRIORITÉ ABSOLUE : Vérification Victoire (4 alignés)
            # On vérifie D'ABORD si on a gagné.
            if self.check_victory((r_found, col), self._current_player, 4):
                self._victory = True
                # La partie est finie, on ne change pas de joueur, on ne déclenche pas l'event.

            # 4. PRIORITÉ SECONDAIRE : Vérification Événement (3 alignés)
            # Si on n'a pas gagné, on regarde si on en a aligné 3.
            elif self.check_victory((r_found, col), self._current_player, 3):
                self._event = True 
                # On reste sur le même joueur pour qu'il puisse effectuer son action bonus.

            # 5. Vérification Égalité
            elif np.all(self.board != 0):
                self._draw = True

            # 6. Sinon, c'est un tour normal qui se termine
            else:
                self._current_player *= -1
        
        ### EVENEMENT ###
        else:
            row, col = move
            other_player = self.current_player * -1

            # 1. Validation
            if (row < 0 or row >= self.height or 
                col < 0 or col >= self.width or 
                self.board[row, col] != other_player):
                raise InvalidMove("Vous devez cliquer sur un pion adverse !")

            # 2. Retrait du pion
            self._board[row, col] = 0

            # 3. Gravité
            for r in range(row, 0, -1):
                self._board[r, col] = self._board[r-1, col]
            self._board[0, col] = 0

            # 4. Vérification Victoire
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

            # 5. Gestion du résultat et du Changement de joueur
            
            if victoire_moi and victoire_autre:
                self._draw = True
                # En cas d'égalité, peu importe qui est current_player
            
            elif victoire_moi:
                self._victory = True
                # IMPORTANT : On NE change PAS de joueur.
                # self.current_player est celui qui a joué, donc le gagnant.
            
            elif victoire_autre:
                self._victory = True
                # IMPORTANT : L'adversaire a gagné (contre son camp ou chute).
                # On force current_player sur l'adversaire pour l'affichage.
                self._current_player = other_player

            else:
                # CAS NORMAL : Personne n'a gagné.
                # C'est SEULEMENT ICI qu'on passe la main à l'adversaire.
                self._current_player *= -1

            # On désactive l'événement quoi qu'il arrive
            self._event = False 


        




# Liste des variantes disponibles (export)
variantes = [ClassicGame, Variante_1]






