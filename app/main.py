from fastapi import FastAPI,HTTPException, Header, Query
import uvicorn
import os
import doc_process

import logging

SERVICE_PORT = int(os.environ["SERVICE_PORT"])

app = FastAPI()



@app.get("/")
async def root():
    return {"message": "teamsync chatbot Api"}



@app.post("/teamsync/nlp/dms/search_documents")
async def search_documents( text: str = Query(..., description="Search text query"),
    username: str = Query(..., description="User performing the search"),
    path: str = Header(..., description="Path provided in the header"),
    fileType: str = Query(..., description="type of search user want")):
    if not text:
        print("Query parameter 'text' is required.")
    logging.warning(f"recieved path and username: {path} {username} {text}")
    path="T"+path.replace("/","_")
    username=username.replace("@","_")
    logging.warning(f"modified path and username is :{path},{username}")
   
    if fileType =='multimedia':
        out_res = doc_process.ES.Audio_Query_search(text,username,path,"audio_text")
        search_out = []
        for i in out_res:
            for j in i["_source"]["details"]:
                time = j["start"]
                Text_ = j["text"].lower()
                if text in Text_:
                    search_out.append({"fId":i["_source"]["fid"], "score": i["_score"],"time":time})
                    break
                if Text_ in text:
                    search_out.append({"fId":i["_source"]["fid"], "score": i["_score"],"time":time})
                    break
        logging.warning(f"Search Audio/video: {search_out}")
        return search_out
    if fileType == "image":
        out_res = doc_process.ES.Image_Query_search(text,username,path)
        search_out = []
        for i in out_res:
            if int(i["_score"]) >10:
                search_out.append({"fId": i["_source"]["fId"], "score": i["_score"]})
        return search_out
        
    result = doc_process.search_documents(text,username,path)
    return result

# ______________________________________________________________________________________________________

@app.post("/teamsync/nlp/docutalk/search_documents")
async def search_documents(text,username,modeltype,answerType,path='T_'):
    path="T"+path.replace("/","_") if not path.startswith("T_") else path
    username=username.replace("@","_")
    logging.warning(f"{text},{username},{modeltype}")
    if not text:
        raise HTTPException(status_code=400, detail="Query parameter 'text' is required.")
    
    else :
        result = doc_process.search_documents_gpt(text,username,modeltype,answerType,path)
    print("Done...")
    return result

@app.post("/teamsync/nlp/docutalk/search_by_fid")
# -----> usename lele java se
async def search_by_fid(fid,query,modeltype ):
    print(fid)
    if not fid:
        raise HTTPException(status_code=400, detail="File id required")
   
    else :
        result = doc_process.Data_By_FID(fid,query,modeltype)
    print("result")
    return result

# ________________________________________________________________________________________________________

@app.post("/teamsync/nlp/dms/search_faq_documents")
async def search_documents_faq(query):
    if not query:
        raise HTTPException(status_code=400,detail="query required")
    result=doc_process.search_faq_document(query)
    return result
    

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=SERVICE_PORT)
