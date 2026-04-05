import requests
import pandas as pd
import time


##############################
# PUBCHEM
##############################

def pubchem_data(nome):

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome}/property/MolecularFormula,ExactMass,MolecularWeight,InChIKey,CanonicalSMILES/JSON"

    r = requests.get(url)

    if r.status_code != 200:
        return {}

    props = r.json()["PropertyTable"]["Properties"][0]

    return props


##############################
# CHEBI
##############################

def buscar_chebi(nome):

    url = f"https://www.ebi.ac.uk/ols4/api/search?q={nome}&ontology=chebi"

    r = requests.get(url).json()

    docs = r["response"]["docs"]

    if docs:
        return docs[0]["obo_id"]

    return None


def obter_classificacao_chebi(chebi_id):

    chebi_formatado = chebi_id.replace(":", "_")

    url = f"https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F{chebi_formatado}"

    r = requests.get(url)

    if r.status_code != 200:
        return {}

    dados = r.json()

    classes = []

    if "is_a" in dados:

        for item in dados["is_a"]:

            if "label" in item:

                classes.append(item["label"])

    classificacao = {}

    if len(classes) >= 1:
        classificacao["Subclass"] = classes[0]

    if len(classes) >= 2:
        classificacao["Class"] = classes[1]

    if len(classes) >= 3:
        classificacao["Superclass"] = classes[2]

    return classificacao


##############################
# LOTUS (Natural product)
##############################

def lotus_taxonomia(nome):

    url = f"https://lotus.naturalproducts.net/api/search/simple?query={nome}"

    r = requests.get(url)

    if r.status_code != 200:
        return {}

    dados = r.json()

    if len(dados) == 0:
        return {}

    org = dados[0]

    return {
        "Kingdom": org.get("organism_taxonomy_kingdom"),
        "Family": org.get("organism_taxonomy_family"),
        "Genus": org.get("organism_taxonomy_genus"),
        "Species": org.get("organism_taxonomy_species"),
        "Natural_product": True
    }


##############################
# CLASSYFIRE
##############################

def classyfire_classification(inchikey):

    url = f"https://gnps-structure.ucsd.edu/classyfire?inchikey={inchikey}"

    r = requests.get(url)

    if r.status_code != 200:
        return {}

    data = r.json()

    return {
        "Chemical_Kingdom": data.get("kingdom", {}).get("name"),
        "Chemical_Superclass": data.get("superclass", {}).get("name"),
        "Chemical_Class": data.get("class", {}).get("name"),
        "Chemical_Subclass": data.get("subclass", {}).get("name")
    }


##############################
# HMDB (human metabolite)
##############################

def hmdb_check(nome):

    url = f"https://hmdb.ca/unearth/q?query={nome}&searcher=metabolites"

    r = requests.get(url)

    if nome.lower() in r.text.lower():
        return {"Human_metabolite": True}

    return {"Human_metabolite": False}


##############################
# FOODDB
##############################

def foodb_check(nome):

    url = f"https://foodb.ca/unearth/q?query={nome}&searcher=compounds"

    r = requests.get(url)

    if nome.lower() in r.text.lower():
        return {"Food_component": True}

    return {"Food_component": False}


##############################
# PIPELINE PRINCIPAL
##############################

def enrich_compound(nome):

    resultado = {"Compound": nome}

    try:

        pubchem = pubchem_data(nome)

        resultado.update(pubchem)

        inchikey = pubchem.get("InChIKey")

        if inchikey:

            classy = classyfire_classification(inchikey)

            resultado.update(classy)

    except:
        pass


    try:

        chebi_id = buscar_chebi(nome)

        if chebi_id:

            resultado["CHEBI_ID"] = chebi_id

            chebi_class = obter_classificacao_chebi(chebi_id)

            resultado.update(chebi_class)

    except:
        pass


    try:

        lotus = lotus_taxonomia(nome)

        resultado.update(lotus)

    except:
        pass


    try:

        hmdb = hmdb_check(nome)

        resultado.update(hmdb)

    except:
        pass


    try:

        foodb = foodb_check(nome)

        resultado.update(foodb)

    except:
        pass


    time.sleep(1)

    return resultado


##############################
# USO COM DATAFRAME
##############################

def enrich_dataframe(df):

    resultados = []

    for compound in df["Compound"]:

        print("Consultando:", compound)

        enriched = enrich_compound(compound)

        resultados.append(enriched)

    return pd.DataFrame(resultados)


##############################
# EXEMPLO
##############################

df = pd.DataFrame({

    "Compound": [
        "caffeine",
        "quercetin",
        "glucose"
    ]

})

df_enriched = enrich_dataframe(df)

print(df_enriched)