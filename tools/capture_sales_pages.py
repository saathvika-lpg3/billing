from pathlib import Path
import os
import sys
from PyQt6.QtWidgets import QApplication
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from config.app_config import AppConfig
from views.main_window import MainWindow


if __name__ == '__main__':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QApplication([])
    window = MainWindow(AppConfig(PROJECT_ROOT, PROJECT_ROOT))
    window.resize(1440, 900)
    window.show()
    app.processEvents()
    out_dir = PROJECT_ROOT / 'screenshots'
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = ['sales_bill', 'sales_order_entry']
    for page in pages:
        window.open_page(page, remember=False)
        app.processEvents()
        shot = window.grab()
        path = out_dir / f'current_{page}.png'
        shot.save(str(path))
        print(path)
