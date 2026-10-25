"""Find licensed Xtream catalog titles for an LG Kodi launch search request."""
import re
import unicodedata


def _normal(s):
    x=unicodedata.normalize('NFKD',str(s or '').translate(str.maketrans({'ł':'l','Ł':'L','ø':'o','Ø':'O'})))
    x=''.join(c for c in x if not unicodedata.combining(c))
    return re.sub(r'\s+',' ', re.sub(r'[^a-z0-9]+',' ',x.casefold())).strip()


def find_matches(catalog,term,limit=24):
    raw=str(term or '').strip()
    if not raw or len(raw)>120:
        return []
    query=_normal(raw)
    if len(query)<2:return []
    tokens=query.split()
    matches=[]
    for media in ('movie','series'):
        for tmdb,entry in (catalog.get(media) or {}).items():
            try:
                name=str(entry[2] if media=='movie' else entry[1])
                norm=_normal(name)
                simplified=re.sub(r'^(en|pl|eng|pol|nf|netflix)\s+','',norm)
                words=simplified.split()
                if not all(t in simplified for t in tokens):continue
                score=4 if simplified==query else 3 if simplified.startswith(query) else 2 if ' '+query in simplified else 1
                score+=(1 if words and words[0]==tokens[0] else 0)
                matches.append((score,media,str(tmdb),name))
            except (IndexError,TypeError):continue
    matches.sort(key=lambda m:(-m[0],len(m[3]),m[3].casefold()))
    return [(media,tmdb,name) for score,media,tmdb,name in matches[:max(0,min(50,int(limit)))]]