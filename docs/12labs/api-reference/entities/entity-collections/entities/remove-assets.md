# Remove assets from an entity

DELETE https://api.twelvelabs.io/v1.3/entity-collections/{entity_collection_id}/entities/{entity_id}/assets
Content-Type: application/json

This method removes from the specified entity. Assets are used to identify the entity in media content, and removing assets may impact the accuracy of entity recognition in searches if too few assets remain.

When assets are removed, the entity may temporarily enter a "processing" state while the system updates the necessary data. Once processing is complete, the entity status will return to "ready."

<Note title="Notes">
  - This operation only removes the association between the entity and the specified assets; it does not delete the assets themselves.
  - An entity must always have at least one asset associated with it. You can't remove the last asset from an entity.
</Note>


Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/entities/remove-assets

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Remove assets from an entity
  version: endpoint_entityCollections/entities.deleteAssets
paths:
  /entity-collections/{entity_collection_id}/entities/{entity_id}/assets:
    delete:
      operationId: delete-assets
      summary: Remove assets from an entity
      description: >
        This method removes from the specified entity. Assets are used to
        identify the entity in media content, and removing assets may impact the
        accuracy of entity recognition in searches if too few assets remain.


        When assets are removed, the entity may temporarily enter a "processing"
        state while the system updates the necessary data. Once processing is
        complete, the entity status will return to "ready."


        <Note title="Notes">
          - This operation only removes the association between the entity and the specified assets; it does not delete the assets themselves.
          - An entity must always have at least one asset associated with it. You can't remove the last asset from an entity.
        </Note>
      tags:
        - - subpackage_entityCollections
          - subpackage_entityCollections/entities
      parameters:
        - name: entity_collection_id
          in: path
          description: >
            The unique identifier of the entity collection that contains the
            entity from which assets will be removed.
          required: true
          schema:
            type: string
        - name: entity_id
          in: path
          description: >
            The unique identifier of the entity within the specified entity
            collection from which the assets will be removed.
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
          description: The assets have been successfully removed from the entity.
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
                asset_ids:
                  type: array
                  items:
                    type: string
              required:
                - asset_ids
components:
  schemas:
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

url = "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets"

payload = { "asset_ids": ["6298d673f1090f1100476d4e", "6298d673f1090f1100476d4f"] }
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.delete(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets';
const options = {
  method: 'DELETE',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"asset_ids":["6298d673f1090f1100476d4e","6298d673f1090f1100476d4f"]}'
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

	url := "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets"

	payload := strings.NewReader("{\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4e\",\n    \"6298d673f1090f1100476d4f\"\n  ]\n}")

	req, _ := http.NewRequest("DELETE", url, payload)

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

url = URI("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4e\",\n    \"6298d673f1090f1100476d4f\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4e\",\n    \"6298d673f1090f1100476d4f\"\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets', [
  'body' => '{
  "asset_ids": [
    "6298d673f1090f1100476d4e",
    "6298d673f1090f1100476d4f"
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
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets");
var request = new RestRequest(Method.DELETE);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"asset_ids\": [\n    \"6298d673f1090f1100476d4e\",\n    \"6298d673f1090f1100476d4f\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["asset_ids": ["6298d673f1090f1100476d4e", "6298d673f1090f1100476d4f"]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c/assets")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
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