# Shopokoa Backend Mobile API

FastAPI-based REST API for the Shopokoa mobile application.

## Features
- Mobile-optimized product endpoints
- User authentication (dummy)
- Shopping cart management
- Featured products
- App version checking
- MongoDB/DocumentDB integration

## Local Development

1. Install dependencies:
```bash
   pip install -r requirements.txt
```

2. Set up environment variables:
```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection string
```

3. Run the application:
```bash
   uvicorn app:app --host 0.0.0.0 --port 5002 --reload
```

The API will be available at `http://localhost:5002`

## API Endpoints

- `GET /health` - Health check
- `GET /api/mobile/version` - App version check
- `POST /api/mobile/auth/login` - User login
- `GET /api/mobile/products` - List products (with optional category filter)
- `GET /api/mobile/featured` - Get featured products
- `POST /api/mobile/cart` - Add item to cart
- `GET /api/mobile/cart/<user_id>` - Get user's cart

## Docker Build
```bash
docker build -t shopokoa-backend-mobile .
docker run -p 5002:5002 -e MONGODB_URI="your-connection-string" shopokoa-backend-mobile
```

## Environment Variables

- `MONGODB_URI` - MongoDB/DocumentDB connection string
- `DB_NAME` - Database name (default: shopokoa)
- `PORT` - Application port (default: 5002)