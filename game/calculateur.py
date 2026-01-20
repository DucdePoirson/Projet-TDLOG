import ctypes
import numpy as np
import os
import platform

class AIModel:
    """Interface Python pour la librairie C++ de l'IA."""
    def __init__(self):
        # Détection de l'extension selon l'OS
        if platform.system() == "Darwin":
            lib_name = "libai_lib.dylib"
        elif platform.system() == "Windows":
            lib_name = "ai_lib.dll"
        else:
            lib_name = "libai_lib.so"

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Recherche du binaire compilé
        lib_path = os.path.join(project_root, "ai_engine", "build", lib_name)

        if not os.path.exists(lib_path):
            lib_path_debug = os.path.join(project_root, "ai_engine", "build", "Debug", lib_name)
            if os.path.exists(lib_path_debug):
                lib_path = lib_path_debug
            else:
                raise FileNotFoundError("Librairie IA introuvable. Veuillez compiler le moteur C++.")

        self.lib = ctypes.CDLL(lib_path)

        # Définition de la signature de la fonction C++
        self.lib.get_best_move.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),
            ctypes.c_int, # Profondeur
            ctypes.c_int  # Mode de jeu
        ]
        self.lib.get_best_move.restype = ctypes.c_int

    def get_best_move(self, board, depth=4, mode=0):
        """Appelle la fonction Minimax du moteur C++."""
        board_flat = board.flatten().astype(np.int32)
        return self.lib.get_best_move(board_flat, depth, mode)
