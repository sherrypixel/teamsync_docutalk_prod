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
    path: str = Header(..., description="Path provided in the header")):
    if not text:
        print("Query parameter 'text' is required.")
    logging.warning(f"recieved path and username: {path} {username} {text}")
    path="T"+path.replace("/","_")
    username=username.replace("@","_")
    logging.warning(f"modified path and username is :{path},{username}")
    
    process_text=text.lower().split(",")
    if "audio" in process_text[0] or "video" in process_text[0]:
        out_res = doc_process.ES.Audio_Query_search(process_text[-1],username,path,"audio_text")
        search_out = []
        for i in out_res:
            for j in i["_source"]["details"]:
                time = j["start"]
                Text_ = j["text"].lower()
                if process_text[-1] in Text_:
                    search_out.append({"fId":i["_source"]["fid"], "score": i["_score"],"time":time})
                    break
                if Text_ in process_text[-1]:
                    search_out.append({"fId":i["_source"]["fid"], "score": i["_score"],"time":time})
                    break
        logging.warning(f"Search Audio/video: {search_out}")
        return search_out
    result_ = doc_process.ES.Query_Type_search(text)
    if result_:
        if result_[0]["_source"]["type"] == "Image":
            out_res = doc_process.ES.Image_Query_search(text,username,path)
            search_out = []
            for i in out_res:
                search_out.append({"fId": i["_source"]["fId"], "score": i["_score"]})
            return search_out
        
    result = doc_process.search_documents(text,username,path)
    return result


    
@app.post("/teamsync/nlp/docutalk/search_documents")
async def search_documents(text,username,modeltype):
    username=username.replace("@","_")
    logging.warning(f"{text},{username},{modeltype}")
    if not text:
        raise HTTPException(status_code=400, detail="Query parameter 'text' is required.")
    result = doc_process.search_documents_gpt(text,username,modeltype)
    print("Done...")
    return result

@app.post("/teamsync/nlp/docutalk/search_by_fid")
async def search_by_fid(fid,query,modeltype):
    print(fid)
    if not fid:
        raise HTTPException(status_code=400, detail="File id required")
    result = doc_process.Data_By_FID(fid,query,modeltype)
    print("result")
    return result
@app.post("/teamsync/nlp/dms/search_faq_documents")
async def search_documents_faq(query):
    if not query:
        raise HTTPException(status_code=400,detail="query required")
    result=doc_process.search_faq_documents(query)
    return result
    

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=SERVICE_PORT)
