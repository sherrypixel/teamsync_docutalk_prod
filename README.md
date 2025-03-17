The main repository for Teamsync's AI functionalities.

Includes : 
1. NLPSearch
2. Docutalk


# API Documentation - DOCUTALK UNIVERSAL

## Overview
This document provides an overview of the API endpoints and functions involved in searching for documents using NLP processing.

## API Endpoint

### `POST /teamsync/nlp/docutalk/search_documents`
**Description:**
Search for relevant documents based on a query using NLP models.

**Request Parameters:**
| Parameter  | Type   | Required | Description |
|------------|--------|----------|-------------|
| `text`     | string | Yes      | Query text to search documents. |
| `username` | string | Yes      | User identifier. |
| `modeltype`| string | Yes      | NLP model type (`mistral` or `phi3`). |
| `answerType` | string | Yes | Response type (`singleDocument` or `multiDocument`). |
| `path`     | string | No       | Document path filter (default: `T_`). |

**Response:**
Returns a JSON object with search results.

**Implementation:**
Calls `search_documents_gpt` from `doc_process.py` to process the request.

---

## Functions

### `search_documents_gpt(query_text, user_name, model_type, answerType, path)`
**Description:**
Processes the search query using Elasticsearch and NLP models.

**Parameters:**
- `query_text` (str): Search query text.
- `user_name` (str): User identifier.
- `model_type` (str): NLP model type (`mistral` or `phi3`).
- `answerType` (str): Type of response (`singleDocument` or `multiDocument`).
- `path` (str): Document path filter.

**Returns:**
- A list of search results containing document details and generated answers.

**Logic Flow:**
1. Queries Elasticsearch using `Search_Docs_gpt`.
2. Filters results based on `answerType` and `model_type`.
3. Retrieves surrounding text using `above_and_below_pagedata`.
4. Generates a response using `ibm_cloud_granite` or `using_gemini`.
5. Returns search results with the generated response prepended.

---

### `above_and_below_pagedata(text, page_no, file_id)`
**Description:**
Fetches text from adjacent pages to provide context for the query.

**Parameters:**
- `text` (str): Current page text.
- `page_no` (int): Current page number.
- `file_id` (str): File identifier.

**Returns:**
- Combined text from the current page and surrounding pages.

---

### `ibm_cloud_granite(text, query)`
**Description:**
Generates an answer based on provided text using IBM Granite NLP model.

**Parameters:**
- `text` (str): Context text.
- `query` (str): User query.

**Returns:**
- Generated answer in HTML format or a moderation message if flagged.

**Implementation Details:**
- Uses IBM Cloud API for text generation.
- Enforces system instructions for strict document-based responses.
- Handles input moderation.

---

## Elasticsearch Functions

### `Search_Docs_gpt(query, username, path)`
**Description:**
Searches documents in Elasticsearch using text matching and sparse vectors.

**Parameters:**
- `query` (str): Search query.
- `username` (str): User identifier.
- `path` (str): Document path filter.

**Returns:**
- List of matching documents with metadata.

**Search Strategy:**
- Filters by username and document path.
- Uses a combination of sparse vector search and exact phrase matching.

---

### `Data_By_pageno(page_no, fid)`
**Description:**
Fetches document text from a specific page in Elasticsearch.

**Parameters:**
- `page_no` (int): Page number.
- `fid` (str): File identifier.

**Returns:**
- Page text if found, else `None`.

---

## Notes
- Ensure valid `model_type` and `answerType` values to prevent errors.
- The API handles input sanitation for `username` and `path`.
- Elasticsearch indices should be correctly configured for optimal performance.

