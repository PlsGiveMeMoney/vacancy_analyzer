from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QHBoxLayout, QHeaderView
)
from sqlalchemy.orm import joinedload
from PyQt5.QtCore import Qt
from core.models import AnalysisSkill, Analysis


class ReportsUI(QWidget):
    def __init__(self, user_db):
        super().__init__()
        self.user_db = user_db
        self.current_analysis = None
        self.setup_ui()
        self.load_last_analysis()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('Анализ навыков по вакансиям')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')

        control_layout = QHBoxLayout()

        self.analysis_combo = QComboBox()
        self.analysis_combo.currentIndexChanged.connect(self.load_analysis)
        control_layout.addWidget(QLabel('Анализ:'))
        control_layout.addWidget(self.analysis_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            'популярности навыков',
            'минимальной зарплате',
            'максимальной зарплате',
            'средней зарплате'
        ])
        self.sort_combo.currentIndexChanged.connect(self.update_table)
        control_layout.addWidget(QLabel('Сортировка:'))
        control_layout.addWidget(self.sort_combo)

        control_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Навык', 'Количество вакансий', 'Частота (%)',
            'Мин. зарплата', 'Макс. зарплата', 'Средняя зарплата'
        ])

        header = self.table.horizontalHeader()
        header.setSectionsClickable(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        self.status_label = QLabel()
        self.status_label.setStyleSheet('color: #666; font-style: italic;')

        layout.addWidget(title)
        layout.addLayout(control_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_last_analysis(self):
        session = self.user_db.get_session()
        try:
            analyses = session.query(Analysis) \
                .order_by(Analysis.created_at.desc()) \
                .all()

            self.analysis_combo.clear()
            for analysis in analyses:
                self.analysis_combo.addItem(
                    f"{analysis.name} ({analysis.created_at.strftime('%d.%m.%Y')})",
                    userData=analysis.id
                )

            if analyses:
                self.load_analysis()
            else:
                self.status_label.setText("Нет доступных анализов")
                self.table.setRowCount(0)

        finally:
            session.close()

    def load_analysis(self):
        analysis_id = self.analysis_combo.currentData()
        if not analysis_id:
            return

        session = self.user_db.get_session()
        try:
            self.current_analysis = session.query(Analysis) \
                .options(joinedload(Analysis.skill_stats).joinedload(AnalysisSkill.skill)) \
                .filter(Analysis.id == analysis_id) \
                .first()

            if self.current_analysis:
                self.update_table()
                self.status_label.setText(
                    f"Дата анализа: {self.current_analysis.created_at.strftime('%d.%m.%Y')} | "
                    f"Всего вакансий: {self.current_analysis.total_vacancies}"
                )
            else:
                self.status_label.setText("Анализ не найден")
                self.table.setRowCount(0)

        finally:
            session.close()

    def update_table(self):
        if not self.current_analysis:
            return

        prepared_data = []
        for stat in self.current_analysis.skill_stats:
            skill_name = stat.skill.name if stat.skill else "Неизвестный навык"

            prepared_data.append({
                'skill_name': skill_name,
                'vacancy_count': stat.vacancy_count,
                'frequency': stat.frequency,
                'min_salary': stat.min_salary,
                'max_salary': stat.max_salary,
                'avg_salary': stat.avg_salary,
                'has_salary': stat.avg_salary is not None
            })

        sort_by = self.sort_combo.currentText()
        if sort_by == 'популярности навыков':
            prepared_data.sort(key=lambda x: -x['vacancy_count'])
        elif sort_by == 'минимальной зарплате':
            prepared_data.sort(key=lambda x: (
                not x['has_salary'],
                x['min_salary'] if x['min_salary'] is not None else float('inf')
            ))
        elif sort_by == 'максимальной зарплате':
            prepared_data.sort(key=lambda x: (
                not x['has_salary'],
                -x['max_salary'] if x['max_salary'] is not None else float('-inf')
            ))
        elif sort_by == 'средней зарплате':
            prepared_data.sort(key=lambda x: (
                not x['has_salary'],
                x['avg_salary'] if x['avg_salary'] is not None else float('inf')
            ))

        self.table.setRowCount(len(prepared_data))
        self.table.setSortingEnabled(False)

        for row, data in enumerate(prepared_data):
            items = [
                self.create_readonly_item(data['skill_name']),
                self.create_readonly_item(str(data['vacancy_count'])),
                self.create_readonly_item(f"{data['frequency']:.2f}%"),
                self.create_readonly_item(f"{data['min_salary']:,.0f}" if data['min_salary'] is not None else "—"),
                self.create_readonly_item(f"{data['max_salary']:,.0f}" if data['max_salary'] is not None else "—"),
                self.create_readonly_item(f"{data['avg_salary']:,.0f}" if data['avg_salary'] is not None else "—")
            ]

            for col, item in enumerate(items):
                self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def create_readonly_item(self, text):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
