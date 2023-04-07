from typing import Dict, Tuple


class ConfidenceTable:
    """
    Container of confidence values for a set of declarators in a knowledge base.
    
    There are two types of declarators:
    - Static: their associated confidence is constant.
    This may be attributed, for instance, to trusted knowledge declarators
    - Non-static: declarators whose confidence mainly depends on the declarations from static declarators.
    By default they have a confidence of 0.5 (50%), which means the system doesn't prefer between trusting
    and not trusting these declarators.

    Confidence for non-static declarators is affected by the agreement with other declarators.
    
    """

    def __init__(self):
        self.confidences: Dict[str, Tuple[float, bool]] = {}

    def update_confidences(self):
        """Update all confidence values of non-static declarators, since they are variable.
        The update frequency is therefore left at the discretion of the user.
        """
        pass

    def register_declarator(self, declarator: str, static_confidence: float=None):
        self.confidences
        pass

    def register_new_knowledge(self, ):
        pass
