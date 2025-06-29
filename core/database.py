from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from core.models import Base, User


class Database:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), '../data/vacancies.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)

        self.create_tables()

        self.create_admin_user()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def create_admin_user(self):
        session = self.get_session()
        try:
            admin = session.query(User).filter_by(login='admin').first()
            if not admin:
                admin = User(
                    login='admin',
                    password=self.hash_password('admin1'),
                    role='admin'
                )
                session.add(admin)
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при создании администратора: {str(e)}")
        finally:
            session.close()

    def get_session(self):
        return self.Session()

    @staticmethod
    def hash_password(password: str) -> str:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class UserDatabase:
    def __init__(self, user_id):
        if not user_id:
            raise ValueError("User ID is required for UserDatabase")

        db_dir = os.path.join(os.path.dirname(__file__), '../data/users')
        os.makedirs(db_dir, exist_ok=True)

        db_path = os.path.join(db_dir, f'user_{user_id}.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        self.create_tables()

    def create_tables(self):
        from core.models import (Base, Vacancy, Company,
                                 Skill, VacancySkill, Analysis,
                                 AnalysisSkill)

        tables = [
            Vacancy.__table__,
            Company.__table__,
            Skill.__table__,
            VacancySkill.__table__,
            Analysis.__table__,
            AnalysisSkill.__table__
        ]

        Base.metadata.create_all(self.engine, tables=tables)

    def get_session(self):
        return self.Session()

    def clear_database(self):
        from core.models import (Base, Vacancy, Company,
                                 Skill, VacancySkill, Analysis,
                                 AnalysisSkill)

        tables = [
            Vacancy.__table__,
            Company.__table__,
            Skill.__table__,
            VacancySkill.__table__,
            Analysis.__table__,
            AnalysisSkill.__table__
        ]

        Base.metadata.drop_all(self.engine, tables=tables)
        self.create_tables()
        self.Session.remove()

    def delete_database(self):
        self.Session.remove()
        db_path = self.engine.url.database
        if os.path.exists(db_path):
            os.remove(db_path)
