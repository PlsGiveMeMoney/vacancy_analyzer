import sys
from PyQt5.QtWidgets import QApplication
from app import VacancyAnalyzerApp


def main():
    app = QApplication(sys.argv)

    try:
        with open('styles/styles.css', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Файл стилей не найден")

    window = VacancyAnalyzerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
