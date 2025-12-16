# Delete an entity

DELETE https://api.twelvelabs.io/v1.3/entity-collections/{entity_collection_id}/entities/{entity_id}

This method deletes a specific entity from an entity collection. It permanently removes the entity and its associated data, but does not affect the assets associated with this entity.

Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/entities/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete an entity
  version: endpoint_entityCollections/entities.delete
paths:
  /entity-collections/{entity_collection_id}/entities/{entity_id}:
    delete:
      operationId: delete
      summary: Delete an entity
      description: >-
        This method deletes a specific entity from an entity collection. It
        permanently removes the entity and its associated data, but does not
        affect the assets associated with this entity.
      tags:
        - - subpackage_entityCollections
          - subpackage_entityCollections/entities
      parameters:
        - name: entity_collection_id
          in: path
          description: >
            The unique identifier of the entity collection containing the entity
            to be deleted.
          required: true
          schema:
            type: string
        - name: entity_id
          in: path
          description: |
            The unique identifier of the entity to delete.
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
          description: The entity has been successfully deleted.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/entity-collections_entities_delete_Response_204
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    entity-collections_entities_delete_Response_204:
      type: object
      properties: {}

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.delete(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c';
const options = {method: 'DELETE', headers: {'x-api-key': '<apiKey>'}};

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

	req, _ := http.NewRequest("DELETE", url, nil)

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

request = Net::HTTP::Delete.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.DELETE);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections/6298d673f1090f1100476d4c/entities/6298d673f1090f1100476d4c")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
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