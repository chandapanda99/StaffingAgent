from enum import Enum


class MessageCategory(str, Enum):
    contractor = "contractor"
    job_posting = "job_posting"
    other = "other"
