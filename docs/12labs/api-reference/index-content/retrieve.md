# Retrieve an indexed asset

GET https://api.twelvelabs.io/v1.3/indexes/{index-id}/indexed-assets/{indexed-asset-id}

This method retrieves information about an indexed asset, including its status, metadata, and optional embeddings or transcription.

Use this method to:

- Monitor the indexing progress:
    - Call this endpoint after creating an indexed asset
    - Check the `status` field until it shows `ready`
    - Once ready, your content is available for search and analysis

- Retrieve the asset metadata:
    - Retrieve system metadata (duration, resolution, filename)
    - Access user-defined metadata

- Retrieve the embeddings:
    - Include the `embeddingOption` parameter to retrieve video embeddings
    - Requires the Marengo video understanding model to be enabled in your index

- Retrieve transcriptions:
  - Set the `transcription` parameter to `true` to retrieve spoken words from your video


Reference: https://docs.twelvelabs.io/api-reference/index-content/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve indexed asset information
  version: endpoint_indexes/indexedAssets.retrieve
paths:
  /indexes/{index-id}/indexed-assets/{indexed-asset-id}:
    get:
      operationId: retrieve
      summary: Retrieve indexed asset information
      description: >
        This method retrieves information about an indexed asset, including its
        status, metadata, and optional embeddings or transcription.


        Use this method to:


        - Monitor the indexing progress:
            - Call this endpoint after creating an indexed asset
            - Check the `status` field until it shows `ready`
            - Once ready, your content is available for search and analysis

        - Retrieve the asset metadata:
            - Retrieve system metadata (duration, resolution, filename)
            - Access user-defined metadata

        - Retrieve the embeddings:
            - Include the `embeddingOption` parameter to retrieve video embeddings
            - Requires the Marengo video understanding model to be enabled in your index

        - Retrieve transcriptions:
          - Set the `transcription` parameter to `true` to retrieve spoken words from your video
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
            The unique identifier of the indexed asset to retrieve.
          required: true
          schema:
            type: string
        - name: embedding_option
          in: query
          description: >
            Specifies which types of embeddings to retrieve. Values vary
            depending on the version of the model:

            - **Marengo 3.0**: `visual`, `audio`, `transcription`.

            - **Marengo 2.7**: `visual-text`, `audio`.


            For details, see the [Embedding
            options](/v1.3/docs/concepts/modalities#embedding-options) section.


            <Note title="Note">

            To retrieve embeddings for a video, it must be indexed using the
            Marengo video understanding model. For details on enabling this
            model for an index, see the [Create an
            index](/reference/create-index) page.

            </Note>
          required: false
          schema:
            type: array
            items:
              $ref: >-
                #/components/schemas/IndexesIndexIdIndexedAssetsIndexedAssetIdGetParametersEmbeddingOptionSchemaItems
        - name: transcription
          in: query
          description: |
            Specifies whether to retrieve a transcription of the spoken words.
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
          description: >-
            The specified indexed asset information has successfully been
            retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/indexedAssetDetailed'
        '400':
          description: The request has failed.
          content: {}
        '404':
          description: The specified resource does not exist.
          content: {}
components:
  schemas:
    IndexesIndexIdIndexedAssetsIndexedAssetIdGetParametersEmbeddingOptionSchemaItems:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
        - value: visual-text
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
    HlsObjectStatus:
      type: string
      enum:
        - value: PROCESSING
        - value: COMPLETE
        - value: CANCELED
        - value: ERROR
    HLSObject:
      type: object
      properties:
        video_url:
          type: string
        thumbnail_urls:
          type: array
          items:
            type: string
        status:
          $ref: '#/components/schemas/HlsObjectStatus'
        updated_at:
          type: string
    StartOffsetSec:
      type: number
      format: double
    EndOffsetSec:
      type: number
      format: double
    VideoSegment:
      type: object
      properties:
        float:
          type: array
          items:
            type: number
            format: double
        start_offset_sec:
          $ref: '#/components/schemas/StartOffsetSec'
        end_offset_sec:
          $ref: '#/components/schemas/EndOffsetSec'
        embedding_option:
          type: string
        embedding_scope:
          type: string
    IndexedAssetDetailedEmbeddingVideoEmbedding:
      type: object
      properties:
        segments:
          type: array
          items:
            $ref: '#/components/schemas/VideoSegment'
    IndexedAssetDetailedEmbedding:
      type: object
      properties:
        model_name:
          type: string
        video_embedding:
          $ref: '#/components/schemas/IndexedAssetDetailedEmbeddingVideoEmbedding'
    TranscriptionDataItems:
      type: object
      properties:
        start:
          type: number
          format: double
        end:
          type: number
          format: double
        value:
          type: string
    TranscriptionData:
      type: array
      items:
        $ref: '#/components/schemas/TranscriptionDataItems'
    indexedAssetDetailed:
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
        user_metadata:
          type: object
          additionalProperties:
            description: Any type
        hls:
          $ref: '#/components/schemas/HLSObject'
        embedding:
          $ref: '#/components/schemas/IndexedAssetDetailedEmbedding'
        transcription:
          $ref: '#/components/schemas/TranscriptionData'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c"

querystring = {"transcription":"true"}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true';
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true"

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets/6298d673f1090f1100476d4c?transcription=true")! as URL,
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