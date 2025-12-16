# Retrieve a specific page of search results

GET https://api.twelvelabs.io/v1.3/search/{page-token}

Use this endpoint to retrieve a specific page of search results.

<Note title="Note">
When you use pagination, you will not be charged for retrieving subsequent pages of results.
</Note>


Reference: https://docs.twelvelabs.io/api-reference/any-to-video-search/retrieve-page

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve a specific page of search results
  version: endpoint_search.retrieve
paths:
  /search/{page-token}:
    get:
      operationId: retrieve
      summary: Retrieve a specific page of search results
      description: >
        Use this endpoint to retrieve a specific page of search results.


        <Note title="Note">

        When you use pagination, you will not be charged for retrieving
        subsequent pages of results.

        </Note>
      tags:
        - - subpackage_search
      parameters:
        - name: page-token
          in: path
          description: |
            A token that identifies the page to retrieve.
          required: true
          schema:
            type: string
        - name: include_user_metadata
          in: query
          description: >
            Specifies whether to include user-defined metadata in the search
            results.
          required: false
          schema:
            type: boolean
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully retrieved the specified page of search results.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/search_retrieve_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    ScoreSearchTerms:
      type: number
      format: double
    StartTime:
      type: number
      format: double
    EndTime:
      type: number
      format: double
    confidence:
      type: string
    rank:
      type: integer
    thumbnail_url:
      type: string
    UserMetadata:
      type: object
      additionalProperties:
        description: Any type
    SearchItemClipsItems:
      type: object
      properties:
        score:
          $ref: '#/components/schemas/ScoreSearchTerms'
        start:
          $ref: '#/components/schemas/StartTime'
        end:
          $ref: '#/components/schemas/EndTime'
        confidence:
          $ref: '#/components/schemas/confidence'
        rank:
          $ref: '#/components/schemas/rank'
        thumbnail_url:
          $ref: '#/components/schemas/thumbnail_url'
        transcription:
          type: string
        video_id:
          type: string
        user_metadata:
          $ref: '#/components/schemas/UserMetadata'
    SearchItem:
      type: object
      properties:
        score:
          $ref: '#/components/schemas/ScoreSearchTerms'
        start:
          $ref: '#/components/schemas/StartTime'
        end:
          $ref: '#/components/schemas/EndTime'
        video_id:
          type: string
        confidence:
          $ref: '#/components/schemas/confidence'
        rank:
          $ref: '#/components/schemas/rank'
        thumbnail_url:
          $ref: '#/components/schemas/thumbnail_url'
        transcription:
          type: string
        id:
          type: string
        user_metadata:
          $ref: '#/components/schemas/UserMetadata'
        clips:
          type: array
          items:
            $ref: '#/components/schemas/SearchItemClipsItems'
    total_inner_matches:
      type: integer
    next_page_token:
      type: string
    SearchResultsPageInfo:
      type: object
      properties:
        limit_per_page:
          type: integer
        page_expires_at:
          type: string
        total_results:
          type: integer
        total_inner_matches:
          $ref: '#/components/schemas/total_inner_matches'
        next_page_token:
          $ref: '#/components/schemas/next_page_token'
    search_pool:
      type: object
      properties:
        total_count:
          type: integer
        total_duration:
          type: number
          format: double
        index_id:
          type: string
    prev_page_token:
      type: string
    SearchPageTokenGetResponsesContentApplicationJsonSchemaPageInfo:
      type: object
      properties:
        limit_per_page:
          type: integer
        page_expires_at:
          type: string
        total_results:
          type: integer
        total_inner_matches:
          $ref: '#/components/schemas/total_inner_matches'
        next_page_token:
          $ref: '#/components/schemas/next_page_token'
        prev_page_token:
          $ref: '#/components/schemas/prev_page_token'
    search_retrieve_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/SearchItem'
        page_info:
          $ref: >-
            #/components/schemas/SearchPageTokenGetResponsesContentApplicationJsonSchemaPageInfo
        search_pool:
          $ref: '#/components/schemas/search_pool'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/search/1234567890"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/search/1234567890';
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

	url := "https://api.twelvelabs.io/v1.3/search/1234567890"

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

url = URI("https://api.twelvelabs.io/v1.3/search/1234567890")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/search/1234567890")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/search/1234567890', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/search/1234567890");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/search/1234567890")! as URL,
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