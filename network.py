from enum import Enum


# TestType nodes for technical areas
class TestType(str, Enum):
    """Test Types  for which KPIs are measured for ATT network entities"""
    PING = "PING"    # Ping
    TWAMP = "TWAMP"  # Twamp

# Measurement nodes for what type of measurement was done
class Measurements(str, Enum):
    """KPI categories for type of measurement performed"""
    JITTER = "JITTER"           # Jitter KPIs
    DELAY = "DELAY"       # Delay KPIs
    LATENCY = "LATENCY"         #Latency KPIs
    COMPOSITE = "COMPOSITE"               #Composite KPIs

# Path on which test packets were sent
class Path(str, Enum):
    """KPI categories for type of measurement performed"""
    FAR = "FAR"           # Jitter KPIs
    NEAR = "NEAR"       # Delay KPIs
    RT = "RT"         #Latency KPIs
    DEFAULT = "DEFAULT"               #Composite KPIs