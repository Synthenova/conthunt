# Titles, topics, or hashtags

POST https://api.twelvelabs.io/v1.3/gist
Content-Type: application/json

This endpoint analyzes videos and generates titles, topics, and hashtags.

<Note title="Note">
This endpoint is rate-limited. For details, see the [Rate limits](/v1.3/docs/get-started/rate-limits) page.
</Note>


Reference: https://docs.twelvelabs.io/api-reference/analyze-videos/gist

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Titles, topics, and hashtags
  version: endpoint_.gist
paths:
  /gist:
    post:
      operationId: gist
      summary: Titles, topics, and hashtags
      description: >
        This endpoint analyzes videos and generates titles, topics, and
        hashtags.


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
            The gist of the specified video has successfully been generated.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/gist_Response_200'
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
          Request to generate a gist for a video.
        content:
          application/json:
            schema:
              type: object
              properties:
                video_id:
                  type: string
                types:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/GistPostRequestBodyContentApplicationJsonSchemaTypesItems
              required:
                - video_id
                - types
components:
  schemas:
    GistPostRequestBodyContentApplicationJsonSchemaTypesItems:
      type: string
      enum:
        - value: title
        - value: topic
        - value: hashtag
    TokenUsage:
      type: object
      properties:
        output_tokens:
          type: integer
    gist_Response_200:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        topics:
          type: array
          items:
            type: string
        hashtags:
          type: array
          items:
            type: string
        usage:
          $ref: '#/components/schemas/TokenUsage'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/gist"

payload = {
    "video_id": "6298d673f1090f1100476d4c",
    "types": ["title", "topic"]
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/gist';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"video_id":"6298d673f1090f1100476d4c","types":["title","topic"]}'
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

	url := "https://api.twelvelabs.io/v1.3/gist"

	payload := strings.NewReader("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"types\": [\n    \"title\",\n    \"topic\"\n  ]\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/gist")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"types\": [\n    \"title\",\n    \"topic\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/gist")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"types\": [\n    \"title\",\n    \"topic\"\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/gist', [
  'body' => '{
  "video_id": "6298d673f1090f1100476d4c",
  "types": [
    "title",
    "topic"
  ]
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/gist");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"video_id\": \"6298d673f1090f1100476d4c\",\n  \"types\": [\n    \"title\",\n    \"topic\"\n  ]\n}", ParameterType.RequestBody);
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
  "types": ["title", "topic"]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/gist")! as URL,
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