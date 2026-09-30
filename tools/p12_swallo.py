"""Historical SWALLO policy with explicit river-infiltration semantics."""
def swallo(system:int, infres_day:float, river_infiltration_indicator:float)->int:
    if int(system)>3 or float(infres_day)>20000.0 or float(river_infiltration_indicator)<10.0:
        return 3
    return 1
