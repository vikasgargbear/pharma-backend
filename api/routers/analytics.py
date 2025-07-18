"""
Analytics Router - Comprehensive business intelligence endpoints
Advanced analytics across all pharmaceutical operations
Real-time dashboards and reporting capabilities
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timedelta
from sqlalchemy import func
from collections import defaultdict

from ..database import get_db
from .. import models
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/analytics", tags=["analytics"])

# ================= DASHBOARD ANALYTICS =================

@router.get("/dashboard/overview")
@handle_database_error
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Get main dashboard overview with key metrics"""
    # Sales metrics
    total_orders = db.query(models.Order).count()
    total_revenue = db.query(func.sum(models.Order.total_amount)).scalar() or 0
    
    # Customer metrics
    total_customers = db.query(models.Customer).count()
    active_customers = db.query(models.Customer).filter(models.Customer.is_active == True).count()
    
    # Inventory metrics
    total_products = db.query(models.Product).count()
    low_stock_products = db.query(models.Product).filter(models.Product.stock_quantity <= models.Product.minimum_stock_level).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_orders = db.query(models.Order).filter(models.Order.created_at >= thirty_days_ago).count()
    recent_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Pending items
    pending_orders = db.query(models.Order).filter(models.Order.status == "pending").count()
    pending_payments = db.query(models.Payment).filter(models.Payment.status == "pending").count()
    pending_challans = db.query(models.Challan).filter(models.Challan.status == "pending").count()
    
    return {
        "sales": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "recent_orders_30d": recent_orders,
            "recent_revenue_30d": recent_revenue,
            "avg_order_value": total_revenue / total_orders if total_orders > 0 else 0
        },
        "customers": {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "customer_retention_rate": (active_customers / total_customers * 100) if total_customers > 0 else 0
        },
        "inventory": {
            "total_products": total_products,
            "low_stock_alerts": low_stock_products,
            "stock_health_score": ((total_products - low_stock_products) / total_products * 100) if total_products > 0 else 0
        },
        "pending_items": {
            "orders": pending_orders,
            "payments": pending_payments,
            "challans": pending_challans,
            "total_pending": pending_orders + pending_payments + pending_challans
        }
    }

@router.get("/dashboard/sales-trend")
@handle_database_error
def get_sales_trend(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get sales trend data for charts"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get orders in the period
    orders = db.query(models.Order).filter(
        models.Order.created_at >= start_date
    ).all()
    
    # Group by date
    daily_sales = defaultdict(lambda: {"orders": 0, "revenue": 0})
    
    for order in orders:
        date_key = order.created_at.date().isoformat()
        daily_sales[date_key]["orders"] += 1
        daily_sales[date_key]["revenue"] += order.total_amount or 0
    
    # Fill missing dates with zeros
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    
    complete_data = []
    while current_date <= end_date:
        date_key = current_date.isoformat()
        complete_data.append({
            "date": date_key,
            "orders": daily_sales[date_key]["orders"],
            "revenue": daily_sales[date_key]["revenue"]
        })
        current_date += timedelta(days=1)
    
    return {
        "period_days": days,
        "data": complete_data,
        "total_orders": sum(d["orders"] for d in complete_data),
        "total_revenue": sum(d["revenue"] for d in complete_data)
    }

# ================= SALES ANALYTICS =================

@router.get("/sales/summary")
@handle_database_error
def get_sales_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive sales summary"""
    # Set default date range (last 30 days)
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.utcnow().date()
    
    # Get orders in date range
    orders = db.query(models.Order).filter(
        func.date(models.Order.created_at) >= start_date,
        func.date(models.Order.created_at) <= end_date
    ).all()
    
    # Calculate metrics
    total_orders = len(orders)
    total_revenue = sum(order.total_amount for order in orders if order.total_amount)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Status distribution
    status_counts = defaultdict(int)
    for order in orders:
        status_counts[order.status] += 1
    
    # Customer analysis
    customer_orders = defaultdict(int)
    for order in orders:
        customer_orders[order.customer_id] += 1
    
    repeat_customers = sum(1 for count in customer_orders.values() if count > 1)
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": avg_order_value,
            "unique_customers": len(customer_orders),
            "repeat_customers": repeat_customers
        },
        "status_distribution": dict(status_counts),
        "customer_insights": {
            "new_customers": len(customer_orders) - repeat_customers,
            "repeat_customer_rate": (repeat_customers / len(customer_orders) * 100) if len(customer_orders) > 0 else 0
        }
    }

@router.get("/sales/top-products")
@handle_database_error
def get_top_selling_products(
    limit: int = Query(10, description="Number of top products to return"),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get top selling products"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get order items from the period
    top_products = db.query(
        models.OrderItem.product_id,
        func.sum(models.OrderItem.quantity).label("total_quantity"),
        func.sum(models.OrderItem.total_amount).label("total_revenue"),
        func.count(models.OrderItem.id).label("order_count")
    ).join(models.Order).filter(
        models.Order.created_at >= start_date
    ).group_by(models.OrderItem.product_id).order_by(
        func.sum(models.OrderItem.total_amount).desc()
    ).limit(limit).all()
    
    # Get product details
    result = []
    for item in top_products:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            result.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "total_quantity": item.total_quantity,
                "total_revenue": item.total_revenue,
                "order_count": item.order_count,
                "avg_order_quantity": item.total_quantity / item.order_count if item.order_count > 0 else 0
            })
    
    return {
        "period_days": days,
        "top_products": result
    }

# ================= INVENTORY ANALYTICS =================

@router.get("/inventory/status")
@handle_database_error
def get_inventory_status(db: Session = Depends(get_db)):
    """Get comprehensive inventory status"""
    # Get all products
    products = db.query(models.Product).all()
    
    # Categorize by stock status
    in_stock = []
    low_stock = []
    out_of_stock = []
    
    for product in products:
        if product.stock_quantity <= 0:
            out_of_stock.append(product)
        elif product.stock_quantity <= product.minimum_stock_level:
            low_stock.append(product)
        else:
            in_stock.append(product)
    
    # Get recent inventory movements
    recent_movements = db.query(models.InventoryMovement).filter(
        models.InventoryMovement.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Calculate inventory value
    total_inventory_value = sum(
        (product.stock_quantity * product.selling_price) for product in products
        if product.stock_quantity and product.selling_price
    )
    
    return {
        "summary": {
            "total_products": len(products),
            "in_stock": len(in_stock),
            "low_stock": len(low_stock),
            "out_of_stock": len(out_of_stock),
            "stock_health_score": (len(in_stock) / len(products) * 100) if products else 0
        },
        "inventory_value": total_inventory_value,
        "recent_movements_7d": recent_movements,
        "alerts": {
            "low_stock_products": [{"id": p.id, "name": p.name, "quantity": p.stock_quantity} for p in low_stock],
            "out_of_stock_products": [{"id": p.id, "name": p.name} for p in out_of_stock]
        }
    }

@router.get("/inventory/turnover")
@handle_database_error
def get_inventory_turnover(
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get inventory turnover analysis"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get products with sales data
    product_sales = db.query(
        models.OrderItem.product_id,
        func.sum(models.OrderItem.quantity).label("total_sold")
    ).join(models.Order).filter(
        models.Order.created_at >= start_date
    ).group_by(models.OrderItem.product_id).all()
    
    # Calculate turnover for each product
    turnover_data = []
    for sale in product_sales:
        product = db.query(models.Product).filter(models.Product.id == sale.product_id).first()
        if product and product.stock_quantity > 0:
            turnover_rate = sale.total_sold / product.stock_quantity
            turnover_data.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock_quantity,
                "total_sold": sale.total_sold,
                "turnover_rate": turnover_rate,
                "days_to_stockout": (product.stock_quantity / sale.total_sold * days) if sale.total_sold > 0 else None
            })
    
    # Sort by turnover rate
    turnover_data.sort(key=lambda x: x["turnover_rate"], reverse=True)
    
    return {
        "period_days": days,
        "fast_moving": turnover_data[:10],
        "slow_moving": turnover_data[-10:],
        "avg_turnover_rate": sum(d["turnover_rate"] for d in turnover_data) / len(turnover_data) if turnover_data else 0
    }

# ================= CUSTOMER ANALYTICS =================

@router.get("/customers/segmentation")
@handle_database_error
def get_customer_segmentation(db: Session = Depends(get_db)):
    """Get customer segmentation analysis"""
    # Get customer purchase data
    customer_data = db.query(
        models.Customer.id,
        models.Customer.name,
        func.count(models.Order.id).label("order_count"),
        func.sum(models.Order.total_amount).label("total_spent"),
        func.max(models.Order.created_at).label("last_order_date")
    ).outerjoin(models.Order).group_by(models.Customer.id, models.Customer.name).all()
    
    # Segment customers
    high_value = []  # >50k spent
    medium_value = []  # 10k-50k spent
    low_value = []  # <10k spent
    inactive = []  # No orders in last 90 days
    
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    
    for customer in customer_data:
        total_spent = customer.total_spent or 0
        last_order = customer.last_order_date
        
        if not last_order or last_order < ninety_days_ago:
            inactive.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_spent": total_spent,
                "order_count": customer.order_count,
                "last_order_date": last_order.isoformat() if last_order else None
            })
        elif total_spent > 50000:
            high_value.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_spent": total_spent,
                "order_count": customer.order_count,
                "avg_order_value": total_spent / customer.order_count if customer.order_count > 0 else 0
            })
        elif total_spent > 10000:
            medium_value.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_spent": total_spent,
                "order_count": customer.order_count,
                "avg_order_value": total_spent / customer.order_count if customer.order_count > 0 else 0
            })
        else:
            low_value.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_spent": total_spent,
                "order_count": customer.order_count,
                "avg_order_value": total_spent / customer.order_count if customer.order_count > 0 else 0
            })
    
    return {
        "segments": {
            "high_value": {
                "count": len(high_value),
                "customers": high_value,
                "total_revenue": sum(c["total_spent"] for c in high_value)
            },
            "medium_value": {
                "count": len(medium_value),
                "customers": medium_value,
                "total_revenue": sum(c["total_spent"] for c in medium_value)
            },
            "low_value": {
                "count": len(low_value),
                "customers": low_value,
                "total_revenue": sum(c["total_spent"] for c in low_value)
            },
            "inactive": {
                "count": len(inactive),
                "customers": inactive,
                "total_revenue": sum(c["total_spent"] for c in inactive)
            }
        }
    }

# ================= FINANCIAL ANALYTICS =================

@router.get("/financial/summary")
@handle_database_error
def get_financial_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get financial summary with profit/loss analysis"""
    # Set default date range
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.utcnow().date()
    
    # Revenue from orders
    total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        func.date(models.Order.created_at) >= start_date,
        func.date(models.Order.created_at) <= end_date
    ).scalar() or 0
    
    # Costs from purchases
    total_costs = db.query(func.sum(models.Purchase.total_amount)).filter(
        func.date(models.Purchase.created_at) >= start_date,
        func.date(models.Purchase.created_at) <= end_date
    ).scalar() or 0
    
    # Tax information
    total_tax = db.query(func.sum(models.TaxEntry.tax_amount)).filter(
        func.date(models.TaxEntry.created_at) >= start_date,
        func.date(models.TaxEntry.created_at) <= end_date
    ).scalar() or 0
    
    # Calculate profit
    gross_profit = total_revenue - total_costs
    net_profit = gross_profit - total_tax
    
    # Profit margins
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "revenue": {
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "gross_profit": gross_profit,
            "net_profit": net_profit
        },
        "margins": {
            "gross_margin_percent": gross_margin,
            "net_margin_percent": net_margin
        },
        "taxes": {
            "total_tax": total_tax,
            "effective_tax_rate": (total_tax / gross_profit * 100) if gross_profit > 0 else 0
        }
    }

@router.get("/financial/cash-flow")
@handle_database_error
def get_cash_flow_analysis(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get cash flow analysis"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get payments (cash inflow)
    payments = db.query(models.Payment).filter(
        models.Payment.created_at >= start_date
    ).all()
    
    # Get purchases (cash outflow)
    purchases = db.query(models.Purchase).filter(
        models.Purchase.created_at >= start_date
    ).all()
    
    # Group by date
    daily_cash_flow = defaultdict(lambda: {"inflow": 0, "outflow": 0})
    
    for payment in payments:
        date_key = payment.created_at.date().isoformat()
        daily_cash_flow[date_key]["inflow"] += payment.amount
    
    for purchase in purchases:
        date_key = purchase.created_at.date().isoformat()
        daily_cash_flow[date_key]["outflow"] += purchase.total_amount or 0
    
    # Calculate net cash flow
    for date_key in daily_cash_flow:
        daily_cash_flow[date_key]["net"] = daily_cash_flow[date_key]["inflow"] - daily_cash_flow[date_key]["outflow"]
    
    # Fill missing dates
    cash_flow_data = []
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    
    while current_date <= end_date:
        date_key = current_date.isoformat()
        cash_flow_data.append({
            "date": date_key,
            "inflow": daily_cash_flow[date_key]["inflow"],
            "outflow": daily_cash_flow[date_key]["outflow"],
            "net": daily_cash_flow[date_key]["net"]
        })
        current_date += timedelta(days=1)
    
    return {
        "period_days": days,
        "cash_flow_data": cash_flow_data,
        "summary": {
            "total_inflow": sum(d["inflow"] for d in cash_flow_data),
            "total_outflow": sum(d["outflow"] for d in cash_flow_data),
            "net_cash_flow": sum(d["net"] for d in cash_flow_data)
        }
    }

# ================= OPERATIONAL ANALYTICS =================

@router.get("/operations/efficiency")
@handle_database_error
def get_operational_efficiency(db: Session = Depends(get_db)):
    """Get operational efficiency metrics"""
    # Order processing efficiency
    total_orders = db.query(models.Order).count()
    completed_orders = db.query(models.Order).filter(models.Order.status == "completed").count()
    
    # Challan delivery efficiency
    total_challans = db.query(models.Challan).count()
    delivered_challans = db.query(models.Challan).filter(models.Challan.status == "delivered").count()
    
    # Inventory accuracy
    total_products = db.query(models.Product).count()
    products_with_movements = db.query(models.Product).join(models.InventoryMovement).distinct().count()
    
    # Payment processing
    total_payments = db.query(models.Payment).count()
    processed_payments = db.query(models.Payment).filter(models.Payment.status == "completed").count()
    
    return {
        "order_processing": {
            "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0,
            "total_orders": total_orders,
            "completed_orders": completed_orders
        },
        "delivery_efficiency": {
            "delivery_rate": (delivered_challans / total_challans * 100) if total_challans > 0 else 0,
            "total_challans": total_challans,
            "delivered_challans": delivered_challans
        },
        "inventory_management": {
            "tracking_coverage": (products_with_movements / total_products * 100) if total_products > 0 else 0,
            "total_products": total_products,
            "tracked_products": products_with_movements
        },
        "payment_processing": {
            "processing_rate": (processed_payments / total_payments * 100) if total_payments > 0 else 0,
            "total_payments": total_payments,
            "processed_payments": processed_payments
        }
    }

# ================= PREDICTIVE ANALYTICS =================

@router.get("/predictions/demand-forecast")
@handle_database_error
def get_demand_forecast(
    product_id: Optional[int] = None,
    days_ahead: int = Query(30, description="Number of days to forecast"),
    db: Session = Depends(get_db)
):
    """Get demand forecast for products"""
    # Simple moving average forecast
    historical_days = days_ahead * 2  # Use 2x period for historical data
    start_date = datetime.utcnow() - timedelta(days=historical_days)
    
    if product_id:
        # Forecast for specific product
        historical_sales = db.query(
            func.date(models.Order.created_at).label("date"),
            func.sum(models.OrderItem.quantity).label("quantity")
        ).join(models.OrderItem).filter(
            models.OrderItem.product_id == product_id,
            models.Order.created_at >= start_date
        ).group_by(func.date(models.Order.created_at)).all()
        
        if not historical_sales:
            return {"error": "No historical sales data found for this product"}
        
        # Calculate average daily demand
        total_quantity = sum(sale.quantity for sale in historical_sales)
        avg_daily_demand = total_quantity / len(historical_sales)
        
        # Simple forecast
        forecast = {
            "product_id": product_id,
            "forecast_period_days": days_ahead,
            "avg_daily_demand": avg_daily_demand,
            "predicted_total_demand": avg_daily_demand * days_ahead,
            "confidence_level": "medium"  # Simple model has medium confidence
        }
        
        return forecast
    
    else:
        # Forecast for top 10 products
        top_products = db.query(
            models.OrderItem.product_id,
            func.sum(models.OrderItem.quantity).label("total_quantity")
        ).join(models.Order).filter(
            models.Order.created_at >= start_date
        ).group_by(models.OrderItem.product_id).order_by(
            func.sum(models.OrderItem.quantity).desc()
        ).limit(10).all()
        
        forecasts = []
        for product in top_products:
            # Get product details
            product_info = db.query(models.Product).filter(models.Product.id == product.product_id).first()
            
            # Calculate forecast
            avg_daily_demand = product.total_quantity / historical_days
            
            forecasts.append({
                "product_id": product.product_id,
                "product_name": product_info.name if product_info else "Unknown",
                "avg_daily_demand": avg_daily_demand,
                "predicted_total_demand": avg_daily_demand * days_ahead,
                "current_stock": product_info.stock_quantity if product_info else 0,
                "stockout_risk": "high" if product_info and product_info.stock_quantity < (avg_daily_demand * days_ahead) else "low"
            })
        
        return {
            "forecast_period_days": days_ahead,
            "top_products_forecast": forecasts
        }

# ================= EXPORT ANALYTICS =================

@router.get("/export/comprehensive-report")
@handle_database_error
def export_comprehensive_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Export comprehensive business report"""
    # Set default date range
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.utcnow().date()
    
    # Collect all analytics data
    report_data = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "report_type": "comprehensive_business_analytics"
        },
        "sales_summary": get_sales_summary(start_date, end_date, db),
        "inventory_status": get_inventory_status(db),
        "customer_segmentation": get_customer_segmentation(db),
        "financial_summary": get_financial_summary(start_date, end_date, db),
        "operational_efficiency": get_operational_efficiency(db)
    }
    
    return report_data 