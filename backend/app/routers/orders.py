from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
def get_user_orders(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get orders. Admins see all orders, other users only see their own."""
    if current_user.role == "admin":
        orders = db.query(Order).offset(skip).limit(limit).all()
    else:
        orders = db.query(Order).filter(
            Order.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order by ID. Admins can see any order, others only their own."""
    if current_user.role == "admin":
        order = db.query(Order).filter(Order.id == order_id).first()
    else:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == order.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check stock availability
    if product.stock < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {product.stock}"
        )
    
    # Calculate total price
    total_price = product.price * order.quantity
    
    # Create order
    db_order = Order(
        user_id=current_user.id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_price=total_price,
        status="pending"
    )
    
    # Reduce product stock
    product.stock -= order.quantity
    
    db.add(db_order)
    db.add(product)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an order. Admins can update any order. Regular users can only update their own pending orders and are restricted to status='cancelled'."""
    if current_user.role == "admin":
        db_order = db.query(Order).filter(Order.id == order_id).first()
    else:
        db_order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    product = db.query(Product).filter(Product.id == db_order.product_id).first()
    
    # Check authorization and restrictions for regular user
    if current_user.role != "admin":
        if db_order.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update pending orders"
            )
            
        if order_update.quantity is not None:
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            quantity_diff = order_update.quantity - db_order.quantity
            if quantity_diff > 0 and product.stock < quantity_diff:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Available: {product.stock}"
                )
            # Update stock and order details
            product.stock -= quantity_diff
            db_order.quantity = order_update.quantity
            db_order.total_price = product.price * order_update.quantity
            db.add(product)
            
        if order_update.status:
            if order_update.status != "cancelled":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Regular users can only update status to 'cancelled'"
                )
            # Cancel order and restore stock
            if product:
                product.stock += db_order.quantity
                db.add(product)
            db_order.status = "cancelled"
            
    else:
        # Admin updates
        if order_update.quantity is not None:
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            quantity_diff = order_update.quantity - db_order.quantity
            if quantity_diff > 0 and product.stock < quantity_diff:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Available: {product.stock}"
                )
            # Adjust stock for the quantity update if not currently cancelled
            if db_order.status != "cancelled":
                product.stock -= quantity_diff
                db.add(product)
            db_order.quantity = order_update.quantity
            db_order.total_price = product.price * order_update.quantity
            
        if order_update.status and order_update.status != db_order.status:
            if product:
                # If moving FROM a state with held stock TO cancelled
                if db_order.status in ["pending", "completed"] and order_update.status == "cancelled":
                    product.stock += db_order.quantity
                    db.add(product)
                # If moving FROM cancelled TO a state with held stock
                elif db_order.status == "cancelled" and order_update.status in ["pending", "completed"]:
                    if product.stock < db_order.quantity:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Insufficient stock to re-activate order. Available: {product.stock}"
                        )
                    product.stock -= db_order.quantity
                    db.add(product)
            db_order.status = order_update.status
            
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an order. Admins can delete any order. Users can only delete their own pending orders."""
    if current_user.role == "admin":
        db_order = db.query(Order).filter(Order.id == order_id).first()
    else:
        db_order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Regular users can only delete pending orders
    if current_user.role != "admin" and db_order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete pending orders"
        )
    
    # Restore product stock if deleting a non-cancelled order
    if db_order.status in ["pending", "completed"]:
        product = db.query(Product).filter(Product.id == db_order.product_id).first()
        if product:
            product.stock += db_order.quantity
            db.add(product)
    
    db.delete(db_order)
    db.commit()
    return {"message": "Order deleted successfully"}
