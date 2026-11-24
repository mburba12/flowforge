from enum import StrEnum


class WorkerType(StrEnum):
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    TEMPORARY = "temporary"
    SEASONAL = "seasonal"
    INTERN = "intern"


class EmploymentStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    LEAVE = "leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    RETIRED = "retired"


class CompensationType(StrEnum):
    SALARY = "salary"
    HOURLY = "hourly"
    BONUS = "bonus"
    COMMISSION = "commission"
    OVERTIME = "overtime"


class PayFrequency(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
