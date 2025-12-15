# Retrieve video information

GET https://api.twelvelabs.io/v1.3/indexes/{index-id}/videos/{video-id}

<Info> This method will be deprecated in a future version. New implementations should use the [Retrieve an indexed asset](/v1.3/api-reference/index-content/retrieve) method.</Info>

This method retrieves information about the specified video.


Reference: https://docs.twelvelabs.io/api-reference/videos/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve video information
  version: endpoint_indexes/videos.retrieve
paths:
  /indexes/{index-id}/videos/{video-id}:
    get:
      operationId: retrieve
      summary: Retrieve video information
      description: >
        <Info> This method will be deprecated in a future version. New
        implementations should use the [Retrieve an indexed
        asset](/v1.3/api-reference/index-content/retrieve) method.</Info>


        This method retrieves information about the specified video.
      tags:
        - - subpackage_indexes
          - subpackage_indexes/videos
      parameters:
        - name: index-id
          in: path
          description: >
            The unique identifier of the index to which the video has been
            uploaded.
          required: true
          schema:
            type: string
        - name: video-id
          in: path
          description: |
            The unique identifier of the video to retrieve.
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
                #/components/schemas/IndexesIndexIdVideosVideoIdGetParametersEmbeddingOptionSchemaItems
        - name: transcription
          in: query
          description: >
            The parameter indicates whether to retrieve a transcription of the
            spoken words for the indexed video.
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
          description: The specified video information has successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/indexes_videos_retrieve_Response_200'
        '400':
          description: The request has failed.
          content: {}
        '404':
          description: The specified resource does not exist.
          content: {}
components:
  schemas:
    IndexesIndexIdVideosVideoIdGetParametersEmbeddingOptionSchemaItems:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
        - value: visual-text
    IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaSystemMetadata:
      type: object
      properties:
        duration:
          type: number
          format: double
        filename:
          type: string
        fps:
          type: number
          format: double
        height:
          type: integer
        width:
          type: integer
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
    IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaEmbeddingVideoEmbedding:
      type: object
      properties:
        segments:
          type: array
          items:
            $ref: '#/components/schemas/VideoSegment'
    IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaEmbedding:
      type: object
      properties:
        model_name:
          type: string
        video_embedding:
          $ref: >-
            #/components/schemas/IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaEmbeddingVideoEmbedding
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
    indexes_videos_retrieve_Response_200:
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
        system_metadata:
          $ref: >-
            #/components/schemas/IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaSystemMetadata
        user_metadata:
          type: object
          additionalProperties:
            description: Any type
        hls:
          $ref: '#/components/schemas/HLSObject'
        embedding:
          $ref: >-
            #/components/schemas/IndexesIndexIdVideosVideoIdGetResponsesContentApplicationJsonSchemaEmbedding
        transcription:
          $ref: '#/components/schemas/TranscriptionData'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c"

querystring = {"transcription":"true"}

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true';
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

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true"

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

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/videos/6298d673f1090f1100476d4c?transcription=true")! as URL,
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