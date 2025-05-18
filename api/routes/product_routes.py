from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field, validator, root_validator
from sqlalchemy import or_

from product_evaluator.models.user.user_model import User
from product_evaluator.models.product.product_model import Product
from product_evaluator.services.auth.authentication import get_current_active_user
from product_evaluator.services.extraction.web_extractor import extract_content_from_url
from product_evaluator.utils.database import get_db
from product_evaluator.utils.logger import log_info, log_error


router = APIRouter(tags=["products"])


# --- Pydantic Models ---

class ProductBase(BaseModel):
    """Base schema for product data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    category: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    price: Optional[float] = None
    pricing_model: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    extract_content: bool = Field(False, description="Whether to extract content from website_url")
    
    @root_validator
    def validate_extraction(cls, values):
        """Validate that website_url is provided if extract_content is True."""
        extract_content = values.get("extract_content", False)
        website_url = values.get("website_url")
        
        if extract_content and not website_url:
            raise ValueError("website_url must be provided if extract_content is True")
        
        return values


class ProductUpdate(ProductBase):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    extract_content: bool = Field(False, description="Whether to extract content from website_url")


class ProductResponse(ProductBase):
    """Schema for product data in responses."""
    id: str
    created_at: str
    updated_at: str
    created_by_id: str
    extracted_content: Optional[str] = None
    extracted_features: Optional[str] = None
    average_rating: Optional[float] = None
    evaluation_count: int
    
    class Config:
        from_attributes = True


class ExtractContentResponse(BaseModel):
    """Schema for content extraction response."""
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


# --- Routes ---

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new product."""
    # Create product object
    product = Product(
        name=product_data.name,
        description=product_data.description,
        website_url=str(product_data.website_url) if product_data.website_url else None,
        category=product_data.category,
        vendor=product_data.vendor,
        version=product_data.version,
        price=product_data.price,
        pricing_model=product_data.pricing_model,
        created_by_id=current_user.id,
    )
    
    # Extract content if requested
    if product_data.extract_content and product_data.website_url:
        try:
            extraction_result = await extract_content_from_url(str(product_data.website_url))
            
            if not extraction_result.get("error"):
                product.extracted_content = extraction_result.get("content", "")
                
                # Extract features if available in metadata
                if "features" in extraction_result.get("metadata", {}):
                    product.extracted_features = extraction_result["metadata"]["features"]
                
                # Update product name or description if empty and available in metadata
                if not product.description and "description" in extraction_result.get("metadata", {}):
                    product.description = extraction_result["metadata"]["description"]
                
                # Update product name if available in metadata
                if "product_name" in extraction_result.get("metadata", {}) and extraction_result["metadata"]["product_name"]:
                    # Only use as name if significantly different and current name is generic
                    metadata_name = extraction_result["metadata"]["product_name"]
                    if (len(product.name) < 10 or product.name.lower() in ["product", "new product"]) and len(metadata_name) > 5:
                        product.name = metadata_name
            else:
                log_error(f"Content extraction failed: {extraction_result.get('error')}")
        except Exception as e:
            log_error(f"Error during content extraction: {str(e)}")
    
    # Add to database
    db.add(product)
    db.commit()
    db.refresh(product)
    
    log_info(f"Product created: {product.name} by user {current_user.username}")
    
    # Calculate properties for response
    setattr(product, 'average_rating', product.average_rating)
    setattr(product, 'evaluation_count', product.evaluation_count)
    
    return product


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering."""
    query = db.query(Product)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.vendor.ilike(search_term)
            )
        )
    
    if category:
        query = query.filter(Product.category == category)
    
    if vendor:
        query = query.filter(Product.vendor == vendor)
    
    # Apply pagination
    products = query.offset(skip).limit(limit).all()
    
    # Calculate additional properties for each product
    for product in products:
        setattr(product, 'average_rating', product.average_rating)
        setattr(product, 'evaluation_count', product.evaluation_count)
    
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Calculate additional properties
    setattr(product, 'average_rating', product.average_rating)
    setattr(product, 'evaluation_count', product.evaluation_count)
    
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user is the creator or an admin
    if product.created_by_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can update this product"
        )
    
    # Update fields if provided
    if product_data.name is not None:
        product.name = product_data.name
    
    if product_data.description is not None:
        product.description = product_data.description
    
    if product_data.website_url is not None:
        product.website_url = str(product_data.website_url)
    
    if product_data.category is not None:
        product.category = product_data.category
    
    if product_data.vendor is not None:
        product.vendor = product_data.vendor
    
    if product_data.version is not None:
        product.version = product_data.version
    
    if product_data.price is not None:
        product.price = product_data.price
    
    if product_data.pricing_model is not None:
        product.pricing_model = product_data.pricing_model
    
    # Extract content if requested
    if product_data.extract_content and product_data.website_url:
        try:
            extraction_result = await extract_content_from_url(str(product_data.website_url))
            
            if not extraction_result.get("error"):
                product.extracted_content = extraction_result.get("content", "")
                
                # Extract features if available in metadata
                if "features" in extraction_result.get("metadata", {}):
                    product.extracted_features = extraction_result["metadata"]["features"]
            else:
                log_error(f"Content extraction failed: {extraction_result.get('error')}")
        except Exception as e:
            log_error(f"Error during content extraction: {str(e)}")
    
    # Update the database
    db.commit()
    db.refresh(product)
    
    log_info(f"Product updated: {product.name} by user {current_user.username}")
    
    # Calculate additional properties
    setattr(product, 'average_rating', product.average_rating)
    setattr(product, 'evaluation_count', product.evaluation_count)
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user is the creator or an admin
    if product.created_by_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can delete this product"
        )
    
    # Delete the product
    db.delete(product)
    db.commit()
    
    log_info(f"Product deleted: {product.name} by user {current_user.username}")
    
    return None


@router.post("/products/extract-content", response_model=ExtractContentResponse)
async def extract_content(
    url: HttpUrl = Query(..., description="URL to extract content from"),
    current_user: User = Depends(get_current_active_user)
):
    """Extract content from a URL."""
    try:
        result = await extract_content_from_url(str(url))
        
        return {
            "content": result.get("content", ""),
            "metadata": result.get("metadata", {}),
            "error": result.get("error")
        }
    except Exception as e:
        log_error(f"Content extraction error: {str(e)}")
        return {
            "content": "",
            "metadata": {},
            "error": str(e)
        }


@router.get("/products/categories/list", response_model=List[str])
async def get_product_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a list of all product categories."""
    categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
    return [category[0] for category in categories]


@router.get("/products/vendors/list", response_model=List[str])
async def get_product_vendors(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a list of all product vendors."""
    vendors = db.query(Product.vendor).distinct().filter(Product.vendor.isnot(None)).all()
    return [vendor[0] for vendor in vendors]