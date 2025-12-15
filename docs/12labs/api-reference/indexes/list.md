# List indexes

GET https://api.twelvelabs.io/v1.3/indexes

This method returns a list of the indexes in your account. The platform returns indexes sorted by creation date, with the oldest indexes at the top of the list.


Reference: https://docs.twelvelabs.io/api-reference/indexes/list

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List indexes
  version: endpoint_indexes.list
paths:
  /indexes:
    get:
      operationId: list
      summary: List indexes
      description: >
        This method returns a list of the indexes in your account. The platform
        returns indexes sorted by creation date, with the oldest indexes at the
        top of the list.
      tags:
        - - subpackage_indexes
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
        - name: sort_by
          in: query
          description: >
            The field to sort on. The following options are available:

            - `updated_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the item was updated.

            - `created_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the item was created.


            **Default**: `created_at`.
          required: false
          schema:
            type: string
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
        - name: index_name
          in: query
          description: Filter by the name of an index.
          required: false
          schema:
            type: string
        - name: model_options
          in: query
          description: >
            Filter by the model options. When filtering by multiple model
            options, the values must be comma-separated.
          required: false
          schema:
            type: string
        - name: model_family
          in: query
          description: >
            Filter by the model family. This parameter can take one of the
            following values: `marengo` or `pegasus`. You can specify a single
            value.
          required: false
          schema:
            type: string
        - name: created_at
          in: query
          description: >
            Filter indexes by the creation date and time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns the indexes that were
            created on the specified date at or after the given time.
          required: false
          schema:
            type: string
        - name: updated_at
          in: query
          description: >
            Filter indexes by the last update date and time, in the RFC 3339
            format ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns the indexes
            that were last updated on the specified date at or after the given
            time.
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
          description: The indexes have successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/indexes_list_Response_200'
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
    indexes_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Index'
        page_info:
          $ref: '#/components/schemas/page_info'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes"

querystring = {"index_name":"myIndex","model_options":"visual,audio","model_family":"marengo","created_at":"2024-08-16T16:53:59Z","updated_at":"2024-08-16T16:55:59Z"}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z';
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

	url := "https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z"

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

url = URI("https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes?index_name=myIndex&model_options=visual%2Caudio&model_family=marengo&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A55%3A59Z")! as URL,
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