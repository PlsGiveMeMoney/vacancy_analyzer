import os
import csv
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QHBoxLayout, QGroupBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from openpyxl import Workbook
from core.database import UserDatabase
from core.models import Analysis


class ExportUI(QWidget):
    def __init__(self, user_db: UserDatabase, user_id="432432"):
        super().__init__()
        self.user_db = user_db
        self.user_id = user_id
        self.setup_ui()
        self.load_analyses()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('Экспорт отчета анализа вакансий')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)

        export_group = QGroupBox('Настройки экспорта')
        export_layout = QVBoxLayout()

        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel('Выбор анализа:'))
        self.analysis_combo = QComboBox()
        analysis_layout.addWidget(self.analysis_combo, stretch=1)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('Формат экспорта:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV', 'JSON', 'Excel (XLSX)'])
        format_layout.addWidget(self.format_combo, stretch=1)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('Путь для сохранения:'))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText('Выберите папку для сохранения')
        path_layout.addWidget(self.path_input, stretch=1)

        browse_btn = QPushButton('Обзор...')
        browse_btn.setStyleSheet('padding: 5px;')
        browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(browse_btn)

        export_layout.addLayout(analysis_layout)
        export_layout.addLayout(format_layout)
        export_layout.addLayout(path_layout)
        export_group.setLayout(export_layout)

        export_btn = QPushButton('Экспортировать отчет')
        export_btn.setStyleSheet('''
            padding: 10px; 
            background-color: #4CAF50; 
            color: white;
            font-weight: bold;
        ''')
        export_btn.clicked.connect(self.export_report)

        layout.addWidget(title)
        layout.addWidget(export_group)
        layout.addWidget(export_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def load_analyses(self):
        session = self.user_db.get_session()
        try:
            analyses = session.query(Analysis).order_by(Analysis.created_at.desc()).all()
            self.analysis_combo.clear()

            for analysis in analyses:
                date_str = analysis.created_at.strftime('%d.%m.%Y %H:%M')
                self.analysis_combo.addItem(f"{analysis.name} ({date_str})", analysis.id)
        finally:
            session.close()

    def browse_save_path(self):
        file_format = self.format_combo.currentText()
        file_ext = {
            'CSV': 'csv',
            'JSON': 'json',
            'Excel (XLSX)': 'xlsx'
        }.get(file_format, 'csv')

        default_name = f"vacancy_analysis_{datetime.now().strftime('%Y%m%d')}.{file_ext}"

        if file_format == 'Excel (XLSX)':
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить файл",
                default_name,
                f"{file_format} (*.{file_ext})"
            )
        else:
            path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
            if path:
                path = os.path.join(path, default_name)

        if path:
            self.path_input.setText(path)

    def export_report(self):
        analysis_id = self.analysis_combo.currentData()
        if not analysis_id:
            QMessageBox.warning(self, "Ошибка", "Не выбран анализ для экспорта")
            return

        file_path = self.path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Ошибка", "Не указан путь для сохранения")
            return

        file_format = self.format_combo.currentText()

        try:
            session = self.user_db.get_session()
            analysis = session.query(Analysis).get(analysis_id)

            if not analysis:
                QMessageBox.warning(self, "Ошибка", "Выбранный анализ не найден")
                return

            skill_stats = []
            for stat in analysis.skill_stats:
                skill_stats.append({
                    'skill': stat.skill.name,
                    'vacancy_count': stat.vacancy_count,
                    'frequency': f"{stat.frequency:.1f}%",
                    'min_salary': stat.min_salary,
                    'max_salary': stat.max_salary,
                    'avg_salary': stat.avg_salary
                })

            skill_stats.sort(key=lambda x: x['vacancy_count'], reverse=True)

            if file_format == 'CSV':
                self.export_to_csv(file_path, skill_stats, analysis)
            elif file_format == 'JSON':
                self.export_to_json(file_path, skill_stats, analysis)
            elif file_format == 'Excel (XLSX)':
                self.export_to_excel(file_path, skill_stats, analysis)

            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Отчет успешно экспортирован в {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Произошла ошибка при экспорте:\n{str(e)}"
            )
        finally:
            session.close()

    def export_to_csv(self, file_path, skill_stats, analysis):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    'skill', 'vacancy_count', 'frequency',
                    'min_salary', 'max_salary', 'avg_salary'
                ])

                writer.writeheader()

                writer.writerow({
                    'skill': f"Анализ: {analysis.name}",
                    'vacancy_count': f"Дата: {analysis.created_at.strftime('%d.%m.%Y %H:%M')}",
                    'frequency': f"Всего вакансий: {analysis.total_vacancies}",
                    'min_salary': '',
                    'max_salary': '',
                    'avg_salary': ''
                })
                writer.writerow({})

                for stat in skill_stats:
                    writer.writerow({
                        'skill': stat['skill'],
                        'vacancy_count': stat['vacancy_count'],
                        'frequency': stat['frequency'],
                        'min_salary': stat['min_salary'],
                        'max_salary': stat['max_salary'],
                        'avg_salary': stat['avg_salary']
                    })
        except Exception as e:
            raise Exception(f"Ошибка при сохранении CSV: {str(e)}")

    def export_to_json(self, file_path, skill_stats, analysis):
        data = {
            'analysis': {
                'name': analysis.name,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'total_vacancies': analysis.total_vacancies,
                'template': analysis.template
            },
            'skill_stats': skill_stats
        }

        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)

    def export_to_excel(self, file_path, skill_stats, analysis):
        wb = Workbook()
        ws = wb.active
        ws.title = "Анализ навыков"

        headers = [
            "Навык", "Количество вакансий", "Частота встречаемости (%)",
            "Мин. зарплата", "Макс. зарплата", "Средняя зарплата"
        ]
        ws.append(headers)

        ws.append([f"Анализ: {analysis.name}"])
        ws.append([f"Дата: {analysis.created_at.strftime('%d.%m.%Y %H:%M')}"])
        ws.append([f"Всего вакансий: {analysis.total_vacancies}"])
        ws.append([])

        for stat in skill_stats:
            ws.append([
                stat['skill'],
                stat['vacancy_count'],
                stat['frequency'],
                stat['min_salary'],
                stat['max_salary'],
                stat['avg_salary']
            ])

        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column_letter].width = adjusted_width

        wb.save(file_path)