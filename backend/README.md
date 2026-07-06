# KrishiSathi-VikasBeejBhandar Backend

Agricultural E-commerce Platform Backend API built with FastAPI.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration from .env
│   │   └── security.py        # Password hashing & JWT
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py              # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── product.py         # Product model
│   │   └── order.py           # Order model (optional)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py            # User Pydantic schemas
│   │   └── product.py         # Product Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── products.py        # Product endpoints
│   │   └── orders.py          # Order endpoints
│   └── services/
│       └── __init__.py
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Example environment file
└── requirements.txt           # Python dependencies
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- PostgreSQL database
- pip (Python package manager)

### 2. Clone and Navigate
```bash
cd /path/to/KRISHI_SATHI-VikasBeejBhandar/backend
```

### 3. Create Virtual Environment
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
```bash
# Copy example to actual .env file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

Example `.`.env` values:
```
DATABASE_URL=postgresql://user:password@localhost:5432/krishi_sathi_db
SECRET_KEY=your-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 6. Create Database (if using PostgreSQL)
```bash
# Using psql or your preferred PostgreSQL client
createdb krishi_sathi_db
```

## How to Run

### From the Backend Directory
```bash
# Make sure you're in: /path/to/KRISHI_SATHI-VikasBeejBhandar/backend
# And your virtual environment is activated

# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### Access Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Products
- `GET /api/products/` - Get all products
- `GET /api/products/{product_id}` - Get product by ID
- `POST /api/products/` - Create product
- `PUT /api/products/{product_id}` - Update product
- `DELETE /api/products/{product_id}` - Delete product

### Orders
- `GET /api/orders/` - Get all orders
- `GET /api/orders/{order_id}` - Get order by ID
- `POST /api/orders/` - Create order
- `PUT /api/orders/{order_id}` - Update order
- `DELETE /api/orders/{order_id}` - Delete order

## Running from Different Locations

**Correct way (from backend directory):**
```bash
cd /home/priyanshu/Desktop/study/GithubProject/KRISHI_SATHI-VikasBeejBhandar/backend
uvicorn app.main:app --reload
```

**Alternative (from project root):**
```bash
cd /home/priyanshu/Desktop/study/GithubProject/KRISHI_SATHI-VikasBeejBhandar
uvicorn backend.app.main:app --reload
```

## Important Notes

1. **Always run from the backend directory** - The import structure expects to be run from there
2. **Virtual environment must be activated** - Required before running `pip install` or `uvicorn`
3. **`.env` file is required** - Copy `.env.example` and update with your values
4. **Database must exist** - Create PostgreSQL database before running
5. **`--reload` flag** - Only use in development; remove in production

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
- Make sure you're in the `backend` directory
- Ensure virtual environment is activated

### "DATABASE_URL not found"
- Create `.env` file from `.env.example`
- Check that DATABASE_URL is set correctly

### "psycopg2 errors"
- Install PostgreSQL dev files (Linux): `sudo apt-get install libpq-dev`
- Ensure PostgreSQL is running

## Development Notes

- Models are in `app/models/`
- Schemas (Pydantic) are in `app/schemas/`
- API routes are in `app/routers/`
- Database config is in `app/database/db.py`
- Security utilities are in `app/core/security.py`
