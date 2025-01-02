import os
from transformers import AutoTokenizer
import requests
import ES_Con
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import logging


API_TOKEN_IBM = os.environ["API_TOKEN_IBM"]
PROJECT_ID_IBM = os.environ["PROJECT_ID_IBM"]
ES= ES_Con.ES_connector()


def dghi_ibm_cloud(text, query):
    prompt = f"You are a helpful Q&A assistant. Your task is to answer this question: {query}. Use only the information from the text ###{text}###. Provide answer strictly in HTML format."
    # Create the authenticator.
    authenticator = IAMAuthenticator(API_TOKEN_IBM)
    # print(authenticator)
    # Construct the service instance.
    service = "Bearer "
    service += authenticator.token_manager.get_token()
    # print("service : ",service)
    # Use 'service' to invoke operations.

    url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    print('---------- prompt ----------', prompt)
    body = {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 2800,
            "stop_sequences": [],
            "repetition_penalty": 1
        },
        "model_id": "mistralai/mixtral-8x7b-instruct-v01",
        "project_id": PROJECT_ID_IBM,
        "moderations": {
            "hap": {
                "input": {
                    "enabled": True,
                    "threshold": 0.5,
                    "mask": {
                        "remove_entity_value": True
                    }
                },
                "output": {
                    "enabled": True,
                    "threshold": 0.5,
                    "mask": {
                        "remove_entity_value": True
                    }
                }
            }
        }
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": service
    }
    response = requests.post(
        url,
        headers=headers,
        json=body
    )
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    data = response.json()
    print(data)
    generated_text=data['results'][0]['generated_text']
    if not generated_text: 
        warnings = data['system']['warnings']
        if warnings:  
            warning_msg = warnings[0]['message']  
            return warning_msg
        else:
            return "No warnings found."
    else:
        return generated_text
    
def dghi_search_documents_gpt(query_text, user_name, model_type):
    hits = ES.DGHI_Search_Docs_gpt(query_text, user_name)
    print("hits ============> ",hits)
    filelist = []
    search_results = []
    model_text=""
    for hit in hits:
        score = hit["_score"]
        filename = hit["_source"].get("fileName", "")
        if filename not in filelist:
            file_id = hit["_source"].get("fId", "")
            filelist.append(filename)
    
            model_text += hit["_source"].get("text", "")
            search_results.append({"filename": filename, "fId": file_id,"score":score})
    if not search_results:
        return [{"text": "I am unable to provide answer based on the information i have .."}]
    
    if model_type == "mistral":
        # model_answer = using_mistral(query_text,combined_text,lst)
        print("text_from_elastic :----->",model_text)
        model_answer = dghi_ibm_cloud(model_text, query_text)

    search_results.insert(0,{"text":model_answer})
    return search_results


def dghi_Data_By_FID(fid,query,model_type):
    hits=ES.DGHI_Data_By_FID_ES(fid,query)
    try:
        text=hits[0]["_source"].get("text","")
    except Exception as e:
        return [{"text":"file is not ready for querying"}]
    
    logging.warning(f"combined_text --> {text}")
    if model_type == "mistral":
        # model_answer = using_mistral(query,combined_text, tables)
        model_answer = dghi_ibm_cloud(text, query)
    
    else:
        outres = f"model type not match :: {model_type}, modeltype :: ['mistral','phi3']"
        print(outres)
        return outres
    
    logging.warning(f"model_answer --> {model_answer}")
    return [{"text":model_answer}]



    
# rs = dghi_search_documents_gpt("BIT DETAILS AND THEIR CORRESPONDING INTERVAL ", "user1" , "mistral")
# print(rs)