# Summaries, chapters, or highlights

POST https://api.twelvelabs.io/v1.3/summarize
Content-Type: application/json

This endpoint analyzes videos and generates summaries, chapters, or highlights. Optionally, you can provide a prompt to customize the output.

<Note title="Note">
This endpoint is rate-limited. For details, see the [Rate limits](/v1.3/docs/get-started/rate-limits) page.
</Note>


Reference: https://docs.twelvelabs.io/api-reference/analyze-videos/summarize

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Summaries, chapters, or highlights
  version: endpoint_.summarize
paths:
  /summarize:
    post:
      operationId: summarize
      summary: Summaries, chapters, or highlights
      description: >
        This endpoint analyzes videos and generates summaries, chapters, or
        highlights. Optionally, you can provide a prompt to customize the
        output.


        <Note title="Note">

        This endpoint is rate-limited. For details, see the [Rate
        limits](/v1.3/docs/get-started/rate-limits) page.

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
            The specified video has successfully been summarized.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/summarize_Response_200'
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
          Request to generate a summary of a video.
        content:
          application/json:
            schema:
              type: object
              properties:
                video_id:
                  type: string
                type:
                  type: string
                prompt:
                  type: string
                temperature:
                  type: number
                  format: double
                response_format:
                  $ref: '#/components/schemas/ResponseFormat'
                max_tokens:
                  type: integer
              required:
                - video_id
                - type
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
    SummarizeSummaryResultSummarizeType:
      type: string
      enum:
        - value: summary
    TokenUsage:
      type: object
      properties:
        output_tokens:
          type: integer
    SummarizeSummaryResult:
      type: object
      properties:
        summarize_type:
          $ref: '#/components/schemas/SummarizeSummaryResultSummarizeType'
        id:
          type: string
        summary:
          type: string
        usage:
          $ref: '#/components/schemas/TokenUsage'
      required:
        - summarize_type
    SummarizeChapterResultSummarizeType:
      type: string
      enum:
        - value: chapter
    SummarizeChapterResultChaptersItems:
      type: object
      properties:
        chapter_number:
          type: integer
        start:
          type: integer
        end:
          type: integer
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        chapter_title:
          type: string
        chapter_summary:
          type: string
    SummarizeChapterResult:
      type: object
      properties:
        summarize_type:
          $ref: '#/components/schemas/SummarizeChapterResultSummarizeType'
        id:
          type: string
        chapters:
          type: array
          items:
            $ref: '#/components/schemas/SummarizeChapterResultChaptersItems'
        usage:
          $ref: '#/components/schemas/TokenUsage'
      required:
        - summarize_type
    SummarizeHighlightResultSummarizeType:
      type: string
      enum:
        - value: highlight
    SummarizeHighlightResultHighlightsItems:
      type: object
      properties:
        start:
          type: integer
        end:
          type: integer
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        highlight:
          type: string
        highlight_summary:
          type: string
    SummarizeHighlightResult:
      type: object
      properties:
        summarize_type:
          $ref: '#/components/schemas/SummarizeHighlightResultSummarizeType'
        id:
          type: string
        highlights:
          type: array
          items:
            $ref: '#/components/schemas/SummarizeHighlightResultHighlightsItems'
        usage:
          $ref: '#/components/schemas/TokenUsage'
      required:
        - summarize_type
    summarize_Response_200:
      oneOf:
        - $ref: '#/components/schemas/SummarizeSummaryResult'
        - $ref: '#/components/schemas/SummarizeChapterResult'
        - $ref: '#/components/schemas/SummarizeHighlightResult'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/summarize"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "type": "summary",
    "prompt": "Generate a summary of this video for a social media post, up to two sentences.",
    "temperature": 0.2
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/summarize';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","type":"summary","prompt":"Generate a summary of this video for a social media post, up to two sentences.","temperature":0.2}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/summarize"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"type\": \"summary\",\n  \"prompt\": \"Generate a summary of this video for a social media post, up to two sentences.\",\n  \"temperature\": 0.2\n}")

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

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/summarize")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"type\": \"summary\",\n  \"prompt\": \"Generate a summary of this video for a social media post, up to two sentences.\",\n  \"temperature\": 0.2\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/summarize")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"type\": \"summary\",\n  \"prompt\": \"Generate a summary of this video for a social media post, up to two sentences.\",\n  \"temperature\": 0.2\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/summarize', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "type": "summary",
  "prompt": "Generate a summary of this video for a social media post, up to two sentences.",
  "temperature": 0.2
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/summarize");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"type\": \"summary\",\n  \"prompt\": \"Generate a summary of this video for a social media post, up to two sentences.\",\n  \"temperature\": 0.2\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "video_id": "6298d673f1090f1100476d4c",
  "type": "summary",
  "prompt": "Generate a summary of this video for a social media post, up to two sentences.",
  "temperature": 0.2
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/summarize")! as URL,
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