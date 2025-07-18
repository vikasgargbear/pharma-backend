"""
Loyalty Router - Customer loyalty program endpoints
Points system, rewards, and customer engagement features
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/loyalty", tags=["loyalty"])

# Create CRUD instances using our generic system
loyalty_account_crud = create_crud(models.LoyaltyAccount)
points_transaction_crud = create_crud(models.PointsTransaction)
reward_crud = create_crud(models.Reward)
reward_redemption_crud = create_crud(models.RewardRedemption)

# ================= LOYALTY ACCOUNTS =================

@router.post("/accounts/", response_model=schemas.LoyaltyAccount)
@handle_database_error
def create_loyalty_account(account: schemas.LoyaltyAccountCreate, db: Session = Depends(get_db)):
    """Create a new loyalty account"""
    # Check if customer already has a loyalty account
    existing_account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == account.customer_id
    ).first()
    
    if existing_account:
        raise HTTPException(status_code=400, detail="Customer already has a loyalty account")
    
    return loyalty_account_crud.create(db, account)

@router.get("/accounts/", response_model=List[schemas.LoyaltyAccount])
@handle_database_error
def get_loyalty_accounts(
    skip: int = 0,
    limit: int = 100,
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get loyalty accounts with filtering"""
    query = db.query(models.LoyaltyAccount)
    
    if tier:
        query = query.filter(models.LoyaltyAccount.tier == tier)
    if is_active is not None:
        query = query.filter(models.LoyaltyAccount.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.get("/accounts/{account_id}", response_model=schemas.LoyaltyAccount)
@handle_database_error
def get_loyalty_account(account_id: int, db: Session = Depends(get_db)):
    """Get a specific loyalty account"""
    account = loyalty_account_crud.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Loyalty account not found")
    return account

@router.get("/accounts/customer/{customer_id}", response_model=schemas.LoyaltyAccount)
@handle_database_error
def get_customer_loyalty_account(customer_id: int, db: Session = Depends(get_db)):
    """Get loyalty account for a specific customer"""
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    return account

@router.put("/accounts/{account_id}", response_model=schemas.LoyaltyAccount)
@handle_database_error
def update_loyalty_account(
    account_id: int,
    account_update: schemas.LoyaltyAccountUpdate,
    db: Session = Depends(get_db)
):
    """Update a loyalty account"""
    account = loyalty_account_crud.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Loyalty account not found")
    
    return loyalty_account_crud.update(db, db_obj=account, obj_in=account_update)

# ================= POINTS TRANSACTIONS =================

@router.post("/points/earn")
@handle_database_error
def earn_points(
    customer_id: int,
    points: int,
    transaction_type: str = "purchase",
    reference_id: Optional[int] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Award points to a customer"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    if not account.is_active:
        raise HTTPException(status_code=400, detail="Loyalty account is not active")
    
    # Create points transaction
    transaction_data = {
        "loyalty_account_id": account.id,
        "points": points,
        "transaction_type": transaction_type,
        "reference_id": reference_id,
        "description": description or f"Points earned from {transaction_type}",
        "transaction_date": datetime.utcnow()
    }
    
    transaction = points_transaction_crud.create(db, schemas.PointsTransactionCreate(**transaction_data))
    
    # Update account balance
    account.points_balance += points
    account.total_points_earned += points
    account.last_activity_date = datetime.utcnow()
    
    # Check for tier upgrade
    account.tier = calculate_tier(account.total_points_earned)
    
    db.commit()
    
    return {
        "message": f"Successfully awarded {points} points",
        "transaction": transaction,
        "new_balance": account.points_balance,
        "tier": account.tier
    }

@router.post("/points/redeem")
@handle_database_error
def redeem_points(
    customer_id: int,
    points: int,
    transaction_type: str = "redemption",
    reference_id: Optional[int] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Redeem points from a customer's account"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    if not account.is_active:
        raise HTTPException(status_code=400, detail="Loyalty account is not active")
    
    if account.points_balance < points:
        raise HTTPException(status_code=400, detail="Insufficient points balance")
    
    # Create points transaction (negative for redemption)
    transaction_data = {
        "loyalty_account_id": account.id,
        "points": -points,
        "transaction_type": transaction_type,
        "reference_id": reference_id,
        "description": description or f"Points redeemed for {transaction_type}",
        "transaction_date": datetime.utcnow()
    }
    
    transaction = points_transaction_crud.create(db, schemas.PointsTransactionCreate(**transaction_data))
    
    # Update account balance
    account.points_balance -= points
    account.total_points_redeemed += points
    account.last_activity_date = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Successfully redeemed {points} points",
        "transaction": transaction,
        "new_balance": account.points_balance,
        "tier": account.tier
    }

@router.get("/points/transactions/{account_id}")
@handle_database_error
def get_points_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get points transactions for a loyalty account"""
    query = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.loyalty_account_id == account_id
    )
    
    if transaction_type:
        query = query.filter(models.PointsTransaction.transaction_type == transaction_type)
    
    return query.order_by(models.PointsTransaction.transaction_date.desc()).offset(skip).limit(limit).all()

def calculate_tier(total_points: int) -> str:
    """Calculate tier based on total points earned"""
    if total_points >= 10000:
        return "platinum"
    elif total_points >= 5000:
        return "gold"
    elif total_points >= 1000:
        return "silver"
    else:
        return "bronze"

# ================= REWARDS =================

@router.post("/rewards/", response_model=schemas.Reward)
@handle_database_error
def create_reward(reward: schemas.RewardCreate, db: Session = Depends(get_db)):
    """Create a new reward"""
    return reward_crud.create(db, reward)

@router.get("/rewards/", response_model=List[schemas.Reward])
@handle_database_error
def get_rewards(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    tier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get rewards with filtering"""
    query = db.query(models.Reward)
    
    if category:
        query = query.filter(models.Reward.category == category)
    if is_active is not None:
        query = query.filter(models.Reward.is_active == is_active)
    if tier:
        query = query.filter(models.Reward.required_tier == tier)
    
    return query.offset(skip).limit(limit).all()

@router.get("/rewards/{reward_id}", response_model=schemas.Reward)
@handle_database_error
def get_reward(reward_id: int, db: Session = Depends(get_db)):
    """Get a specific reward"""
    reward = reward_crud.get(db, reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    return reward

@router.get("/rewards/customer/{customer_id}")
@handle_database_error
def get_available_rewards(customer_id: int, db: Session = Depends(get_db)):
    """Get rewards available to a customer based on their tier and points"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    # Get rewards that customer can redeem
    tier_hierarchy = {"bronze": 1, "silver": 2, "gold": 3, "platinum": 4}
    customer_tier_level = tier_hierarchy.get(account.tier, 1)
    
    available_rewards = db.query(models.Reward).filter(
        models.Reward.is_active == True,
        models.Reward.points_required <= account.points_balance,
        models.Reward.required_tier.in_([tier for tier, level in tier_hierarchy.items() if level <= customer_tier_level])
    ).all()
    
    return {
        "customer_tier": account.tier,
        "points_balance": account.points_balance,
        "available_rewards": available_rewards
    }

# ================= REWARD REDEMPTIONS =================

@router.post("/rewards/redeem")
@handle_database_error
def redeem_reward(
    customer_id: int,
    reward_id: int,
    db: Session = Depends(get_db)
):
    """Redeem a reward for a customer"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    # Get reward
    reward = reward_crud.get(db, reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if not reward.is_active:
        raise HTTPException(status_code=400, detail="Reward is not active")
    
    # Check if customer has enough points
    if account.points_balance < reward.points_required:
        raise HTTPException(status_code=400, detail="Insufficient points balance")
    
    # Check tier requirement
    tier_hierarchy = {"bronze": 1, "silver": 2, "gold": 3, "platinum": 4}
    customer_tier_level = tier_hierarchy.get(account.tier, 1)
    required_tier_level = tier_hierarchy.get(reward.required_tier, 1)
    
    if customer_tier_level < required_tier_level:
        raise HTTPException(status_code=400, detail=f"Reward requires {reward.required_tier} tier")
    
    # Create redemption record
    redemption_data = {
        "loyalty_account_id": account.id,
        "reward_id": reward_id,
        "points_used": reward.points_required,
        "redemption_date": datetime.utcnow(),
        "status": "redeemed"
    }
    
    redemption = reward_redemption_crud.create(db, schemas.RewardRedemptionCreate(**redemption_data))
    
    # Deduct points
    account.points_balance -= reward.points_required
    account.total_points_redeemed += reward.points_required
    account.last_activity_date = datetime.utcnow()
    
    # Create points transaction
    transaction_data = {
        "loyalty_account_id": account.id,
        "points": -reward.points_required,
        "transaction_type": "reward_redemption",
        "reference_id": redemption.id,
        "description": f"Redeemed reward: {reward.title}",
        "transaction_date": datetime.utcnow()
    }
    
    points_transaction_crud.create(db, schemas.PointsTransactionCreate(**transaction_data))
    
    db.commit()
    
    return {
        "message": f"Successfully redeemed {reward.title}",
        "redemption": redemption,
        "points_used": reward.points_required,
        "new_balance": account.points_balance
    }

@router.get("/rewards/redemptions/{customer_id}")
@handle_database_error
def get_customer_redemptions(
    customer_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get reward redemptions for a customer"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    redemptions = db.query(models.RewardRedemption).filter(
        models.RewardRedemption.loyalty_account_id == account.id
    ).order_by(models.RewardRedemption.redemption_date.desc()).offset(skip).limit(limit).all()
    
    return redemptions

# ================= LOYALTY ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_loyalty_analytics(db: Session = Depends(get_db)):
    """Get loyalty program analytics summary"""
    # Total accounts
    total_accounts = db.query(models.LoyaltyAccount).count()
    active_accounts = db.query(models.LoyaltyAccount).filter(models.LoyaltyAccount.is_active == True).count()
    
    # Tier distribution
    tier_counts = db.query(models.LoyaltyAccount.tier, func.count(models.LoyaltyAccount.id)).group_by(models.LoyaltyAccount.tier).all()
    
    # Points statistics
    total_points_earned = db.query(func.sum(models.LoyaltyAccount.total_points_earned)).scalar() or 0
    total_points_redeemed = db.query(func.sum(models.LoyaltyAccount.total_points_redeemed)).scalar() or 0
    total_points_outstanding = db.query(func.sum(models.LoyaltyAccount.points_balance)).scalar() or 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_transactions = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.transaction_date >= thirty_days_ago
    ).count()
    
    recent_redemptions = db.query(models.RewardRedemption).filter(
        models.RewardRedemption.redemption_date >= thirty_days_ago
    ).count()
    
    # Active rewards
    active_rewards = db.query(models.Reward).filter(models.Reward.is_active == True).count()
    
    return {
        "accounts": {
            "total": total_accounts,
            "active": active_accounts,
            "inactive": total_accounts - active_accounts
        },
        "tier_distribution": dict(tier_counts),
        "points": {
            "total_earned": total_points_earned,
            "total_redeemed": total_points_redeemed,
            "outstanding": total_points_outstanding,
            "redemption_rate": (total_points_redeemed / total_points_earned * 100) if total_points_earned > 0 else 0
        },
        "recent_activity_30d": {
            "transactions": recent_transactions,
            "redemptions": recent_redemptions
        },
        "active_rewards": active_rewards
    }

@router.get("/analytics/customer-engagement")
@handle_database_error
def get_customer_engagement_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get customer engagement analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get accounts with activity in the period
    active_accounts = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.last_activity_date >= start_date
    ).all()
    
    # Calculate engagement metrics
    total_accounts = db.query(models.LoyaltyAccount).count()
    engagement_rate = (len(active_accounts) / total_accounts * 100) if total_accounts > 0 else 0
    
    # Points activity
    transactions = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.transaction_date >= start_date
    ).all()
    
    points_earned = sum(t.points for t in transactions if t.points > 0)
    points_redeemed = sum(abs(t.points) for t in transactions if t.points < 0)
    
    # Daily engagement
    daily_activity = {}
    for account in active_accounts:
        if account.last_activity_date:
            day_key = account.last_activity_date.date().isoformat()
            if day_key not in daily_activity:
                daily_activity[day_key] = 0
            daily_activity[day_key] += 1
    
    return {
        "period_days": days,
        "engagement_rate": engagement_rate,
        "active_accounts": len(active_accounts),
        "total_accounts": total_accounts,
        "points_activity": {
            "earned": points_earned,
            "redeemed": points_redeemed,
            "net_change": points_earned - points_redeemed
        },
        "daily_activity": daily_activity,
        "avg_daily_engagement": len(active_accounts) / days if days > 0 else 0
    }

@router.get("/analytics/tier-performance")
@handle_database_error
def get_tier_performance_analytics(db: Session = Depends(get_db)):
    """Get tier performance analytics"""
    # Get accounts by tier
    tiers = ["bronze", "silver", "gold", "platinum"]
    tier_analytics = {}
    
    for tier in tiers:
        accounts = db.query(models.LoyaltyAccount).filter(models.LoyaltyAccount.tier == tier).all()
        
        if accounts:
            total_points_earned = sum(a.total_points_earned for a in accounts)
            total_points_redeemed = sum(a.total_points_redeemed for a in accounts)
            avg_balance = sum(a.points_balance for a in accounts) / len(accounts)
            
            tier_analytics[tier] = {
                "account_count": len(accounts),
                "total_points_earned": total_points_earned,
                "total_points_redeemed": total_points_redeemed,
                "avg_points_balance": avg_balance,
                "redemption_rate": (total_points_redeemed / total_points_earned * 100) if total_points_earned > 0 else 0
            }
        else:
            tier_analytics[tier] = {
                "account_count": 0,
                "total_points_earned": 0,
                "total_points_redeemed": 0,
                "avg_points_balance": 0,
                "redemption_rate": 0
            }
    
    return tier_analytics

# ================= TIER MANAGEMENT =================

@router.post("/tiers/upgrade/{customer_id}")
@handle_database_error
def upgrade_customer_tier(
    customer_id: int,
    new_tier: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Manually upgrade a customer's tier"""
    # Get customer's loyalty account
    account = db.query(models.LoyaltyAccount).filter(
        models.LoyaltyAccount.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Customer loyalty account not found")
    
    # Validate tier
    valid_tiers = ["bronze", "silver", "gold", "platinum"]
    if new_tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")
    
    old_tier = account.tier
    account.tier = new_tier
    account.last_activity_date = datetime.utcnow()
    
    # Create transaction record for tier upgrade
    transaction_data = {
        "loyalty_account_id": account.id,
        "points": 0,
        "transaction_type": "tier_upgrade",
        "description": f"Tier upgraded from {old_tier} to {new_tier}. {reason or ''}",
        "transaction_date": datetime.utcnow()
    }
    
    points_transaction_crud.create(db, schemas.PointsTransactionCreate(**transaction_data))
    
    db.commit()
    
    return {
        "message": f"Successfully upgraded tier from {old_tier} to {new_tier}",
        "old_tier": old_tier,
        "new_tier": new_tier,
        "account": account
    }

@router.get("/tiers/benefits/{tier}")
@handle_database_error
def get_tier_benefits(tier: str, db: Session = Depends(get_db)):
    """Get benefits for a specific tier"""
    valid_tiers = ["bronze", "silver", "gold", "platinum"]
    if tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")
    
    # Get rewards available for this tier
    tier_hierarchy = {"bronze": 1, "silver": 2, "gold": 3, "platinum": 4}
    tier_level = tier_hierarchy.get(tier, 1)
    
    available_rewards = db.query(models.Reward).filter(
        models.Reward.is_active == True,
        models.Reward.required_tier.in_([t for t, l in tier_hierarchy.items() if l <= tier_level])
    ).all()
    
    # Define tier benefits
    tier_benefits = {
        "bronze": {
            "points_multiplier": 1.0,
            "special_offers": False,
            "priority_support": False,
            "free_shipping": False
        },
        "silver": {
            "points_multiplier": 1.2,
            "special_offers": True,
            "priority_support": False,
            "free_shipping": False
        },
        "gold": {
            "points_multiplier": 1.5,
            "special_offers": True,
            "priority_support": True,
            "free_shipping": True
        },
        "platinum": {
            "points_multiplier": 2.0,
            "special_offers": True,
            "priority_support": True,
            "free_shipping": True
        }
    }
    
    return {
        "tier": tier,
        "benefits": tier_benefits.get(tier, {}),
        "available_rewards_count": len(available_rewards),
        "available_rewards": available_rewards
    } 