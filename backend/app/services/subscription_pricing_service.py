class SubscriptionPricingService:
    # Base costs and feature costs (In a real app, this could come from DB)
    BASE_PLATFORM_COST = 50000

    FEATURE_PRICING = {
        "reports": 3000,
        "analytics": 5000,
        "exports": 2000,
        "resume_screening": 5000,
        "interview_analysis": 10000,
        "voice_interview": 15000,
        "explainability": 5000,
        "branding": 8000,
        "api_access": 10000,
        "custom_questions": 2000,
    }

    LIMIT_PRICING = {
        "recruiters": {
            "tier_1": {"limit": 5, "price": 0},
            "tier_2": {"limit": 20, "price": 5000},
            "tier_3": {"limit": 999999, "price": 15000},
        },
        "monthly_interviews": {
            "tier_1": {"limit": 100, "price": 0},
            "tier_2": {"limit": 300, "price": 10000},
            "tier_3": {"limit": 1000, "price": 20000},
            "tier_4": {"limit": 999999, "price": 50000},
        },
        "candidates": {
            "tier_1": {"limit": 500, "price": 0},
            "tier_2": {"limit": 2000, "price": 5000},
            "tier_3": {"limit": 999999, "price": 10000},
        },
        "campaigns": {
            "tier_1": {"limit": 5, "price": 0},
            "tier_2": {"limit": 20, "price": 4000},
            "tier_3": {"limit": 999999, "price": 12000},
        }
    }

    @classmethod
    def calculate_price(cls, features: dict, limits: dict, duration_months: int = 12) -> dict:
        feature_cost = 0.0
        for feature, enabled in features.items():
            if enabled and feature in cls.FEATURE_PRICING:
                feature_cost += cls.FEATURE_PRICING[feature]

        limit_cost = 0.0
        # Calculate recruiters cost
        recruiter_limit = limits.get("max_recruiters", 5)
        limit_cost += cls._get_tier_price("recruiters", recruiter_limit)
        
        # Calculate interviews cost
        interviews_limit = limits.get("monthly_interviews", 100)
        limit_cost += cls._get_tier_price("monthly_interviews", interviews_limit)

        # Calculate candidates cost
        candidates_limit = limits.get("max_candidates", 500)
        limit_cost += cls._get_tier_price("candidates", candidates_limit)
        
        # Calculate campaigns cost
        campaigns_limit = limits.get("max_campaigns", 5)
        limit_cost += cls._get_tier_price("campaigns", campaigns_limit)

        subtotal = (cls.BASE_PLATFORM_COST + feature_cost + limit_cost) * (duration_months / 12)
        
        # Assume 18% Tax for example
        tax = subtotal * 0.18
        total = subtotal + tax

        return {
            "base_price": cls.BASE_PLATFORM_COST * (duration_months / 12),
            "feature_cost": feature_cost * (duration_months / 12),
            "limit_cost": limit_cost * (duration_months / 12),
            "discount": 0.0,
            "tax": tax,
            "total": total,
            "currency": "INR"
        }

    @classmethod
    def calculate_prorated_upgrade(cls, old_features: dict, old_limits: dict, old_billing_cycle: str, 
                                 new_features: dict, new_limits: dict, new_billing_cycle: str, 
                                 days_remaining: int) -> dict:
        
        # We always base daily value on an annual cost for accurate comparison
        old_annual = cls.calculate_price(old_features, old_limits, duration_months=12)
        old_annual_total = old_annual["total"] - old_annual["tax"]
        old_daily_value = old_annual_total / 365.0
        
        new_annual = cls.calculate_price(new_features, new_limits, duration_months=12)
        new_annual_total = new_annual["total"] - new_annual["tax"]
        new_daily_value = new_annual_total / 365.0
        
        # The difference in daily value for the remaining days
        daily_diff = new_daily_value - old_daily_value
        
        if daily_diff <= 0:
            # It's a downgrade or equal price
            return {
                "current_price": old_annual["total"],
                "new_price": new_annual["total"],
                "difference": 0.0,
                "tax": 0.0,
                "final_amount": 0.0,
                "currency": "INR",
                "is_upgrade": False
            }
            
        # It's an upgrade
        difference_subtotal = daily_diff * days_remaining
        tax = difference_subtotal * 0.18
        final_amount = difference_subtotal + tax
        
        return {
            "current_price": old_annual["total"],
            "new_price": new_annual["total"],
            "difference": difference_subtotal + tax,
            "tax": tax,
            "final_amount": final_amount,
            "currency": "INR",
            "is_upgrade": True
        }

    @classmethod
    def _get_tier_price(cls, limit_type: str, limit_val: int) -> float:
        tiers = cls.LIMIT_PRICING.get(limit_type, {})
        selected_price = 0.0
        for tier_key, tier_data in tiers.items():
            if limit_val <= tier_data["limit"]:
                selected_price = tier_data["price"]
                break
        return selected_price
