import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.controller import Controller 

if __name__ == "__main__":
    app_ctrl = Controller()
    app_ctrl.start()
