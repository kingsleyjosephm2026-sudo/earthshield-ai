"""Modeled exposure. NOT verified loss, NOT an insurance payout."""
SCENARIOS = {"low": 0.10, "central": 0.25, "high": 0.50}  # ASSUMED damage fractions
def exposure(area_ha, yield_t_ha, price_per_t, damage_fraction):
    """gross = area*yield*price (INR); estimated_loss = gross*damage_fraction. None if any input missing/invalid."""
    for v in (area_ha, yield_t_ha, price_per_t, damage_fraction):
        if v is None or v != v or v < 0: return None
    if damage_fraction > 1: return None
    gross = area_ha * yield_t_ha * price_per_t
    return {"gross_crop_value_inr": gross, "estimated_loss_inr": gross * damage_fraction}
def scenarios(area_ha, yield_t_ha, price_per_t):
    return {k: exposure(area_ha, yield_t_ha, price_per_t, f) for k, f in SCENARIOS.items()}
