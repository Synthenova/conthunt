# Create sync embeddings

POST https://api.twelvelabs.io/v1.3/embed-v2
Content-Type: application/json

This endpoint synchronously creates embeddings for multimodal content and returns the results immediately in the response.

<Note title="Note">
  This method only supports Marengo version 3.0 or newer.
</Note>

**When to use this endpoint**:
- Create embeddings for text, images, audio, or video content
- Get immediate results without waiting for background processing
- Process audio or video content up to 10 minutes in duration

**Do not use this endpoint for**:
- Audio or video content longer than 10 minutes. Use the [`POST`](/v1.3/api-reference/create-embeddings-v2/create-async-embedding-task) method of the `/embed-v2/tasks` endpoint instead.

<Accordion title="Input requirements">
  **Text**:
  - Maximum length: 500 tokens

  **Images**:
  - Formats: JPEG, PNG
  - Minimum size: 128x128 pixels
  - Maximum file size: 5 MB

  **Audio and video**:
  - Maximum duration: 10 minutes
  - Maximum file size for base64 encoded strings: 36 MB
  - Audio formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
  - Video formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
  - Video resolution: 360x360 to 5184x2160 pixels
  - Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1
</Accordion>


Reference: https://docs.twelvelabs.io/api-reference/create-embeddings-v2/create-embeddings

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create sync embeddings
  version: endpoint_embed/v2.create
paths:
  /embed-v2:
    post:
      operationId: create
      summary: Create sync embeddings
      description: >
        This endpoint synchronously creates embeddings for multimodal content
        and returns the results immediately in the response.


        <Note title="Note">
          This method only supports Marengo version 3.0 or newer.
        </Note>


        **When to use this endpoint**:

        - Create embeddings for text, images, audio, or video content

        - Get immediate results without waiting for background processing

        - Process audio or video content up to 10 minutes in duration


        **Do not use this endpoint for**:

        - Audio or video content longer than 10 minutes. Use the
        [`POST`](/v1.3/api-reference/create-embeddings-v2/create-async-embedding-task)
        method of the `/embed-v2/tasks` endpoint instead.


        <Accordion title="Input requirements">
          **Text**:
          - Maximum length: 500 tokens

          **Images**:
          - Formats: JPEG, PNG
          - Minimum size: 128x128 pixels
          - Maximum file size: 5 MB

          **Audio and video**:
          - Maximum duration: 10 minutes
          - Maximum file size for base64 encoded strings: 36 MB
          - Audio formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
          - Video formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
          - Video resolution: 360x360 to 5184x2160 pixels
          - Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1
        </Accordion>
      tags:
        - - subpackage_embed
          - subpackage_embed/v2
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful request; normal operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EmbeddingSuccessResponse'
        '400':
          description: Validation failure or inaccessible artifact
          content: {}
        '429':
          description: Client exceeded rate limits
          content: {}
        '500':
          description: Unhandled edge or corner case
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateEmbeddingsRequest'
components:
  schemas:
    CreateEmbeddingsRequestInputType:
      type: string
      enum:
        - value: text
        - value: image
        - value: text_image
        - value: audio
        - value: video
    CreateEmbeddingsRequestModelName:
      type: string
      enum:
        - value: marengo3.0
    TextInputRequest:
      type: object
      properties:
        input_text:
          type: string
      required:
        - input_text
    MediaSource:
      type: object
      properties:
        base64_string:
          type: string
        url:
          type: string
          format: uri
        asset_id:
          type: string
    ImageInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
      required:
        - media_source
    TextImageInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
        input_text:
          type: string
      required:
        - media_source
        - input_text
    AudioSegmentationFixed:
      type: object
      properties:
        duration_sec:
          type: integer
      required:
        - duration_sec
    AudioSegmentation:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: fixed
        fixed:
          $ref: '#/components/schemas/AudioSegmentationFixed'
      required:
        - strategy
        - fixed
    AudioInputRequestEmbeddingOptionItems:
      type: string
      enum:
        - value: audio
        - value: transcription
    AudioInputRequestEmbeddingScopeItems:
      type: string
      enum:
        - value: clip
        - value: asset
    AudioInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        segmentation:
          $ref: '#/components/schemas/AudioSegmentation'
        embedding_option:
          type: array
          items:
            $ref: '#/components/schemas/AudioInputRequestEmbeddingOptionItems'
        embedding_scope:
          type: array
          items:
            $ref: '#/components/schemas/AudioInputRequestEmbeddingScopeItems'
      required:
        - media_source
    VideoSegmentationOneOf0Dynamic:
      type: object
      properties:
        min_duration_sec:
          type: integer
      required:
        - min_duration_sec
    VideoSegmentation0:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: dynamic
        dynamic:
          $ref: '#/components/schemas/VideoSegmentationOneOf0Dynamic'
      required:
        - strategy
        - dynamic
    VideoSegmentationOneOf1Fixed:
      type: object
      properties:
        duration_sec:
          type: integer
      required:
        - duration_sec
    VideoSegmentation1:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: fixed
        fixed:
          $ref: '#/components/schemas/VideoSegmentationOneOf1Fixed'
      required:
        - strategy
        - fixed
    VideoSegmentation:
      oneOf:
        - $ref: '#/components/schemas/VideoSegmentation0'
        - $ref: '#/components/schemas/VideoSegmentation1'
    VideoInputRequestEmbeddingOptionItems:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
    VideoInputRequestEmbeddingScopeItems:
      type: string
      enum:
        - value: clip
        - value: asset
    VideoInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        segmentation:
          $ref: '#/components/schemas/VideoSegmentation'
        embedding_option:
          type: array
          items:
            $ref: '#/components/schemas/VideoInputRequestEmbeddingOptionItems'
        embedding_scope:
          type: array
          items:
            $ref: '#/components/schemas/VideoInputRequestEmbeddingScopeItems'
      required:
        - media_source
    CreateEmbeddingsRequest:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/CreateEmbeddingsRequestInputType'
        model_name:
          $ref: '#/components/schemas/CreateEmbeddingsRequestModelName'
        text:
          $ref: '#/components/schemas/TextInputRequest'
        image:
          $ref: '#/components/schemas/ImageInputRequest'
        text_image:
          $ref: '#/components/schemas/TextImageInputRequest'
        audio:
          $ref: '#/components/schemas/AudioInputRequest'
        video:
          $ref: '#/components/schemas/VideoInputRequest'
      required:
        - input_type
        - model_name
    EmbeddingDataEmbeddingOption:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
    EmbeddingDataEmbeddingScope:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingData:
      type: object
      properties:
        embedding:
          type: array
          items:
            type: number
            format: double
        embedding_option:
          oneOf:
            - $ref: '#/components/schemas/EmbeddingDataEmbeddingOption'
            - type: 'null'
        embedding_scope:
          oneOf:
            - $ref: '#/components/schemas/EmbeddingDataEmbeddingScope'
            - type: 'null'
        start_sec:
          type:
            - number
            - 'null'
          format: double
        end_sec:
          type:
            - number
            - 'null'
          format: double
      required:
        - embedding
    EmbeddingImageMetadataInputType:
      type: string
      enum:
        - value: image
    EmbeddingImageMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingImageMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
      required:
        - input_type
    EmbeddingTextImageMetadataInputType:
      type: string
      enum:
        - value: text_image
    EmbeddingTextImageMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingTextImageMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
      required:
        - input_type
    EmbeddingAudioMetadataInputType:
      type: string
      enum:
        - value: audio
    EmbeddingAudioMetadataEmbeddingScopesItems:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingAudioMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingAudioMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
        embedding_options:
          type: array
          items:
            type: string
        embedding_scopes:
          type: array
          items:
            $ref: '#/components/schemas/EmbeddingAudioMetadataEmbeddingScopesItems'
        duration:
          type: number
          format: double
        start_offset_sec:
          type: number
          format: double
        end_offset_sec:
          type: number
          format: double
      required:
        - input_type
        - embedding_options
        - embedding_scopes
        - duration
    EmbeddingVideoMetadataInputType:
      type: string
      enum:
        - value: video
    EmbeddingVideoMetadataEmbeddingScopesItems:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingVideoMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingVideoMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
        clip_length:
          type: integer
        embedding_scopes:
          type: array
          items:
            $ref: '#/components/schemas/EmbeddingVideoMetadataEmbeddingScopesItems'
        embedding_options:
          type: array
          items:
            type: string
        duration:
          type: number
          format: double
        start_offset_sec:
          type: number
          format: double
        end_offset_sec:
          type: number
          format: double
      required:
        - input_type
        - embedding_scopes
        - embedding_options
        - duration
    EmbeddingMediaMetadata:
      oneOf:
        - $ref: '#/components/schemas/EmbeddingImageMetadata'
        - $ref: '#/components/schemas/EmbeddingTextImageMetadata'
        - $ref: '#/components/schemas/EmbeddingAudioMetadata'
        - $ref: '#/components/schemas/EmbeddingVideoMetadata'
    EmbeddingSuccessResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/EmbeddingData'
        metadata:
          $ref: '#/components/schemas/EmbeddingMediaMetadata'
      required:
        - data

```

## SDK Code Examples

```python Text embedding response
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(response.json())
```

```javascript Text embedding response
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: undefined
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Text embedding response
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Text embedding response
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'

response = http.request(request)
puts response.read_body
```

```java Text embedding response
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .asString();
```

```php Text embedding response
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Text embedding response
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
IRestResponse response = client.Execute(request);
```

```swift Text embedding response
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
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

```python Video clip embedding response
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(response.json())
```

```javascript Video clip embedding response
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: undefined
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Video clip embedding response
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Video clip embedding response
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'

response = http.request(request)
puts response.read_body
```

```java Video clip embedding response
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .asString();
```

```php Video clip embedding response
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Video clip embedding response
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
IRestResponse response = client.Execute(request);
```

```swift Video clip embedding response
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
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

```python Audio asset embedding response
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(response.json())
```

```javascript Audio asset embedding response
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: undefined
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Audio asset embedding response
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Audio asset embedding response
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'

response = http.request(request)
puts response.read_body
```

```java Audio asset embedding response
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .asString();
```

```php Audio asset embedding response
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Audio asset embedding response
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
IRestResponse response = client.Execute(request);
```

```swift Audio asset embedding response
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
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

```python Text example
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "text",
    "model_name": "marengo3.0",
    "text": { "input_text": "man walking a dog" }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Text example
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"text","model_name":"marengo3.0","text":{"input_text":"man walking a dog"}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Text example
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"text\",\n  \"model_name\": \"marengo3.0\",\n  \"text\": {\n    \"input_text\": \"man walking a dog\"\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Text example
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"text\",\n  \"model_name\": \"marengo3.0\",\n  \"text\": {\n    \"input_text\": \"man walking a dog\"\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Text example
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"text\",\n  \"model_name\": \"marengo3.0\",\n  \"text\": {\n    \"input_text\": \"man walking a dog\"\n  }\n}")
  .asString();
```

```php Text example
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "text",
  "model_name": "marengo3.0",
  "text": {
    "input_text": "man walking a dog"
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Text example
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"text\",\n  \"model_name\": \"marengo3.0\",\n  \"text\": {\n    \"input_text\": \"man walking a dog\"\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Text example
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "text",
  "model_name": "marengo3.0",
  "text": ["input_text": "man walking a dog"]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Image via publicly accessible URL
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "image",
    "model_name": "marengo3.0",
    "image": { "media_source": { "url": "https://user-bucket.com/folder/dog.jpg" } }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Image via publicly accessible URL
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"image","model_name":"marengo3.0","image":{"media_source":{"url":"https://user-bucket.com/folder/dog.jpg"}}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Image via publicly accessible URL
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    }\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Image via publicly accessible URL
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    }\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Image via publicly accessible URL
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    }\n  }\n}")
  .asString();
```

```php Image via publicly accessible URL
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "image",
  "model_name": "marengo3.0",
  "image": {
    "media_source": {
      "url": "https://user-bucket.com/folder/dog.jpg"
    }
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Image via publicly accessible URL
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    }\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Image via publicly accessible URL
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "image",
  "model_name": "marengo3.0",
  "image": ["media_source": ["url": "https://user-bucket.com/folder/dog.jpg"]]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Text and image via publicly accessible URL
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "text_image",
    "model_name": "marengo3.0",
    "text_image": {
        "media_source": { "url": "https://user-bucket.com/folder/dog.jpg" },
        "input_text": "man walking a dog"
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Text and image via publicly accessible URL
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"text_image","model_name":"marengo3.0","text_image":{"media_source":{"url":"https://user-bucket.com/folder/dog.jpg"},"input_text":"man walking a dog"}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Text and image via publicly accessible URL
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"text_image\",\n  \"model_name\": \"marengo3.0\",\n  \"text_image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    },\n    \"input_text\": \"man walking a dog\"\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Text and image via publicly accessible URL
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"text_image\",\n  \"model_name\": \"marengo3.0\",\n  \"text_image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    },\n    \"input_text\": \"man walking a dog\"\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Text and image via publicly accessible URL
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"text_image\",\n  \"model_name\": \"marengo3.0\",\n  \"text_image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    },\n    \"input_text\": \"man walking a dog\"\n  }\n}")
  .asString();
```

```php Text and image via publicly accessible URL
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "text_image",
  "model_name": "marengo3.0",
  "text_image": {
    "media_source": {
      "url": "https://user-bucket.com/folder/dog.jpg"
    },
    "input_text": "man walking a dog"
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Text and image via publicly accessible URL
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"text_image\",\n  \"model_name\": \"marengo3.0\",\n  \"text_image\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/folder/dog.jpg\"\n    },\n    \"input_text\": \"man walking a dog\"\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Text and image via publicly accessible URL
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "text_image",
  "model_name": "marengo3.0",
  "text_image": [
    "media_source": ["url": "https://user-bucket.com/folder/dog.jpg"],
    "input_text": "man walking a dog"
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Image with asset id
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "image",
    "model_name": "marengo3.0",
    "image": { "media_source": { "asset_id": "1234567890" } }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Image with asset id
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"image","model_name":"marengo3.0","image":{"media_source":{"asset_id":"1234567890"}}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Image with asset id
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"asset_id\": \"1234567890\"\n    }\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Image with asset id
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"asset_id\": \"1234567890\"\n    }\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Image with asset id
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"asset_id\": \"1234567890\"\n    }\n  }\n}")
  .asString();
```

```php Image with asset id
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "image",
  "model_name": "marengo3.0",
  "image": {
    "media_source": {
      "asset_id": "1234567890"
    }
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Image with asset id
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"image\",\n  \"model_name\": \"marengo3.0\",\n  \"image\": {\n    \"media_source\": {\n      \"asset_id\": \"1234567890\"\n    }\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Image with asset id
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "image",
  "model_name": "marengo3.0",
  "image": ["media_source": ["asset_id": "1234567890"]]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Audio with fixed segmentation
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "audio",
    "model_name": "marengo3.0",
    "audio": {
        "media_source": { "url": "https://user-bucket.com/audio/a.wav" },
        "start_sec": 0,
        "end_sec": 6,
        "segmentation": {
            "strategy": "fixed",
            "fixed": { "duration_sec": 6 }
        },
        "embedding_option": ["audio", "transcription"],
        "embedding_scope": ["clip", "asset"]
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Audio with fixed segmentation
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"audio","model_name":"marengo3.0","audio":{"media_source":{"url":"https://user-bucket.com/audio/a.wav"},"start_sec":0,"end_sec":6,"segmentation":{"strategy":"fixed","fixed":{"duration_sec":6}},"embedding_option":["audio","transcription"],"embedding_scope":["clip","asset"]}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Audio with fixed segmentation
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/a.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 6,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Audio with fixed segmentation
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/a.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 6,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Audio with fixed segmentation
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/a.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 6,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")
  .asString();
```

```php Audio with fixed segmentation
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": {
    "media_source": {
      "url": "https://user-bucket.com/audio/a.wav"
    },
    "start_sec": 0,
    "end_sec": 6,
    "segmentation": {
      "strategy": "fixed",
      "fixed": {
        "duration_sec": 6
      }
    },
    "embedding_option": [
      "audio",
      "transcription"
    ],
    "embedding_scope": [
      "clip",
      "asset"
    ]
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Audio with fixed segmentation
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/a.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 6,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Audio with fixed segmentation
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": [
    "media_source": ["url": "https://user-bucket.com/audio/a.wav"],
    "start_sec": 0,
    "end_sec": 6,
    "segmentation": [
      "strategy": "fixed",
      "fixed": ["duration_sec": 6]
    ],
    "embedding_option": ["audio", "transcription"],
    "embedding_scope": ["clip", "asset"]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Video with dynamic segmentation
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "video",
    "model_name": "marengo3.0",
    "video": {
        "media_source": { "url": "https://user-bucket.com/video/clip.mp4" },
        "start_sec": 0,
        "end_sec": 12,
        "segmentation": {
            "strategy": "dynamic",
            "dynamic": { "min_duration_sec": 4 }
        },
        "embedding_option": ["visual", "audio", "transcription"],
        "embedding_scope": ["clip", "asset"]
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Video with dynamic segmentation
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"video","model_name":"marengo3.0","video":{"media_source":{"url":"https://user-bucket.com/video/clip.mp4"},"start_sec":0,"end_sec":12,"segmentation":{"strategy":"dynamic","dynamic":{"min_duration_sec":4}},"embedding_option":["visual","audio","transcription"],"embedding_scope":["clip","asset"]}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Video with dynamic segmentation
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/clip.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 12,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Video with dynamic segmentation
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/clip.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 12,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Video with dynamic segmentation
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/clip.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 12,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")
  .asString();
```

```php Video with dynamic segmentation
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": {
    "media_source": {
      "url": "https://user-bucket.com/video/clip.mp4"
    },
    "start_sec": 0,
    "end_sec": 12,
    "segmentation": {
      "strategy": "dynamic",
      "dynamic": {
        "min_duration_sec": 4
      }
    },
    "embedding_option": [
      "visual",
      "audio",
      "transcription"
    ],
    "embedding_scope": [
      "clip",
      "asset"
    ]
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Video with dynamic segmentation
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/clip.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 12,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Video with dynamic segmentation
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": [
    "media_source": ["url": "https://user-bucket.com/video/clip.mp4"],
    "start_sec": 0,
    "end_sec": 12,
    "segmentation": [
      "strategy": "dynamic",
      "dynamic": ["min_duration_sec": 4]
    ],
    "embedding_option": ["visual", "audio", "transcription"],
    "embedding_scope": ["clip", "asset"]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Video with minimal configuration
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "video",
    "model_name": "marengo3.0",
    "video": { "media_source": { "url": "https://user-bucket.com/video/simple.mp4" } }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Video with minimal configuration
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"video","model_name":"marengo3.0","video":{"media_source":{"url":"https://user-bucket.com/video/simple.mp4"}}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Video with minimal configuration
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/simple.mp4\"\n    }\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Video with minimal configuration
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/simple.mp4\"\n    }\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Video with minimal configuration
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/simple.mp4\"\n    }\n  }\n}")
  .asString();
```

```php Video with minimal configuration
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": {
    "media_source": {
      "url": "https://user-bucket.com/video/simple.mp4"
    }
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Video with minimal configuration
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/simple.mp4\"\n    }\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Video with minimal configuration
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": ["media_source": ["url": "https://user-bucket.com/video/simple.mp4"]]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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

```python Audio with transcription embeddings only
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2"

payload = {
    "input_type": "audio",
    "model_name": "marengo3.0",
    "audio": {
        "media_source": { "url": "https://user-bucket.com/audio/speech.wav" },
        "embedding_option": ["transcription"],
        "embedding_scope": ["asset"]
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Audio with transcription embeddings only
const url = 'https://api.twelvelabs.io/v1.3/embed-v2';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"audio","model_name":"marengo3.0","audio":{"media_source":{"url":"https://user-bucket.com/audio/speech.wav"},"embedding_option":["transcription"],"embedding_scope":["asset"]}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Audio with transcription embeddings only
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2"

	payload := strings.NewReader("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/speech.wav\"\n    },\n    \"embedding_option\": [\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"asset\"\n    ]\n  }\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Audio with transcription embeddings only
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/speech.wav\"\n    },\n    \"embedding_option\": [\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"asset\"\n    ]\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Audio with transcription embeddings only
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/speech.wav\"\n    },\n    \"embedding_option\": [\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"asset\"\n    ]\n  }\n}")
  .asString();
```

```php Audio with transcription embeddings only
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2', [
  'body' => '{
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": {
    "media_source": {
      "url": "https://user-bucket.com/audio/speech.wav"
    },
    "embedding_option": [
      "transcription"
    ],
    "embedding_scope": [
      "asset"
    ]
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Audio with transcription embeddings only
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/speech.wav\"\n    },\n    \"embedding_option\": [\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"asset\"\n    ]\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Audio with transcription embeddings only
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": [
    "media_source": ["url": "https://user-bucket.com/audio/speech.wav"],
    "embedding_option": ["transcription"],
    "embedding_scope": ["asset"]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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