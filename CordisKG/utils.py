import os
import time
import spacy
import platform
import functools
import operator
import CordisKG.config
from suffix_trees import STree
from string import punctuation
from difflib import get_close_matches
from keybert import KeyBERT
from collections import OrderedDict
from stempel import StempelStemmer
from nltk.stem import SnowballStemmer


# Initialize all required stemmers once.
stemmers = {
    'english': SnowballStemmer('english'),
    'french': SnowballStemmer('french'),
    'spanish': SnowballStemmer('spanish'),
    'portuguese': SnowballStemmer('portuguese'),
    'polish': StempelStemmer.default()
}


# Augment the stopwords set.
stop_words = set(stopwords.words('english')).union([ 
    'don','didn', 'doesn', 'aren', 'ain', 'hadn',
    'hasn', 'mightn', 'mustn', 'couldn', 'shouldn',
    'dont', 'didnt', 'doesnt', 'arent', 'aint',
    'hadnt', 'hasnt', 'may', 'mightve', 'couldnt',
    'shouldnt', 'shouldnot', 'shouldntve', 'mustnt',
    'would', 'woulda', 'wouldany', 'wouldnot', 'woudnt',
    'wouldve', 'must', 'could', 'can', 'have', 'has',
    'do', 'does', 'did', 'are', 'is', 'ive', 'cant', 'thats',
    'isnt', 'youre', 'wont', 'from', 'subject', 'hes', 'etc',
    'edu', 'com', 'org', 've', 'll', 'd', 're', 't', 's'])


def counter(func):
    """
    Print the elapsed system time in seconds, 
    if only the debug flag is set to True.
    """
    if not CordisKG.config.debug:
        return func
    @functools.wraps(func)
    def wrapper_counter(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f'{func.__name__}: {end_time - start_time} secs')
        return result
    return wrapper_counter


def load_models():
    """
    Function which loads the english NLP model, and the Keybert model.
    This needs to run once since all models need a few seconds to load.
    """
    return (
        spacy.load('en_core_web_sm'),
        KeyBERT('distiluse-base-multilingual-cased-v2')
    )


def preprocess(lis, language):
    """
    Function which applies stemming to a 
    lowercase version of each string of the list,
    which has all punctuation removed.
    """
    return list(map(stemmers[language].stem, 
           map(lambda s: s.translate(str.maketrans('', '', punctuation)),
           map(str.lower, lis))))


def postprocess(lis):
    """
    Function which removes punctuation, and trims any whitespace 
    from a list of strings (extracted names). '.' is kept
    and '-' is replaced with ' '.
    """
    custom_punc = punctuation.replace('.', '').replace('-', '')
    return list(map(lambda s: ' '.join(s.replace('-', ' ').split()), 
           map(lambda s: s.translate(str.maketrans('', '', custom_punc)), lis)))



def rreplace(s, old, new, occurrence):
    """
    Function which replaces a string occurence
    in a string from the end of the string.
    """
    return new.join(s.rsplit(old, occurrence))


def clear_screen():
    """
    Function which clears the output of the terminal 
    by using the platform specific system call.
    """
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear') # Linux/OS X.
    return


def flatten_list(l):
    """
    Function which flattens a list of lists to a list.
    """
    return functools.reduce(operator.iconcat, l, [])


def find_keys_in_text(text, keyphrases):
    """
    Function that exactly matches each keyphrase from 
    an auxiliary list of keyphrases and returns the 
    matched keyphrases.
    """
    # Lowercase all keyphrases and the text below.
    keyphrases = list(map(str.lower, keyphrases))

    # Return keyphrases that exact match in text.
    return [
        keyphrase for keyphrase in keyphrases
        if keyphrase in text.lower()
    ]

def remove_common_strings_from_list(keyphrases, cutoff = 0.7):
    """
    Function which removes strings from a list that share a common substring,
    and includes the largest common substring between them in the final list.
    This is achieved by grouping similar strings using get_close_matches()
    and then by extracting their largest common substring using a suffix tree.
    """
    results = []

    # Lowercase all keyphrases
    keyphrases = list(map(str.lower, keyphrases))

    for keyphrase in keyphrases:
        close_matches = get_close_matches(
            keyphrase, keyphrases, 
            n = len(keyphrases), 
            cutoff = cutoff
        )
        if len(close_matches) > 1:
           # Create a suffix tree based on the list of highly similar keyphrases
           # in order to calculate the largest common substring.
           st = STree.STree([keyphrase] + close_matches)
           largest_common_string = st.lcs().strip() # Strip extra whitespace around the substring.
           
           # Remove incomplete terms.
           largest_common_string = ' '.join(
               term for term in largest_common_string.split()
               if len(term) > 2
           ) 
           # If the string is not empty, append it.
           if largest_common_string:
               results.append(largest_common_string)

        else: # unique keyphrase case
            results.append(keyphrase)
    
    # Remove duplicate values using ordered dict.
    # and return the result list.
    return list(OrderedDict.fromkeys(results).keys())


def get_diff_of_keys(source, target):
    """
    Function which returns a list of keyphrases, 
    that are included in source but not in target.
    This done through partial match of their keyphrases.
    Each keyphrase is lowercase and split in a set of terms
    to enable this partial match.
    """
    return [
        key_src for key_src in source 
        if not any(
            set(key_src.lower().split())
            & set(key_tar.lower().split())
            for key_tar in target)
    ]
