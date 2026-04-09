import requests
import time
import xml.etree.ElementTree as ET


##############################
# PUBCHEM
##############################

def pubchem_data(nome):

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome}/property/MolecularFormula,ExactMass,MolecularWeight,InChIKey,CanonicalSMILES,CID/JSON"

    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        return {}

    props = r.json()["PropertyTable"]["Properties"][0]

    try:
        synonyms_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{props.get('CID')}/synonyms/JSON"
        syn_r = requests.get(synonyms_url, timeout=10)

        if syn_r.status_code == 200:
            syn_data = syn_r.json()

            synonyms = syn_data["InformationList"]["Information"][0].get("Synonym", [])

            props["Synonyms"] = synonyms[:5]

    except:
        pass

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

    return {

        "Subclass": classes[0] if len(classes) >= 1 else None,
        "Class": classes[1] if len(classes) >= 2 else None,
        "Superclass": classes[2] if len(classes) >= 3 else None,
        "role": dados.get("definition", [None])[0],
        "ontologia": "chebi"
    }


##############################
# LOTUS
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
        "Species": org.get("organism_taxonomy_species")
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
# HMDB
##############################

def hmdb_check(nome):

    url = f"https://hmdb.ca/unearth/q?query={nome}&searcher=metabolites"

    r = requests.get(url)

    return {"Human_metabolite": nome.lower() in r.text.lower()}


##############################
# CHEMSPIDER
##############################

def chemspider_search(nome):

    url = f"https://www.chemspider.com/api/search.asmx/FindCompoundsByName?query={nome}"

    r = requests.get(url)

    if r.status_code != 200:

        return {}

    root = ET.fromstring(r.text)

    csid = root.find('.//{http://www.chemspider.com/}CSID')

    if csid is not None:

        return {"ChemSpider_ID": csid.text}

    return {}


##############################
# FOODB
##############################

def foodb_check(nome):

    url = f"https://foodb.ca/unearth/q?query={nome}&searcher=compounds"

    r = requests.get(url)

    return {"Food_component": nome.lower() in r.text.lower()}