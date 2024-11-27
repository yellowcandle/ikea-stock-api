from dataclasses import dataclass
from typing import Dict, Optional
from decimal import Decimal

@dataclass
class Product:
    name: str
    url: str
    description: str
    image_url: str
    price: Optional[Decimal]

@dataclass
class StockInfo:
    warehouse: int = 0
    causeway_bay: int = 0
    kowloon_bay: int = 0
    macau_taipa: int = 0
    shatin: int = 0
    tsuen_wan: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'StockInfo':
        return cls(
            warehouse=data.get('Warehouse', 0),
            causeway_bay=data.get('Causeway Bay', 0),
            kowloon_bay=data.get('Kowloon Bay', 0),
            macau_taipa=data.get('Macau Taipa', 0),
            shatin=data.get('Shatin', 0),
            tsuen_wan=data.get('Tsuen Wan', 0)
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            'Warehouse': self.warehouse,
            'Causeway Bay': self.causeway_bay,
            'Kowloon Bay': self.kowloon_bay,
            'Macau Taipa': self.macau_taipa,
            'Shatin': self.shatin,
            'Tsuen Wan': self.tsuen_wan
        }

    def __str__(self) -> str:
        """Format stock information in IKEA's style"""
        lines = []
        for store, qty in self.to_dict().items():
            if qty > 0:
                lines.append(f"In stock at {store} {qty} in stock")
            else:
                lines.append(f"Out of stock at {store}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return str(self)
