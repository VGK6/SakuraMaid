#!/usr/bin/env python3
"""
樱花庄小女仆 · 桌宠 v2.0
入口点: 先显示配置UI → 再启动桌宠
"""
import os, sys
from PySide6.QtWidgets import QApplication
from ui.config_ui import ConfigUI, load_config
from core.pet_window import MaidPet
from modules.config_store import save as save_store

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MaidPet")

    # 第一步: 配置UI
    cfg_ui = ConfigUI()
    cfg_ui.show()
    app.exec()

    # 如果用户点了保存，才启动桌宠
    if cfg_ui.accepted:
        # 同步配置到config_store
        cfg = cfg_ui.cfg
        save_store(cfg)
        
        # 启动桌宠
        pet = MaidPet(cfg)
        sys.exit(app.exec())
    else:
        print("用户取消配置，退出")

if __name__ == '__main__':
    main()
