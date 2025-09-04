from sqlmodel import Field, Session, SQLModel, Relationship, JSON, Column
from sqlalchemy import JSON as SAJSON
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.cart import CartProduct

class ProductBase(SQLModel):
    title: str
    price: float
    thumbnail: str
    images: List[str] = Field(sa_column=Column(SAJSON))
    description: str
    category: str

class Product(ProductBase, table=True):
    id: int = Field(default=None, primary_key=True)
    
    # Relation many-to-many avec Cart via CartProduct
    cart_products: List["CartProduct"] = Relationship(back_populates="product")

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

class ProductUpdate(SQLModel):
    title: Optional[str] = None
    price: Optional[float] = None
    thumbnail: Optional[str] = None
    images: Optional[list[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None

class ProductsResponse(SQLModel):
    products: List[ProductRead]
    total: int