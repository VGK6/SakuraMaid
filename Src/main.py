#!/usr/bin/env python3
"""
樱花庄小女仆 · 桌宠 v1.0
入口点
"""
import sys
from PySide6.QtWidgets import QApplication
from core.pet_window import MaidPet

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MaidPet")
    pet = MaidPet()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
