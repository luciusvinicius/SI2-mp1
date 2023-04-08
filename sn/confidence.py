from typing import Dict, List, Set, Tuple

from sn.kb import KnowledgeBase


class ConfidenceTable:
    """
    Container of confidence values for a set of declarators in a knowledge base.
    
    "Confidence" represents the degree of trust in a declarator's declarations.
    "Confidence" is also associated with a particular declaration, which takes into account the confidence
    of the involved declarators.

    There are two types of declarators:
    - Static: their associated confidence is constant.
    This may be attributed, for instance, to trusted knowledge declarators
    - Non-static: declarators whose confidence mainly depends on the declarations from static declarators.
    By default they have a confidence of 0.5 (50%), which means the system doesn't prefer between trusting
    and not trusting these declarators.

    Confidence for non-static declarators is calculated by considering their agreement with the static and
    other non-static declarators separately.
    The weight of this agreement is represented by the factors `saf_weight` and `nsaf_weight` respectively.
    If `saf_weight + nsaf_weight > 1`, then the non-static declarator's confidence can overshoot and be
    greater than 1. In practice, the value is clamped.

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
                 knowledge_base: KnowledgeBase,
                 saf_weight: float=0.5,
                 nsaf_weight: float=0.5,
                 base_confidence: float=0.5):

        self._kb = knowledge_base
        self._saf_weight = saf_weight
        self._nsaf_weight = nsaf_weight
        self._base_confidence = base_confidence
        
        self._confidences:               Dict[str, float]   = {}
        self._static_declarators:        Set[str]           = []
        self._non_static_declarators:    Set[str]           = []

    def update_confidences(self):
        """Update all confidence values of non-static declarators, since they are variable.
        The update frequency is therefore left at the discretion of the user.
        """

        for non_static_declarator in self._non_static_declarators:
            saf = self._get_agreement_factor(non_static_declarator, static=True)
            nsaf = self._get_agreement_factor(non_static_declarator, static=False)
            
            # Values are put into the range [0, 1] (previously in range [-1, 1])
            saf = (saf + 1) / 2
            nsaf = (nsaf + 1) / 2

            self._confidences[non_static_declarator] = min(1.0, self._base_confidence
                + (1 - self._base_confidence) * saf * self._saf_weight
                + (1 - self._base_confidence) * nsaf * self._nsaf_weight)

    def register_declarator(self, declarator: str, static_confidence: float=None):
        """Register a static/non-static declarator.

        It's idempotent unless the `static_confidence` attributed to a given `declarator`
        is different in separate calls to this function, in which case the declarator's associated
        confidence value is updated in each call.

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
            self._confidences[declarator] = static_confidence
            self._static_declarators.add(declarator)
        
        # Registered non-static declarator
        else:
            self._confidences[declarator] = self._base_confidence
            self._non_static_declarators.add(declarator)

    def get_relation_confidence(self, ent1: str, ent2: str, relation: str, relation_type: str, not_: bool=True) -> float:
        """Obtain the confidence of the given relation based on its declarators' confidence values.
        
        Parameters
        ----------
        ent1 : str
            The first entity of the declared relation
        ent2 : str
            The second entity of the declared relation
        relation : str
            The name of the declared relation
        relation_type : str
            The type of the declared relation (given by the enum `RelType`)

        Returns
        -------
        float
            The declaration's confidence, or `None` the relation wasn't declared
        """

        declarators = self._kb.query_declarators(ent1, ent2, relation, relation_type, not_=not_)
        adversary_declarators = self._kb.query_declarators(ent1, ent2, relation, relation_type, not_=not not_)

        obtain_confidences = lambda ds, filter_ds: {self._confidences[declarator] for declarator in ds if declarator in filter_ds}

        static_confidences = obtain_confidences(declarators, self._static_declarators)
        non_static_confidences = obtain_confidences(declarators, self._non_static_declarators)

        adversary_static_confidences = obtain_confidences(adversary_declarators, self._static_declarators)
        adversary_non_static_confidences = obtain_confidences(adversary_declarators, self._non_static_declarators)

        greatest_static_confidence = (max(static_confidences) + (1 - max(adversary_static_confidences))) / 2
        greatest_non_static_confidence = (max(non_static_confidences) + (1 - max(adversary_non_static_confidences))) / 2
        
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
        "Disagreement", on the other hand, is defined as matching all of the relation's attributes except the `not_` attribute.

        Parameters
        ----------
        declarator : str
            The declarator to calculate the agreement factor of
        static : bool
            Whether to consider only static or non-static declarators
        """
        other_declarators = self._static_declarators if static else self._non_static_declarators
        
        our_declarations = set(self._kb.query_declarations(declarator))
        our_declarations_adversary = our_declarations.copy()
        for relation in our_declarations_adversary:
            relation.not_ = not relation.not_

        other_declarations_n = 0
        agreement_n = 0
        disagreement_n = 0

        for other_declarator in other_declarators:
            if other_declarator == declarator:
                continue

            their_declarations = set(self._kb.query_declarations(other_declarator))
            other_declarations_n += len(their_declarations)
            agreement_n += len(their_declarations & our_declarations)
            disagreement_n += len(their_declarations & our_declarations_adversary)
        
        return ((agreement_n - disagreement_n) / other_declarations_n) if other_declarations_n > 0 else 0
