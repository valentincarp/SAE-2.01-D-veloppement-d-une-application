"""Cache simple en mémoire avec durée de vie."""
import time
from functools import wraps

class Cache:
    def __init__(self, duree_vie_seconde=300):
        self._duree = duree_vie_seconde
        self._entrees = {} # {cle: (valeur, horodatage)}

    def get(self, cle):
        """Retourne la valeur si présente et pas expirée, None sinon."""
        if cle not in self._entrees:
            return None
        valeur, horodatage = self._entrees[cle]
        if time.time() - horodatage > self._duree:
            # Entrée expirée, on la retire
            del self._entrees[cle]
            return None
        return valeur
    
    def set(self, cle, valeur):
        self._entrees[cle] = (valeur, time.time())

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