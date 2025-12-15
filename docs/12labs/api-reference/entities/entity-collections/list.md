# List entity collections

GET https://api.twelvelabs.io/v1.3/entity-collections

This method returns a list of the entity collections in your account.


Reference: https://docs.twelvelabs.io/api-reference/entities/entity-collections/list

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List entity collections
  version: endpoint_entityCollections.list
paths:
  /entity-collections:
    get:
      operationId: list
      summary: List entity collections
      description: |
        This method returns a list of the entity collections in your account.
      tags:
        - - subpackage_entityCollections
      parameters:
        - name: page
          in: query
          description: |
            A number that identifies the page to retrieve.

            **Default**: `1`.
          required: false
          schema:
            type: integer
        - name: page_limit
          in: query
          description: |
            The number of items to return on each page.

            **Default**: `10`.
            **Max**: `50`.
          required: false
          schema:
            type: integer
        - name: name
          in: query
          description: |
            Filter entity collections by name.
          required: false
          schema:
            type: string
        - name: sort_by
          in: query
          description: >
            The field to sort on. The following options are available:

            - `created_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the entity collection was updated.

            - `updated_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the entity collection was created.

            - `name`: Sorts by the name.
          required: false
          schema:
            $ref: '#/components/schemas/EntityCollectionsGetParametersSortBy'
        - name: sort_option
          in: query
          description: |
            The sorting direction. The following options are available:
            - `asc`
            - `desc`

            **Default**: `desc`.
          required: false
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
          description: The entity collections have been successfully retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/entity-collections_list_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    EntityCollectionsGetParametersSortBy:
      type: string
      enum:
        - value: created_at
        - value: updated_at
        - value: name
    EntityCollection:
      type: object
      properties:
        _id:
          type: string
        name:
          type: string
        description:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    limit_per_page_simple:
      type: integer
    page:
      type: integer
    total_page:
      type: integer
    total_results:
      type: integer
    page_info:
      type: object
      properties:
        limit_per_page:
          $ref: '#/components/schemas/limit_per_page_simple'
        page:
          $ref: '#/components/schemas/page'
        total_page:
          $ref: '#/components/schemas/total_page'
        total_results:
          $ref: '#/components/schemas/total_results'
    entity-collections_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/EntityCollection'
        page_info:
          $ref: '#/components/schemas/page_info'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/entity-collections"

querystring = {"name":"My entity collection","sort_by":"created_at"}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at';
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

	url := "https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at"

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

url = URI("https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/entity-collections?name=My+entity+collection&sort_by=created_at")! as URL,
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