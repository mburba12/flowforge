from enum import StrEnum


class PartyKind(StrEnum):
    ORGANIZATION = "organization"
    PERSON = "person"


class PartyStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    MERGED = "merged"


class PartyRole(StrEnum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    FINANCIAL_INSTITUTION = "financial_institution"
    GOVERNMENT_AUTHORITY = "government_authority"
    LEGAL_ENTITY = "legal_entity"


class AddressType(StrEnum):
    BILLING = "billing"
    SHIPPING = "shipping"
    REGISTERED = "registered"
    WORK = "work"
    HOME = "home"


class ContactType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    WEBSITE = "website"


class RelationshipType(StrEnum):
    PARENT = "parent"
    SUBSIDIARY = "subsidiary"
    CONTACT = "contact"
    EMPLOYER = "employer"
    CONTRACTOR = "contractor"
    PARTNER = "partner"
