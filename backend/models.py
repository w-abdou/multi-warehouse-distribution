from dataclasses import dataclass


@dataclass(frozen=True)
class Warehouse:
    id: str
    name: str
    x: float
    y: float
    stock: int


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    x: float
    y: float
    region: str


@dataclass(frozen=True)
class Order:
    id: str
    customer_id: str
    weight: float
    volume: float
    units: int = 1
    priority: int = 0
