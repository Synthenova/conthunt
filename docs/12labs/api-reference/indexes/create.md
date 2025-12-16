# Create an index

POST https://api.twelvelabs.io/v1.3/indexes
Content-Type: application/json

This method creates an index.


Reference: https://docs.twelvelabs.io/api-reference/indexes/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create an index
  version: endpoint_indexes.create
paths:
  /indexes:
    post:
      operationId: create
      summary: Create an index
      description: |
        This method creates an index.
      tags:
        - - subpackage_indexes
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: An index has successfully been created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/indexes_create_Response_201'
        '400':
          description: The request has failed.
          content: {}
      requestBody:
        description: |
          Request to create an index.
        content:
          application/json:
            schema:
              type: object
              properties:
                index_name:
                  type: string
                models:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/IndexesPostRequestBodyContentApplicationJsonSchemaModelsItems
                addons:
                  type: array
                  items:
                    type: string
              required:
                - index_name
                - models
components:
  schemas:
    IndexesPostRequestBodyContentApplicationJsonSchemaModelsItems:
      type: object
      properties:
        model_name:
          type: string
        model_options:
          type: array
          items:
            type: string
      required:
        - model_name
        - model_options
    indexes_create_Response_201:
      type: object
      properties:
        _id:
          type: string

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes"

payload = {
    "index_name": "myIndex",
    "models": [
        {
            "model_name": "marengo3.0",
            "model_options": ["visual", "audio"]
        },
        {
            "model_name": "pegasus1.2",
            "model_options": ["visual", "audio"]
        }
    ],
    "addons": ["thumbnail"]
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"index_name":"myIndex","models":[{"model_name":"marengo3.0","model_options":["visual","audio"]},{"model_name":"pegasus1.2","model_options":["visual","audio"]}],"addons":["thumbnail"]}'
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

	url := "https://api.twelvelabs.io/v1.3/indexes"

	payload := strings.NewReader("{\n  \"index_name\": \"myIndex\",\n  \"models\": [\n    {\n      \"model_name\": \"marengo3.0\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    },\n    {\n      \"model_name\": \"pegasus1.2\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    }\n  ],\n  \"addons\": [\n    \"thumbnail\"\n  ]\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/indexes")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"index_name\": \"myIndex\",\n  \"models\": [\n    {\n      \"model_name\": \"marengo3.0\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    },\n    {\n      \"model_name\": \"pegasus1.2\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    }\n  ],\n  \"addons\": [\n    \"thumbnail\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/indexes")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"index_name\": \"myIndex\",\n  \"models\": [\n    {\n      \"model_name\": \"marengo3.0\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    },\n    {\n      \"model_name\": \"pegasus1.2\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    }\n  ],\n  \"addons\": [\n    \"thumbnail\"\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/indexes', [
  'body' => '{
  "index_name": "myIndex",
  "models": [
    {
      "model_name": "marengo3.0",
      "model_options": [
        "visual",
        "audio"
      ]
    },
    {
      "model_name": "pegasus1.2",
      "model_options": [
        "visual",
        "audio"
      ]
    }
  ],
  "addons": [
    "thumbnail"
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
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"index_name\": \"myIndex\",\n  \"models\": [\n    {\n      \"model_name\": \"marengo3.0\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    },\n    {\n      \"model_name\": \"pegasus1.2\",\n      \"model_options\": [\n        \"visual\",\n        \"audio\"\n      ]\n    }\n  ],\n  \"addons\": [\n    \"thumbnail\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "index_name": "myIndex",
  "models": [
    [
      "model_name": "marengo3.0",
      "model_options": ["visual", "audio"]
    ],
    [
      "model_name": "pegasus1.2",
      "model_options": ["visual", "audio"]
    ]
  ],
  "addons": ["thumbnail"]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes")! as URL,
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