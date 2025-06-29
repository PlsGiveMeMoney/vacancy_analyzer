from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QGroupBox, QComboBox,
    QDateEdit, QSpinBox, QMessageBox, QScrollArea,
    QFormLayout, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime
from core.database import UserDatabase
from core.models import Template, TemplateVacancy, Vacancy, Company, Skill, VacancySkill, Analysis, AnalysisSkill
from core.constants import EmploymentType
from collections import defaultdict


class CollectionUI(QWidget):
    def __init__(self, main_db, user_id):
        super().__init__()
        self.main_db = main_db
        self.user_db = UserDatabase(user_id)
        self.user_id = user_id
        self.parent_window = None
        self.setup_ui()
        self.load_templates()

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    def setup_ui(self):
        self.setMinimumSize(800, 600)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        title = QLabel('Сбор вакансий для анализа')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)

        sources_group = QGroupBox("Источники вакансий")
        sources_layout = QVBoxLayout()

        self.hh_checkbox = QCheckBox("HeadHunter (hh.ru)")
        self.hh_checkbox.setChecked(True)
        self.sj_checkbox = QCheckBox("SuperJob")
        self.rabota_checkbox = QCheckBox("Rabota.ru")

        sources_layout.addWidget(self.hh_checkbox)
        sources_layout.addWidget(self.sj_checkbox)
        sources_layout.addWidget(self.rabota_checkbox)
        sources_group.setLayout(sources_layout)
        content_layout.addWidget(sources_group)

        templates_group = QGroupBox("Шаблон поиска")
        templates_layout = QFormLayout()

        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(300)
        templates_layout.addRow("Выберите шаблон:", self.template_combo)

        self.template_desc_label = QLabel()
        self.template_desc_label.setWordWrap(True)
        self.template_desc_label.setStyleSheet("color: #666; font-style: italic;")
        templates_layout.addRow("Описание:", self.template_desc_label)

        templates_group.setLayout(templates_layout)
        content_layout.addWidget(templates_group)

        filters_group = QGroupBox("Фильтры вакансий")
        filters_layout = QVBoxLayout()

        date_filter = QGroupBox("Дата публикации")
        date_layout = QHBoxLayout()

        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setMaximumWidth(150)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setMaximumWidth(150)

        date_layout.addWidget(QLabel("От:"))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel("до:"))
        date_layout.addWidget(self.date_to)
        date_layout.addStretch()
        date_filter.setLayout(date_layout)
        filters_layout.addWidget(date_filter)

        salary_filter = QGroupBox("Зарплата")
        salary_layout = QHBoxLayout()

        self.salary_min = QSpinBox()
        self.salary_min.setRange(0, 1000000)
        self.salary_min.setPrefix("от ")
        self.salary_min.setSuffix(" ₽")
        self.salary_min.setSpecialValueText("не указано")
        self.salary_min.setMaximumWidth(150)

        self.salary_max = QSpinBox()
        self.salary_max.setRange(0, 1000000)
        self.salary_max.setPrefix("до ")
        self.salary_max.setSuffix(" ₽")
        self.salary_max.setSpecialValueText("не указано")
        self.salary_max.setMaximumWidth(150)

        self.salary_currency_combo = QComboBox()
        self.salary_currency_combo.addItems(["любая валюта", "RUR", "USD", "EUR"])
        self.salary_currency_combo.setMaximumWidth(150)

        salary_layout.addWidget(self.salary_min)
        salary_layout.addWidget(self.salary_max)
        salary_layout.addWidget(self.salary_currency_combo)
        salary_layout.addStretch()
        salary_filter.setLayout(salary_layout)
        filters_layout.addWidget(salary_filter)

        work_type_filter = QGroupBox("Тип занятости")
        work_type_layout = QHBoxLayout()

        self.fulltime_check = QCheckBox("Полная занятость")
        self.fulltime_check.setChecked(True)
        self.parttime_check = QCheckBox("Частичная занятость")
        self.project_check = QCheckBox("Проектная работа")
        self.remote_check = QCheckBox("Удалённая работа")

        work_type_layout.addWidget(self.fulltime_check)
        work_type_layout.addWidget(self.parttime_check)
        work_type_layout.addWidget(self.project_check)
        work_type_layout.addWidget(self.remote_check)
        work_type_layout.addStretch()
        work_type_filter.setLayout(work_type_layout)
        filters_layout.addWidget(work_type_filter)

        filters_group.setLayout(filters_layout)
        content_layout.addWidget(filters_group)

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()

        self.start_btn = QPushButton("Начать сбор данных")
        self.start_btn.setStyleSheet(
            "QPushButton { padding: 10px; background-color: #4CAF50; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.start_btn.clicked.connect(self.start_data_collection)

        self.reports_btn = QPushButton("Сформировать отчеты")
        self.reports_btn.setStyleSheet(
            "QPushButton { padding: 10px; background-color: #FF9800; color: white; }"
            "QPushButton:hover { background-color: #e68a00; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.reports_btn.clicked.connect(self.generate_reports)
        self.reports_btn.setEnabled(True)

        self.view_btn = QPushButton("Просмотреть результаты")
        self.view_btn.setStyleSheet(
            "QPushButton { padding: 10px; background-color: #2196F3; color: white; }"
            "QPushButton:hover { background-color: #0b7dda; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.view_btn.clicked.connect(self.view_results)
        self.view_btn.setEnabled(False)

        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.reports_btn)
        buttons_layout.addWidget(self.view_btn)
        buttons_layout.addStretch()
        buttons_frame.setLayout(buttons_layout)
        content_layout.addWidget(buttons_frame)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def generate_reports(self):
        session = None
        try:
            session = self.user_db.get_session()

            vacancy_count = session.query(Vacancy).count()
            if vacancy_count == 0:
                QMessageBox.warning(self, "Нет данных", "Нет вакансий для анализа")
                return False

            analysis_name = f"Анализ от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            new_analysis = Analysis(
                user_id=self.user_id,
                name=analysis_name,
                template=self.template_combo.currentText(),
                created_at=datetime.now(),
                total_vacancies=vacancy_count
            )
            session.add(new_analysis)
            session.flush()

            skill_stats = defaultdict(lambda: {
                'count': 0,
                'min_salaries': [],
                'max_salaries': [],
                'avg_salaries': [],
                'skill_id': None
            })

            vacancies = session.query(Vacancy).all()

            for vacancy in vacancies:
                for skill in vacancy.skills:
                    stats = skill_stats[skill.name]
                    stats['count'] += 1
                    stats['skill_id'] = skill.id

                    if vacancy.salary_min:
                        stats['min_salaries'].append(vacancy.salary_min)
                    if vacancy.salary_max:
                        stats['max_salaries'].append(vacancy.salary_max)
                    if vacancy.salary_min and vacancy.salary_max:
                        avg = (vacancy.salary_min + vacancy.salary_max) / 2
                        stats['avg_salaries'].append(avg)

            for skill_name, data in skill_stats.items():
                if not data['skill_id']:
                    continue

                min_salary = min(data['min_salaries']) if data['min_salaries'] else None
                max_salary = max(data['max_salaries']) if data['max_salaries'] else None
                avg_salary = sum(data['avg_salaries']) / len(data['avg_salaries']) if data['avg_salaries'] else None
                frequency = (data['count'] / vacancy_count) * 100

                analysis_skill = AnalysisSkill(
                    analysis_id=new_analysis.id,
                    skill_id=data['skill_id'],
                    vacancy_count=data['count'],
                    frequency=frequency,
                    min_salary=min_salary,
                    max_salary=max_salary,
                    avg_salary=avg_salary
                )
                session.add(analysis_skill)

            session.commit()

            if self.parent_window:
                self.parent_window.reports_ui.load_last_analysis()
                self.parent_window.visualization_ui.load_analyses()
                self.parent_window.export_ui.load_analyses()
                self.parent_window.navigate_to_reports()

            QMessageBox.information(self, "Успех", "Новый анализ успешно создан!")
            return True

        except Exception as e:
            if session:
                session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании анализа: {str(e)}")
            return False
        finally:
            if session:
                session.close()

    def load_templates(self):
        session = self.main_db.get_session()
        try:
            templates = session.query(Template).order_by(Template.name).all()
            self.template_combo.clear()

            for template in templates:
                self.template_combo.addItem(template.name, template.id)

            if templates:
                self.update_template_description(templates[0].id)

            self.template_combo.currentIndexChanged.connect(
                lambda: self.update_template_description(
                    self.template_combo.currentData()
                )
            )
        finally:
            session.close()

    def update_template_description(self, template_id):
        session = self.main_db.get_session()
        try:
            template = session.query(Template).get(template_id)
            if not template:
                return

            vacancies = session.query(TemplateVacancy.vacancy_query) \
                .filter_by(template_id=template_id) \
                .order_by(TemplateVacancy.vacancy_query) \
                .all()

            queries = [v.vacancy_query for v in vacancies]
            desc = f"Шаблон содержит {len(queries)} запросов:\n" + ", ".join(queries)
            self.template_desc_label.setText(desc)
        finally:
            session.close()

    def start_data_collection(self):
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Ошибка", "Не выбран шаблон для поиска")
            return

        filters = self.get_current_filters()

        search_queries = self.get_template_queries(template_id)
        if not search_queries:
            QMessageBox.warning(self, "Ошибка", "Выбранный шаблон не содержит запросов")
            return

        try:
            copied_count = self.copy_vacancies(search_queries, filters)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Сбор завершен")
            msg.setText(f"Собрано {copied_count} вакансий по выбранным параметрам")
            msg.setDetailedText(f"Использованы запросы: {', '.join(search_queries)}")
            msg.exec_()

            self.view_btn.setEnabled(copied_count > 0)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сборе данных:\n{str(e)}")

    def get_current_filters(self):
        return {
            'date_from': self.date_from.date().toPyDate(),
            'date_to': self.date_to.date().toPyDate(),
            'salary_min': self.salary_min.value() if self.salary_min.value() > 0 else None,
            'salary_max': self.salary_max.value() if self.salary_max.value() > 0 else None,
            'salary_currency': self.salary_currency_combo.currentText()
            if self.salary_currency_combo.currentIndex() > 0 else None,
            'fulltime': self.fulltime_check.isChecked(),
            'parttime': self.parttime_check.isChecked(),
            'project': self.project_check.isChecked(),
            'remote': self.remote_check.isChecked()
        }

    def get_template_queries(self, template_id):
        session = self.main_db.get_session()
        try:
            template_vacancies = session.query(TemplateVacancy) \
                .filter_by(template_id=template_id) \
                .order_by(TemplateVacancy.vacancy_query) \
                .all()
            return [tv.vacancy_query for tv in template_vacancies]
        finally:
            session.close()

    def copy_vacancies(self, search_queries, filters):
        from sqlalchemy import or_, and_

        main_session = self.main_db.get_session()
        user_session = self.user_db.get_session()
        copied_count = 0

        try:

            user_session.query(Vacancy).delete()
            user_session.query(VacancySkill).delete()
            user_session.commit()

            query = main_session.query(Vacancy).join(Company)

            if search_queries:
                query = query.filter(
                    or_(*[Vacancy.title.ilike(f'%{q}%') for q in search_queries])
                )

            if filters['date_from']:
                query = query.filter(Vacancy.published_date >= filters['date_from'])
            if filters['date_to']:
                query = query.filter(Vacancy.published_date <= filters['date_to'])

            if filters['salary_min']:
                query = query.filter(
                    or_(
                        Vacancy.salary_min >= filters['salary_min'],
                        Vacancy.salary_min == None
                    )
                )
            if filters['salary_max']:
                query = query.filter(
                    or_(
                        Vacancy.salary_max <= filters['salary_max'],
                        Vacancy.salary_max == None
                    )
                )

            if filters['salary_currency']:
                if filters['salary_currency'] == 'RUR':
                    query = query.filter(
                        or_(
                            Vacancy.salary_currency == 'RUR',
                            Vacancy.salary_currency == 'RUB',
                            Vacancy.salary_currency == None
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            Vacancy.salary_currency == filters['salary_currency'],
                            Vacancy.salary_currency == None
                        )
                    )

            if filters.get('remote'):
                query = query.filter(
                    or_(
                        Vacancy.is_remote == True,
                        Vacancy.is_remote == None
                    )
                )

            employment_filters = []
            if filters.get('fulltime'):
                employment_filters.append(
                    or_(
                        Vacancy.employment_type == EmploymentType.FULL,
                        Vacancy.employment_type == None
                    )
                )
            if filters.get('parttime'):
                employment_filters.append(
                    or_(
                        Vacancy.employment_type == EmploymentType.PART,
                        Vacancy.employment_type == None
                    )
                )
            if filters.get('project'):
                employment_filters.append(
                    or_(
                        Vacancy.employment_type == EmploymentType.PROJECT,
                        Vacancy.employment_type == None
                    )
                )

            if employment_filters:
                query = query.filter(or_(*employment_filters))

            vacancies = query.order_by(Vacancy.published_date.desc()).all()

            for vacancy in vacancies:
                company = user_session.query(Company) \
                    .filter_by(name=vacancy.company.name) \
                    .first()

                if not company:
                    company = Company(name=vacancy.company.name)
                    user_session.add(company)
                    user_session.flush()

                new_vacancy = Vacancy(
                    company_id=company.id,
                    title=vacancy.title,
                    description=vacancy.description,
                    url=vacancy.url,
                    published_date=vacancy.published_date,
                    source=vacancy.source,
                    salary_min=vacancy.salary_min,
                    salary_max=vacancy.salary_max,
                    salary_currency=vacancy.salary_currency,
                    is_remote=vacancy.is_remote,
                    employment_type=vacancy.employment_type,
                    city=vacancy.city
                )
                user_session.add(new_vacancy)
                user_session.flush()

                for skill in vacancy.skills:
                    db_skill = user_session.query(Skill) \
                        .filter_by(name=skill.name) \
                        .first()

                    if not db_skill:
                        db_skill = Skill(name=skill.name)
                        user_session.add(db_skill)
                        user_session.flush()

                    user_session.add(VacancySkill(
                        vacancy_id=new_vacancy.id,
                        skill_id=db_skill.id
                    ))

                copied_count += 1

            user_session.commit()
            return copied_count

        except Exception as e:
            user_session.rollback()
            raise e
        finally:
            main_session.close()
            user_session.close()

    def save_analysis(self, search_queries, filters, vacancy_count):
        session = self.user_db.get_session()
        try:
            analysis = Analysis(
                user_id=self.user_id,
                name=f"Анализ от {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                created_at=datetime.now(),
                template=self.template_combo.currentText(),
                total_vacancies=vacancy_count
            )
            session.add(analysis)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при сохранении анализа: {str(e)}")
        finally:
            session.close()
    def view_results(self):
        session = self.user_db.get_session()
        try:
            vacancy_count = session.query(Vacancy).count()
            if vacancy_count == 0:
                QMessageBox.information(self, "Результаты", "Нет данных для отображения")
                return

            QMessageBox.information(
                self,
                "Результаты",
                f"Готово к анализу {vacancy_count} вакансий.\n"
                "Переход к экрану анализа..."
            )
        finally:
            session.close()
