import numpy as np
from game.calculateur import AIModel

def test():
    print("Test de connexion au moteur C++...")
    try:
        ai = AIModel()
    except Exception as e:
        print(f"Erreur : {e}")
        return

    # Création d'un plateau vide
    board = np.zeros((6, 7), dtype=np.int32)

    # Simulation : L'adversaire a 3 pions alignés, l'IA doit bloquer
    board[5, 0] = 1 
    board[5, 1] = 1
    board[5, 2] = 1
    
    print("\nPlateau envoyé à l'IA :")
    print(board)

    print("\nCalcul du coup (Profondeur 4)...")
    col = ai.get_best_move(board, depth=4)

    print(f"L'IA a choisi la colonne : {col}")
    
    if col == 3:
        print("SUCCES : L'IA a complété l'alignement.")
    else:
        print("ECHEC : L'IA n'a pas joué le coup optimal.")

if __name__ == "__main__":
    test()