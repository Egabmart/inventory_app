from dataclasses import dataclass

@dataclass
class Department:
    dept_id: int
    abbreviation: str
    name: str

@dataclass
class SubDepartment:
    sub_id: int
    parent: Department
    abbreviation: str
    name: str

@dataclass
class Product:
    prod_id: str
    parent: SubDepartment
    name: str
    description: str
    price: float
    quantity: int

@dataclass
class Local:
    local_id: int
    name: str
