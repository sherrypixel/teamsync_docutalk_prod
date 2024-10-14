import os
from transformers import AutoTokenizer
import requests
import ES_Con
import google.generativeai as genai
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


API_TOKEN = os.environ["API_TOKEN"]
API_TOKEN_GEMINI = os.environ["API_TOKEN_GEMINI"]
API_TOKEN_IBM = os.environ["API_TOKEN_IBM"]
PROJECT_ID_IBM = os.environ["PROJECT_ID_IBM"]

genai.configure(api_key=API_TOKEN_GEMINI)

try:
    Mixtral_tokenizer = AutoTokenizer.from_pretrained("app/model/Mixtral-8x7B-Instruct-v0.1")
    print("Custom model load...2")
    Phi_tokenizer = AutoTokenizer.from_pretrained("app/model/Phi-3-mini-4k-instruct")
    print("Custom model load...3")
except:
    from huggingface_hub import login
    login(API_TOKEN)
    Mixtral_tokenizer = AutoTokenizer.from_pretrained("mistralai/Mixtral-8x7B-Instruct-v0.1")
    Phi_tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")

ES= ES_Con.ES_connector()

def search_documents(query, user_name):
    """
    Search documents in Elasticsearch based on the provided query.
    """
    hits = ES.Search_Docs(query)
    search_results = []
    if not hits:
        return []
    max_score = hits[0]["_score"]
    file_list = []
    for hit in hits:
        score = hit["_score"]
        relative_score = (score / max_score) * 100
        username = hit["_source"].get("username", "")
        fileid = hit["_source"].get("fId")
        if (relative_score > 60) and (username == user_name) and (fileid not in file_list):
            file_list.append(fileid)
            search_results.append({"fId": fileid, "score": score})
    return search_results

def search_documents_gpt(query_text, user_name, model_type):
    hits = ES.Search_Docs_gpt(query_text, user_name)
    filelist = []
    search_results = []
    combined_text=''
    lst=[]
    for hit in hits:
        score = hit["_score"]
        if score > 3:
            filename = hit["_source"].get("fileName", "")
            if filename not in filelist:
                file_id = hit["_source"].get("fId", "")
                text = hit["_source"].get("text", "")
                page_no = hit["_source"].get("pageNo", "")
                base,extension=os.path.splitext(filename)
                extension=str.upper(extension)
                if extension!='.CSV':
                    combined_text = combined_text+ above_and_below_pagedata(text, int(page_no), file_id)+"\n"
                table_data = hit["_source"].get("tables", "")
                lst.append(table_data)
                search_results.append({"filename": filename, "fId": file_id, "page_no": page_no})
    if not search_results:
        return [{"text": "I am unable to provide answer based on the information i have .."}]
    
    if model_type == "mistral":
        # model_answer = using_mistral(query_text,combined_text,lst)
        model_answer = ibm_cloud(combined_text, query_text)
    # elif model_type == "phi3":
    #     model_answer = using_phi3(query_text,text,lst)
    #     try:
    #         model_answer = extract_text_after_assistant(model_answer)
    #         model_answer = truncate_after_text(model_answer)
    #     except Exception as e:
    #         model_answer =f"i am unable to answer Reason{e}"

    elif model_type == 'phi3': # gemini
        model_answer = using_gemini(combined_text, query_text)

    else:
        out_res = f"model type not match :: {model_type}, model_type :: ['mistral','phi3']"
        print(out_res)
        return out_res
    search_results.insert(0,{"text":model_answer})
    
    return search_results

def above_and_below_pagedata(text, page_no, file_id):
    page_no_below = page_no + 1
    below_page_text = ES.Data_By_pageno(page_no_below, file_id)

    if below_page_text is not None:
        below_page_text = below_page_text['text'][0]
    else:
        below_page_text = ''
    if (page_no != 1):
        page_no_above = page_no - 1
        above_page_text = ES.Data_By_pageno(page_no_above, file_id)

        if above_page_text is not None:
            above_page_text = above_page_text['text'][0]
        else:
            above_page_text = ''
        return above_page_text + text + below_page_text

    else:
        page_no_above = page_no + 2
        below_page_text_2 = ES.Data_By_pageno(page_no_above, file_id)

        if below_page_text_2 is not None:
            below_page_text_2 = below_page_text_2['text'][0]
        else:
            below_page_text_2 = ''
        return text + below_page_text + below_page_text_2

def Data_By_FID(fid,query,model_type):
    hits=ES.Data_By_FID_ES(fid,query)
    text=hits[0]["_source"].get("text","")
    tables = hits[0]["_source"].get("tables", "")
    page_no=hits[0]["_source"].get("pageNo","")
    combined_text = above_and_below_pagedata(text, int(page_no),fid)
    if model_type == "mistral":
        # model_answer = using_mistral(query,combined_text, tables)
        model_answer = ibm_cloud(combined_text, query)
    # elif model_type == "phi3":
    #     model_answer = using_phi3(query,combined_text,tables)
    #     try:
    #         model_answer = extract_text_after_assistant(model_answer)
    #         model_answer = truncate_after_text(model_answer)
    #     except Exception as e:
    #         model_answer =f"i am unable to answer Reason{e}"

    elif model_type == 'phi3': # gemini
        model_answer = using_gemini(combined_text, query)
    else:
        outres = f"model type not match :: {model_type}, modeltype :: ['mistral','phi3']"
        print(outres)
        return outres

    return [{"text":model_answer}]

def truncate_text(text, max_tokens, model_name):
    tokenizer_truncate= Mixtral_tokenizer if model_name == "Mixtral" else Phi_tokenizer
    tokens = tokenizer_truncate.encode(text, add_special_tokens=False)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    truncated_text = tokenizer_truncate.decode(truncated_tokens, skip_special_tokens=True)
    return truncated_text

def query_mistral(payload):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    
    try:
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None

        data = response.json()
        generated_text = data[0]['generated_text']

        # Find the index of '[/INST]' to extract the actual answer
        prompt_index = generated_text.find('[/INST]')
        if prompt_index != -1:
            generated_text = generated_text[prompt_index + len('[/INST]'):].strip()

        return generated_text
    except requests.exceptions.RequestException as e:
        print("Request exception:", e)
        return None
    except ValueError as e:
        print("Value error:", e)
        return None

def using_mistral(query_text, text, tables):
    negResponse = "I'm unable to answer the question based on the information I have."
    prompt = f"[INST] Answer the following question based on the provided text: {query_text}. Only use the following information: {text}. If the answer is not present, reply with 'I'm unable to answer the question based on the information I have.Provide answer strictly in HTML format[/INST]"
    max_new_tokens = 2000
    max_token = 28000
    input_tokens = max_token - max_new_tokens
    model_name='mistralai/Mixtral-8x7B-Instruct-v0.1'
    prompt= truncate_text(prompt, input_tokens,model_name)
    
   
    data = query_mistral({"parameters": {"max_new_tokens": max_new_tokens}, "inputs": prompt})
    return data
def using_phi3(text,query_text,tables):
    max_new_tokens = 1000
    max_total_tokens = 4096
    max_input_tokens = max_total_tokens - max_new_tokens
    
    negResponse = "I'm unable to answer the question based on the Context Provided."
    prompt = f"""<|system|>
                 You have been provided with a question and context,find out the answer to the question only using the context information. If the answer to the question is not found within the context, return {negResponse} as the response.<|end|>
                 <|user|>
                 Question:{query_text}
                 Context:{text}
                 {tables}
                 <|end|>
                 <|assistant|>"""
    prompt=truncate_text(prompt,max_input_tokens,model_name="Phi-3")
    
    prompt_index=prompt.find("<|assistant|>")
    
    if prompt_index==-1:
        extra_text='<|end|>'
        prompt=prompt+"\n" +extra_text +"\n" +"<|assistant|>"
    
    data = query_phi3({"parameters":{"max_new_tokens":1000},"inputs": prompt})
    return data

def query_phi3(payload):
    API_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        data = response.json()
        generated_text = data[0]['generated_text']
        # Find the index of the first occurrence of '[/INST]'
        prompt_index = generated_text.find('[/INST]')
        # Extract the text after the prompt
        if prompt_index != -1:
            generated_text = generated_text[prompt_index + len('[/INST]'):]
        return generated_text
    except Exception as e:
        print("Error decoding response:", e)
        print("Response content:", response.content)
        return None

def extract_text_after_assistant(response_text):
    # Find the index of "Assistant:"
    assistant_index = response_text.find("<|assistant|>")
    if assistant_index != -1:
        # Extract the text after "Assistant:"
        truncated_answer = response_text[assistant_index + len("<|assistant|>"):]
        return truncated_answer.strip()  # Remove leading/trailing whitespaces
    else:
        return "I'm unable to answer the question based on the information I have"

def truncate_after_text(text):
    # Find the index of the delimiter
    end_index = text.find("<|end|>")
    if end_index != -1:
        # Truncate the string after the delimiter
        truncated_text = text[:end_index]
        return truncated_text.strip()  # Remove leading/trailing whitespaces
    return text

safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def get_gemini_response(text, prompt):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", safety_settings=safety_settings)
    response = model.generate_content([text, prompt])
    return response.text


def using_gemini(text, query_text):
    prompt = (
        f"You are a helpful Q&A assistant. Your task is to answer this question: {query_text}. Use only the information from the text. Provide answer strictly in HTML format."
    )
    return get_gemini_response(text, prompt)


def ibm_cloud(text, query):
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
    return data['results'][0]['generated_text']
def search_faq_document(query):
    hits=ES_Con.search_docs_faq(query):
    search_results = []
    
    for hit in hits:
        score = hit["_score"]
        if score > 3:
            content= hit["_source"].get("content", "")
            title = hit["_source"].get("title", "")
            
            
        search_results.append({"title": title, "content": content,"score":score})
    return search_results

