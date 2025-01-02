from elasticsearch import Elasticsearch
import os


ES_HOST = os.environ["ES_HOST"]
ES_PORT = int(os.environ["ES_PORT"])
ELASTIC_PASSWORD =os.environ["ELASTIC_PASSWORD"]
ELASTIC_USER = os.environ["ELASTIC_USER"]


class ES_connector:
    def __init__(self) -> None:
        self.es_client = None
        self.Connect()

    def Connect(self):
        self.es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT, 'scheme': 'http'}],basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
        es_version = self.es.info()['version']['number']
        if es_version == "8.17.0":
            self.model_id = ".elser_model_2_linux-x86_64_search"
        else:
            self.model_id = ".elser_model_2"

    def Query_Type_search(self,text, index_name="query_type_check"):
        ''' Search Query For Type Check --> (Document/Image) '''
        response = self.es.search(
            index=index_name,
            size=3,
            query={
                "text_expansion": {
                    "type_detail": {
                        "model_id": self.model_id,
                        "model_text": text,
                    }
                }
            },
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
                       
                        {
                            "text_expansion": {
                                "descr_embedding": {
                                    "model_id": self.model_id,
                                    "model_text": text
                                }
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
                        {
                            "text_expansion": {
                                "audio_detail_embed": {
                                    "model_id": self.model_id,
                                    "model_text": text
                                }
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
                            "text_expansion": {
                            "text_embedding": {
                                "model_id": self.model_id,
                                "model_text": text
                            }
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



    def Search_Docs_gpt(self, query, username):
        response = self.es.search(
            index="teamsyncfirstn",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"username": username}},  # Filter by username
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "text_expansion": {
                                                "text_embedding": {
                                                    "model_text": query,
                                                    "model_id": self.model_id  # ELSER model for embeddings
                                                }
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
                ]  # Fields to include in the response
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
                                            "text_expansion": {
                                                "text_embedding": {
                                                    "model_text": query,
                                                    "model_id": self.model_id,
                                                }
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
                                "text_expansion": {
                                    "combined_text_embedding": {
                                        "model_text": query,
                                        "model_id": self.model_id,
                                    }
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

    

# ________________________________________________________________________________________________________

    def DGHI_Search_Docs_gpt(self, query, username):
            print("query recieved by elastic", query,username)
            response = self.es.search(
                index="dghi_teamsync",
                body={
                    "size": 3,
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"username": username}},  # Filter by username
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "text_expansion": {
                                                    "text_embedding": {
                                                        "model_text": query,
                                                        "model_id": self.model_id  # ELSER model for embeddings
                                                    }
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
                        "text", "fId", "username", "fileName"
                    ]  # Fields to include in the response
                }
            )
            return response['hits']['hits']

        #
    def DGHI_Data_By_FID_ES(self, f_id, query):
            response = self.es.search(
                index="dghi_teamsync",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"fId": f_id}},  # Filter by fid
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "text_expansion": {
                                                    "text_embedding": {
                                                        "model_text": query,
                                                        "model_id": self.model_id,
                                                    }
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
        
# _______________________________________________________________________________________________________
