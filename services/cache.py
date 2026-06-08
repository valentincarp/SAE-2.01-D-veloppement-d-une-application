"""Cache simple en mémoire avec durée de vie."""
import time
from functools import wraps

def avec_cache(duree_vie_seconde=300):
    """Décorateur : mémorise le résultat d'une méthode pendant N secondes."""
    def decorateur(methode):
        memoire = {} # {cle: (valeur, horodatage)}

        @wraps(methode)
        def enveloppe(self, *args):
            cle = (methode.__name__,) + args
            if cle in memoire:
                valeur, horodatage = memoire[cle]
                if time.time() - horodatage <= duree_vie_seconde:
                    return valeur
            resultat = methode(self, *args)
            memoire[cle] = (resultat, time.time())
            return resultat
        return enveloppe
    return decorateur