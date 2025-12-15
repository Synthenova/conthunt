# Partial update indexed asset

PATCH https://api.twelvelabs.io/v1.3/indexes/{index-id}/indexed-assets/{indexed-asset-id}
Content-Type: application/json

This method updates one or more fields of the metadata of an indexed asset. Also, can delete a field by setting it to `null`.

Reference: https://docs.twelvelabs.io/api-reference/index-content/update

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Partial update indexed asset information
  version: endpoint_indexes/indexedAssets.update
paths:
  /indexes/{index-id}/indexed-assets/{indexed-asset-id}:
    patch:
      operationId: update
      summary: Partial update indexed asset information
      description: >-
        This method updates one or more fields of the metadata of an indexed
        asset. Also, can delete a field by setting it to `null`.
      tags:
        - - subpackage_indexes
          - subpackage_indexes/indexedAssets
      parameters:
        - name: index-id
          in: path
          description: >
            The unique identifier of the index to which the indexed asset has
            been uploaded.
          required: true
          schema:
            type: string
        - name: indexed-asset-id
          in: path
          description: |
            The unique identifier of the indexed asset to update.
          required: true
          schema:
            type: string
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '204':
          description: >-
            If successful, this method returns a `204 No Content` response code.
            It does not return anything in the response body.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/indexes_indexed_assets_update_Response_204
        '400':
          description: The request has failed.
          content: {}
      requestBody:
        description: >
          Request to update the metadata of a video. Delete the fields with a
          `null` value.
        content:
          application/json:
            schema:
              type: object
              properties:
                user_metadata:
                  $ref: '#/components/schemas/UserMetadata'
components:
  schemas:
    UserMetadata:
      type: object
      additionalProperties:
        description: Any type
    indexes_indexed_assets_update_Response_204:
      type: object
      properties: {}

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c"

payload = { "user_metadata": {
        "category": "recentlyAdded",
        "batchNumber": 5,
        "rating": 9.3,
        "needsReview": True
    } }
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c';
const options = {
  method: 'PATCH',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"user_metadata":{"category":"recentlyAdded","batchNumber":5,"rating":9.3,"needsReview":true}}'
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c"

	payload := strings.NewReader("{\n  \"user_metadata\": {\n    \"category\": \"recentlyAdded\",\n    \"batchNumber\": 5,\n    \"rating\": 9.3,\n    \"needsReview\": true\n  }\n}")

	req, _ := http.NewRequest("PATCH", url, payload)

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"user_metadata\": {\n    \"category\": \"recentlyAdded\",\n    \"batchNumber\": 5,\n    \"rating\": 9.3,\n    \"needsReview\": true\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.patch("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"user_metadata\": {\n    \"category\": \"recentlyAdded\",\n    \"batchNumber\": 5,\n    \"rating\": 9.3,\n    \"needsReview\": true\n  }\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c', [
  'body' => '{
  "user_metadata": {
    "category": "recentlyAdded",
    "batchNumber": 5,
    "rating": 9.3,
    "needsReview": true
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.PATCH);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"user_metadata\": {\n    \"category\": \"recentlyAdded\",\n    \"batchNumber\": 5,\n    \"rating\": 9.3,\n    \"needsReview\": true\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["user_metadata": [
    "category": "recentlyAdded",
    "batchNumber": 5,
    "rating": 9.3,
    "needsReview": true
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
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