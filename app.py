# mobile-backend/app.py
import os
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field, confloat, conint

app = FastAPI(
    title="Shopokoa Mobile API",
    description="E-commerce backend API for mobile applications built with FastAPI",
    version="2.0.0"
)

# ==================== MongoDB Connection (LAZY + GRACEFUL) ====================
# Get MongoDB URI from environment variable (set by ECS) or use fallback for local development
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://ezinne:documentdb12@"
    "docdb-2025-11-19-16-33-00.cluster-clcgs4eoscam.eu-west-1.docdb.amazonaws.com:27017"
    "/shopokoa?"
    "tls=true"
    "&tlsCAFile=global-bundle.pem"
    "&retryWrites=false"
    "&directConnection=true"
    "&tlsAllowInvalidCertificates=true"   # Critical for DocumentDB
)

# CORS Configuration - allow origins from environment variable or default to all for development
# For mobile apps, you may want to keep allow_origins=["*"] or specify your mobile app domains
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "*"  # Default to allow all for development
).split(",")

# Remove empty strings and handle wildcard
if "*" in allowed_origins:
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: Optional[MongoClient] = None
db = None
products_collection = None
orders_collection = None


def get_db_client() -> MongoClient:
    """Lazy-load the MongoDB client and test connection only once."""
    global client, db, products_collection, orders_collection
    if client is None:
        print("Creating MongoDB client...")
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCAFile="global-bundle.pem",           # Make sure this file is in project root
            tlsAllowInvalidCertificates=True,        # Required for DocumentDB
            retryWrites=False,
            directConnection=True,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        # Test connection (non-blocking for the app startup)
        try:
            client.admin.command("ping")
            print("Successfully connected to Amazon DocumentDB! 🚀")
        except Exception as e:
            print("⚠️ DocumentDB not reachable yet:", e)
            print("   Endpoints will fall back to dummy data where possible.")

        db = client.shopokoa
        products_collection = db.products
        orders_collection = db.orders

    return client


# Call it once at startup (won't crash the app)
get_db_client()


# ==================== Pydantic Models ====================
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: confloat(gt=0)
    category: str
    stock: conint(ge=0) = 0
    image: Optional[str] = None
    brand: Optional[str] = "Generic"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[confloat(gt=0)] = None
    category: Optional[str] = None
    stock: Optional[conint(ge=0)] = None
    image: Optional[str] = None


class ProductInDB(ProductBase):
    id: str = Field(..., alias="id")
    rating: float = 0.0
    reviews: int = 0
    createdAt: datetime
    updatedAt: datetime

    class Config:
        populate_by_name = True


class OrderItem(BaseModel):
    productId: str
    quantity: conint(gt=0)


class ShippingAddress(BaseModel):
    street: str
    city: str
    state: str
    zipCode: str
    country: str


class OrderCreate(BaseModel):
    items: List[OrderItem]
    total: confloat(gt=0)
    customerName: str = "Guest"
    customerEmail: Optional[str] = None
    shippingAddress: ShippingAddress


class OrderInDB(BaseModel):
    orderId: str
    items: List[OrderItem]
    total: float
    customerName: str
    customerEmail: Optional[str] = None
    shippingAddress: ShippingAddress
    status: str
    createdAt: datetime
    updatedAt: datetime


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|processing|shipped|delivered|cancelled)$")


# ==================== Dummy Data Fallback ====================
def get_dummy_products() -> List[Dict[str, Any]]:
    return [
        {
            "id": "1",
            "name": "Laptop Pro",
            "description": "High-performance laptop for professionals",
            "price": 1299.99,
            "category": "Electronics",
            "stock": 15,
            "image": "https://via.placeholder.com/300x300?text=Laptop",
            "rating": 4.8,
            "reviews": 127,
            "brand": "ProBook",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
        {
            "id": "2",
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse",
            "price": 29.99,
            "category": "Accessories",
            "stock": 50,
            "image": "https://via.placeholder.com/300x300?text=Mouse",
            "rating": 4.5,
            "reviews": 89,
            "brand": "LogiTech",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
        {
            "id": "3",
            "name": "USB-C Hub",
            "description": "7-in-1 USB-C hub adapter",
            "price": 49.99,
            "category": "Accessories",
            "stock": 30,
            "image": "https://via.placeholder.com/300x300?text=Hub",
            "rating": 4.6,
            "reviews": 201,
            "brand": "Anker",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        },
    ]


# ==================== Routes ====================
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "mobile-api", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/mobile/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "mobile-api", "timestamp": datetime.utcnow().isoformat()}

# ------------------- Products -------------------
@app.get("/api/mobile/products", response_model=List[ProductInDB], tags=["Products"])
async def get_products(category: Optional[str] = Query(None)):
    query = {"category": category} if category else {}
    try:
        products = list(products_collection.find(query, {"_id": 0}))
    except Exception as e:
        print("DB error, falling back to dummy products:", e)
        products = []

    if not products:
        products = get_dummy_products()

    # Serialize datetime fields
    for p in products:
        for field in ["createdAt", "updatedAt"]:
            if field in p and isinstance(p[field], datetime):
                p[field] = p[field].isoformat()

    return products


@app.get("/api/mobile/products/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    try:
        product = products_collection.find_one({"id": product_id}, {"_id": 0})
    except Exception:
        product = None

    if not product:
        # Fallback to dummy if ID matches
        dummy = next((p for p in get_dummy_products() if p["id"] == product_id), None)
        if dummy:
            return dummy
        raise HTTPException(status_code=404, detail="Product not found")

    for field in ["createdAt", "updatedAt"]:
        if isinstance(product.get(field), datetime):
            product[field] = product[field].isoformat()
    return product


@app.post("/api/mobile/products", status_code=status.HTTP_201_CREATED, response_model=ProductInDB, tags=["Products"])
async def create_product(product: ProductCreate):
    if not products_collection:
        raise HTTPException(status_code=503, detail="Database not available")

    product_id = secrets.token_hex(4)
    new_product = product.dict()
    new_product.update({
        "id": product_id,
        "rating": 0.0,
        "reviews": 0,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    })

    products_collection.insert_one(new_product)
    new_product["createdAt"] = new_product["createdAt"].isoformat()
    new_product["updatedAt"] = new_product["updatedAt"].isoformat()
    return new_product


@app.put("/api/mobile/products/{product_id}", response_model=ProductInDB, tags=["Products"])
async def update_product(product_id: str, product_update: ProductUpdate):
    update_data = product_update.dict(exclude_unset=True)
    if "updatedAt" not in update_data:
        update_data["updatedAt"] = datetime.utcnow()

    if not update_data.keys() - {"updatedAt"}:  # only updatedAt was set
        updated_product = products_collection.find_one({"id": product_id}, {"_id": 0})
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
    else:
        result = products_collection.update_one(
            {"id": product_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        updated_product = products_collection.find_one({"id": product_id}, {"_id": 0})

    # Serialize datetimes
    for field in ["createdAt", "updatedAt"]:
        if isinstance(updated_product.get(field), datetime):
            updated_product[field] = updated_product[field].isoformat()

    return updated_product


@app.delete("/api/mobile/products/{product_id}", tags=["Products"])
async def delete_product(product_id: str):
    result = products_collection.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


# ============= ORDERS ENDPOINTS =============

@app.post("/api/mobile/orders", status_code=status.HTTP_201_CREATED, response_model=OrderInDB, tags=["Orders"])
async def create_order(order: OrderCreate):
    # Validate stock
    for item in order.items:
        product = products_collection.find_one({"id": item.productId})
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.productId} not found"
            )
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product['name']}"
            )

    order_id = f"ORD{int(datetime.utcnow().timestamp())}"

    new_order = {
        "orderId": order_id,
        "items": [item.dict() for item in order.items],
        "total": order.total,
        "customerName": order.customerName,
        "customerEmail": order.customerEmail,
        "shippingAddress": order.shippingAddress.dict(),
        "status": "pending",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }

    orders_collection.insert_one(new_order)

    # Decrease stock
    for item in order.items:
        products_collection.update_one(
            {"id": item.productId},
            {
                "$inc": {"stock": -item.quantity},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )

    # Serialize for response
    new_order["createdAt"] = new_order["createdAt"].isoformat()
    new_order["updatedAt"] = new_order["updatedAt"].isoformat()

    return new_order


@app.get("/api/mobile/orders", response_model=List[OrderInDB], tags=["Orders"])
async def get_orders(limit: int = Query(10, le=100), status_filter: Optional[str] = Query(None, alias="status")):
    query = {"status": status_filter} if status_filter else {}
    orders = list(
        orders_collection.find(query, {"_id": 0})
        .sort("createdAt", -1)
        .limit(limit))

    # Serialize datetimes
    for o in orders:
        for field in ["createdAt", "updatedAt"]:
            if isinstance(o.get(field), datetime):
                o[field] = o[field].isoformat()

    return orders


@app.get("/api/mobile/orders/{order_id}", response_model=OrderInDB, tags=["Orders"])
async def get_order(order_id: str):
    order = orders_collection.find_one({"orderId": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    for field in ["createdAt", "updatedAt"]:
        if isinstance(order.get(field), datetime):
            order[field] = order[field].isoformat()

    return order


@app.patch("/api/mobile/orders/{order_id}/status", response_model=OrderInDB, tags=["Orders"])
async def update_order_status(order_id: str, payload: OrderStatusUpdate):
    result = orders_collection.update_one(
        {"orderId": order_id},
        {
            "$set": {
                "status": payload.status,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    updated_order = orders_collection.find_one({"orderId": order_id}, {"_id": 0})

    for field in ["createdAt", "updatedAt"]:
        if isinstance(updated_order.get(field), datetime):
            updated_order[field] = updated_order[field].isoformat()

    return updated_order


@app.get("/api/mobile/orders/stats", tags=["Orders"])
async def get_order_stats():
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "totalRevenue": {"$sum": "$total"}
            }
        }
    ]

    stats = list(orders_collection.aggregate(pipeline))
    total_orders = orders_collection.count_documents({})

    return {
        "stats": stats,
        "totalOrders": total_orders
    }


# Run with: uvicorn app:app --host 0.0.0.0 --port 5002 --reload (for dev)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5002))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
