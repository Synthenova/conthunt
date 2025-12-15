# Update an entity

PATCH https://api.twelvelabs.io/v1.3/entity-collections/{entity_collection_id}/entities/{entity_id}
Content-Type: application/json

This method updates the specified entity within an entity collection. This operation allows modification of the entity's name, description, or metadata. Note that this endpoint does not affect the assets associated with the entity.


Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/entities/update

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Update an entity
  version: endpoint_entityCollections/entities.update
paths:
  /entity-collections/{entity_collection_id}/entities/{entity_id}:
    patch:
      operationId: update
      summary: Update an entity
      description: >
        This method updates the specified entity within an entity collection.
        This operation allows modification of the entity's name, description, or
        metadata. Note that this endpoint does not affect the assets associated
        with the entity.
      tags:
        - - subpackage_entityCollections
          - subpackage_entityCollections/entities
      parameters:
        - name: entity_collection_id
          in: path
          description: >
            The unique identifier of the entity collection containing the entity
            to be updated.
          required: true
          schema:
            type: string
        - name: entity_id
          in: path
          description: |
            The unique identifier of the entity to update.
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
        '200':
          description: The entity has been successfully updated.
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
                    #/components/schemas/EntityCollectionsEntityCollectionIdEntitiesEntityIdPatchRequestBodyContentApplicationJsonSchemaMetadata
components:
  schemas:
    EntityCollectionsEntityCollectionIdEntitiesEntityIdPatchRequestBodyContentApplicationJsonSchemaMetadata:
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

url = "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c"

payload = {}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c';
const options = {
  method: 'PATCH',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{}'
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

	url := "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c"

	payload := strings.NewReader("{}")

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

url = URI("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.patch("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.PATCH);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")! as URL,
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