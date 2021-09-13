
def partial_match(assigned, extracted):
    """
    Computes the average partial match 
    between two lists of keywords.
    The partial precision is defined as the number 
    of correctly partially matched tokens
    Arguments
    ---------
    assigned  : A list of manually assigned keywords,
                (order doesn't matter in the list).
    extracted : A list of extracted keywords,
                (order matters in the list).
    Returned value
    --------------
              : double
    """
    # Assigned should always contain the shorter list, while extracted the longest,
    # as to avoid counting partial matches more times than necessary.
    assigned, extracted = min((assigned, extracted), key = len), max((assigned, extracted), key = len)
    assigned_sets = [set(keyword.split()) for keyword in assigned]
    extracted_sets = [set(keyword.split()) for keyword in extracted]

    return sum(
        1.0 for i in assigned_sets  
            if any(True for j in extracted_sets if i & j))
