from typing import List, Dict

import pandas as pd
from pydantic import BaseModel, FilePath


class StudentInfoModel(BaseModel):
    student_user_id: int
    discord_username: str
    identifiers: List[str] = []


class ClassRosterModel(BaseModel):
    students: Dict[str, StudentInfoModel]

    @classmethod
    def from_csv(cls, file_path: FilePath) -> 'ClassRosterModel':
        students = {}
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            student = StudentInfoModel(
                student_user_id=row['student_user_id'],
                discord_username=row['discord_username'],
                identifiers=row['identifiers'].split(',')
            )
            students[student.student_hex_id] = student
        return cls(students=students)


# Usage example:
# class_roster = ClassRosterModel.load_from_csv('path_to_csv.csv')
