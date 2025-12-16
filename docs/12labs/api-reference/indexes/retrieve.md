# Retrieve an index

GET https://api.twelvelabs.io/v1.3/indexes/{index-id}

This method retrieves details about the specified index.


Reference: https://docs.twelvelabs.io/api-reference/indexes/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve an index
  version: endpoint_indexes.retrieve
paths:
  /indexes/{index-id}:
    get:
      operationId: retrieve
      summary: Retrieve an index
      description: |
        This method retrieves details about the specified index.
      tags:
        - - subpackage_indexes
      parameters:
        - name: index-id
          in: path
          description: |
            Unique identifier of the index to retrieve.
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
          description: The specified index has successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Index'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    IndexModelsItems:
      type: object
      properties:
        model_name:
          type: string
        model_options:
          type: array
          items:
            type: string
    Index:
      type: object
      properties:
        _id:
          type: string
        created_at:
          type: string
        updated_at:
          type: string
        expires_at:
          type: string
        index_name:
          type: string
        total_duration:
          type: number
          format: double
        video_count:
          type: number
          format: double
        models:
          type: array
          items:
            $ref: '#/components/schemas/IndexModelsItems'
        addons:
          type: array
          items:
            type: string

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c';
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c"

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c")! as URL,
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