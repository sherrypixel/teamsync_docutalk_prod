from elasticsearch import Elasticsearch
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# python -m nltk.downloader stopwords punkt_tab

ES_HOST = os.environ["ES_HOST"]
ES_PORT = int(os.environ["ES_PORT"])
ELASTIC_PASSWORD = os.environ["ELASTIC_PASSWORD"]
ELASTIC_USER = os.environ["ELASTIC_USER"]


class ES_connector:
    def __init__(self) -> None:
        self.es_client = None
        self.Connect()

    def Connect(self):
        self.es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT, 'scheme': 'http'}],basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
        es_version = self.es.info()['version']['number']
        try:
            if es_version == "8.17.0":
                self.model_id = ".elser_model_2_linux-x86_64_search"
            else:
                self.model_id = ".elser_model_2"
        except Exception as e :
            print(f"elser model incompatibility with elastic version")
            self.model_id=".elser_model_2_linux-x86_64_search"

    def Query_Type_search(self,text, index_name="query_type_check"):
        ''' Search Query For Type Check --> (Document/Image) '''
        response = self.es.search(
            index=index_name,
            size=3,
            query={
                "sparse_vector": {
                    "field": "type_detail",
                    "inference_id": self.model_id,
                    "query": text
                    }
                }
        )
        return response["hits"]["hits"]

    def Image_Query_search(self, text, username,path,index_name="object_det"):
        ''' Search Query For Image Search in Teamsync '''
        response = self.es.search(
            index=index_name,
            query={
                "bool": {
                    "must": [
                        {"match_phrase": {"username": username}},
                        {"match_phrase_prefix":{"path":path}}],

                    "should": [
                        {"sparse_vector": {
                            "field": "descr_embedding",
                            "inference_id": self.model_id,
                            "query": text
                            }
                        }
                        ]
                    }
                }
            )
        return response["hits"]["hits"]
    
    def Audio_Query_search(self,text,username,path, index_name="audio_text"):
        ''' Search Query For Image Search in Teamsync '''
        response = self.es.search(
            index=index_name,
            query={
                "bool": {
                    "must": [
                        {"match_phrase": {"username": username}},
                        {"match_phrase_prefix":{"path":path}}],
                    "should": [
                        {"sparse_vector": {
                            "field": "audio_detail_embed",
                            "inference_id": self.model_id,
                            "query": text
                            }
                        }
                        ]
                    }
                }
            )
        return response["hits"]["hits"]
    
    def Search_Docs(self,text,username,path):
        response = self.es.search(
        index="teamsyncfirstn",
        body={
            "query": {
                "bool": {
                "must": [
                    {
                    "match": {
                        "username": username
                    }
                    },
                    {
                    "match_phrase_prefix": {
                        "path": path
                    }
                    },
                    {
                    "bool": {
                        "must": [
                        {
                            "match": {
                            "text": text
                            }
                        },
                        {
                            "sparse_vector": {
                                "field": "text_embedding",
                                "inference_id": self.model_id,
                                "query": text
                                            }
                        }
                        ]
                    }
                    }
                ]
                }
            }
        }
        )
            
        return response["hits"]["hits"]



    def Search_Docs_gpt(self, query, username,path):
        response = self.es.search(
            index="teamsyncfirstn",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"username": username}},# Filter by username
                            {"match_phrase_prefix": {"path": path}}, 
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "sparse_vector": {
                                                "field": "text_embedding",
                                                "inference_id": self.model_id,
                                                "query": query
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "text": query  # Match exact phrase in the text field
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                "_source": [
                    "text", "pageNo", "fId", "username", "tables", "fileName"
                ]  
            }
        )
        return response['hits']['hits']

    #
    def Data_By_FID_ES(self, f_id, query):
        response = self.es.search(
            index="teamsyncfirstn",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"fId": f_id}},  # Filter by fid
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "sparse_vector": {
                                                "field": "text_embedding",
                                                "inference_id": self.model_id,
                                                "query": query
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        )

        if response['hits']['hits']:
            return response['hits']['hits']

    def Data_By_pageno(self,page_no, fid):
        match = self.es.search(
            index='teamsyncfirstn',
            body={
                "size": 1,
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"pageNo": page_no}},
                            {"match": {"fId": fid}}
                        ]
                    }
                },
                "script_fields": {
                    "text": {
                        "script": "params['_source']['text']"
                    }
                }
            }
        )
        if match['hits']['hits']:
            details = match['hits']['hits']
            return details[0]["fields"]
    def search_docs_faq(self,query):
        response = self.es.search(
            index="teamsyncfaq",
            body={
                "size": 3,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "sparse_vector": {
                                    "field": "combined_text_embedding",
                                    "inference_id": self.model_id,
                                    "query": query
                                            }
                            },
                            {
                                "match_phrase": {
                                    "text": query
                                }
                            }
                        ]
                    }
                },
                "_source": ["title", "content","score"] 
            },
        )
        return response['hits']['hits']
