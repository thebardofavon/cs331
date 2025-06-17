"""FastAPI backend for user-related functionality"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi.responses import JSONResponse  # Import JSONResponse
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt as jose_jwt  # Rename to avoid conflict with stdlib jwt
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Float,
    Boolean,
    TEXT,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from dotenv import load_dotenv
import logging
from sqladmin import Admin, ModelView

load_dotenv()

DATABASE_URL = os.getenv("SQLITE_DB_PATH", "sqlite:///./user.db")
SECRET_KEY = os.getenv("SECRET", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
PORT = 3001

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine_args = (
    {"connect_args": {"check_same_thread": False}}
    if DATABASE_URL.startswith("sqlite")
    else {}
)
engine = create_engine(
    DATABASE_URL, echo=False, **engine_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Models (SQLAlchemy) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    orders = relationship("Order", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user")
    save_for_later_items = relationship("SaveForLaterItem", back_populates="user")
    addresses = relationship(
        "UserAddress", back_populates="user", cascade="all, delete-orphan"
    )

    # Add constraints for username length if DB supports it, otherwise validate in Pydantic/API
    # __table_args__ = (CheckConstraint('length(username) >= 3'), {}) - May vary by DB


class Administrator(Base):
    __tablename__ = "administrators"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    security_question = Column(String(255), nullable=False)
    security_answer_hash = Column(String(255), nullable=False)
    # Add constraints if needed


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    orderNumber = Column(String(255), unique=True, nullable=False)
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, processing, shipped, delivered, cancelled
    paymentMethod = Column(String(50), nullable=False)
    paymentStatus = Column(
        String(50), default="pending"
    )  # pending, paid, failed, refunded
    paymentDetails = Column(JSON, nullable=True)
    subtotal = Column(Float, nullable=False)
    shippingCost = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    shippingInfo = Column(JSON, nullable=False)  # Store address snapshot or address ID
    expectedDeliveryDate = Column(DateTime, nullable=True)
    deliveredAt = Column(DateTime, nullable=True)
    cancelledDate = Column(DateTime, nullable=True)
    cancellationReason = Column(String(255), nullable=True)
    razorpayOrderId = Column(String(255), nullable=True)  # Example payment gateway ID
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    productId = Column(
        Integer, nullable=False
    )  # Assuming product IDs are integers from another service/DB
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price per item at the time of order
    size = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)

    order = relationship("Order", back_populates="items")
    # Add constraints (e.g., quantity > 0) if needed


class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    productId = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Float, nullable=True)  # Price might be fetched dynamically or stored
    size = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="cart_items")
    __table_args__ = (
        UniqueConstraint(
            "user_id", "productId", "size", "color", name="_user_product_variant_uc"
        ),
    )


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    productId = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="wishlist_items")
    __table_args__ = (
        UniqueConstraint("user_id", "productId", name="_user_product_wishlist_uc"),
    )


class SaveForLaterItem(Base):
    __tablename__ = "save_for_later_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    productId = Column(Integer, nullable=False)
    size = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="save_for_later_items")
    __table_args__ = (
        UniqueConstraint(
            "user_id", "productId", "size", "color", name="_user_product_sfl_variant_uc"
        ),
    )


class UserAddress(Base):
    __tablename__ = "user_addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fullName = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    pincode = Column(String(10), nullable=False)
    address = Column(TEXT, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    addressType = Column(String(50), default="home")  # home, work, other
    isDefault = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="addresses")


# --- Create Database Tables ---
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---


# Base Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=3)


class UserUpdate(UserBase):
    new_username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=3)


class UserPublic(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class AdminCreate(AdminBase):
    password: str = Field(..., min_length=3)
    security_question: str = Field(..., min_length=10, max_length=255)
    security_answer: str = Field(..., min_length=3)


class AdminUpdate(BaseModel):
    new_username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=3)
    security_question: Optional[str] = Field(None, min_length=10, max_length=255)
    security_answer: Optional[str] = Field(None, min_length=3)


class AdminPublic(AdminBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=3)


class UserLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    # Add scopes if needed: scopes: List[str] = []


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    email: EmailStr
    type: str  # "standard_user" or "administrator"


class CartItemBase(BaseModel):
    productId: int
    quantity: int = Field(..., gt=0)
    size: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)


class CartItemAdd(CartItemBase):
    price: Optional[float] = None  # Price might be added server-side


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemResponse(CartItemBase):
    id: int
    price: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]


class WishlistItemBase(BaseModel):
    productId: int


class WishlistItemCreate(WishlistItemBase):
    pass


class WishlistItemResponse(WishlistItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WishlistResponse(BaseModel):
    items: List[WishlistItemResponse]


class OrderItemBase(BaseModel):
    productId: int
    quantity: int = Field(..., gt=0)
    price: float  # Price must be provided when creating order item
    size: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)


class OrderItemResponse(OrderItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AddressBase(BaseModel):
    fullName: str = Field(..., max_length=255)
    phone: str = Field(
        ..., max_length=20
    )  # Consider more specific validation if needed
    pincode: str = Field(..., max_length=10)
    address: str = Field(..., max_length=1000)  # TEXT field
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    addressType: Optional[str] = Field("home", pattern="^(home|work|other)$")
    isDefault: Optional[bool] = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(AddressBase):
    # Allow all fields to be optional on update
    fullName: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    pincode: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    addressType: Optional[str] = Field(None, pattern="^(home|work|other)$")
    isDefault: Optional[bool] = None


class AddressResponse(AddressBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AddressListResponse(BaseModel):
    addresses: List[AddressResponse]


class OrderCreate(BaseModel):
    items: List[OrderItemBase]
    shippingInfo: AddressBase  # Store the full address snapshot with the order
    paymentMethod: str = Field(..., pattern="^(cod|online)$")  # Example methods
    subtotal: float = Field(..., gt=0)
    shippingCost: float = Field(..., ge=0)
    tax: float = Field(..., ge=0)
    total: float = Field(..., gt=0)


class OrderResponse(BaseModel):
    id: int
    orderNumber: str
    status: str
    paymentMethod: str
    paymentStatus: str
    paymentDetails: Optional[Dict[str, Any]] = None
    subtotal: float
    shippingCost: float
    tax: float
    total: float
    shippingInfo: Dict[str, Any]  # Return as dict
    expectedDeliveryDate: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    cancelledDate: Optional[datetime] = None
    cancellationReason: Optional[str] = None
    razorpayOrderId: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse]
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]


class PaymentCreateRequest(BaseModel):
    amount: float = Field(..., gt=0)


class PaymentCreateResponse(BaseModel):
    success: bool
    order_id: str  # Razorpay Order ID (or mock)
    amount: float
    currency: str
    key_id: str  # Razorpay Key ID (or mock)


class PaymentVerifyRequest(BaseModel):
    orderId: int  # Our internal Order ID
    paymentId: str  # Razorpay Payment ID
    signature: Optional[str] = None  # Razorpay signature (optional for mock)


class PaymentVerifyResponse(BaseModel):
    success: bool
    message: str


class PaymentStatusResponse(BaseModel):
    paymentStatus: str
    paymentDetails: Optional[Dict[str, Any]] = None


# --- FastAPI App Instance ---
app = FastAPI(title="User Management API Port", version="1.0.0")

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email]
    can_create = True
    can_edit = True
    can_delete = True


class AdministratorAdmin(ModelView, model=Administrator):
    column_list = [
        Administrator.id,
        Administrator.username,
        Administrator.email,
        Administrator.security_question,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.orderNumber,
        Order.status,
        Order.paymentStatus,
        Order.total,
        Order.created_at,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.productId,
        OrderItem.quantity,
        OrderItem.price,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class CartAdmin(ModelView, model=Cart):
    column_list = [
        Cart.id,
        Cart.user_id,
        Cart.productId,
        Cart.quantity,
        Cart.price,
        Cart.created_at,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class WishlistItemAdmin(ModelView, model=WishlistItem):
    column_list = [
        WishlistItem.id,
        WishlistItem.user_id,
        WishlistItem.productId,
        WishlistItem.created_at,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class SaveForLaterItemAdmin(ModelView, model=SaveForLaterItem):
    column_list = [
        SaveForLaterItem.id,
        SaveForLaterItem.user_id,
        SaveForLaterItem.productId,
        SaveForLaterItem.created_at,
    ]
    can_create = True
    can_edit = True
    can_delete = True


class UserAddressAdmin(ModelView, model=UserAddress):
    column_list = [
        UserAddress.id,
        UserAddress.user_id,
        UserAddress.fullName,
        UserAddress.city,
        UserAddress.state,
        UserAddress.isDefault,
    ]
    can_create = True
    can_edit = True
    can_delete = True


# Register all admin views
admin.add_view(UserAdmin)
admin.add_view(AdministratorAdmin)
# admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)
admin.add_view(CartAdmin)
admin.add_view(WishlistItemAdmin)
admin.add_view(SaveForLaterItemAdmin)
admin.add_view(UserAddressAdmin)


# --- Dependency Functions ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login/user"
)  # Or a generic /api/login if preferred


async def get_current_user_or_admin(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Union[User, Administrator]:
    print(token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        username: str = payload.get("username")  # Assuming 'sub' holds the username
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user:
        return user

    admin = (
        db.query(Administrator)
        .filter(Administrator.username == token_data.username)
        .first()
    )
    if admin:
        return admin

    raise credentials_exception


async def get_current_user(
    current_user_or_admin: Union[User, Administrator] = Depends(
        get_current_user_or_admin
    ),
) -> User:
    if isinstance(current_user_or_admin, User):
        return current_user_or_admin
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: User rights required",
    )


async def get_current_admin(
    current_user_or_admin: Union[User, Administrator] = Depends(
        get_current_user_or_admin
    ),
) -> Administrator:
    if isinstance(current_user_or_admin, Administrator):
        return current_user_or_admin
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Administrator rights required",
    )


# --- Utility Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Request Logger Middleware (Example) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Method: {request.method}")
    logger.info(f"Path:   {request.url.path}")
    # Be cautious logging body in production due to sensitive data
    # body = await request.body()
    # logger.info(f"Body:   {body.decode()}")
    response = await call_next(request)
    logger.info("---")
    return response


# --- Error Handling ---
# FastAPI handles Pydantic validation errors (422) automatically.
# Add custom handlers if needed.
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"IntegrityError: {exc}")
    # Check for unique constraint violations
    # The exact error message string might vary based on DB and driver
    err_str = str(exc.orig).lower()
    if "unique constraint failed" in err_str or "duplicate entry" in err_str:
        # Try to parse which field caused the error (more complex)
        field = "resource"
        if "users.username" in err_str or "administrators.username" in err_str:
            field = "username"
        elif "users.email" in err_str or "administrators.email" in err_str:
            field = "email"
        # Add more specific checks based on your unique constraints
        elif "_user_product_variant_uc" in err_str:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This product variant is already in the cart.",
            )
        elif "_user_product_wishlist_uc" in err_str:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This product is already in the wishlist.",
            )
        elif "_user_product_sfl_variant_uc" in err_str:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This product variant is already saved for later.",
            )

        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {field} with that value already exists",
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database integrity error",
    )


# --- API Routes ---

# --- Signup Route (Open registration) ---
@app.post("/api/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def signup_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Username already exists"},
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Email already exists"},
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip(),
        password_hash=hashed_password,
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create access token for immediate login after signup
        access_token = create_access_token(
            data={
                "username": db_user.username,
                "email": db_user.email,
            }
        )
        
        return {
            "message": "User created successfully",
            "token": access_token,
            "username": db_user.username,
            "email": db_user.email,
            "type": "standard_user"
        }
        
    except IntegrityError as e:
        db.rollback()
        # Handle race condition where user was created between our checks
        logger.error(f"IntegrityError during signup: {e}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "User with that username or email already exists"},
        )

# --- User Routes ---
@app.get("/api/users", response_model=List[UserPublic], tags=["Users"])
def read_users(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    users = db.query(User).all()
    return users


@app.post("/api/users", status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip(),
        password_hash=hashed_password,
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Let the exception handler deal with the specifics
        raise e
    # No response body needed for 201 on this endpoint as per original API
    return None


@app.post(
    "/api/users/changepassword", status_code=status.HTTP_200_OK, tags=["Users", "Admin"]
)
def change_user_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user_or_admin: Union[User, Administrator] = Depends(
        get_current_user_or_admin
    ),
):
    user_or_admin = current_user_or_admin  # Can be User or Administrator object

    if not verify_password(password_data.current_password, user_or_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password"
        )

    new_hashed_password = get_password_hash(password_data.new_password.strip())
    user_or_admin.password_hash = new_hashed_password
    db.add(user_or_admin)
    db.commit()
    return None


@app.put("/api/users/{username}", status_code=status.HTTP_200_OK, tags=["Users"])
def update_user(
    username: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    update_data = user_in.model_dump(
        exclude_unset=True
    )  # Use model_dump in Pydantic v2+
    needs_commit = False

    if "new_username" in update_data and update_data["new_username"] != username:
        new_username = update_data["new_username"].strip()
        if len(new_username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_username must be at least 3 characters long",
            )
        existing_user = db.query(User).filter(User.username == new_username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with the username {new_username} already exists",
            )
        db_user.username = new_username
        needs_commit = True

    if "email" in update_data and update_data["email"] != db_user.email:
        new_email = update_data["email"].strip()
        # Pydantic already validates email format
        existing_email = db.query(User).filter(User.email == new_email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with that email already exists",
            )
        db_user.email = new_email
        needs_commit = True

    if "password" in update_data:
        new_password = update_data["password"].strip()
        if len(new_password) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="password must be at least 3 characters long",
            )
        db_user.password_hash = get_password_hash(new_password)
        needs_commit = True

    # Ensure we only update if necessary, handle non-provided fields gracefully
    # The Pydantic model ensures fields not explicitly included aren't in update_data
    # Re-fetch excluded fields if needed or handle directly as above

    if needs_commit:
        try:
            db.add(db_user)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise e  # Let handler manage
    return None


@app.delete(
    "/api/users/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"]
)
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    # Return 204 even if user not found, as per idempotent delete pattern
    return None


# --- Admin Routes ---
@app.get("/api/admin", response_model=List[AdminPublic], tags=["Admin"])
def read_admins(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    admins = db.query(Administrator).all()
    return admins


@app.post("/api/admin", status_code=status.HTTP_201_CREATED, tags=["Admin"])
def create_admin(admin_in: AdminCreate, db: Session = Depends(get_db)):
    # Potentially restrict admin creation (e.g., only first admin, or only by existing admins)
    # Here, allowing any call for simplicity, matching Node.js behavior
    hashed_password = get_password_hash(admin_in.password.strip())
    hashed_answer = get_password_hash(admin_in.security_answer.strip())

    db_admin = Administrator(
        username=admin_in.username.strip(),
        email=admin_in.email.strip(),
        password_hash=hashed_password,
        security_question=admin_in.security_question.strip(),
        security_answer_hash=hashed_answer,
    )
    db.add(db_admin)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise e
    return None


@app.post("/api/admin/changepassword", status_code=status.HTTP_200_OK, tags=["Admin"])
def change_admin_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    # Re-use the user/admin password change logic by calling the other endpoint's core
    # Or duplicate logic here for clarity if preferred
    if not verify_password(password_data.current_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current_password"
        )

    new_hashed_password = get_password_hash(password_data.new_password.strip())
    current_admin.password_hash = new_hashed_password
    db.add(current_admin)
    db.commit()
    return None


@app.put("/api/admin/{username}", status_code=status.HTTP_200_OK, tags=["Admin"])
def update_admin(
    username: str,
    admin_in: AdminUpdate,
    db: Session = Depends(get_db),
    current_admin_acting: Administrator = Depends(
        get_current_admin
    ),  # The admin performing the action
):
    # Allow admins to update other admins (or restrict to self-update if needed)
    db_admin_to_update = (
        db.query(Administrator).filter(Administrator.username == username).first()
    )
    if not db_admin_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Administrator not found"
        )

    update_data = admin_in.model_dump(exclude_unset=True)
    needs_commit = False

    if "new_username" in update_data and update_data["new_username"] != username:
        new_username = update_data["new_username"].strip()
        if len(new_username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_username must be at least 3 characters long",
            )
        existing_admin = (
            db.query(Administrator)
            .filter(Administrator.username == new_username)
            .first()
        )
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username {new_username} already exists",
            )
        db_admin_to_update.username = new_username
        needs_commit = True

    if "email" in update_data and update_data["email"] != db_admin_to_update.email:
        new_email = update_data["email"].strip()
        existing_email = (
            db.query(Administrator).filter(Administrator.email == new_email).first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An administrator with that email already exists",
            )
        db_admin_to_update.email = new_email
        needs_commit = True

    if "password" in update_data:
        new_password = update_data["password"].strip()
        if len(new_password) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="password must be at least 3 characters long",
            )
        db_admin_to_update.password_hash = get_password_hash(new_password)
        needs_commit = True

    if "security_question" in update_data:
        new_question = update_data["security_question"].strip()
        if len(new_question) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="security_question must be at least 10 characters long",
            )
        db_admin_to_update.security_question = new_question
        needs_commit = True

    if "security_answer" in update_data:
        new_answer = update_data["security_answer"].strip()
        if len(new_answer) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="security_answer must be at least 3 characters long",
            )
        db_admin_to_update.security_answer_hash = get_password_hash(new_answer)
        needs_commit = True

    if needs_commit:
        try:
            db.add(db_admin_to_update)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise e
    return None


@app.delete(
    "/api/admin/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin"]
)
def delete_admin(
    username: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    # Prevent admin from deleting themselves? Optional rule.
    # if current_admin.username == username:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    db_admin = (
        db.query(Administrator).filter(Administrator.username == username).first()
    )
    if db_admin:
        db.delete(db_admin)
        db.commit()
    return None


# --- Auth Routes ---
@app.post("/api/login/user", response_model=LoginResponse, tags=["Auth"])
def login_user(
    login_data: UserLoginRequest, db: Session = Depends(get_db)
):  # Change dependency to expect JSON via Pydantic model
    # 1. Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()

    # 2. Check if user exists - return specific error if not
    if not user:
        # Use JSONResponse to exactly match the Express error structure and message
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid username"},
        )

    # 3. Verify password - return specific error if incorrect
    password_correct = verify_password(login_data.password, user.password_hash)
    if not password_correct:
        # Use JSONResponse to exactly match the Express error structure and message
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid password"},
        )

    # 4. Create token with the original payload structure
    access_token = create_access_token(
        data={
            "username": user.username,
            "email": user.email,
        }  # Use 'username' key like in Express
        # expires_delta can be added here if needed, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # 5. Return the success response (FastAPI handles serialization via response_model)
    return LoginResponse(
        token=access_token,
        username=user.username,
        email=user.email,
        type="standard_user",
    )


@app.post("/api/login/admin", response_model=LoginResponse, tags=["Auth"])
def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # NOTE: This endpoint still uses form data. Modify like login_user if it should accept JSON
    # and match exact error messages/structure from the original Node version.
    admin = (
        db.query(Administrator)
        .filter(Administrator.username == form_data.username)
        .first()
    )
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(  # This still uses the generic error and detail structure
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # This still uses 'sub' in the token payload. Change if needed.
    access_token = create_access_token(
        data={"sub": admin.username, "email": admin.email}
    )

    return LoginResponse(
        token=access_token,
        username=admin.username,
        email=admin.email,
        type="administrator",
    )


# --- Cart Routes ---
@app.get("/api/cart", response_model=CartResponse, tags=["Cart"])
def get_cart(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    return CartResponse(items=cart_items)


@app.post("/api/cart/add", response_model=CartResponse, tags=["Cart"])
def add_to_cart(
    item_in: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if item already exists with the same variant (product, size, color)
    existing_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == current_user.id,
            Cart.productId == item_in.productId,
            Cart.size == item_in.size,
            Cart.color == item_in.color,
        )
        .first()
    )

    if existing_item:
        existing_item.quantity += item_in.quantity
        # Optionally update price if provided
        if item_in.price is not None:
            existing_item.price = item_in.price
        db.add(existing_item)
    else:
        # Here you might want to fetch the product price from another service/DB
        # For now, using the provided price or null
        new_item = Cart(
            user_id=current_user.id,
            productId=item_in.productId,
            quantity=item_in.quantity,
            price=item_in.price,  # Store price if provided
            size=item_in.size,
            color=item_in.color,
        )
        db.add(new_item)

    try:
        db.commit()
    except (
        IntegrityError
    ) as e:  # Should ideally not happen if logic above is correct, but good practice
        db.rollback()
        raise e

    # Return the updated cart
    updated_cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    return CartResponse(items=updated_cart_items)


@app.put("/api/cart/item/{item_id}", response_model=CartResponse, tags=["Cart"])
def update_cart_item(
    item_id: int,
    item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_item = (
        db.query(Cart)
        .filter(Cart.id == item_id, Cart.user_id == current_user.id)
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found"
        )

    cart_item.quantity = item_update.quantity
    db.add(cart_item)
    db.commit()

    # Return updated cart
    updated_cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    return CartResponse(items=updated_cart_items)


@app.delete(
    "/api/cart/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Cart"]
)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_item = (
        db.query(Cart)
        .filter(Cart.id == item_id, Cart.user_id == current_user.id)
        .first()
    )
    if cart_item:
        db.delete(cart_item)
        db.commit()
    return None


@app.delete("/api/cart", status_code=status.HTTP_204_NO_CONTENT, tags=["Cart"])
def clear_cart(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    deleted_count = db.query(Cart).filter(Cart.user_id == current_user.id).delete()
    db.commit()
    logger.info(f"Cleared {deleted_count} items from cart for user {current_user.id}")
    return None


# --- Wishlist Routes ---
@app.get("/api/wishlist", response_model=WishlistResponse, tags=["Wishlist"])
def get_wishlist(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    wishlist_items = (
        db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    )
    return WishlistResponse(items=wishlist_items)


@app.post("/api/wishlist/add", status_code=status.HTTP_201_CREATED, tags=["Wishlist"])
def add_to_wishlist(
    item_in: WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if item already exists
    existing_item = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.productId == item_in.productId,
        )
        .first()
    )

    if not existing_item:
        new_item = WishlistItem(user_id=current_user.id, productId=item_in.productId)
        db.add(new_item)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            # It means item was added concurrently, which is fine.
            logger.warning(
                f"Wishlist item {item_in.productId} already exists for user {current_user.id}, likely due to concurrent request."
            )
            # Optionally raise 409, but 201 implies success/state achieved
            # raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item already in wishlist")
    # Original API returns 201 with a simple message body, FastAPI prefers structured responses or status only
    return {"message": "Item added to wishlist"}  # Or return None if 201 is sufficient


@app.delete(
    "/api/wishlist/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Wishlist"],
)
def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.productId == product_id,
            WishlistItem.user_id == current_user.id,
        )
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return None


# --- Orders Routes ---
@app.get("/api/orders", response_model=OrderListResponse, tags=["Orders"])
def get_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    # Convert shippingInfo from AddressBase Pydantic model to dict for response
    for order in orders:
        if isinstance(order.shippingInfo, AddressBase):
            order.shippingInfo = order.shippingInfo.model_dump()
        elif not isinstance(
            order.shippingInfo, dict
        ):  # Ensure it's a dict if loaded from JSON
            order.shippingInfo = {}  # Or handle error appropriately

    return OrderListResponse(orders=orders)


@app.get("/api/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Convert shippingInfo if needed
    if isinstance(order.shippingInfo, AddressBase):
        order.shippingInfo = order.shippingInfo.model_dump()
    elif not isinstance(order.shippingInfo, dict):
        order.shippingInfo = {}

    return order


@app.post("/api/orders", status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Generate order number
    order_number = f"ORD{int(datetime.now(timezone.utc).timestamp() * 1000)}{current_user.id % 1000}"

    # Calculate expected delivery date (e.g., 7 days from now)
    expected_delivery = datetime.now(timezone.utc) + timedelta(days=7)

    # Store shipping address as JSON/dict snapshot
    shipping_info_dict = order_in.shippingInfo.model_dump()

    try:
        # Start transaction
        with db.begin_nested():  # Use nested transaction if within a larger one, or db.begin()
            # Create order
            new_order = Order(
                user_id=current_user.id,
                orderNumber=order_number,
                status="pending",
                paymentMethod=order_in.paymentMethod,
                paymentStatus="pending",  # Assume pending initially, update on payment success/COD confirmation
                subtotal=order_in.subtotal,
                shippingCost=order_in.shippingCost,
                tax=order_in.tax,
                total=order_in.total,
                shippingInfo=shipping_info_dict,
                expectedDeliveryDate=expected_delivery,
            )
            db.add(new_order)
            db.flush()  # Flush to get the new_order.id

            # Create order items
            order_items = []
            for item_data in order_in.items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    productId=item_data.productId,
                    quantity=item_data.quantity,
                    price=item_data.price,
                    size=item_data.size,
                    color=item_data.color,
                )
                order_items.append(order_item)
            db.add_all(order_items)

            # Clear the cart (important: do this within the transaction)
            db.query(Cart).filter(Cart.user_id == current_user.id).delete()

        db.commit()  # Commit the transaction
        db.refresh(new_order)  # Refresh to load relationships if needed immediately
        # Eager load items for the response
        db.refresh(new_order, attribute_names=["items"])

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )

    # Convert shippingInfo back to dict for response consistency
    new_order.shippingInfo = shipping_info_dict

    return {  # Custom response structure matching Node version
        "success": True,
        "message": "Order created successfully",
        "order": OrderResponse.model_validate(
            new_order
        ),  # Use model_validate in Pydantic v2
    }


@app.get(
    "/api/orders/{order_id}/payment",
    response_model=PaymentStatusResponse,
    tags=["Orders", "Payment"],
)
def get_order_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return PaymentStatusResponse(
        paymentStatus=order.paymentStatus, paymentDetails=order.paymentDetails
    )


# --- Addresses Routes ---
@app.get(
    "/api/user/addresses", response_model=AddressListResponse, tags=["User Profile"]
)
def get_user_addresses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    addresses = (
        db.query(UserAddress)
        .filter(UserAddress.user_id == current_user.id)
        .order_by(UserAddress.isDefault.desc(), UserAddress.created_at.desc())
        .all()
    )
    return AddressListResponse(addresses=addresses)


@app.post(
    "/api/user/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["User Profile"],
)
async def add_user_address(
    address_in: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # If setting as default, unset other defaults first within a transaction
        if address_in.isDefault:
            db.query(UserAddress).filter(
                UserAddress.user_id == current_user.id, UserAddress.isDefault == True
            ).update({"isDefault": False})

        new_address = UserAddress(**address_in.model_dump(), user_id=current_user.id)
        db.add(new_address)

        # Check if this is the only address, make it default if so
        address_count = (
            db.query(UserAddress).filter(UserAddress.user_id == current_user.id).count()
        )
        if address_count == 0:  # Count is before commit, so 0 means this is the first
            new_address.isDefault = True

        db.commit()
        db.refresh(new_address)
        return new_address
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create address",
        )


@app.put(
    "/api/user/addresses/{address_id}",
    response_model=AddressResponse,
    tags=["User Profile"],
)
async def update_user_address(
    address_id: int,
    address_in: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_address = (
        db.query(UserAddress)
        .filter(UserAddress.id == address_id, UserAddress.user_id == current_user.id)
        .first()
    )
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    update_data = address_in.model_dump(exclude_unset=True)

    try:
        # Handle default address logic within transaction
        if update_data.get("isDefault") is True and not db_address.isDefault:
            # Unset other default addresses for this user
            db.query(UserAddress).filter(
                UserAddress.user_id == current_user.id,
                UserAddress.isDefault == True,
                UserAddress.id != address_id,  # Don't unset the one we're about to set
            ).update({"isDefault": False})

        # Apply updates
        for key, value in update_data.items():
            setattr(db_address, key, value)

        db.add(db_address)  # Add to session to track changes
        db.commit()
        db.refresh(db_address)
        return db_address
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address",
        )


@app.delete(
    "/api/user/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["User Profile"],
)
async def delete_user_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_address = (
        db.query(UserAddress)
        .filter(UserAddress.id == address_id, UserAddress.user_id == current_user.id)
        .first()
    )
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    if db_address.isDefault:
        # Check if there are other addresses
        other_addresses_count = (
            db.query(UserAddress)
            .filter(
                UserAddress.user_id == current_user.id, UserAddress.id != address_id
            )
            .count()
        )
        if other_addresses_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default address. Set another address as default first.",
            )
        # If it's the *only* address, allow deletion (or disallow based on rules)
        # logger.info("Deleting the only address which was default.")

    db.delete(db_address)
    db.commit()
    return None


@app.put(
    "/api/user/addresses/{address_id}/default",
    status_code=status.HTTP_200_OK,
    tags=["User Profile"],
)
async def set_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_address = (
        db.query(UserAddress)
        .filter(UserAddress.id == address_id, UserAddress.user_id == current_user.id)
        .first()
    )
    if not db_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    if db_address.isDefault:
        return {"message": "Address is already the default"}  # No change needed

    try:
        # Start transaction
        with db.begin_nested():
            # Unset current default
            db.query(UserAddress).filter(
                UserAddress.user_id == current_user.id, UserAddress.isDefault == True
            ).update({"isDefault": False})

            # Set new default
            db_address.isDefault = True
            db.add(db_address)

        db.commit()
        return {"message": "Default address updated"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting default address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update default address",
        )


# --- Payment Routes (Mock Implementation) ---
@app.post("/api/payment/create", response_model=PaymentCreateResponse, tags=["Payment"])
async def create_payment_order(
    payment_req: PaymentCreateRequest, current_user: User = Depends(get_current_user)
):
    # Mock Razorpay order creation
    # In a real scenario, interact with Razorpay SDK here
    mock_razorpay_order_id = (
        f"order_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    )
    mock_key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_your_key_id")  # Use test key

    # Optionally, link this mock_razorpay_order_id to an internal order
    # For example, if creating payment for a specific existing order:
    # order = db.query(Order).filter(Order.id == payment_req.orderId, Order.user_id == current_user.id).first()
    # if not order: raise HTTPException(404, "Order not found")
    # order.razorpayOrderId = mock_razorpay_order_id
    # db.commit()

    return PaymentCreateResponse(
        success=True,
        order_id=mock_razorpay_order_id,
        amount=payment_req.amount,
        currency="INR",
        key_id=mock_key_id,
    )


@app.post("/api/payment/verify", response_model=PaymentVerifyResponse, tags=["Payment"])
async def verify_payment(
    verify_req: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Mock payment verification
    # In a real scenario, verify the signature using Razorpay SDK and secret key

    order = (
        db.query(Order)
        .filter(Order.id == verify_req.orderId, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Mock success - Assume payment is verified if the request reaches here
    try:
        order.paymentStatus = "paid"
        order.paymentDetails = {
            "paymentId": verify_req.paymentId,
            "paidAt": datetime.now(timezone.utc).isoformat(),
            "method": "mock",  # Add signature if verifying for real
            "signature": verify_req.signature,  # Store signature if provided/verified
        }
        # If razorpayOrderId was stored on the order during creation, you might check it matches
        # if order.razorpayOrderId and order.razorpayOrderId != verify_req.razorpayOrderId: # If razorpayOrderId is part of req
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID mismatch")

        db.add(order)
        db.commit()
        return PaymentVerifyResponse(
            success=True, message="Payment verified successfully"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update order payment status: {e}")
        # Even if DB update fails, might return success to client if payment gateway confirmed? Depends on logic.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        )


@app.get("/")
async def root():
    return {"message": "Welcome to the User Management API"}


@app.get("/health")
async def health():
    return {"status": "ok!!!!"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on port {PORT}")
    uvicorn.run("main:app", host="localhost", port=PORT)
