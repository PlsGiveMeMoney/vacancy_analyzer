from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton,  QStackedWidget
)
from PyQt5.QtCore import Qt
from gui.collection_ui import CollectionUI

from gui.reports_ui import ReportsUI
from gui.visualization_ui import VisualizationUI
from gui.export_ui import ExportUI
from gui.account_ui import AccountUI
from core.database import Database, UserDatabase


class MainWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.user_id = app.current_user.id if app.current_user else None
        self.user_db = UserDatabase(self.user_id)
        self.db = Database()
        self.current_active_button = None
        self.setup_ui()

    def navigate_to_reports(self):
        self.stacked_widget.setCurrentWidget(self.reports_ui)
        self.set_active_button('Отчёты')
    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        menu_widget = QWidget()
        menu_widget.setFixedWidth(200)
        menu_widget.setStyleSheet('background-color: #f0f0f0;')
        menu_layout = QVBoxLayout()
        menu_layout.setAlignment(Qt.AlignTop)
        menu_layout.setSpacing(10)
        menu_layout.setContentsMargins(10, 20, 10, 20)

        menu_title = QLabel('Меню')
        menu_title.setStyleSheet('font-size: 16px; font-weight: bold;')
        menu_title.setAlignment(Qt.AlignCenter)

        self.menu_buttons = {
            'Сбор данных': QPushButton('Сбор данных'),
            'Отчёты': QPushButton('Отчёты'),
            'Визуализация': QPushButton('Визуализация'),
            'Экспорт': QPushButton('Экспорт'),
            'Аккаунт': QPushButton('Аккаунт')
        }

        for btn in self.menu_buttons.values():
            btn.setStyleSheet('''
                QPushButton {
                    text-align: left; 
                    padding: 8px;
                    border: none;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            ''')
            btn.setCursor(Qt.PointingHandCursor)

        menu_layout.addWidget(menu_title)
        for btn in self.menu_buttons.values():
            menu_layout.addWidget(btn)

        menu_layout.addStretch()
        menu_widget.setLayout(menu_layout)

        self.stacked_widget = QStackedWidget()

        self.collection_ui = CollectionUI(self.db, self.user_id)
        self.collection_ui.set_parent_window(self)

        self.reports_ui = ReportsUI(self.user_db)
        self.visualization_ui = VisualizationUI(self.user_db)
        self.export_ui = ExportUI(self.user_db)
        self.account_ui = AccountUI(self.app.current_user)

        self.stacked_widget.addWidget(self.create_home_screen())
        self.stacked_widget.addWidget(self.collection_ui)
        self.stacked_widget.addWidget(self.reports_ui)
        self.stacked_widget.addWidget(self.visualization_ui)
        self.stacked_widget.addWidget(self.export_ui)
        self.stacked_widget.addWidget(self.account_ui)

        self.menu_buttons['Сбор данных'].clicked.connect(
            lambda: self.switch_page(self.collection_ui, 'Сбор данных'))
        self.menu_buttons['Отчёты'].clicked.connect(
            lambda: self.switch_page(self.reports_ui, 'Отчёты'))
        self.menu_buttons['Визуализация'].clicked.connect(
            lambda: self.switch_page(self.visualization_ui, 'Визуализация'))
        self.menu_buttons['Экспорт'].clicked.connect(
            lambda: self.switch_page(self.export_ui, 'Экспорт'))
        self.menu_buttons['Аккаунт'].clicked.connect(
            lambda: self.switch_page(self.account_ui, 'Аккаунт'))

        self.stacked_widget.currentChanged.connect(self.update_active_button)

        main_layout.addWidget(menu_widget)
        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

    def switch_page(self, widget, button_name):
        self.stacked_widget.setCurrentWidget(widget)
        self.set_active_button(button_name)

    def set_active_button(self, button_name):
        if self.current_active_button:
            self.current_active_button.setStyleSheet('''
                QPushButton {
                    text-align: left; 
                    padding: 8px;
                    border: none;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            ''')

        active_button = self.menu_buttons[button_name]
        active_button.setStyleSheet('''
            QPushButton {
                text-align: left; 
                padding: 8px;
                border: none;
                background-color: #d0d0d0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
        ''')
        self.current_active_button = active_button

    def update_active_button(self, index):
        widget = self.stacked_widget.widget(index)
        if widget == self.collection_ui:
            self.set_active_button('Сбор данных')
        elif widget == self.reports_ui:
            self.set_active_button('Отчёты')
        elif widget == self.visualization_ui:
            self.set_active_button('Визуализация')
        elif widget == self.export_ui:
            self.set_active_button('Экспорт')
        elif widget == self.account_ui:
            self.set_active_button('Аккаунт')
        else:
            if self.current_active_button:
                self.current_active_button.setStyleSheet('''
                    QPushButton {
                        text-align: left; 
                        padding: 8px;
                        border: none;
                        background-color: transparent;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                ''')
                self.current_active_button = None

    def create_home_screen(self):
        home_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel('Программное средство для анализа вакансий')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')

        welcome = QLabel('Рады видеть вас, чем сегодня займемся?')
        welcome.setStyleSheet('font-size: 16px;')

        hint = QLabel('Выберите действие в левом меню')
        hint.setStyleSheet('font-size: 14px; color: #666;')

        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addWidget(hint)
        layout.addStretch()

        home_widget.setLayout(layout)
        return home_widget
