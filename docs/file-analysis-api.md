# File Analysis API Documentation

This document describes the File Analysis API for Web+, which enables AI-powered analysis of uploaded files and extraction of content from various file formats.

## API Overview

The File Analysis API provides endpoints for:

1. Requesting analysis of uploaded files
2. Retrieving analysis results 
3. Managing file metadata and content

## Endpoints

### Request File Analysis

```
POST /api/files/{file_id}/analyze
```

Initiates the analysis of a previously uploaded file. Analysis includes text extraction and AI-powered content analysis.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the file to analyze |

#### Request Headers

```
Authorization: Bearer <your_token>
```

#### Response

```json
{
  "id": "file-123abc",
  "analyzed": true,
  "analysis_status": "completed",
  "analysis_result": {
    "summary": "This document discusses the implementation of AI models...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "topics": ["AI", "Machine Learning", "Implementation"],
    "sentiment": "neutral",
    "language": "en",
    "entities": [
      {"name": "GPT-4", "type": "MODEL"},
      {"name": "Microsoft", "type": "ORGANIZATION"}
    ]
  },
  "extracted_text": "The first few lines of extracted text...",
  "extraction_quality": 0.95
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Analysis completed successfully |
| 202 | Analysis initiated (for large files) |
| 400 | Invalid request |
| 404 | File not found |
| 422 | File cannot be analyzed (unsupported format) |
| 500 | Internal server error |

### Get Analysis Results

```
GET /api/files/{file_id}/analysis
```

Retrieves the analysis results for a file. If analysis is still in progress, returns the current status.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the file to get analysis for |

#### Request Headers

```
Authorization: Bearer <your_token>
```

#### Response

```json
{
  "id": "file-123abc",
  "analyzed": true,
  "analysis_status": "completed",
  "analysis_result": {
    "summary": "This document discusses the implementation of AI models...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "topics": ["AI", "Machine Learning", "Implementation"],
    "sentiment": "neutral",
    "language": "en",
    "entities": [
      {"name": "GPT-4", "type": "MODEL"},
      {"name": "Microsoft", "type": "ORGANIZATION"}
    ]
  },
  "extracted_text": "The first 1000 characters of extracted text...",
  "extraction_quality": 0.95
}
```

If analysis is still in progress:

```json
{
  "id": "file-123abc",
  "analyzed": false,
  "analysis_status": "in_progress",
  "progress": 0.45,
  "estimated_completion_time": "2025-05-15T14:30:00Z"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 404 | File not found |
| 500 | Internal server error |

### Get Extracted Text

```
GET /api/files/{file_id}/text
```

Retrieves only the extracted text from a file, without the full analysis. Useful for large files.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the file to get text from |
| offset | integer | No | Character offset to start from (default: 0) |
| limit | integer | No | Maximum number of characters to return (default: 10000) |

#### Request Headers

```
Authorization: Bearer <your_token>
```

#### Response

```json
{
  "id": "file-123abc",
  "extraction_status": "completed",
  "extracted_text": "The extracted text content...",
  "total_length": 56789,
  "offset": 0,
  "limit": 10000,
  "has_more": true
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 404 | File not found or text not extracted |
| 500 | Internal server error |

## Analysis Result Structure

The analysis result contains structured information extracted from the file:

### Common Fields

| Field | Type | Description |
|-------|------|-------------|
| summary | string | Brief summary of the file content |
| key_points | array | Array of key points extracted from the document |
| topics | array | Main topics covered in the document |
| sentiment | string | Overall sentiment (positive, neutral, negative) |
| language | string | Detected language code |
| entities | array | Named entities extracted from the text |

### Document-Specific Fields

For text documents (PDF, DOCX, TXT):

| Field | Type | Description |
|-------|------|-------------|
| page_count | integer | Number of pages in the document |
| word_count | integer | Approximate word count |
| reading_time | integer | Estimated reading time in minutes |
| structure | object | Document structure information |

### Image-Specific Fields

For image files:

| Field | Type | Description |
|-------|------|-------------|
| objects | array | Objects detected in the image |
| text_blocks | array | Text blocks detected in the image |
| colors | array | Dominant colors in the image |
| image_quality | float | Estimated image quality score |

## Error Handling

Errors are returned in the following format:

```json
{
  "error": {
    "code": "file_analysis_failed",
    "message": "Analysis failed due to unsupported file format",
    "details": "The system only supports PDF, DOCX, TXT, and image files for analysis."
  }
}
```

## Limitations

- Maximum file size for analysis: 50MB
- Supported file formats: PDF, DOCX, TXT, JPG, PNG
- Maximum text extraction: 1,000,000 characters
- Analysis timeout: 5 minutes for standard files, 15 minutes for large files
- Rate limit: 10 analysis requests per minute per user

## Implementation Examples

### Request File Analysis (JavaScript)

```javascript
// Request file analysis
async function analyzeFile(fileId) {
  try {
    const response = await fetch(`/api/files/${fileId}/analyze`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || 'Analysis request failed');
    }
    
    return data;
  } catch (error) {
    console.error('Error analyzing file:', error);
    throw error;
  }
}
```

### Poll for Analysis Results (JavaScript)

```javascript
// Poll for analysis results until complete
async function pollAnalysisResults(fileId, interval = 2000, maxAttempts = 30) {
  let attempts = 0;
  
  return new Promise((resolve, reject) => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/files/${fileId}/analysis`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          clearInterval(intervalId);
          reject(new Error(data.error?.message || 'Failed to get analysis results'));
          return;
        }
        
        if (data.analyzed && data.analysis_status === 'completed') {
          clearInterval(intervalId);
          resolve(data);
          return;
        }
        
        attempts++;
        if (attempts >= maxAttempts) {
          clearInterval(intervalId);
          reject(new Error('Analysis timed out'));
        }
      } catch (error) {
        clearInterval(intervalId);
        reject(error);
      }
    };
    
    const intervalId = setInterval(checkStatus, interval);
    checkStatus(); // Initial check
  });
}
```

### Python Example

```python
import requests
import time

API_URL = "https://your-api-url.com"
TOKEN = "your_auth_token"

def analyze_file(file_id):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_URL}/api/files/{file_id}/analyze",
        headers=headers
    )
    
    if response.status_code in (200, 202):
        return response.json()
    else:
        raise Exception(f"Analysis request failed: {response.text}")

def get_analysis_results(file_id, max_attempts=30, interval=2):
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    for attempt in range(max_attempts):
        response = requests.get(
            f"{API_URL}/api/files/{file_id}/analysis",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get analysis results: {response.text}")
            
        data = response.json()
        
        if data.get("analyzed") and data.get("analysis_status") == "completed":
            return data
            
        print(f"Analysis in progress: {data.get('progress', 0) * 100:.1f}%")
        time.sleep(interval)
        
    raise Exception("Analysis timed out")
```

## Best Practices

1. **Analysis Requests**
   - Analyze files immediately after upload when possible
   - Consider file size before requesting analysis
   - Set reasonable timeouts for large files

2. **Displaying Results**
   - Show analysis results in a structured, readable format
   - Display progress indicators for long-running analyses
   - Provide options to view full extracted text separately

3. **Error Handling**
   - Implement proper error handling for failed analyses
   - Provide clear error messages to users
   - Offer retry options for failed analyses

4. **Performance**
   - Use polling with increasing intervals for large files
   - Cache analysis results when appropriate
   - Consider paginating large extracted text

## Future API Enhancements

Planned enhancements for future versions:

1. **Streaming Analysis**: Real-time streaming of analysis results for large files
2. **Custom Analysis Templates**: User-defined analysis templates for specific file types
3. **Batch Analysis**: Support for analyzing multiple files in a single request
4. **Enhanced Media Analysis**: Improved analysis for audio and video files
5. **Collaborative Annotations**: API for adding annotations to analyzed files