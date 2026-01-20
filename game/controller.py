from game.gamemanager import variantes, InvalidMove
from game.graphicinterface import Interface


class Controller:
    """Contrôleur principal gérant la boucle de jeu et les interactions utilisateur."""
    def __init__(self):
        self._interface = Interface()
        self._variantes = variantes
        self._gestionnaire = None
        self._in_menu = True
        self._in_game = False

    def start(self):
        """Lance l'application."""
        while self._interface._running:
            if self._in_menu:
                self.menu_principal()
            elif self._in_game:
                self.game_loop()

    def menu_principal(self):
        #  ETAPE 1 : Choix de la Variante 
        choix_variante = self._interface.send_menu(
            "Bienvenue sur Puissance 4",
            [v.name for v in self._variantes]
        )

        if choix_variante is None: 
            return # Fermeture de la fenêtre

        #  ETAPE 2 : Choix du Mode 
        choix_mode = self._interface.send_menu(
            "Choisissez le mode de jeu",
            ["1 Joueur (Contre l'IA)", "2 Joueurs (Local)"]
        )

        if choix_mode is None: 
            return

        mode_solo = (choix_mode == 0)
        difficulty = 4

        #  ETAPE 3 : Difficulté (Mode solo uniquement) 
        if mode_solo:
            choix_diff = self._interface.send_menu(
                "Niveau de difficulté",
                ["Facile", "Moyen", "Difficile"]
            )
            if choix_diff is None: return
            
            # Mapping : Index -> Profondeur de recherche
            niveaux = [2, 4, 6]
            difficulty = niveaux[choix_diff]

        #  INITIALISATION 
        self._gestionnaire = self._variantes[choix_variante](
            mode_solo=mode_solo, 
            difficulty=difficulty
        )
        
        self._in_menu = False
        self._in_game = True

    def game_loop(self):
        """Boucle principale d'une partie."""
        # Récupération de l'action humaine via l'interface
        move = self._interface.send_game(
            self._gestionnaire.current_player,
            self._gestionnaire.board
        )

        if move is None:  # Retour au Menu
            self._in_game = False
            self._in_menu = True
            self._gestionnaire = None
            return

        try:
            #  TOUR HUMAIN 
            self._gestionnaire.play(move)

            if self.check_game_end():
                return 

            #  TOUR IA 
            if getattr(self._gestionnaire, 'mode_solo', False):
                
                # Mise à jour visuelle avant le coup de l'IA
                self._interface.refresh_only(self._gestionnaire.current_player, self._gestionnaire.board)
                
                # Pause pour la fluidité de l'animation
                self._interface.pause(700) 
                
                # Calcul et exécution du coup de l'IA
                self._gestionnaire.play_ai_turn()

                if self.check_game_end():
                    return

        except InvalidMove:
            pass  # Le coup est invalide, on attend une nouvelle entrée

    def check_game_end(self):
        """Vérifie les conditions de fin de partie (Victoire, Égalité) ou les événements."""
        
        if self._gestionnaire.victory:
            self._interface.refresh_only(self._gestionnaire.current_player, self._gestionnaire.board)
            self._interface.notify_victory(self._gestionnaire.current_player)
            self._in_game = False
            self._in_menu = True
            return True

        elif self._gestionnaire.draw:
            self._interface.refresh_only(self._gestionnaire.current_player, self._gestionnaire.board)
            self._interface.notify_draw()
            self._in_game = False
            self._in_menu = True
            return True

        # Gestion des messages liés aux événements de variante
        elif getattr(self._gestionnaire, 'event', False):
            self._interface.notify_message(self._gestionnaire.message_event)
            self._interface.refresh_only(self._gestionnaire.current_player, self._gestionnaire.board)
            return False 

        return False
