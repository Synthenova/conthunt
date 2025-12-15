# Retrieve an asset

GET https://api.twelvelabs.io/v1.3/assets/{asset_id}

This method retrieves details about the specified asset.

Reference: https://docs.twelvelabs.io/api-reference/upload-content/direct-uploads/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve an asset
  version: endpoint_assets.retrieve
paths:
  /assets/{asset_id}:
    get:
      operationId: retrieve
      summary: Retrieve an asset
      description: This method retrieves details about the specified asset.
      tags:
        - - subpackage_assets
      parameters:
        - name: asset_id
          in: path
          description: |
            The unique identifier of the asset to retrieve.
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
          description: The asset has been successfully retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Asset'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    AssetMethod:
      type: string
      enum:
        - value: direct
        - value: url
    AssetStatus:
      type: string
      enum:
        - value: failed
        - value: processing
        - value: ready
    Asset:
      type: object
      properties:
        _id:
          type: string
        method:
          $ref: '#/components/schemas/AssetMethod'
        status:
          $ref: '#/components/schemas/AssetStatus'
        filename:
          type: string
        file_type:
          type: string
        created_at:
          type: string
          format: date-time

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c';
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

	url := "https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c"

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

url = URI("https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets/6298d673f1090f1100476d4c")! as URL,
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