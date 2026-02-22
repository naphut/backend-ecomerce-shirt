from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app import crud, schemas, models
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.ProductList])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    search: Optional[str] = Query(None, description="Search by product name"),
    sort: Optional[str] = Query(None, description="Sort by: price_asc, price_desc, name_asc, name_desc"),
    featured: Optional[bool] = Query(None, description="Filter featured products"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get products with optional filtering and sorting
    """
    products = crud.get_products(
        db, 
        category_slug=category,
        search=search,
        sort=sort,
        featured=featured,
        skip=skip,
        limit=limit
    )
    return products

@router.get("/{product_id}", response_model=schemas.Product)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID
    """
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/slug/{slug}", response_model=schemas.Product)
async def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by slug
    """
    product = crud.get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=schemas.Product)
async def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product (admin only)
    """
    # ពិនិត្យមើល slug
    existing_slug = crud.get_product_by_slug(db, product.slug)
    if existing_slug:
        raise HTTPException(
            status_code=400,
            detail=f"Product with slug '{product.slug}' already exists"
        )
    
    # ពិនិត្យមើល SKU (ប្រសិនបើមាន)
    if product.sku:
        existing_sku = db.query(models.Product).filter(models.Product.sku == product.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product.sku}' already exists"
            )
    
    return crud.create_product(db, product)

@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Update a product (admin only)
    """
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # ពិនិត្យមើល slug មិនឲ្យដូចអ្នកដទៃ
    if product.slug != db_product.slug:
        existing = crud.get_product_by_slug(db, product.slug)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Product with slug '{product.slug}' already exists"
            )
    
    # ពិនិត្យមើល SKU មិនឲ្យដូចអ្នកដទៃ
    if product.sku and product.sku != db_product.sku:
        existing_sku = db.query(models.Product).filter(models.Product.sku == product.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product.sku}' already exists"
            )
    
    updated_product = crud.update_product(db, product_id, product.dict())
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a product (admin only)
    """
    success = crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@router.get("/featured/", response_model=List[schemas.ProductList])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get featured products
    """
    return crud.get_featured_products(db, limit)