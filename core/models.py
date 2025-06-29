from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from sqlalchemy import DateTime
Base = declarative_base()


class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    registration_date = Column(Date)
    role = Column(String, default='user')
    analyses = relationship("Analysis", back_populates="user")


class Vacancy(Base):
    __tablename__ = 'vacancies'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    title = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, unique=True)
    city = Column(String, nullable=True)
    published_date = Column(Date)
    source = Column(String)
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String)
    is_remote = Column(Boolean, default=False)
    employment_type = Column(String, nullable=True)

    company = relationship("Company")
    skills = relationship("Skill", secondary='vacancies_skills')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company.name if self.company else None,
            'salary': f"{self.salary_min or ''}-{self.salary_max or ''} {self.salary_currency or ''}",
            'skills': [skill.name for skill in self.skills],
            'is_remote': self.is_remote,
            'employment_type': self.employment_type,
            'published_date': str(self.published_date) if self.published_date else None,
            'url': self.url
        }


class VacancySkill(Base):
    __tablename__ = 'vacancies_skills'
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)


class AnalysisSkill(Base):
    __tablename__ = 'analysis_skills'
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'))
    skill_id = Column(Integer, ForeignKey('skills.id'))
    vacancy_count = Column(Integer)
    frequency = Column(Float)
    min_salary = Column(Float)
    max_salary = Column(Float)
    avg_salary = Column(Float)

    analysis = relationship("Analysis", back_populates="skill_stats")
    skill = relationship("Skill")


class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    template = Column(String)

    total_vacancies = Column(Integer)

    user = relationship("User", back_populates="analyses")
    skill_stats = relationship("AnalysisSkill", back_populates="analysis")

    def add_skill_stat(self, skill_id: int, vacancy_count: int, frequency: float,
                       min_salary: float, max_salary: float, avg_salary: float):
        stat = AnalysisSkill(
            skill_id=skill_id,
            vacancy_count=vacancy_count,
            frequency=frequency,
            min_salary=min_salary,
            max_salary=max_salary,
            avg_salary=avg_salary
        )
        self.skill_stats.append(stat)


class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class TemplateVacancy(Base):
    __tablename__ = 'template_vacancies'
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('templates.id'))
    vacancy_query = Column(String, nullable=False)
    template = relationship("Template")
