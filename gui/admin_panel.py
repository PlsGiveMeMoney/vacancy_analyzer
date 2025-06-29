from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QListWidget,
    QListWidgetItem, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.database import Database
from core.models import Skill, Company, Vacancy, VacancySkill, Template, TemplateVacancy
import requests
import time
from datetime import datetime


class HHApiParserThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, db, search_query):
        super().__init__()
        self.db = Database()
        self.search_query = search_query
        self.stop_flag = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })

    def process_vacancy(self, session, item):
        try:
            if not item or not isinstance(item, dict):
                self.update_signal.emit("Получена пустая или некорректная вакансия")
                return False

            vacancy_url = item.get('url')
            if not vacancy_url:
                self.update_signal.emit("Вакансия без URL - пропускаем")
                return False

            if session.query(Vacancy).filter_by(url=vacancy_url).first():
                return False

            details = self.get_vacancy_details(vacancy_url)
            if not details:
                self.update_signal.emit(f"Не удалось получить детали для вакансии: {item.get('name', 'Без названия')}")
                return False

            employer = item.get('employer', {}) or {}
            company_name = employer.get('name', "Не указана")
            company = session.query(Company).filter_by(name=company_name).first()
            if not company:
                company = Company(name=company_name)
                session.add(company)
                session.flush()

            salary = item.get('salary', {}) or {}
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            salary_currency = salary.get('currency')

            published_at = item.get('published_at')
            try:
                publish_date = datetime.strptime(published_at,
                                                 '%Y-%m-%dT%H:%M:%S%z') if published_at else datetime.now()
            except:
                publish_date = datetime.now()
            area = item.get('area', {}) or {}
            city = area.get('name')

            employment_type = None
            employment = item.get('employment', {}) or {}
            if employment:
                employment_type = employment.get('name')

            new_vacancy = Vacancy(
                company_id=company.id,
                title=item.get('name', 'Без названия'),
                description=details.get('description', ''),
                url=vacancy_url,
                published_date=publish_date,
                source='hh.ru',
                salary_min=salary_from,
                salary_max=salary_to,
                salary_currency=salary_currency,
                is_remote=item.get('schedule', {}).get('id') == 'remote',
                city=city,
                employment_type=employment_type
            )

            session.add(new_vacancy)
            session.flush()

            for skill in details.get('key_skills', []):
                if not isinstance(skill, dict):
                    continue

                skill_name = skill.get('name')
                if not skill_name:
                    continue

                db_skill = session.query(Skill).filter_by(name=skill_name).first()
                if not db_skill:
                    db_skill = Skill(name=skill_name)
                    session.add(db_skill)
                    session.flush()

                session.add(VacancySkill(
                    vacancy_id=new_vacancy.id,
                    skill_id=db_skill.id
                ))

            return True

        except Exception as e:
            self.update_signal.emit(f"Критическая ошибка обработки вакансии: {str(e)}")
            return False

    def get_vacancy_details(self, vacancy_url):
        try:
            if 'hh.ru/vacancy/' in vacancy_url:
                vacancy_id = vacancy_url.split('/')[-1].split('?')[0]
                vacancy_url = f"https://api.hh.ru/vacancies/{vacancy_id}"

            for attempt in range(3):
                try:
                    response = self.session.get(vacancy_url, timeout=(3.05, 10))

                    if response.status_code == 404:
                        return None
                    elif response.status_code == 403:
                        time.sleep(2 ** attempt)
                        continue
                    elif not response.ok:
                        return None

                    data = response.json()

                    if not data or not isinstance(data, dict):
                        return None

                    return {
                        'description': data.get('description', '')[:15000],
                        'key_skills': data.get('key_skills', []) or []
                    }

                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        raise
                    time.sleep(1)

            return None

        except Exception as e:
            self.update_signal.emit(f"Critical error in details: {str(e)}")
            return None

    def run(self):
        session = None
        try:
            session = self.db.get_session()
            vacancies_count = 0
            page = 0
            pages = 1

            while not self.stop_flag and page < pages:
                try:
                    search_query_encoded = requests.utils.quote(self.search_query)
                    url = f"https://api.hh.ru/vacancies?text={search_query_encoded}&area=1&page={page}&per_page=50"

                    response = self.session.get(url, timeout=10)

                    if response.status_code != 200:
                        self.update_signal.emit(f"Ошибка API: {response.status_code}")
                        break

                    try:
                        data = response.json()
                        pages = data.get('pages', 1)
                        found = data.get('found', 0)
                        items = data.get('items', []) or []

                        self.update_signal.emit(f"Страница {page + 1}/{pages}. Найдено: {found}")

                        for item in items:
                            if self.stop_flag:
                                break

                            if self.process_vacancy(session, item):
                                vacancies_count += 1
                                self.update_signal.emit(f"Успешно добавлена: {item.get('name', 'Без названия')}")

                    except ValueError as e:
                        self.update_signal.emit(f"Ошибка парсинга JSON: {str(e)}")
                        break

                    page += 1
                    time.sleep(0.5)

                except requests.exceptions.RequestException as e:
                    self.update_signal.emit(f"Ошибка сети: {str(e)}")
                    break
                except Exception as e:
                    self.update_signal.emit(f"Ошибка обработки страницы: {str(e)}")
                    break

        except Exception as e:
            self.update_signal.emit(f"Критическая ошибка: {str(e)}")
        finally:
            if session:
                session.commit()
                session.close()
            self.finished_signal.emit(vacancies_count)

    def stop(self):
        self.stop_flag = True


class AdminPanel(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = Database()
        self.db.create_tables()
        self.parser_thread = None
        self.current_template_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.setup_collection_tab()
        self.setup_templates_tab()

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_collection_tab(self):
        collection_tab = QWidget()
        layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Начать сбор по шаблонам")
        self.start_btn.setStyleSheet("padding: 8px; background-color: #4CAF50; color: white;")
        self.start_btn.clicked.connect(self.start_parsing_by_templates)

        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setStyleSheet("padding: 8px; background-color: #f44336; color: white;")
        self.stop_btn.clicked.connect(self.stop_parsing)
        self.stop_btn.setEnabled(False)

        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("font-family: monospace;")

        self.vacancies_table = QTableWidget()
        self.vacancies_table.setColumnCount(4)
        self.vacancies_table.setHorizontalHeaderLabels(["Название", "Компания", "Зарплата", "Навыки"])
        self.vacancies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vacancies_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addLayout(buttons_layout)
        layout.addWidget(QLabel("Лог выполнения:"))
        layout.addWidget(self.log_output)
        layout.addWidget(QLabel("Последние добавленные вакансии:"))
        layout.addWidget(self.vacancies_table)

        collection_tab.setLayout(layout)
        self.tabs.addTab(collection_tab, "Сбор данных")

    def setup_templates_tab(self):
        templates_tab = QWidget()
        layout = QVBoxLayout()

        self.templates_list = QListWidget()
        self.templates_list.itemClicked.connect(self.load_template)
        self.load_templates()

        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить шаблон")
        add_btn.clicked.connect(self.add_template)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_template)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_template)

        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(delete_btn)

        self.template_vacancies_list = QListWidget()

        vac_buttons_layout = QHBoxLayout()
        add_vac_btn = QPushButton("Добавить вакансию")
        add_vac_btn.clicked.connect(self.add_vacancy_to_template)

        remove_vac_btn = QPushButton("Удалить вакансию")
        remove_vac_btn.clicked.connect(self.remove_vacancy_from_template)

        vac_buttons_layout.addWidget(add_vac_btn)
        vac_buttons_layout.addWidget(remove_vac_btn)

        layout.addWidget(QLabel("Шаблоны:"))
        layout.addWidget(self.templates_list)
        layout.addLayout(buttons_layout)
        layout.addWidget(QLabel("Вакансии в шаблоне:"))
        layout.addWidget(self.template_vacancies_list)
        layout.addLayout(vac_buttons_layout)

        templates_tab.setLayout(layout)
        self.tabs.addTab(templates_tab, "Шаблоны")

    def load_templates(self):
        self.templates_list.clear()
        session = self.db.get_session()
        try:
            templates = session.query(Template).all()
            for template in templates:
                item = QListWidgetItem(template.name)
                item.setData(Qt.UserRole, template.id)
                self.templates_list.addItem(item)
        finally:
            session.close()

    def load_template(self, item):
        self.current_template_id = item.data(Qt.UserRole)
        self.template_vacancies_list.clear()

        session = self.db.get_session()
        try:
            vacancies = session.query(TemplateVacancy).filter_by(template_id=self.current_template_id).all()
            for vac in vacancies:
                self.template_vacancies_list.addItem(vac.vacancy_query)
        finally:
            session.close()

    def add_template(self):
        name, ok = QInputDialog.getText(self, "Новый шаблон", "Введите название шаблона:")
        if ok and name:
            session = self.db.get_session()
            try:
                template = Template(name=name)
                session.add(template)
                session.commit()
                self.load_templates()
            finally:
                session.close()

    def edit_template(self):
        if not self.current_template_id:
            return

        current_item = self.templates_list.currentItem()
        if not current_item:
            return

        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(self, "Редактирование", "Введите новое название:", text=old_name)

        if ok and new_name:
            session = self.db.get_session()
            try:
                template = session.query(Template).filter_by(id=self.current_template_id).first()
                if template:
                    template.name = new_name
                    session.commit()
                    self.load_templates()
            finally:
                session.close()

    def delete_template(self):
        if not self.current_template_id:
            return

        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Удалить этот шаблон?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            session = self.db.get_session()
            try:
                session.query(TemplateVacancy).filter_by(template_id=self.current_template_id).delete()
                session.query(Template).filter_by(id=self.current_template_id).delete()
                session.commit()
                self.current_template_id = None
                self.template_vacancies_list.clear()
                self.load_templates()
            finally:
                session.close()

    def add_vacancy_to_template(self):
        if not self.current_template_id:
            return

        query, ok = QInputDialog.getText(self, "Добавить вакансию", "Введите название вакансии:")
        if ok and query:
            session = self.db.get_session()
            try:
                template_vac = TemplateVacancy(
                    template_id=self.current_template_id,
                    vacancy_query=query
                )
                session.add(template_vac)
                session.commit()
                self.load_template(self.templates_list.currentItem())
            finally:
                session.close()

    def remove_vacancy_from_template(self):
        if not self.current_template_id or not self.template_vacancies_list.currentItem():
            return

        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Удалить эту вакансию из шаблона?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            session = self.db.get_session()
            try:
                query = self.template_vacancies_list.currentItem().text()
                session.query(TemplateVacancy).filter_by(
                    template_id=self.current_template_id,
                    vacancy_query=query
                ).delete()
                session.commit()
                self.load_template(self.templates_list.currentItem())
            finally:
                session.close()

    def start_parsing_by_templates(self):
        session = self.db.get_session()
        try:
            templates = session.query(Template).all()
            if not templates:
                QMessageBox.warning(self, "Ошибка", "Нет шаблонов для сбора данных")
                return

            search_queries = []
            for template in templates:
                vacancies = session.query(TemplateVacancy).filter_by(template_id=template.id).all()
                for vac in vacancies:
                    if vac.vacancy_query not in search_queries:
                        search_queries.append(vac.vacancy_query)

            if not search_queries:
                QMessageBox.warning(self, "Ошибка", "В шаблонах нет вакансий для сбора")
                return

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.log_output.clear()

            search_query = " OR ".join(f'"{q}"' for q in search_queries)

            self.parser_thread = HHApiParserThread(self.db, search_query)
            self.parser_thread.update_signal.connect(self.update_log)
            self.parser_thread.finished_signal.connect(self.parsing_finished)
            self.parser_thread.start()

        finally:
            session.close()

    def start_parsing(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            QMessageBox.warning(self, "Ошибка", "Введите поисковый запрос")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_output.clear()

        self.parser_thread = HHApiParserThread(self.db, search_query)
        self.parser_thread.update_signal.connect(self.update_log)
        self.parser_thread.finished_signal.connect(self.parsing_finished)
        self.parser_thread.start()

    def update_log(self, message):
        self.log_output.append(message)

    def parsing_finished(self, count):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_log(f"\nСбор завершен. Добавлено вакансий: {count}")
        self.update_vacancies_table()

    def stop_parsing(self):
        if self.parser_thread and self.parser_thread.isRunning():
            self.parser_thread.stop()
            self.update_log("Сбор данных остановлен")

    def update_vacancies_table(self):
        headers = ["Название", "Компания", "Зарплата", "Навыки", "Город", "Тип занятости"]
        self.vacancies_table.setColumnCount(len(headers))
        self.vacancies_table.setHorizontalHeaderLabels(headers)

        session = self.db.get_session()
        try:
            vacancies = session.query(Vacancy).order_by(Vacancy.id.desc()).limit(10).all()
            self.vacancies_table.setRowCount(len(vacancies))

            for row, vacancy in enumerate(vacancies):
                company = session.query(Company).filter_by(id=vacancy.company_id).first()

                salary_parts = []
                if vacancy.salary_min: salary_parts.append(f"от {vacancy.salary_min}")
                if vacancy.salary_max: salary_parts.append(f"до {vacancy.salary_max}")
                salary = " ".join(salary_parts)
                if vacancy.salary_currency: salary += f" {vacancy.salary_currency}"

                skills = ", ".join(
                    skill.name for skill in session.query(Skill)
                    .join(VacancySkill, Skill.id == VacancySkill.skill_id)
                    .filter(VacancySkill.vacancy_id == vacancy.id)
                )

                self.vacancies_table.setItem(row, 0, QTableWidgetItem(vacancy.title))
                self.vacancies_table.setItem(row, 1, QTableWidgetItem(company.name if company else ""))
                self.vacancies_table.setItem(row, 2, QTableWidgetItem(salary))
                self.vacancies_table.setItem(row, 3, QTableWidgetItem(skills))
                self.vacancies_table.setItem(row, 4, QTableWidgetItem(vacancy.city or ""))
                self.vacancies_table.setItem(row, 5, QTableWidgetItem(vacancy.employment_type or ""))

            self.vacancies_table.resizeColumnsToContents()

        finally:
            session.close()
