# Retrieve an entity

GET https://api.twelvelabs.io/v1.3/entity-collections/{entity_collection_id}/entities/{entity_id}

This method retrieves details about the specified entity.

Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/entities/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve an entity
  version: endpoint_entityCollections/entities.retrieve
paths:
  /entity-collections/{entity_collection_id}/entities/{entity_id}:
    get:
      operationId: retrieve
      summary: Retrieve an entity
      description: This method retrieves details about the specified entity.
      tags:
        - - subpackage_entityCollections
          - subpackage_entityCollections/entities
      parameters:
        - name: entity_collection_id
          in: path
          description: |
            The unique identifier of the entity collection.
          required: true
          schema:
            type: string
        - name: entity_id
          in: path
          description: |
            The unique identifier of the entity to retrieve.
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
          description: The entity has been successfully retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Entity'
        '400':
          description: The request has failed.
          content: {}
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

url = "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c';
const options = {method: 'GET', headers: {'x-api-key': '<apiKey>'}};

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
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c"

	req, _ := http.NewRequest("GET", url, nil)

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

url = URI("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

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