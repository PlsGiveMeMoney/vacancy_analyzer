from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from core.models import User
import bcrypt


class LoginWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel('Программное средство для анализа вакансий')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        email_label = QLabel('Логин:')
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('Введите логин')

        password_label = QLabel('Пароль:')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Введите пароль')
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)

        buttons_layout = QHBoxLayout()

        login_btn = QPushButton('Войти')
        login_btn.setFixedWidth(200)
        login_btn.clicked.connect(self.handle_login)

        register_btn = QPushButton('Регистрация')
        register_btn.setFixedWidth(200)
        register_btn.clicked.connect(self.handle_register)

        buttons_layout.addWidget(login_btn)
        buttons_layout.addWidget(register_btn)
        buttons_layout.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def check_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def handle_login(self):
        username = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return

        try:
            session = self.app.database.get_session()
            user = session.query(User).filter_by(login=username).first()

            if not user:
                QMessageBox.warning(self, 'Ошибка', 'Пользователь не найден')
                return

            if not self.check_password(password, user.password):
                QMessageBox.warning(self, 'Ошибка', 'Неверный пароль')
                return

            if user.login == 'admin' and self.check_password('admin1', user.password):
                self.app.show_admin_panel()
            else:
                self.app.current_user = user
                self.app.show_main_window()

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')
        finally:
            session.close()

    def handle_register(self):
        username = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return

        if len(username) < 4:
            QMessageBox.warning(self, 'Ошибка', 'Логин должен содержать минимум 4 символа')
            return

        if len(password) < 6:
            QMessageBox.warning(self, 'Ошибка', 'Пароль должен содержать минимум 6 символов')
            return

        try:
            session = self.app.database.get_session()

            existing_user = session.query(User).filter_by(login=username).first()
            if existing_user:
                QMessageBox.warning(self, 'Ошибка', 'Пользователь с таким логином уже существует')
                return

            hashed_password = self.hash_password(password)

            new_user = User(
                login=username,
                password=hashed_password,
                registration_date=datetime.now(),
                role='user'
            )

            session.add(new_user)
            session.commit()

            QMessageBox.information(self, 'Успех', 'Регистрация прошла успешно! Теперь вы можете войти.')

        except IntegrityError:
            session.rollback()
            QMessageBox.warning(self, 'Ошибка', 'Пользователь с таким логином уже существует')
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при регистрации: {str(e)}')
        finally:
            session.close()
