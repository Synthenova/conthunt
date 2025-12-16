# Create an entity

POST https://api.twelvelabs.io/v1.3/entity-collections/{entity_collection_id}/entities
Content-Type: application/json

This method creates an entity within a specified entity collection. Each entity must be associated with at least one asset.


Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/entities/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create an entity
  version: endpoint_entityCollections/entities.create
paths:
  /entity-collections/{entity_collection_id}/entities:
    post:
      operationId: create
      summary: Create an entity
      description: >
        This method creates an entity within a specified entity collection. Each
        entity must be associated with at least one asset.
      tags:
        - - subpackage_entityCollections
          - subpackage_entityCollections/entities
      parameters:
        - name: entity_collection_id
          in: path
          description: >
            The unique identifier of the entity collection in which to create
            the entity.
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
        '201':
          description: The entity has been successfully created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Entity'
        '400':
          description: The request has failed.
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                description:
                  type: string
                metadata:
                  $ref: >-
                    #/components/schemas/EntityCollectionsEntityCollectionIdEntitiesPostRequestBodyContentApplicationJsonSchemaMetadata
                asset_ids:
                  type: array
                  items:
                    type: string
              required:
                - name
                - asset_ids
components:
  schemas:
    EntityCollectionsEntityCollectionIdEntitiesPostRequestBodyContentApplicationJsonSchemaMetadata:
      type: object
      properties: {}
    EntityMetadata:
      type: object
      properties: {}
    EntityStatus:
      type: string
      enum:
        - value: processing
        - value: ready
    Entity:
      type: object
      properties:
        _id:
          type: string
        name:
          type: string
        description:
          type: string
        metadata:
          $ref: '#/components/schemas/EntityMetadata'
        asset_ids:
          type: array
          items:
            type: string
        status:
          $ref: '#/components/schemas/EntityStatus'
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities"

payload = {
    "name": "My entity",
    "asset_ids": ["6298d673f1090f1100476d4c", "6298d673f1090f1100476d4d"]
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"name":"My entity","asset_ids":["6298d673f1090f1100476d4c","6298d673f1090f1100476d4d"]}'
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

	url := "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities"

	payload := strings.NewReader("{\n  \"name\": \"My entity\",\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4c\",\n    \"6298d673f1090f1100476d4d\"\n  ]\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"name\": \"My entity\",\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4c\",\n    \"6298d673f1090f1100476d4d\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"name\": \"My entity\",\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4c\",\n    \"6298d673f1090f1100476d4d\"\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities', [
  'body' => '{
  "name": "My entity",
  "asset_ids": [
    "6298d673f1090f1100476d4c",
    "6298d673f1090f1100476d4d"
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
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"name\": \"My entity\",\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4c\",\n    \"6298d673f1090f1100476d4d\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "name": "My entity",
  "asset_ids": ["6298d673f1090f1100476d4c", "6298d673f1090f1100476d4d"]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities")! as URL,
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