# Create an asset

POST https://api.twelvelabs.io/v1.3/assets
Content-Type: multipart/form-data

This method creates an asset by uploading a file to the platform. Assets are media files that you can use in downstream workflows, including indexing, analyzing video content, and creating entities.

**Supported content**: Video, audio, and images.

**Upload methods**:
- **Local file**: Set the `method` parameter to `direct` and use the `file` parameter to specify the file.
- **Publicly accessible URL**: Set the `method` parameter to `url` and use the `url` parameter to specify the URL of your file.

**File size**: 200MB maximum for local file uploads, 4GB maximum for URL uploads.

**Additional requirements** depend on your workflow:
- **Search**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)
- **Video analysis**: [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#input-requirements)
- **Entity search**: [Marengo image requirements](/v1.3/docs/concepts/models/marengo#image-file-requirements)
- **Create embeddings**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#input-requirements)


Reference: https://docs.twelvelabs.io/api-reference/upload-content/direct-uploads/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create an asset
  version: endpoint_assets.create
paths:
  /assets:
    post:
      operationId: create
      summary: Create an asset
      description: >
        This method creates an asset by uploading a file to the platform. Assets
        are media files that you can use in downstream workflows, including
        indexing, analyzing video content, and creating entities.


        **Supported content**: Video, audio, and images.


        **Upload methods**:

        - **Local file**: Set the `method` parameter to `direct` and use the
        `file` parameter to specify the file.

        - **Publicly accessible URL**: Set the `method` parameter to `url` and
        use the `url` parameter to specify the URL of your file.


        **File size**: 200MB maximum for local file uploads, 4GB maximum for URL
        uploads.


        **Additional requirements** depend on your workflow:

        - **Search**: [Marengo
        requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)

        - **Video analysis**: [Pegasus
        requirements](/v1.3/docs/concepts/models/pegasus#input-requirements)

        - **Entity search**: [Marengo image
        requirements](/v1.3/docs/concepts/models/marengo#image-file-requirements)

        - **Create embeddings**: [Marengo
        requirements](/v1.3/docs/concepts/models/marengo#input-requirements)
      tags:
        - - subpackage_assets
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The asset has been successfully created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Asset'
        '400':
          description: The request has failed.
          content: {}
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                method:
                  $ref: >-
                    #/components/schemas/AssetsPostRequestBodyContentMultipartFormDataSchemaMethod
                url:
                  type: string
                filename:
                  type: string
components:
  schemas:
    AssetsPostRequestBodyContentMultipartFormDataSchemaMethod:
      type: string
      enum:
        - value: direct
        - value: url
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

url = "https://api.twelvelabs.io/v1.3/assets"

files = { "file": "open('<file1>', 'rb')" }
payload = {
    "method": "direct",
    "url": ,
    "filename": 
}
headers = {"x-api-key": "<apiKey>"}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets';
const form = new FormData();
form.append('method', 'direct');
form.append('file', '<file1>');
form.append('url', '');
form.append('filename', '');

const options = {method: 'POST', headers: {'x-api-key': '<apiKey>'}};

options.body = form;

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
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/assets"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"method\"\r\n\r\ndirect\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

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

url = URI("https://api.twelvelabs.io/v1.3/assets")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"method\"\r\n\r\ndirect\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/assets")
  .header("x-api-key", "<apiKey>")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"method\"\r\n\r\ndirect\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/assets', [
  'multipart' => [
    [
        'name' => 'method',
        'contents' => 'direct'
    ],
    [
        'name' => 'file',
        'filename' => '<file1>',
        'contents' => null
    ]
  ]
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"method\"\r\n\r\ndirect\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"<file1>\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]
let parameters = [
  [
    "name": "method",
    "value": "direct"
  ],
  [
    "name": "file",
    "fileName": "<file1>"
  ],
  [
    "name": "url",
    "value": 
  ],
  [
    "name": "filename",
    "value": 
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets")! as URL,
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