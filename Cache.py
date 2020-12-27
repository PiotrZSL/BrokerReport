import pickle

CACHE = {}

def saveCache(filename):
    if not filename:
        return
    try:
        with open(filename, "wb") as f:
            pickle.dump(CACHE, f)
    except:
        pass

def loadCache(filename):
    if not filename:
        return
    try:
        with open(filename, "rb") as f:
            CACHE = pickle.load(f)
    except:
        CACHE = {}
