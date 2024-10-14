from fastapi import FastAPI,HTTPException
import uvicorn
import os
import doc_process

service_port = int(os.environ["Service_Port"])

app = FastAPI()



@app.get("/")
async def root():
    return {"message": "teamsync chatbot Api"}



@app.post("/claros/facerec/teamsync/search_documents")
async def search_documents(text,username):
    if not text:
        raise HTTPException(status_code=400, detail="Query parameter 'text' is required.")
    result_ = doc_process.ES.Query_Type_search(text)
    if result_:
        if result_[0]["_source"]["type"] == "Image":
            out_res = doc_process.ES.Image_Query_search(text)
            search_out = []
            for i in out_res:
                search_out.append({"fId": i["_source"]["fId"], "score": i["_score"]})
            return search_out
    result = doc_process.search_documents(text,username)
    return result

@app.post("/claros/facerec/gptforall/search_documents")
async def search_documents(text,username,modeltype):
    print(text,username,modeltype)
    if not text:
        raise HTTPException(status_code=400, detail="Query parameter 'text' is required.")
    result = doc_process.search_documents_gpt(text,username,modeltype)
    print("Done...")
    return result

@app.post("/claros/facerec/gptforall/search_by_fid")
async def search_by_fid(fid,query,modeltype):
    print(fid)
    if not fid:
        raise HTTPException(status_code=400, detail="File id required")
    result = doc_process.Data_By_FID(fid,query,modeltype)
    print("result")
    return result
@app.post("/claros/facerec/gptforall/search_faq_documents)
async def search_documents_faq(query):
    if not query:
        raise HTTPException(status_code=400,detail="query required")
    result=doc_process.search_faq_documents(query)
    return result
    

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=service_port)
