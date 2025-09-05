from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
import os
import shutil
import uuid
from pathlib import Path
from sqlmodel import create_engine, Session, select, SQLModel, func, or_
from models.product import Product, ProductCreate, ProductRead, ProductUpdate, ProductsResponse
from models.cart import Cart, CartProduct, CartCreate, CartRead, CartProductCreate, CartProductUpdate, CartProductRead, CartWithProducts
from typing import Annotated, Optional, List
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware


database_url = os.getenv("DATABASE_URL")

print(database_url)
# Pour PostgreSQL, pas besoin de connect_args spéciaux
engine = create_engine(database_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def create_images_directory():
    """Créer le dossier data/images s'il n'existe pas"""
    images_dir = Path("data/images")
    images_dir.mkdir(parents=True, exist_ok=True)

def get_session():
    with Session(engine) as session:
        yield session



tags_metadata = [
    {
        "name": "Products",
        "description": "Opérations sur les produits : création, lecture, mise à jour et suppression. Inclut également la gestion des catégories.",
    },
    {
        "name": "Carts",
        "description": "Gestion des paniers d'achat : création, gestion des produits dans le panier, et opérations utilisateur.",
    },
    {
        "name": "Images",
        "description": "Upload et récupération d'images pour les produits.",
    },
]

app = FastAPI(
    title="E-commerce API",
    description="API complète pour une application e-commerce avec gestion des produits, paniers et images",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Configuration CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_images_directory()


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Définir SessionDep ici
SessionDep = Annotated[Session, Depends(get_session)]

# Endpoints Products
@app.post("/products", response_model=ProductRead, tags=["Products"])
def create_product(product: ProductCreate, session: SessionDep):
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@app.get("/products", response_model=ProductsResponse, tags=["Products"])
def get_products(
    session: SessionDep,
    limit: Optional[int] = Query(None, ge=1, description="Nombre de produits à récupérer"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination"),
    categories: Optional[List[str]] = Query(None, description="Filtrer par catégories"),
    search: Optional[str] = Query(None, description="Recherche fuzzy dans le titre et la description"),
    min_price: Optional[float] = Query(None, ge=0, description="Prix minimum"),
    max_price: Optional[float] = Query(None, ge=0, description="Prix maximum")
):
    # Construire la requête de base
    query = select(Product)
    
    # Appliquer le filtre de recherche fuzzy
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Product.title).contains(search_term),
                func.lower(Product.description).contains(search_term)
            )
        )
    
    # Appliquer le filtre par catégories
    if categories:
        query = query.where(Product.category.in_(categories))
    
    # Appliquer le filtre par fourchette de prix
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    
    # Compter le total des produits (avant pagination)
    total_query = select(func.count()).select_from(query.subquery())
    total = session.exec(total_query).one()
    
    # Appliquer la pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    # Exécuter la requête
    products = session.exec(query).all()
    
    return ProductsResponse(products=products, total=total)

@app.get("/products/{product_id}", response_model=ProductRead, tags=["Products"])
def get_product(product_id: int, session: SessionDep):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product

@app.patch("/products/{product_id}", response_model=ProductRead, tags=["Products"])
def update_product(product_id: int, product_update: ProductUpdate, session: SessionDep):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    product_data = product_update.model_dump(exclude_unset=True)
    for field, value in product_data.items():
        setattr(product, field, value)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@app.delete("/products/{product_id}", tags=["Products"])
def delete_product(product_id: int, session: SessionDep):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    session.delete(product)
    session.commit()
    return {"message": "Produit supprimé avec succès"}

@app.get("/categories", response_model=List[str], tags=["Products"])
def get_categories(session: SessionDep):
    """Récupère toutes les catégories distinctes de produits"""
    categories = session.exec(
        select(Product.category).distinct()
    ).all()
    
    # Filtrer les catégories None et trier par ordre alphabétique
    categories = [cat for cat in categories if cat is not None]
    categories.sort()
    
    return categories

# Endpoints Cart
@app.post("/carts", response_model=CartRead, tags=["Carts"])
def create_cart(cart: CartCreate, session: SessionDep):
    db_cart = Cart.model_validate(cart)
    session.add(db_cart)
    session.commit()
    session.refresh(db_cart)
    return db_cart

@app.get("/carts/{cart_id}", response_model=CartRead, tags=["Carts"])
def get_cart(cart_id: int, session: SessionDep):
    cart = session.get(Cart, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    return cart

@app.get("/carts/{cart_id}/products", response_model=list[CartProductRead], tags=["Carts"])
def get_cart_products(cart_id: int, session: SessionDep):
    cart = session.get(Cart, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    
    cart_products = session.exec(
        select(CartProduct).where(CartProduct.cart_id == cart_id)
    ).all()
    return cart_products

@app.get("/carts/{cart_id}/details", response_model=CartWithProducts, tags=["Carts"])
def get_cart_with_products(cart_id: int, session: SessionDep):
    cart = session.get(Cart, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    
    cart_products = session.exec(
        select(CartProduct).where(CartProduct.cart_id == cart_id)
    ).all()
    
    # Créer la réponse avec les produits
    cart_data = cart.model_dump()
    cart_data["products"] = [cp.model_dump() for cp in cart_products]
    
    return CartWithProducts(**cart_data)

@app.get("/carts/user/{user_id}", response_model=list[CartRead], tags=["Carts"])
def get_user_carts(user_id: str, session: SessionDep):
    carts = session.exec(select(Cart).where(Cart.user_id == user_id)).all()
    return carts

@app.get("/carts/user/{user_id}/active", response_model=CartRead, tags=["Carts"])
def get_user_active_cart(user_id: str, session: SessionDep):
    """Récupère le panier actif de l'utilisateur, ou en crée un nouveau s'il n'en existe pas"""
    cart = session.exec(
        select(Cart).where(
            Cart.user_id == user_id,
            Cart.status == "active"
        )
    ).first()
    
    if not cart:
        # Créer un nouveau panier actif pour l'utilisateur
        cart = Cart(user_id=user_id, status="active", total_price=0.0)
        session.add(cart)
        session.commit()
        session.refresh(cart)
    
    return cart

@app.post("/carts/{cart_id}/products", tags=["Carts"])
def add_product_to_cart(cart_id: int, cart_product: CartProductCreate, session: SessionDep):
    # Vérifier que le panier existe
    cart = session.get(Cart, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    
    # Vérifier que le produit existe
    product = session.get(Product, cart_product.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Vérifier si le produit est déjà dans le panier
    existing_cart_product = session.exec(
        select(CartProduct).where(
            CartProduct.cart_id == cart_id,
            CartProduct.product_id == cart_product.product_id
        )
    ).first()
    
    if existing_cart_product:
        # Mettre à jour la quantité
        existing_cart_product.quantity += cart_product.quantity
        session.add(existing_cart_product)
    else:
        # Créer un nouveau CartProduct
        db_cart_product = CartProduct(
            cart_id=cart_id,
            product_id=cart_product.product_id,
            quantity=cart_product.quantity,
            price_at_time=product.price
        )
        session.add(db_cart_product)
    
    # Recalculer le prix total du panier
    cart_products = session.exec(
        select(CartProduct).where(CartProduct.cart_id == cart_id)
    ).all()
    total_price = sum(cp.quantity * cp.price_at_time for cp in cart_products)
    cart.total_price = total_price
    
    session.add(cart)
    session.commit()
    
    return {"message": "Produit ajouté au panier avec succès"}

@app.patch("/carts/{cart_id}/products/{product_id}", tags=["Carts"])
def update_cart_product(cart_id: int, product_id: int, update_data: CartProductUpdate, session: SessionDep):
    cart_product = session.exec(
        select(CartProduct).where(
            CartProduct.cart_id == cart_id,
            CartProduct.product_id == product_id
        )
    ).first()
    
    if not cart_product:
        raise HTTPException(status_code=404, detail="Produit non trouvé dans le panier")
    
    cart_product.quantity = update_data.quantity
    session.add(cart_product)
    
    # Recalculer le prix total du panier
    cart = session.get(Cart, cart_id)
    cart_products = session.exec(
        select(CartProduct).where(CartProduct.cart_id == cart_id)
    ).all()
    total_price = sum(cp.quantity * cp.price_at_time for cp in cart_products)
    cart.total_price = total_price
    
    session.add(cart)
    session.commit()
    
    return {"message": "Quantité mise à jour avec succès"}

@app.delete("/carts/{cart_id}/products/{product_id}", tags=["Carts"])
def remove_product_from_cart(cart_id: int, product_id: int, session: SessionDep):
    cart_product = session.exec(
        select(CartProduct).where(
            CartProduct.cart_id == cart_id,
            CartProduct.product_id == product_id
        )
    ).first()
    
    if not cart_product:
        raise HTTPException(status_code=404, detail="Produit non trouvé dans le panier")
    
    session.delete(cart_product)
    
    # Recalculer le prix total du panier
    cart = session.get(Cart, cart_id)
    cart_products = session.exec(
        select(CartProduct).where(CartProduct.cart_id == cart_id)
    ).all()
    total_price = sum(cp.quantity * cp.price_at_time for cp in cart_products)
    cart.total_price = total_price
    
    session.add(cart)
    session.commit()
    
    return {"message": "Produit retiré du panier avec succès"}

# Endpoints Images
@app.post("/images/upload", tags=["Images"])
async def upload_image(file: UploadFile = File(...)):
    """Uploader une image dans le dossier data/images"""
    
    # Vérifier le type de fichier
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    
    # Générer un nom de fichier unique
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(status_code=400, detail="Type d'image non supporté. Utilisez jpg, jpeg, png, gif ou webp")
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = Path("data/images") / unique_filename
    
    try:
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Image uploadée avec succès",
            "filename": unique_filename,
            "original_filename": file.filename,
            "url": f"/images/{unique_filename}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/images/{filename}", tags=["Images"])
async def get_image(filename: str):
    """Récupérer une image par son nom de fichier"""
    
    file_path = Path("data/images") / filename
    
    # Vérifier que le fichier existe
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Vérifier que c'est bien un fichier (pas un dossier)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Déterminer le type MIME basé sur l'extension
    file_extension = file_path.suffix.lower()
    media_type_mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", 
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    
    media_type = media_type_mapping.get(file_extension, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )