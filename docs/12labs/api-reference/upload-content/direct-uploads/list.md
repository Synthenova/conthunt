# List assets

GET https://api.twelvelabs.io/v1.3/assets

This method returns a list of assets in your account.

The platform returns your assets sorted by creation date, with the newest at the top of the list.


Reference: https://docs.twelvelabs.io/api-reference/upload-content/direct-uploads/list

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List assets
  version: endpoint_assets.list
paths:
  /assets:
    get:
      operationId: list
      summary: List assets
      description: >
        This method returns a list of assets in your account.


        The platform returns your assets sorted by creation date, with the
        newest at the top of the list.
      tags:
        - - subpackage_assets
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
        - name: asset_ids
          in: query
          description: >
            Filters the response to include only assets with the specified IDs.
            Provide one or more asset IDs. When you specify multiple IDs, the
            platform returns all matching assets.
          required: false
          schema:
            type: array
            items:
              type: string
        - name: asset_types
          in: query
          description: >
            Filters the response to include only assets of the specified types.
            Provide one or more asset types. When you specify multiple types,
            the platform returns all matching assets.
          required: false
          schema:
            type: array
            items:
              $ref: '#/components/schemas/AssetsGetParametersAssetTypesSchemaItems'
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The assets have been successfully retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/assets_list_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    AssetsGetParametersAssetTypesSchemaItems:
      type: string
      enum:
        - value: image
        - value: video
        - value: audio
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
    assets_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Asset'
        page_info:
          $ref: '#/components/schemas/page_info'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets"

querystring = {"asset_ids":"[\"6298d673f1090f1100476d4c\",\"6298d673f1090f1100476d4d\"]","asset_types":"[\"image\",\"video\"]"}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D';
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

	url := "https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D"

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

url = URI("https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets?asset_ids=%5B%226298d673f1090f1100476d4c%22%2C%226298d673f1090f1100476d4d%22%5D&asset_types=%5B%22image%22%2C%22video%22%5D")! as URL,
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