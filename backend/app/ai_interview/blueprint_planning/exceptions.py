class BlueprintPlanningError(Exception):
    pass

class BlueprintValidationError(BlueprintPlanningError):
    pass

class ContextValidationError(BlueprintPlanningError):
    pass
