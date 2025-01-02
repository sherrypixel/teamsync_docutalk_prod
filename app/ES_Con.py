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
        self.es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT, 'scheme': 'http'}],basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
        self.model_id = ".elser_model_2_linux-x86_64_search"

    def Query_Type_search(self, text, index_name="query_type_check"):
        ''' Search Query For Type Check --> (Document/Image) using RRF '''
        response = self.es.search(
            index=index_name,
            size=3,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            # Term-based retrieval with the text query
                            {
                                "standard": {
                                    "query": {
                                        "match": {
                                            "text": text  # Term-based search in the text field
                                        }
                                    }
                                }
                            },
                            # Vector-based retrieval using text expansion with model embeddings
                            {
                                "standard": {
                                    "query": {
                                        "text_expansion": {
                                            "type_detail": {
                                                "model_id": self.model_id,  # Model ID for embeddings
                                                "model_text": text  # Original query text
                                            }
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 3,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking fusion
                    }
                }
            }
        )

        return response["hits"]["hits"]

    def Image_Query_search(self, text, username, path, index_name="object_det"):
        response = self.es.search(
            index=index_name,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            # Term-based retrieval with filters for username and path
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "must": [
                                                {"match_phrase": {"username": username}},  # Filter by username
                                                {"match_phrase_prefix": {"path": path}}  # Filter by path prefix
                                            ]
                                        }
                                    }
                                }
                            },
                            # Vector-based retrieval using text expansion
                            {
                                "standard": {
                                    "query": {
                                        "sparse_vector": {
                                            "field": "descr_embedding",  # Vector embeddings field
                                            "inference_id": self.model_id,  # Model ID for embeddings
                                            "query": text  # Original query text
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 10,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking
                    }
                }
            }
        )

        # Return the hits if available
        return response["hits"]["hits"]

    def Audio_Query_search(self, text, username, path, index_name="audio_text"):
        response = self.es.search(
            index=index_name,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            # Term-based retrieval with filters for username and path
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "must": [
                                                {"match_phrase": {"username": username}},  # Filter by username
                                                {"match_phrase_prefix": {"path": path}}  # Filter by path prefix
                                            ]
                                        }
                                    }
                                }
                            },
                            # Vector-based retrieval using text expansion
                            {
                                "standard": {
                                    "query": {
                                        "sparse_vector": {
                                            "field": "audio_detail_embed",  # Vector embeddings field
                                            "inference_id": self.model_id,  # Model ID for embeddings
                                            "query": text  # Original query text
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 10,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking
                    }
                }
            }
        )
        # Return the hits if available
        return response["hits"]["hits"]

    def preprocess_term_query(self, query):
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(query.lower())
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        return " ".join(filtered_words)

    def Search_Docs(self,user_query,username,path,index_name="teamsyncfirstn"):
        # Generate term query by preprocessing the natural language query
        term_query = self.preprocess_term_query(user_query)

        # Vector query is the original query
        vector_query = user_query
        # Elasticsearch query using RRF (Reciprocal Rank Fusion)
        response = self.es.search(
        index=index_name,
        body={
            "retriever": {
                "rrf": {
                    "retrievers": [
                        # Standard keyword-based retrieval using term queries
                        {
                            "standard": {
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"username": username}},  # Match username
                                            {"match_phrase_prefix": {"path": path}},  # Path prefix matching
                                            {"match": {"text": term_query}}  # Text-based term query
                                        ]
                                    }
                                }
                            }
                        },
                        # Sparse vector-based retrieval for semantic search
                        {
                            "standard": {
                                "query": {
                                    "sparse_vector": {
                                        "field": "ml.tokens",  # Field for storing vector embeddings
                                        "inference_id": self.model_id,  # The inference model ID
                                        "query": vector_query  # The query text for semantic search
                                    }
                                }
                            }
                        }
                    ],
                    "rank_window_size": 5,  # Number of results to consider for ranking
                    "rank_constant": 1  # Weighting constant for ranking fusion
                    }
                }
            }
        )
        return response["hits"]["hits"]

    def Search_Docs_gpt(self, query, username, index_name="teamsyncfirstn"):
        # Preprocess the query for term-based retrieval
        term_query = self.preprocess_term_query(query)

        # Elasticsearch query using Reciprocal Rank Fusion (RRF)
        response = self.es.search(
            index=index_name,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "must": [
                                                {"match": {"username": username}}  # Filter by username
                                            ],
                                            "should": [
                                                {"match_phrase": {"text": term_query}}  # Term-based query
                                            ]
                                        }
                                    }
                                }
                            },
                            {
                                "standard": {
                                    "query": {
                                        "sparse_vector": {
                                            "field": "ml.tokens",  # Field storing vector embeddings
                                            "inference_id": self.model_id,  # Vector-based model ID
                                            "query": query  # Original query for semantic retrieval
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 5,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking
                    }
                },
                "_source": [
                    "text", "pageNo", "fId", "username", "tables", "fileName"
                ]
            }
        )
        return response['hits']['hits']

    def Data_By_FID_ES(self, f_id, query, index_name="teamsyncfirstn"):
        term_query = self.preprocess_term_query(query)
        response = self.es.search(
            index=index_name,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            # Term-based retrieval
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "must": [
                                                {"match": {"fId": f_id}},  # Filter by FID
                                            ],
                                            "should": [
                                                {"match_phrase": {"text": term_query}}  # Term-based query
                                            ]
                                        }
                                    }
                                }
                            },
                            # Vector-based retrieval using sparse_vector
                            {
                                "standard": {
                                    "query": {
                                        "sparse_vector": {
                                            "field": "ml.tokens",
                                            "inference_id": self.model_id,
                                            "query": query  # Original query text for semantic search
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 10,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking
                    }
                },
                "_source": [
                    "text", "pageNo", "fId", "username", "tables", "fileName"
                ]
            }
        )
        return response['hits']['hits']

    def Data_By_pageno(self,page_no, fid,index_name="teamsyncfirstn"):
        match = self.es.search(
            index=index_name,
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

    def search_docs_faq(self, query, index_name="teamsyncfaq"):
        response = self.es.search(
            index=index_name,
            body={
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            # Term-based retrieval using match_phrase
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "should": [
                                                {
                                                    "match_phrase": {
                                                        "text": query  # Phrase match for the query
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            # Vector-based retrieval using sparse_vector
                            {
                                "standard": {
                                    "query": {
                                        "sparse_vector": {
                                            "field": "ml.tokens",  # Field for vector embeddings
                                            "inference_id": self.model_id,  # Model ID for embeddings
                                            "query": query  # Original query text
                                        }
                                    }
                                }
                            }
                        ],
                        "rank_window_size": 10,  # Number of results to consider for ranking
                        "rank_constant": 1  # Weighting constant for ranking
                    }
                },
                "_source": ["title", "content", "score"]  # Fields to include in the response
            }
        )
        return response['hits']['hits']

    # ________________________________________________________________________________________________________

    def DGHI_Search_Docs_gpt(self, query, username):
        result =self.Search_Docs_gpt(query, username,index_name="dghi_teamsync",)
        return result

    def DGHI_Data_By_FID_ES(self, f_id, query):
        result = self.Data_By_FID_ES(f_id, query,index_name="dghi_teamsync", )
        return result
    # _______________________________________________________________________________________________________