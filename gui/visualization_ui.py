from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QPushButton, QHBoxLayout, QGroupBox,  QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QImage
from core.database import UserDatabase
from core.models import Analysis, AnalysisSkill, Skill
from datetime import datetime
import os


class VisualizationUI(QWidget):
    def __init__(self, user_db: UserDatabase):
        super().__init__()
        self.user_db = user_db
        self.current_analysis = None
        self.chart_view = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('Программное средство для анализа вакансий')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')

        settings_group = QGroupBox('Настройки визуализации')
        settings_layout = QVBoxLayout()

        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel('Анализ:'))
        self.analysis_combo = QComboBox()
        self.analysis_combo.currentIndexChanged.connect(self.load_analysis)
        analysis_layout.addWidget(self.analysis_combo)

        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel('Вид диаграммы:'))
        self.chart_type = QComboBox()
        self.chart_type.addItems(['Столбчатая', 'Круговая'])
        chart_type_layout.addWidget(self.chart_type)

        data_type_layout = QHBoxLayout()
        data_type_layout.addWidget(QLabel('Тип данных:'))
        self.data_type = QComboBox()
        self.data_type.addItems([
            'Частота навыков',
            'Средняя зарплата',
            'Минимальная зарплата',
            'Максимальная зарплата'
        ])
        data_type_layout.addWidget(self.data_type)

        update_btn = QPushButton('Обновить диаграмму')
        update_btn.clicked.connect(self.update_chart)

        settings_layout.addLayout(analysis_layout)
        settings_layout.addLayout(chart_type_layout)
        settings_layout.addLayout(data_type_layout)
        settings_layout.addWidget(update_btn)
        settings_group.setLayout(settings_layout)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        save_btn = QPushButton('Сохранить визуализацию')
        save_btn.setStyleSheet('padding: 10px; background-color: #4CAF50; color: white;')
        save_btn.clicked.connect(self.save_visualization)

        layout.addWidget(title)
        layout.addWidget(settings_group)
        layout.addWidget(self.chart_view)
        layout.addWidget(save_btn)

        self.setLayout(layout)
        self.load_analyses()

    def load_analyses(self):
        session = self.user_db.get_session()
        try:
            analyses = session.query(Analysis).order_by(Analysis.created_at.desc()).all()
            self.analysis_combo.clear()
            for analysis in analyses:
                self.analysis_combo.addItem(
                    f"{analysis.name} ({analysis.created_at.strftime('%d.%m.%Y')})",
                    userData=analysis.id
                )
        finally:
            session.close()

    def load_analysis(self):
        analysis_id = self.analysis_combo.currentData()
        if not analysis_id:
            return

        session = self.user_db.get_session()
        try:
            self.current_analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            self.update_chart()
        finally:
            session.close()

    def update_chart(self):
        if not self.current_analysis:
            return

        data_type = self.data_type.currentText()
        chart_type = self.chart_type.currentText()

        session = self.user_db.get_session()
        try:
            stats = session.query(AnalysisSkill, Skill.name) \
                .join(Skill) \
                .filter(AnalysisSkill.analysis_id == self.current_analysis.id) \
                .order_by(AnalysisSkill.frequency.desc()) \
                .all()
        finally:
            session.close()

        if not stats:
            return

        data = []
        for stat, skill_name in stats:
            if data_type == 'Частота навыков':
                value = stat.frequency
            elif data_type == 'Средняя зарплата':
                value = stat.avg_salary if stat.avg_salary else 0
            elif data_type == 'Минимальная зарплата':
                value = stat.min_salary if stat.min_salary else 0
            elif data_type == 'Максимальная зарплата':
                value = stat.max_salary if stat.max_salary else 0
            else:
                value = 0

            data.append((skill_name, value))

        if len(data) > 15:
            data = data[:15]

        if chart_type == 'Круговая':
            self.create_pie_chart(data, data_type)
        elif chart_type == 'Столбчатая':
            self.create_bar_chart(data, data_type)

    def create_pie_chart(self, data, data_type):
        series = QPieSeries()

        for name, value in data:
            if value > 0:
                slice_ = series.append(f"{name} ({value:.1f})", value)
                slice_.setLabelVisible()

        chart = QChart()
        chart.addSeries(series)

        chart_title = f"{data_type}\n(Шаблон: {self.current_analysis.template})"
        chart.setTitle(chart_title)
        chart.legend().setVisible(True)

        self.chart_view.setChart(chart)

    def create_bar_chart(self, data, data_type):
        series = QBarSeries()
        bar_set = QBarSet(data_type)

        categories = []
        for name, value in data:
            if value > 0:
                bar_set.append(value)
                categories.append(name)

        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)

        chart_title = f"{data_type}\n(Шаблон: {self.current_analysis.template})"
        chart.setTitle(chart_title)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(v for _, v in data) * 1.1)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        self.chart_view.setChart(chart)

    def save_visualization(self):
        if not self.chart_view.chart():
            return

        save_dir = "saved_visualizations"
        os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_name = self.current_analysis.template if self.current_analysis else "unknown"
        safe_template_name = "".join(c if c.isalnum() else "_" for c in template_name)
        filename = f"{save_dir}/{timestamp}_{safe_template_name}.png"

        image = QImage(self.chart_view.size(), QImage.Format_ARGB32)
        painter = QPainter(image)
        self.chart_view.render(painter)
        painter.end()
        image.save(filename)

        QMessageBox.information(
            self,
            "Сохранение завершено",
            f"Визуализация сохранена в файл:\n{filename}"
        )
