# Open-ended analysis

POST https://api.twelvelabs.io/v1.3/analyze
Content-Type: application/json

This endpoint analyzes your videos and creates fully customizable text based on your prompts, including but not limited to tables of content, action items, memos, and detailed analyses.

<Note title="Notes">
- This endpoint is rate-limited. For details, see the [Rate limits](/v1.3/docs/get-started/rate-limits) page.
- This endpoint supports streaming responses. For details on integrating this feature into your application, refer to the [Open-ended analysis](/v1.3/docs/guides/analyze-videos/open-ended-analysis#streaming-responses).
</Note>


Reference: https://docs.twelvelabs.io/api-reference/analyze-videos/analyze

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Open-ended analysis
  version: endpoint_.analyze
paths:
  /analyze:
    post:
      operationId: analyze
      summary: Open-ended analysis
      description: >
        This endpoint analyzes your videos and creates fully customizable text
        based on your prompts, including but not limited to tables of content,
        action items, memos, and detailed analyses.


        <Note title="Notes">

        - This endpoint is rate-limited. For details, see the [Rate
        limits](/v1.3/docs/get-started/rate-limits) page.

        - This endpoint supports streaming responses. For details on integrating
        this feature into your application, refer to the [Open-ended
        analysis](/v1.3/docs/guides/analyze-videos/open-ended-analysis#streaming-responses).

        </Note>
      tags:
        - []
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: |
            The specified video has successfully been processed.
            <Note title="Note">
              The maximum length of the response is 4,096 tokens.
            </Note>
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/analyze_Response_200'
        '400':
          description: The request has failed.
          content: {}
        '429':
          description: >
            If the rate limit is reached, the platform returns an `HTTP 429 -
            Too many requests` error response. The response body is empty.
          content: {}
      requestBody:
        description: |
          Request to analyze a video and generate text based on its content.
        content:
          application/json:
            schema:
              type: object
              properties:
                video_id:
                  type: string
                prompt:
                  type: string
                temperature:
                  type: number
                  format: double
                stream:
                  type: boolean
                response_format:
                  $ref: '#/components/schemas/ResponseFormat'
                max_tokens:
                  type: integer
              required:
                - video_id
                - prompt
components:
  schemas:
    ResponseFormatType:
      type: string
      enum:
        - value: json_schema
    ResponseFormatJsonSchema:
      type: object
      properties: {}
    ResponseFormat:
      type: object
      properties:
        type:
          $ref: '#/components/schemas/ResponseFormatType'
        json_schema:
          $ref: '#/components/schemas/ResponseFormatJsonSchema'
      required:
        - type
        - json_schema
    StreamStartResponseEventType:
      type: string
      enum:
        - value: stream_start
    StreamStartResponseMetadata:
      type: object
      properties:
        generation_id:
          type: string
    StreamStartResponse:
      type: object
      properties:
        event_type:
          $ref: '#/components/schemas/StreamStartResponseEventType'
        metadata:
          $ref: '#/components/schemas/StreamStartResponseMetadata'
      required:
        - event_type
    StreamTextResponseEventType:
      type: string
      enum:
        - value: text_generation
    StreamTextResponse:
      type: object
      properties:
        event_type:
          $ref: '#/components/schemas/StreamTextResponseEventType'
        text:
          type: string
      required:
        - event_type
    StreamEndResponseEventType:
      type: string
      enum:
        - value: stream_end
    FinishReason:
      type: string
      enum:
        - value: stop
        - value: length
    TokenUsage:
      type: object
      properties:
        output_tokens:
          type: integer
    StreamEndResponseMetadata:
      type: object
      properties:
        generation_id:
          type: string
        usage:
          $ref: '#/components/schemas/TokenUsage'
    StreamEndResponse:
      type: object
      properties:
        event_type:
          $ref: '#/components/schemas/StreamEndResponseEventType'
        finish_reason:
          $ref: '#/components/schemas/FinishReason'
        metadata:
          $ref: '#/components/schemas/StreamEndResponseMetadata'
      required:
        - event_type
    StreamAnalyzeResponse:
      oneOf:
        - $ref: '#/components/schemas/StreamStartResponse'
        - $ref: '#/components/schemas/StreamTextResponse'
        - $ref: '#/components/schemas/StreamEndResponse'
    NonStreamAnalyzeResponse:
      type: object
      properties:
        id:
          type: string
        data:
          type: string
        finish_reason:
          $ref: '#/components/schemas/FinishReason'
        usage:
          $ref: '#/components/schemas/TokenUsage'
    analyze_Response_200:
      oneOf:
        - $ref: '#/components/schemas/StreamAnalyzeResponse'
        - $ref: '#/components/schemas/NonStreamAnalyzeResponse'

```

## SDK Code Examples

```python Non-streamed response
import requests

url = "https://api.twelvelabs.io/v1.3/analyze"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
    "temperature": 0.2,
    "stream": True,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "type": "object",
            "properties": {
                "title": { "type": "string" },
                "summary": { "type": "string" },
                "keywords": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        }
    },
    "max_tokens": 2000
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Non-streamed response
const url = 'https://api.twelvelabs.io/v1.3/analyze';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","prompt":"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.","temperature":0.2,"stream":true,"response_format":{"type":"json_schema","json_schema":{"type":"object","properties":{"title":{"type":"string"},"summary":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}}}}},"max_tokens":2000}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Non-streamed response
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/analyze"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Non-streamed response
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/analyze")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}"

response = http.request(request)
puts response.read_body
```

```java Non-streamed response
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/analyze")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")
  .asString();
```

```php Non-streamed response
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/analyze', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string"
        },
        "summary": {
          "type": "string"
        },
        "keywords": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
  "max_tokens": 2000
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Non-streamed response
var client = new RestClient("https://api.twelvelabs.io/v1.3/analyze");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Non-streamed response
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": [
    "type": "json_schema",
    "json_schema": [
      "type": "object",
      "properties": [
        "title": ["type": "string"],
        "summary": ["type": "string"],
        "keywords": [
          "type": "array",
          "items": ["type": "string"]
        ]
      ]
    ]
  ],
  "max_tokens": 2000
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/analyze")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

```python Stream start
import requests

url = "https://api.twelvelabs.io/v1.3/analyze"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
    "temperature": 0.2,
    "stream": True,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "type": "object",
            "properties": {
                "title": { "type": "string" },
                "summary": { "type": "string" },
                "keywords": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        }
    },
    "max_tokens": 2000
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Stream start
const url = 'https://api.twelvelabs.io/v1.3/analyze';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","prompt":"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.","temperature":0.2,"stream":true,"response_format":{"type":"json_schema","json_schema":{"type":"object","properties":{"title":{"type":"string"},"summary":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}}}}},"max_tokens":2000}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Stream start
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/analyze"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Stream start
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/analyze")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}"

response = http.request(request)
puts response.read_body
```

```java Stream start
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/analyze")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")
  .asString();
```

```php Stream start
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/analyze', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string"
        },
        "summary": {
          "type": "string"
        },
        "keywords": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
  "max_tokens": 2000
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Stream start
var client = new RestClient("https://api.twelvelabs.io/v1.3/analyze");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Stream start
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": [
    "type": "json_schema",
    "json_schema": [
      "type": "object",
      "properties": [
        "title": ["type": "string"],
        "summary": ["type": "string"],
        "keywords": [
          "type": "array",
          "items": ["type": "string"]
        ]
      ]
    ]
  ],
  "max_tokens": 2000
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/analyze")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

```python Text generation
import requests

url = "https://api.twelvelabs.io/v1.3/analyze"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
    "temperature": 0.2,
    "stream": True,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "type": "object",
            "properties": {
                "title": { "type": "string" },
                "summary": { "type": "string" },
                "keywords": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        }
    },
    "max_tokens": 2000
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Text generation
const url = 'https://api.twelvelabs.io/v1.3/analyze';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","prompt":"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.","temperature":0.2,"stream":true,"response_format":{"type":"json_schema","json_schema":{"type":"object","properties":{"title":{"type":"string"},"summary":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}}}}},"max_tokens":2000}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Text generation
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/analyze"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Text generation
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/analyze")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}"

response = http.request(request)
puts response.read_body
```

```java Text generation
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/analyze")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")
  .asString();
```

```php Text generation
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/analyze', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string"
        },
        "summary": {
          "type": "string"
        },
        "keywords": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
  "max_tokens": 2000
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Text generation
var client = new RestClient("https://api.twelvelabs.io/v1.3/analyze");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Text generation
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": [
    "type": "json_schema",
    "json_schema": [
      "type": "object",
      "properties": [
        "title": ["type": "string"],
        "summary": ["type": "string"],
        "keywords": [
          "type": "array",
          "items": ["type": "string"]
        ]
      ]
    ]
  ],
  "max_tokens": 2000
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/analyze")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

```python Stream end
import requests

url = "https://api.twelvelabs.io/v1.3/analyze"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
    "temperature": 0.2,
    "stream": True,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "type": "object",
            "properties": {
                "title": { "type": "string" },
                "summary": { "type": "string" },
                "keywords": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        }
    },
    "max_tokens": 2000
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Stream end
const url = 'https://api.twelvelabs.io/v1.3/analyze';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","prompt":"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.","temperature":0.2,"stream":true,"response_format":{"type":"json_schema","json_schema":{"type":"object","properties":{"title":{"type":"string"},"summary":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}}}}},"max_tokens":2000}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Stream end
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/analyze"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Stream end
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/analyze")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}"

response = http.request(request)
puts response.read_body
```

```java Stream end
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/analyze")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}")
  .asString();
```

```php Stream end
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/analyze', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string"
        },
        "summary": {
          "type": "string"
        },
        "keywords": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
  "max_tokens": 2000
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Stream end
var client = new RestClient("https://api.twelvelabs.io/v1.3/analyze");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"prompt\": \"I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.\",\n  \"temperature\": 0.2,\n  \"stream\": true,\n  \"response_format\": {\n    \"type\": \"json_schema\",\n    \"json_schema\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"title\": {\n          \"type\": \"string\"\n        },\n        \"summary\": {\n          \"type\": \"string\"\n        },\n        \"keywords\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      }\n    }\n  },\n  \"max_tokens\": 2000\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Stream end
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "video_id": "6298d673f1090f1100476d4c",
  "prompt": "I want to generate a description for my video with the following format - Title of the video, followed by a summary in 2-3 sentences, highlighting the main topic, key events, and concluding remarks.",
  "temperature": 0.2,
  "stream": true,
  "response_format": [
    "type": "json_schema",
    "json_schema": [
      "type": "object",
      "properties": [
        "title": ["type": "string"],
        "summary": ["type": "string"],
        "keywords": [
          "type": "array",
          "items": ["type": "string"]
        ]
      ]
    ]
  ],
  "max_tokens": 2000
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/analyze")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```