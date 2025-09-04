from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.product import Product

# Modèles de base
class CartBase(SQLModel):
    user_id: str  # ID utilisateur géré par un service externe
    status: str = Field(default="active")

class CartProductBase(SQLModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)

# Modèles de base de données
class Cart(CartBase, table=True):
    id: int = Field(default=None, primary_key=True)
    total_price: float = Field(default=0.0)
    
    # Relation one-to-many avec CartProduct
    cart_products: List["CartProduct"] = Relationship(back_populates="cart")

class CartProduct(CartProductBase, table=True):
    cart_id: int = Field(foreign_key="cart.id", primary_key=True)
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    price_at_time: float  # Prix du produit au moment de l'ajout au panier
    
    # Relations
    cart: Cart = Relationship(back_populates="cart_products")
    product: "Product" = Relationship(back_populates="cart_products")

# Modèles de requête/réponse simplifiés
class CartCreate(CartBase):
    pass

class CartProductRead(CartProductBase):
    cart_id: int
    price_at_time: float

class CartRead(CartBase):
    id: int
    total_price: float

class CartProductCreate(SQLModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)

class CartProductUpdate(SQLModel):
    quantity: int = Field(gt=0)

# Modèle enrichi pour les réponses avec détails
class CartWithProducts(CartRead):
    products: List[CartProductRead] = []