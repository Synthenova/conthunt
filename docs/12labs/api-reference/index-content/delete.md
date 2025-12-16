# Delete an indexed asset

DELETE https://api.twelvelabs.io/v1.3/indexes/{index-id}/indexed-assets/{indexed-asset-id}

This method deletes all the information about the specified indexed asset. This action cannot be undone.


Reference: https://docs.twelvelabs.io/api-reference/index-content/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete indexed asset information
  version: endpoint_indexes/indexedAssets.delete
paths:
  /indexes/{index-id}/indexed-assets/{indexed-asset-id}:
    delete:
      operationId: delete
      summary: Delete indexed asset information
      description: >
        This method deletes all the information about the specified indexed
        asset. This action cannot be undone.
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
            The unique identifier of the indexed asset to delete.
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
                  #/components/schemas/indexes_indexed_assets_delete_Response_204
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    indexes_indexed_assets_delete_Response_204:
      type: object
      properties: {}

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.delete(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c';
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c"

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.DELETE);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c")! as URL,
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