# List indexed assets

GET https://api.twelvelabs.io/v1.3/indexes/{index-id}/indexed-assets

This method returns a list of the indexed assets in the specified index. By default, the platform returns your indexed assets sorted by creation date, with the newest at the top of the list.


Reference: https://docs.twelvelabs.io/api-reference/index-content/list

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List indexed assets
  version: endpoint_indexes/indexedAssets.list
paths:
  /indexes/{index-id}/indexed-assets:
    get:
      operationId: list
      summary: List indexed assets
      description: >
        This method returns a list of the indexed assets in the specified index.
        By default, the platform returns your indexed assets sorted by creation
        date, with the newest at the top of the list.
      tags:
        - - subpackage_indexes
          - subpackage_indexes/indexedAssets
      parameters:
        - name: index-id
          in: path
          description: >-
            The unique identifier of the index for which the platform will
            retrieve the indexed assets.
          required: true
          schema:
            type: string
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
        - name: status
          in: query
          description: >
            Filter by one or more indexing task statuses. The following options
            are available:

            - `ready`: The indexed asset has been successfully uploaded and
            indexed.

            - `pending`: The indexed asset is pending.

            - `queued`: The indexed asset is queued.

            - `indexing`: The indexed asset is being indexed.

            - `failed`: The indexed asset indexing task failed.


            To filter by multiple statuses, specify the `status` parameter for
            each value:

            ```

            status=ready&status=validating

            ```
          required: false
          schema:
            type: array
            items:
              $ref: >-
                #/components/schemas/IndexesIndexIdIndexedAssetsGetParametersStatusSchemaItems
        - name: filename
          in: query
          description: |
            Filter by filename.
          required: false
          schema:
            type: string
        - name: duration
          in: query
          description: |
            Filter by duration. Expressed in seconds.
          required: false
          schema:
            type: number
            format: double
        - name: fps
          in: query
          description: |
            Filter by frames per second.
          required: false
          schema:
            type: number
            format: double
        - name: width
          in: query
          description: |
            Filter by width.
          required: false
          schema:
            type: number
            format: double
        - name: height
          in: query
          description: |
            Filter by height.
          required: false
          schema:
            type: integer
        - name: size
          in: query
          description: |
            Filter by size. Expressed in bytes.
          required: false
          schema:
            type: number
            format: double
        - name: created_at
          in: query
          description: >
            Filter indexed assets by the creation date and time of their
            associated indexing tasks, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns indexed assets
            created on or after the specified date and time.
          required: false
          schema:
            type: string
        - name: updated_at
          in: query
          description: >
            This filter applies only to indexed assets updated using the
            [`PUT`](/v1.3/api-reference/videos/update) method of the
            `/indexes/{index-id}/indexed-assets/{indexed-asset-id}` endpoint. It
            filters indexed assets by the last update date and time, in the RFC
            3339 format ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns the
            indexed assets that were last updated on the specified date at or
            after the given time.
          required: false
          schema:
            type: string
        - name: user_metadata
          in: query
          description: >
            To enable filtering by custom fields, you must first add
            user-defined metadata to your video by calling the
            [`PUT`](/v1.3/api-reference/videos/update) method of the
            `/indexes/:index-id/indexed-assets/:indexed-asset-id` endpoint.


            Examples:

            - To filter on a string: `?category=recentlyAdded`

            - To filter on an integer: `?batchNumber=5`

            - To filter on a float: `?rating=9.3`

            - To filter on a boolean: `?needsReview=true`
          required: false
          schema:
            type: object
            additionalProperties:
              $ref: >-
                #/components/schemas/IndexesIndexIdIndexedAssetsGetParametersUserMetadataSchema
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: >-
            The indexed assets in the specified index have successfully been
            retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/indexes_indexed_assets_list_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    IndexesIndexIdIndexedAssetsGetParametersStatusSchemaItems:
      type: string
      enum:
        - value: ready
        - value: pending
        - value: queued
        - value: indexing
        - value: failed
    IndexesIndexIdIndexedAssetsGetParametersUserMetadataSchema:
      oneOf:
        - type: string
        - type: number
          format: double
        - type: boolean
    IndexedAssetStatus:
      type: string
      enum:
        - value: ready
        - value: pending
        - value: queued
        - value: indexing
        - value: failed
    IndexedAssetSystemMetadata:
      type: object
      properties:
        filename:
          type: string
        duration:
          type: number
          format: double
        fps:
          type: number
          format: double
        width:
          type: integer
        height:
          type: integer
        size:
          type: number
          format: double
    indexedAsset:
      type: object
      properties:
        _id:
          type: string
        created_at:
          type: string
        updated_at:
          type: string
        indexed_at:
          type: string
        status:
          $ref: '#/components/schemas/IndexedAssetStatus'
        system_metadata:
          $ref: '#/components/schemas/IndexedAssetSystemMetadata'
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
    indexes_indexed_assets_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/indexedAsset'
        page_info:
          $ref: '#/components/schemas/page_info'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets"

querystring = {"filename":"01.mp4","duration":"10","fps":"25","width":"1920","height":"1080","size":"1048576","created_at":"2024-08-16T16:53:59Z","updated_at":"2024-08-16T16:53:59Z","user_metadata":""}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=';
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata="

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets?filename=01.mp4&duration=10&fps=25&width=1920&height=1080&size=1048576&created_at=2024-08-16T16%3A53%3A59Z&updated_at=2024-08-16T16%3A53%3A59Z&user_metadata=")! as URL,
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