# Make any-to-video search requests

POST https://api.twelvelabs.io/v1.3/search
Content-Type: multipart/form-data

Use this endpoint to search for relevant matches in an index using text, media, or a combination of both as your query.

**Text queries**:
- Use the `query_text` parameter to specify your query.

**Media queries**:
- Set the `query_media_type` parameter to the corresponding media type (example: `image`).
- Specify either one of the following parameters:
  - `query_media_url`: Publicly accessible URL of your media file.
  - `query_media_file`: Local media file.
  If both `query_media_url` and `query_media_file` are specified in the same request, `query_media_url` takes precedence.

**Composed text and media queries** (Marengo 3.0 only):
- Use the `query_text` parameter for your text query.
- Set `query_media_type` to `image`.
- Specify the image using either the `query_media_url` or the `query_media_file` parameter.

  Example: Provide an image of a car and include  "red color"  in your query to find red instances of that car model.

**Entity search** (Marengo 3.0 only and in beta):

- To find a specific person in your videos, enclose the unique identifier of the entity you want to find in the `query_text` parameter.

<Note title="Note">
  When using images in your search queries (either as media queries or in composed searches), ensure your image files meet the [format requirements](/v1.3/docs/concepts/models/marengo#image-file-requirements).
</Note>

<Note title="Note">
This endpoint is rate-limited. For details, see the [Rate limits](/v1.3/docs/get-started/rate-limits) page.
</Note>


Reference: https://docs.twelvelabs.io/api-reference/any-to-video-search/make-search-request

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Make any-to-video search requests
  version: endpoint_search.create
paths:
  /search:
    post:
      operationId: create
      summary: Make any-to-video search requests
      description: >
        Use this endpoint to search for relevant matches in an index using text,
        media, or a combination of both as your query.


        **Text queries**:

        - Use the `query_text` parameter to specify your query.


        **Media queries**:

        - Set the `query_media_type` parameter to the corresponding media type
        (example: `image`).

        - Specify either one of the following parameters:
          - `query_media_url`: Publicly accessible URL of your media file.
          - `query_media_file`: Local media file.
          If both `query_media_url` and `query_media_file` are specified in the same request, `query_media_url` takes precedence.

        **Composed text and media queries** (Marengo 3.0 only):

        - Use the `query_text` parameter for your text query.

        - Set `query_media_type` to `image`.

        - Specify the image using either the `query_media_url` or the
        `query_media_file` parameter.

          Example: Provide an image of a car and include  "red color"  in your query to find red instances of that car model.

        **Entity search** (Marengo 3.0 only and in beta):


        - To find a specific person in your videos, enclose the unique
        identifier of the entity you want to find in the `query_text` parameter.


        <Note title="Note">
          When using images in your search queries (either as media queries or in composed searches), ensure your image files meet the [format requirements](/v1.3/docs/concepts/models/marengo#image-file-requirements).
        </Note>


        <Note title="Note">

        This endpoint is rate-limited. For details, see the [Rate
        limits](/v1.3/docs/get-started/rate-limits) page.

        </Note>
      tags:
        - - subpackage_search
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully performed a search request.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResults'
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
          Request to perform a search on a video index.
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                query_media_type:
                  $ref: >-
                    #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaQueryMediaType
                query_media_url:
                  type: string
                query_text:
                  type: string
                index_id:
                  type: string
                search_options:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaSearchOptionsItems
                transcription_options:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaTranscriptionOptionsItems
                adjust_confidence_level:
                  type: number
                  format: double
                group_by:
                  $ref: >-
                    #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaGroupBy
                threshold:
                  $ref: '#/components/schemas/threshold_search'
                sort_option:
                  $ref: >-
                    #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaSortOption
                operator:
                  $ref: >-
                    #/components/schemas/SearchPostRequestBodyContentMultipartFormDataSchemaOperator
                page_limit:
                  type: integer
                filter:
                  type: string
                include_user_metadata:
                  type: boolean
components:
  schemas:
    SearchPostRequestBodyContentMultipartFormDataSchemaQueryMediaType:
      type: string
      enum:
        - value: image
    SearchPostRequestBodyContentMultipartFormDataSchemaSearchOptionsItems:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
    SearchPostRequestBodyContentMultipartFormDataSchemaTranscriptionOptionsItems:
      type: string
      enum:
        - value: lexical
        - value: semantic
    SearchPostRequestBodyContentMultipartFormDataSchemaGroupBy:
      type: string
      enum:
        - value: video
        - value: clip
    threshold_search:
      type: string
      enum:
        - value: high
        - value: medium
        - value: low
        - value: none
    SearchPostRequestBodyContentMultipartFormDataSchemaSortOption:
      type: string
      enum:
        - value: score
        - value: clip_count
    SearchPostRequestBodyContentMultipartFormDataSchemaOperator:
      type: string
      enum:
        - value: or
        - value: and
    ScoreSearchTerms:
      type: number
      format: double
    StartTime:
      type: number
      format: double
    EndTime:
      type: number
      format: double
    confidence:
      type: string
    rank:
      type: integer
    thumbnail_url:
      type: string
    UserMetadata:
      type: object
      additionalProperties:
        description: Any type
    SearchItemClipsItems:
      type: object
      properties:
        score:
          $ref: '#/components/schemas/ScoreSearchTerms'
        start:
          $ref: '#/components/schemas/StartTime'
        end:
          $ref: '#/components/schemas/EndTime'
        confidence:
          $ref: '#/components/schemas/confidence'
        rank:
          $ref: '#/components/schemas/rank'
        thumbnail_url:
          $ref: '#/components/schemas/thumbnail_url'
        transcription:
          type: string
        video_id:
          type: string
        user_metadata:
          $ref: '#/components/schemas/UserMetadata'
    SearchItem:
      type: object
      properties:
        score:
          $ref: '#/components/schemas/ScoreSearchTerms'
        start:
          $ref: '#/components/schemas/StartTime'
        end:
          $ref: '#/components/schemas/EndTime'
        video_id:
          type: string
        confidence:
          $ref: '#/components/schemas/confidence'
        rank:
          $ref: '#/components/schemas/rank'
        thumbnail_url:
          $ref: '#/components/schemas/thumbnail_url'
        transcription:
          type: string
        id:
          type: string
        user_metadata:
          $ref: '#/components/schemas/UserMetadata'
        clips:
          type: array
          items:
            $ref: '#/components/schemas/SearchItemClipsItems'
    total_inner_matches:
      type: integer
    next_page_token:
      type: string
    SearchResultsPageInfo:
      type: object
      properties:
        limit_per_page:
          type: integer
        page_expires_at:
          type: string
        total_results:
          type: integer
        total_inner_matches:
          $ref: '#/components/schemas/total_inner_matches'
        next_page_token:
          $ref: '#/components/schemas/next_page_token'
    search_pool:
      type: object
      properties:
        total_count:
          type: integer
        total_duration:
          type: number
          format: double
        index_id:
          type: string
    SearchResults:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/SearchItem'
        page_info:
          $ref: '#/components/schemas/SearchResultsPageInfo'
        search_pool:
          $ref: '#/components/schemas/search_pool'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/search"

files = { "query_media_file": "open('<file1>', 'rb')" }
payload = {
    "query_media_type": ,
    "query_media_url": ,
    "query_text": "A man walking a dog",
    "index_id": "6298d673f1090f1100476d4c",
    "transcription_options": ,
    "adjust_confidence_level": "0.5",
    "group_by": "clip",
    "threshold": ,
    "sort_option": "score",
    "operator": "or",
    "page_limit": "10",
    "filter": "{\"id\":[\"66284191ea717fa66a274832\"]}",
    "include_user_metadata": 
}
headers = {"x-api-key": "<apiKey>"}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/search';
const form = new FormData();
form.append('query_media_type', '');
form.append('query_media_url', '');
form.append('query_media_file', '<file1>');
form.append('query_text', 'A man walking a dog');
form.append('index_id', '6298d673f1090f1100476d4c');
form.append('transcription_options', '');
form.append('adjust_confidence_level', '0.5');
form.append('group_by', 'clip');
form.append('threshold', '');
form.append('sort_option', 'score');
form.append('operator', 'or');
form.append('page_limit', '10');
form.append('filter', '{"id":["66284191ea717fa66a274832"]}');
form.append('include_user_metadata', '');

const options = {method: 'POST', headers: {'x-api-key': '<apiKey>'}};

options.body = form;

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

	url := "https://api.twelvelabs.io/v1.3/search"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_type\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_text\"\r\n\r\nA man walking a dog\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"index_id\"\r\n\r\n6298d673f1090f1100476d4c\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"transcription_options\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"adjust_confidence_level\"\r\n\r\n0.5\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"group_by\"\r\n\r\nclip\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"threshold\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"sort_option\"\r\n\r\nscore\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"operator\"\r\n\r\nor\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"page_limit\"\r\n\r\n10\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filter\"\r\n\r\n{\"id\":[\"66284191ea717fa66a274832\"]}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"include_user_metadata\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")

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

url = URI("https://api.twelvelabs.io/v1.3/search")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_type\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_text\"\r\n\r\nA man walking a dog\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"index_id\"\r\n\r\n6298d673f1090f1100476d4c\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"transcription_options\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"adjust_confidence_level\"\r\n\r\n0.5\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"group_by\"\r\n\r\nclip\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"threshold\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"sort_option\"\r\n\r\nscore\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"operator\"\r\n\r\nor\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"page_limit\"\r\n\r\n10\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filter\"\r\n\r\n{\"id\":[\"66284191ea717fa66a274832\"]}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"include_user_metadata\"\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/search")
  .header("x-api-key", "<apiKey>")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_type\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_text\"\r\n\r\nA man walking a dog\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"index_id\"\r\n\r\n6298d673f1090f1100476d4c\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"transcription_options\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"adjust_confidence_level\"\r\n\r\n0.5\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"group_by\"\r\n\r\nclip\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"threshold\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"sort_option\"\r\n\r\nscore\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"operator\"\r\n\r\nor\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"page_limit\"\r\n\r\n10\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filter\"\r\n\r\n{\"id\":[\"66284191ea717fa66a274832\"]}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"include_user_metadata\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/search', [
  'multipart' => [
    [
        'name' => 'query_media_file',
        'filename' => '<file1>',
        'contents' => null
    ],
    [
        'name' => 'query_text',
        'contents' => 'A man walking a dog'
    ],
    [
        'name' => 'index_id',
        'contents' => '6298d673f1090f1100476d4c'
    ],
    [
        'name' => 'adjust_confidence_level',
        'contents' => '0.5'
    ],
    [
        'name' => 'group_by',
        'contents' => 'clip'
    ],
    [
        'name' => 'sort_option',
        'contents' => 'score'
    ],
    [
        'name' => 'operator',
        'contents' => 'or'
    ],
    [
        'name' => 'page_limit',
        'contents' => '10'
    ],
    [
        'name' => 'filter',
        'contents' => '{"id":["66284191ea717fa66a274832"]}'
    ]
  ]
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/search");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_type\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_media_file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"query_text\"\r\n\r\nA man walking a dog\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"index_id\"\r\n\r\n6298d673f1090f1100476d4c\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"transcription_options\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"adjust_confidence_level\"\r\n\r\n0.5\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"group_by\"\r\n\r\nclip\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"threshold\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"sort_option\"\r\n\r\nscore\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"operator\"\r\n\r\nor\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"page_limit\"\r\n\r\n10\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filter\"\r\n\r\n{\"id\":[\"66284191ea717fa66a274832\"]}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"include_user_metadata\"\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]
let parameters = [
  [
    "name": "query_media_type",
    "value": 
  ],
  [
    "name": "query_media_url",
    "value": 
  ],
  [
    "name": "query_media_file",
    "fileName": "<file1>"
  ],
  [
    "name": "query_text",
    "value": "A man walking a dog"
  ],
  [
    "name": "index_id",
    "value": "6298d673f1090f1100476d4c"
  ],
  [
    "name": "transcription_options",
    "value": 
  ],
  [
    "name": "adjust_confidence_level",
    "value": "0.5"
  ],
  [
    "name": "group_by",
    "value": "clip"
  ],
  [
    "name": "threshold",
    "value": 
  ],
  [
    "name": "sort_option",
    "value": "score"
  ],
  [
    "name": "operator",
    "value": "or"
  ],
  [
    "name": "page_limit",
    "value": "10"
  ],
  [
    "name": "filter",
    "value": "{\"id\":[\"66284191ea717fa66a274832\"]}"
  ],
  [
    "name": "include_user_metadata",
    "value": 
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/search")! as URL,
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