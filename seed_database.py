#!/usr/bin/env python3
"""
Script pour alimenter la base de données avec des produits d'exemple.
Génère 100 produits avec des données variées et réalistes.
"""

import os
import random
from sqlmodel import create_engine, Session, SQLModel
from models.product import Product
from models.cart import Cart, CartProduct  # Importer tous les modèles pour éviter les erreurs de référence
from typing import List

# Configuration de la base de données
database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ecommerce")

# Données d'exemple pour générer des produits variés
CATEGORIES = [
    "Électronique",
    "Vêtements",
    "Maison & Jardin",
    "Sport & Loisirs",
    "Livres",
    "Beauté & Santé",
    "Automobile",
    "Jouets",
    "Alimentation",
    "High-Tech"
]

PRODUCT_NAMES = {
    "Électronique": [
        "Smartphone Samsung Galaxy S24",
        "iPhone 15 Pro Max",
        "MacBook Air M3",
        "Tablette iPad Pro",
        "Écouteurs AirPods Pro",
        "Casque Sony WH-1000XM5",
        "Téléviseur OLED 55 pouces",
        "Console PlayStation 5",
        "Nintendo Switch OLED",
        "Montre connectée Apple Watch"
    ],
    "Vêtements": [
        "T-shirt en coton bio",
        "Jean slim délavé",
        "Robe d'été fleurie",
        "Veste en cuir vintage",
        "Baskets Nike Air Max",
        "Chemise en lin blanc",
        "Pull en laine mérinos",
        "Manteau d'hiver",
        "Chaussures de randonnée",
        "Polo Ralph Lauren"
    ],
    "Maison & Jardin": [
        "Aspirateur robot Roomba",
        "Cafetière expresso DeLonghi",
        "Set de casseroles inox",
        "Plantes vertes d'intérieur",
        "Lampe LED design",
        "Tapis persan authentique",
        "Miroir décoratif rond",
        "Bougie parfumée artisanale",
        "Coussin velours bleu",
        "Table basse scandinave"
    ],
    "Sport & Loisirs": [
        "Vélo électrique urbain",
        "Tapis de yoga premium",
        "Haltères ajustables",
        "Raquette de tennis Wilson",
        "Ballon de football Nike",
        "Sac de sport Adidas",
        "Montre de sport Garmin",
        "Tente de camping 4 places",
        "Sac à dos de randonnée",
        "Planche de surf débutant"
    ],
    "Livres": [
        "Roman policier bestseller",
        "Guide de développement Python",
        "Livre de cuisine française",
        "Bande dessinée One Piece",
        "Manuel de jardinage bio",
        "Biographie Steve Jobs",
        "Livre de méditation",
        "Atlas du monde illustré",
        "Roman fantasy épique",
        "Guide de voyage Japon"
    ],
    "Beauté & Santé": [
        "Crème hydratante visage",
        "Parfum Chanel N°5",
        "Brosse à dents électrique",
        "Sérum anti-âge vitamine C",
        "Masque cheveux réparateur",
        "Complément alimentaire bio",
        "Diffuseur d'huiles essentielles",
        "Gommage corps exfoliant",
        "Rouge à lèvres mat longue tenue",
        "Démaquillant bi-phase"
    ],
    "Automobile": [
        "Pneus été Michelin",
        "Porte-vélos sur toit",
        "GPS Garmin DriveSmart",
        "Chargeur voiture USB-C",
        "Tapis de sol auto",
        "Housse de siège cuir",
        "Kit de nettoyage auto",
        "Dashcam full HD",
        "Antivol volant",
        "Compresseur d'air portable"
    ],
    "Jouets": [
        "LEGO Creator Expert",
        "Poupée Barbie collector",
        "Puzzle 1000 pièces",
        "Peluche teddy bear géant",
        "Voiture télécommandée",
        "Jeu de société Monopoly",
        "Tablette éducative enfant",
        "Cuisine jouet en bois",
        "Train électrique miniature",
        "Trottinette enfant 3 roues"
    ],
    "Alimentation": [
        "Huile d'olive extra vierge",
        "Chocolat noir 70% cacao",
        "Miel de lavande bio",
        "Thé vert japonais premium",
        "Café arabica torréfaction",
        "Confiture fraise artisanale",
        "Pâtes italiennes artisanales",
        "Épices du monde coffret",
        "Vin rouge Bordeaux",
        "Fromage comté 24 mois"
    ],
    "High-Tech": [
        "Drone 4K avec caméra",
        "Imprimante 3D Ender",
        "Clavier mécanique gaming",
        "Webcam 4K streaming",
        "Disque SSD externe 1To",
        "Enceinte Bluetooth JBL",
        "Projecteur LED portable",
        "Station de charge sans fil",
        "Hub USB-C multiport",
        "Caméra d'action GoPro"
    ]
}

DESCRIPTIONS_BASE = {
    "Électronique": "Technologie de pointe avec des performances exceptionnelles. Design élégant et fonctionnalités avancées pour une expérience utilisateur optimale.",
    "Vêtements": "Confort et style réunis dans un vêtement de qualité supérieure. Matières nobles et coupe moderne pour un look tendance.",
    "Maison & Jardin": "Transformez votre intérieur avec cet article design et fonctionnel. Qualité premium pour votre confort quotidien.",
    "Sport & Loisirs": "Équipement sportif professionnel pour améliorer vos performances. Durabilité et confort garantis.",
    "Livres": "Découvrez une lecture captivante qui vous transportera dans un autre univers. Contenu riche et passionnant.",
    "Beauté & Santé": "Prenez soin de vous avec ce produit de beauté premium. Formule naturelle et résultats visibles.",
    "Automobile": "Accessoire automobile de qualité pour améliorer votre expérience de conduite. Fiabilité et sécurité assurées.",
    "Jouets": "Jouet éducatif et amusant pour développer la créativité. Sécurité certifiée et plaisir garanti.",
    "Alimentation": "Produit gastronomique d'exception pour les fins gourmets. Saveurs authentiques et qualité premium.",
    "High-Tech": "Innovation technologique de dernière génération. Performance et design futuriste pour les passionnés de tech."
}

SAMPLE_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1560472355-536de3962603",
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
    "https://images.unsplash.com/photo-1572635196237-14b3f281503f",
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
    "https://images.unsplash.com/photo-1549298916-b41d501d3772",
    "https://images.unsplash.com/photo-1484723091739-30a097e8f929",
    "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f",
    "https://images.unsplash.com/photo-1503602642458-232111445657",
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8"
]

def generate_price(category: str) -> float:
    """Génère un prix réaliste selon la catégorie"""
    price_ranges = {
        "Électronique": (50, 2000),
        "Vêtements": (15, 300),
        "Maison & Jardin": (20, 500),
        "Sport & Loisirs": (25, 800),
        "Livres": (8, 45),
        "Beauté & Santé": (12, 150),
        "Automobile": (30, 600),
        "Jouets": (10, 200),
        "Alimentation": (5, 80),
        "High-Tech": (40, 1500)
    }
    
    min_price, max_price = price_ranges.get(category, (10, 100))
    return round(random.uniform(min_price, max_price), 2)

def generate_description(category: str, product_name: str) -> str:
    """Génère une description détaillée pour le produit"""
    base_desc = DESCRIPTIONS_BASE.get(category, "Produit de qualité exceptionnelle.")
    
    additional_features = [
        "Livraison gratuite sous 48h",
        "Garantie 2 ans incluse",
        "Retour gratuit sous 30 jours",
        "Service client 7j/7",
        "Paiement sécurisé",
        "Stock limité",
        "Meilleure vente",
        "Nouveau produit",
        "Écologique et durable",
        "Fabriqué en Europe"
    ]
    
    features = random.sample(additional_features, random.randint(2, 4))
    feature_text = " • ".join(features)
    
    return f"{base_desc}\n\n✨ Caractéristiques :\n• {feature_text}"

def generate_all_products() -> List[Product]:
    """Génère tous les produits disponibles sans duplication"""
    products = []
    
    # Générer tous les produits de chaque catégorie
    for category in CATEGORIES:
        category_products = PRODUCT_NAMES[category]
        
        for product_name in category_products:
            # Générer le prix
            price = generate_price(category)
            
            # Sélectionner des images aléatoires (mais différentes pour chaque produit)
            # Utiliser l'index du produit pour avoir des images différentes
            product_index = len(products)
            thumbnail_index = product_index % len(SAMPLE_IMAGE_URLS)
            thumbnail = SAMPLE_IMAGE_URLS[thumbnail_index]
            
            # Sélectionner des images différentes pour la galerie
            num_images = min(4, len(SAMPLE_IMAGE_URLS) - 1)  # Maximum 4 images en plus du thumbnail
            start_index = (product_index + 1) % len(SAMPLE_IMAGE_URLS)
            images = []
            for i in range(num_images):
                img_index = (start_index + i) % len(SAMPLE_IMAGE_URLS)
                if SAMPLE_IMAGE_URLS[img_index] != thumbnail:  # Éviter de dupliquer le thumbnail
                    images.append(SAMPLE_IMAGE_URLS[img_index])
            
            # S'assurer d'avoir au moins 2 images différentes du thumbnail
            if len(images) < 2:
                for url in SAMPLE_IMAGE_URLS:
                    if url != thumbnail and url not in images:
                        images.append(url)
                        if len(images) >= 2:
                            break
            
            # Générer la description
            description = generate_description(category, product_name)
            
            product = Product(
                title=product_name,
                price=price,
                thumbnail=thumbnail,
                images=images,
                description=description,
                category=category
            )
            
            products.append(product)
            print(f"Généré: {product_name} - {price}€ ({category})")
    
    return products

def create_db_and_tables(engine):
    """Crée les tables de la base de données"""
    SQLModel.metadata.create_all(engine)

def seed_database():
    """Fonction principale pour alimenter la base de données"""
    print("🌱 Démarrage du script de peuplement de la base de données...")
    
    # Créer le moteur de base de données
    engine = create_engine(database_url, echo=True)
    
    # Créer les tables si elles n'existent pas
    create_db_and_tables(engine)
    
    # Générer tous les produits uniques
    print("📦 Génération de tous les produits disponibles (sans duplication)...")
    products = generate_all_products()
    
    # Insérer les produits dans la base de données
    with Session(engine) as session:
        print("💾 Insertion des produits dans la base de données...")
        
        for product in products:
            session.add(product)
        
        try:
            session.commit()
            print(f"✅ {len(products)} produits ajoutés avec succès!")
            
            # Afficher quelques statistiques
            print("\n📊 Statistiques:")
            categories_count = {}
            total_value = 0
            
            for product in products:
                categories_count[product.category] = categories_count.get(product.category, 0) + 1
                total_value += product.price
            
            print(f"💰 Valeur totale du stock: {total_value:.2f}€")
            print(f"💶 Prix moyen: {total_value/len(products):.2f}€")
            print("\n🏷️ Répartition par catégorie:")
            
            for category, count in sorted(categories_count.items()):
                print(f"  • {category}: {count} produits")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur lors de l'insertion: {e}")
            raise

if __name__ == "__main__":
    seed_database()
