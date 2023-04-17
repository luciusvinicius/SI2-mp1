from typing import Dict, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from kb import KnowledgeBase, Relation


class ConfidenceTable:
    """
    Container of confidence values for a set of declarators in a knowledge base.
    
    "Confidence" represents the degree of trust in a declarator's declarations.
    "Confidence" is also associated with a particular declaration, which takes into account the confidence
    of the involved declarators.

    There are two types of declarators:
    - Static: their associated confidence is constant.
    This may be attributed, for instance, to trusted knowledge declarators
    - Non-static: declarators whose confidence mainly depends on the declarations from other declarators.
    By default they have a confidence of 0.5 (50%), which means the system doesn't prefer between trusting
    and not trusting these declarators.

    Confidence for non-static declarators is calculated by considering their agreement with the static and
    other non-static declarators separately.
    The weight of this agreement is represented by the factors `saf_weight` and `nsaf_weight` respectively.
    If `saf_weight + nsaf_weight > 1`, then the non-static declarator's confidence can overshoot and
    undershoot, and thus be greater than 1 or lower than 0. In practice, the value is clamped.

    Parameters
    ----------
    knowledge_base : KnowledgeBase
        The knowledge base housing the declarators and their declarations
    saf_weight : float = 0.5
        The weight of the static agreement factor when calculating the confidence of a non-static declarator
    nsaf_weight : float = 0.5
        The weight of the non-static agreement factor when calculating the confidence of a non-static declarator
    base_confidence : float = 0.5
        The base confidence of a non-static declarator
    """

    def __init__(self,
                 knowledge_base: 'KnowledgeBase',
                 saf_weight: float=0.5,
                 nsaf_weight: float=0.5,
                 base_confidence: float=0.5):

        self._kb = knowledge_base
        self._saf_weight = saf_weight
        self._nsaf_weight = nsaf_weight
        self._base_confidence = base_confidence
        
        self._confidences:               Dict[str, float]   = {}
        self._static_declarators:        Set[str]           = set()
        self._non_static_declarators:    Set[str]           = set()

    def update_confidences(self):
        """Update all confidence values of non-static declarators, since they are variable.
        The update frequency is therefore left at the discretion of the user.
        """

        for non_static_declarator in self._non_static_declarators:
            saf = self._get_agreement_factor(non_static_declarator, static=True)
            nsaf = self._get_agreement_factor(non_static_declarator, static=False)

            self._confidences[non_static_declarator] = max(0.0, min(1.0, self._base_confidence
                + (1 - self._base_confidence) * saf * self._saf_weight
                + (1 - self._base_confidence) * nsaf * self._nsaf_weight))

    def register_declarator(self, declarator: str, static_confidence: float=None):
        """Register a static/non-static declarator.

        It's idempotent unless the `static_confidence` attributed to a given `declarator`
        is different in separate calls to this function, in which case the declarator's associated
        confidence value is updated in each call.

        If a registered non-static declarator is then registered as static, then it switch from non-
        static to static, and vice-versa.

        Parameters
        ----------
        declarator : str
            The declarator to register
        static_confidence : float = None
            If `None`, register this declarator as non-static with a base confidence value.
            Otherwise, register as a static declarator with the given `static_confidence`.
        """

        # Registered static declarator
        if static_confidence is not None:
            if declarator in self._non_static_declarators:
                self._non_static_declarators.remove(declarator)
            self._confidences[declarator] = static_confidence
            self._static_declarators.add(declarator)
        
        # Registered non-static declarator
        else:
            if declarator in self._static_declarators:
                self._static_declarators.remove(declarator)
            self._confidences[declarator] = self._base_confidence
            self._non_static_declarators.add(declarator)

    def get_relation_confidence(self, relation: 'Relation') -> float:
        """Obtain the confidence of the given relation based on its declarators' confidence values.
        
        The relation confidence is calculated as the maximum value between:
        - the "aggregated" confidences of the static declarators involved in the relation
        - the "aggregated" confidences of the non-static declarators involved in the relation

        The "aggregation" of declarator confidences is given by the mean value between `dt` and `1 - df`, where:
        - `dt` is the greatest declarator confidence for the queried relation
        - `df` is the greatest declarator confidence for the inverse of the queried relation

        Parameters
        ----------
        relation : Relation
            The relation to obtain the confidence of

        Returns
        -------
        float
            The declaration's confidence, or `None` the relation wasn't declared
        """

        declarators = self._kb.query_declarators(relation)
        adversary_declarators = self._kb.query_declarators(relation.inverse())

        obtain_confidences = lambda ds, filter_ds: {self._confidences[declarator] for declarator in ds if declarator in filter_ds}

        static_confidences = obtain_confidences(declarators, self._static_declarators)
        non_static_confidences = obtain_confidences(declarators, self._non_static_declarators)

        adversary_static_confidences = obtain_confidences(adversary_declarators, self._static_declarators)
        adversary_non_static_confidences = obtain_confidences(adversary_declarators, self._non_static_declarators)

        if len(static_confidences) > 0:
            if len(adversary_static_confidences) > 0:
                greatest_static_confidence = (max(static_confidences) + (1 - max(adversary_static_confidences))) / 2
            else:
                greatest_static_confidence = max(static_confidences)
        else:
            greatest_static_confidence = 0
        
        if len(non_static_confidences) > 0:
            if len(adversary_non_static_confidences) > 0:
                greatest_non_static_confidence = (max(non_static_confidences) + (1 - max(adversary_non_static_confidences))) / 2
            else:
                greatest_non_static_confidence = max(non_static_confidences)
        else:
            greatest_non_static_confidence = 0
        
        return max(greatest_static_confidence, greatest_non_static_confidence)

    def _get_agreement_factor(self, declarator: str, static: bool) -> float:
        """Calculate the agreement factor of a declarator, which represents the degree of
        agreement with other declarators on the knowledge base.

        The `static` parameter restricts the declarators with which `declarator` is compared.
        If `True`, only static declarators are considered. Otherwise, only non-static declarators are considered.

        The agreement factor corresponds to the formula `P(A | D) - P(~A | D)`, where:
        - `P(A | D)` is the probability of agreement `A` of this declarator given a declaration on the knowledge
        base from the other declarators `D`
        - `P(~A | D)` is the probability of disagreement `~A` of this declarator given a declaration on the knowledge
        base from the other declarators `D`

        "Agreement" is defined as matching all of the relation's attributes including the `not_` attribute.
        "Disagreement", on the other hand, is defined as matching all of the relation's attributes but not the `not_` attribute.

        Parameters
        ----------
        declarator : str
            The declarator to calculate the agreement factor of
        static : bool
            Whether to consider only static or non-static declarators
        """

        other_declarators = (self._static_declarators if static else self._non_static_declarators) - {declarator}
        
        our_declarations = set(self._kb.query_declarations(declarator))
        our_declarations_adversary = {relation.inverse() for relation in our_declarations}

        other_declarations_n = 0
        agreement_n = 0
        disagreement_n = 0

        for other_declarator in other_declarators:
            their_declarations = set(self._kb.query_declarations(other_declarator))
            other_declarations_n += len(their_declarations)
            agreement_n += len(their_declarations & our_declarations)
            disagreement_n += len(their_declarations & our_declarations_adversary)
        
        return ((agreement_n - disagreement_n) / other_declarations_n) if other_declarations_n > 0 else 0
