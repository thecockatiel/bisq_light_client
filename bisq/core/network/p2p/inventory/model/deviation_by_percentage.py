
from bisq.core.network.p2p.inventory.model.deviation_severity import DeviationSeverity
from bisq.core.network.p2p.inventory.model.deviation_type import DeviationType


class DeviationByPercentage(DeviationType):
    
    # In case want to see the % deviation but not trigger any warnings or alerts
    # don't pass any values to the constructor
    def __init__(self, 
                 lower_alert_trigger: float = 0,
                 upper_alert_trigger: float = float('inf'),
                 lower_warn_trigger: float = 0, 
                 upper_warn_trigger: float = float('inf')):
        self.lower_alert_trigger = lower_alert_trigger
        self.upper_alert_trigger = upper_alert_trigger
        self.lower_warn_trigger = lower_warn_trigger
        self.upper_warn_trigger = upper_warn_trigger

    def get_deviation_severity(self, deviation: float) -> DeviationSeverity:
        if deviation <= self.lower_alert_trigger or deviation >= self.upper_alert_trigger:
            return DeviationSeverity.ALERT
            
        if deviation <= self.lower_warn_trigger or deviation >= self.upper_warn_trigger:
            return DeviationSeverity.WARN
            
        return DeviationSeverity.OK