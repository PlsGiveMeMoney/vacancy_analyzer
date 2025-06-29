from PyQt5.QtWidgets import QStackedWidget, QMessageBox
from gui.login_window import LoginWindow
from core.database import Database


class VacancyAnalyzerApp:
    def __init__(self):
        self.stacked_widget = QStackedWidget()
        self.current_user = None
        self.database = Database()

        self.database.create_tables()

        self.login_window = LoginWindow(self)
        self.main_window = None
        self.admin_panel = None

        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.setWindowTitle('Анализатор вакансий')
        self.stacked_widget.resize(1000, 700)
        self.stacked_widget.show()

    def show_main_window(self):
        try:
            if self.main_window is None:
                from gui.main_window import MainWindow
                self.main_window = MainWindow(self)
                self.stacked_widget.addWidget(self.main_window)

            self.stacked_widget.setCurrentWidget(self.main_window)
            self.stacked_widget.setWindowTitle(f'Анализатор вакансий - {self.current_user.login}')
        except Exception as e:
            QMessageBox.critical(None, 'Ошибка', f'Не удалось открыть главное окно: {str(e)}')

    def show_admin_panel(self):
        try:
            if self.admin_panel is None:
                from gui.admin_panel import AdminPanel
                self.admin_panel = AdminPanel(self)
                self.stacked_widget.addWidget(self.admin_panel)

            self.stacked_widget.setCurrentWidget(self.admin_panel)
            self.stacked_widget.setWindowTitle('Анализатор вакансий - Панель администратора')
        except Exception as e:
            QMessageBox.critical(None, 'Ошибка', f'Не удалось открыть панель администратора: {str(e)}')
            self.stacked_widget.setCurrentWidget(self.login_window)

    def logout(self):
        self.current_user = None
        self.stacked_widget.setCurrentWidget(self.login_window)

        if self.main_window:
            self.main_window.deleteLater()
            self.main_window = None

        if self.admin_panel:
            self.admin_panel.deleteLater()
            self.admin_panel = None
