from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from core.models import User
from core.database import Database
import bcrypt


class AccountUI(QWidget):
    def __init__(self, user, app=None):
        super().__init__()
        self.user = user
        self.app = app
        self.db = Database()
        self.setup_ui()
        self.load_user_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel('Настройки аккаунта')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)

        info_group = QGroupBox('Информация о пользователе')
        info_layout = QVBoxLayout()

        self.user_info = QLabel()
        self.user_info.setStyleSheet('font-size: 14px;')
        info_layout.addWidget(self.user_info)

        info_group.setLayout(info_layout)

        profile_group = QGroupBox('Редактирование данных')
        profile_layout = QVBoxLayout()
        profile_layout.setSpacing(10)

        login_layout = QHBoxLayout()
        login_layout.addWidget(QLabel('Логин:'))
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText('Введите новый логин')
        login_layout.addWidget(self.login_input)

        current_pass_layout = QHBoxLayout()
        current_pass_layout.addWidget(QLabel('Текущий пароль:'))
        self.current_pass_input = QLineEdit()
        self.current_pass_input.setPlaceholderText('Обязательно для изменений')
        self.current_pass_input.setEchoMode(QLineEdit.Password)
        current_pass_layout.addWidget(self.current_pass_input)

        new_pass_layout = QHBoxLayout()
        new_pass_layout.addWidget(QLabel('Новый пароль:'))
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setPlaceholderText('Оставьте пустым, если не нужно менять')
        self.new_pass_input.setEchoMode(QLineEdit.Password)
        new_pass_layout.addWidget(self.new_pass_input)

        confirm_pass_layout = QHBoxLayout()
        confirm_pass_layout.addWidget(QLabel('Подтвердите пароль:'))
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setPlaceholderText('Повторите новый пароль')
        self.confirm_pass_input.setEchoMode(QLineEdit.Password)
        confirm_pass_layout.addWidget(self.confirm_pass_input)

        profile_layout.addLayout(login_layout)
        profile_layout.addLayout(current_pass_layout)
        profile_layout.addLayout(new_pass_layout)
        profile_layout.addLayout(confirm_pass_layout)
        profile_group.setLayout(profile_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.save_btn = QPushButton('Сохранить изменения')
        self.save_btn.setStyleSheet('padding: 10px; background-color: #4CAF50; color: white;')
        self.save_btn.clicked.connect(self.save_changes)

        buttons_layout.addWidget(self.save_btn)

        layout.addWidget(title)
        layout.addWidget(info_group)
        layout.addWidget(profile_group)
        layout.addLayout(buttons_layout)
        layout.addStretch()

        self.setLayout(layout)

    def load_user_data(self):
        if self.user:
            self.user_info.setText(
                f"Логин: {self.user.login}\n"
                f"Дата регистрации: {self.user.registration_date.strftime('%d.%m.%Y')}\n"
                f"Роль: {self.user.role}"
            )
            self.login_input.setText(self.user.login)
            self.current_pass_input.clear()
            self.new_pass_input.clear()
            self.confirm_pass_input.clear()

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except:
            return False

    def save_changes(self):
        session = None
        try:
            session = self.db.get_session()
            user = session.query(User).get(self.user.id)

            if not user:
                QMessageBox.warning(self, 'Ошибка', 'Пользователь не найден!')
                return

            current_pass = self.current_pass_input.text().strip()
            if not current_pass or not self.check_password(current_pass, user.password):
                QMessageBox.warning(self, 'Ошибка', 'Неверный текущий пароль!')
                return

            new_login = self.login_input.text().strip()
            new_pass = self.new_pass_input.text().strip()
            confirm_pass = self.confirm_pass_input.text().strip()

            if not new_login:
                QMessageBox.warning(self, 'Ошибка', 'Логин не может быть пустым!')
                return

            if new_pass and new_pass != confirm_pass:
                QMessageBox.warning(self, 'Ошибка', 'Новый пароль и подтверждение не совпадают!')
                return

            if new_login != user.login:
                existing_user = session.query(User).filter_by(login=new_login).first()
                if existing_user:
                    QMessageBox.warning(self, 'Ошибка', 'Пользователь с таким логином уже существует!')
                    return

            user.login = new_login
            if new_pass:
                user.password = self.hash_password(new_pass)

            session.commit()

            self.user = user
            if self.app:
                self.app.current_user = user

            QMessageBox.information(self, 'Успех', 'Изменения сохранены!')
            self.load_user_data()

        except Exception as e:
            if session:
                session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')
        finally:
            if session:
                session.close()