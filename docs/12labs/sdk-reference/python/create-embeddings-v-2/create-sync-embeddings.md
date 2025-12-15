# Create sync embeddings

The `EmbedClient.V2Client` class provides methods to create embeddings synchronously for multimodal content. This endpoint returns embeddings immediately in the response.

<Note title="Note">
  This class only supports Marengo version 3.0 or newer.
</Note>

**When to use this class**:

* Create embeddings for text, images, audio, or video content
* Retrieve immediate results without waiting for background processing
* Process audio or video content up to 10 minutes in duration

**Do not use this class for**:

* Audio or video content longer than 10 minutes. Use the [`embed.v_2.tasks.create`](/v1.3/sdk-reference/python/create-embeddings-v-2/create-async-embeddings#create-an-async-embedding-task) method instead.

# Methods

## Create sync embeddings

**Description**: This method synchronously creates embeddings for multimodal content and returns the results immediately in the response.

<Accordion title="Input requirements">
  **Text**:

  * Maximum length: 500 tokens

  **Images**:

  * Formats: JPEG, PNG
  * Minimum size: 128x128 pixels
  * Maximum file size: 5 MB

  **Audio and video**:

  * Maximum duration: 10 minutes
  * Maximum file size for base64 encoded strings: 36 MB
  * Audio formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
  * Video formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
  * Video resolution: 360x360 to 5184x2160 pixels
  * Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1
</Accordion>

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      input_type: CreateEmbeddingsRequestInputType,
      model_name: str,
      text: typing.Optional[TextInputRequest] = OMIT,
      image: typing.Optional[ImageInputRequest] = OMIT,
      text_image: typing.Optional[TextImageInputRequest] = OMIT,
      audio: typing.Optional[AudioInputRequest] = OMIT,
      video: typing.Optional[VideoInputRequest] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> EmbeddingSuccessResponse
  ```

  ```python Create text embeddings
  from twelvelabs import TwelveLabs, TextInputRequest

  response = client.embed.v_2.create(
      input_type="text",
      model_name="marengo3.0",
      text=TextInputRequest(
          input_text="<YOUR_TEXT>",
      ),
  )

  print(f"Number of embeddings: {len(response.data)}")
  for embedding_data in response.data:
      print(f"Embedding dimensions: {len(embedding_data.embedding)}")
      print(f"First 10 values: {embedding_data.embedding[:10]}")
  ```

  ```python Create image embeddings
  from twelvelabs import TwelveLabs, ImageInputRequest, MediaSource

  response = client.embed.v_2.create(
      input_type="image",
      model_name="marengo3.0",
      image=ImageInputRequest(
          media_source=MediaSource(
              url="<YOUR_IMAGE_URL>",
          ),
      ),
  )

  print(f"Number of embeddings: {len(response.data)}")
  for embedding_data in response.data:
      print(f"Embedding dimensions: {len(embedding_data.embedding)}")
      print(f"First 10 values: {embedding_data.embedding[:10]}")
  ```

  ```python Create video embeddings
  from twelvelabs import TwelveLabs, VideoInputRequest, MediaSource

  response = client.embed.v_2.create(
      input_type="video",
      model_name="marengo3.0",
      video=VideoInputRequest(
          media_source=MediaSource(
              url="<YOUR_VIDEO_URL>",
          ),
      ),
  )

  print(f"Number of embeddings: {len(response.data)}")
  for embedding_data in response.data:
      print(f"Embedding dimensions: {len(embedding_data.embedding)}")
      print(f"First 10 values: {embedding_data.embedding[:10]}")

  ```
</CodeGroup>

**Parameters**:

| Name              | Type                               | Required | Description                                                                                                                                               |
| ----------------- | ---------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input_type`      | `CreateEmbeddingsRequestInputType` | Yes      | The type of content for the embeddings. Values: `text`, `image`, `text_image`, `audio`, `video`.                                                          |
| `model_name`      | `str`                              | Yes      | The video understanding model you wish to use. Value: `marengo3.0`.                                                                                       |
| `text`            | `TextInputRequest`                 | No       | Text input configuration. Required when `input_type` is `text`. See [TextInputRequest](#textinputrequest) for details.                                    |
| `image`           | `ImageInputRequest`                | No       | Image input configuration. Required when `input_type` is `image`. See [ImageInputRequest](#imageinputrequest) for details.                                |
| `text_image`      | `TextImageInputRequest`            | No       | Combined text and image input configuration. Required when `input_type` is `text_image`. See [TextImageInputRequest](#textimageinputrequest) for details. |
| `audio`           | `AudioInputRequest`                | No       | Audio input configuration. Required when `input_type` is `audio`. See [AudioInputRequest](#audioinputrequest) for details.                                |
| `video`           | `VideoInputRequest`                | No       | Video input configuration. Required when `input_type` is `video`. See [VideoInputRequest](#videoinputrequest) for details.                                |
| `request_options` | `RequestOptions`                   | No       | Request-specific configuration.                                                                                                                           |

### TextInputRequest

The `TextInputRequest` class specifies configuration for processing text content. Required when `input_type` is `text`.

| Name         | Type  | Required | Description                                                                           |
| ------------ | ----- | -------- | ------------------------------------------------------------------------------------- |
| `input_text` | `str` | Yes      | The text for which you wish to create an embedding. The maximum length is 500 tokens. |

### ImageInputRequest

The `ImageInputRequest` class specifies configuration for processing image content. Required when `input_type` is `image`.

| Name           | Type          | Required | Description                                                                          |
| -------------- | ------------- | -------- | ------------------------------------------------------------------------------------ |
| `media_source` | `MediaSource` | Yes      | Specifies the source of the image file. See [MediaSource](#mediasource) for details. |

### TextImageInputRequest

The `TextImageInputRequest` class specifies configuration for processing combined text and image content. Required when `input_type` is `text_image`.

| Name           | Type          | Required | Description                                                                           |
| -------------- | ------------- | -------- | ------------------------------------------------------------------------------------- |
| `media_source` | `MediaSource` | Yes      | Specifies the source of the image file. See [MediaSource](#mediasource) for details.  |
| `input_text`   | `str`         | Yes      | The text for which you wish to create an embedding. The maximum length is 500 tokens. |

### AudioInputRequest

The `AudioInputRequest` class specifies configuration for processing audio content. Required when `input_type` is `audio`.

| Name               | Type                | Required | Description                                                                                                                                                                                                                                                                                                                   |
| ------------------ | ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `media_source`     | `MediaSource`       | Yes      | Specifies the source of the audio file. See [MediaSource](#mediasource) for details.                                                                                                                                                                                                                                          |
| `start_sec`        | `float`             | No       | The start time in seconds for processing the audio file. Use this parameter to process a portion of the audio file starting from a specific time. Default: `0` (start from the beginning).                                                                                                                                    |
| `end_sec`          | `float`             | No       | The end time in seconds for processing the audio file. Use this parameter to process a portion of the audio file ending at a specific time. The end time must be greater than the start time. Default: End of the audio file.                                                                                                 |
| `segmentation`     | `AudioSegmentation` | No       | Specifies how the platform divides the audio into segments. When combined with `embedding_scope=["clip"]`, creates separate embeddings for each segment. Use this to generate embeddings for specific portions of your audio. See [AudioSegmentation](#audiosegmentation) for details.                                        |
| `embedding_option` | `List[str]`         | No       | The types of embeddings you wish to generate. Values:<br />- `audio`: Generates embeddings based on audio content (sounds, music, effects)<br />- `transcription`: Generates embeddings based on transcribed speech<br /><br />You can specify multiple options to generate different types of embeddings for the same audio. |
| `embedding_scope`  | `List[str]`         | No       | The scope for which you wish to generate embeddings. Values:<br />- `clip`: Generates one embedding for each segment<br />- `asset`: Generates one embedding for the entire audio file<br /><br />You can specify multiple scopes to generate embeddings at different levels.                                                 |

### VideoInputRequest

The `VideoInputRequest` class specifies configuration for processing video content. Required when `input_type` is `video`.

| Name               | Type                | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------ | ------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `media_source`     | `MediaSource`       | Yes      | Specifies the source of the video file. See [MediaSource](#mediasource) for details.                                                                                                                                                                                                                                                                                                                                                                                         |
| `start_sec`        | `float`             | No       | The start time in seconds for processing the video file. Use this parameter to process a portion of the video file starting from a specific time. Default: `0` (start from the beginning).                                                                                                                                                                                                                                                                                   |
| `end_sec`          | `float`             | No       | The end time in seconds for processing the video file. Use this parameter to process a portion of the video file ending at a specific time. The end time must be greater than the start time. Default: End of the video file.                                                                                                                                                                                                                                                |
| `segmentation`     | `VideoSegmentation` | No       | Specifies how the platform divides the video into segments. When combined with `embedding_scope=["clip"]`, creates separate embeddings for each segment. Supports fixed-duration segments or dynamic segmentation that adapts to scene changes. See [VideoSegmentation](#videosegmentation) for details.                                                                                                                                                                     |
| `embedding_option` | `List[str]`         | No       | The types of embeddings to generate for the video. Values:<br />- `visual`: Generates embeddings based on visual content (scenes, objects, actions)<br />- `audio`: Generates embeddings based on audio content (sounds, music, effects)<br />- `transcription`: Generates embeddings based on transcribed speech<br /><br />You can specify multiple options to generate different types of embeddings for the same video. Default: `["visual", "audio", "transcription"]`. |
| `embedding_scope`  | `List[str]`         | No       | The scope for which you wish to generate embeddings. Values:<br />- `clip`: Generates one embedding for each segment<br />- `asset`: Generates one embedding for the entire video file. Use this scope for videos up to 10-30 seconds to maintain optimal performance.<br /><br />You can specify multiple scopes to generate embeddings at different levels. Default: `["clip", "asset"]`.                                                                                  |

### MediaSource

The `MediaSource` class specifies the source of the media file. Provide exactly one of the following:

| Name            | Type  | Required | Description                                                                                                                                                                                     |
| --------------- | ----- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `base64_string` | `str` | No       | The base64-encoded media data.                                                                                                                                                                  |
| `url`           | `str` | No       | The publicly accessible URL of the media file. Use direct links to raw media files. Video hosting platforms and cloud storage sharing links are not supported.                                  |
| `asset_id`      | `str` | No       | The unique identifier of an asset from a [direct](/v1.3/sdk-reference/python/upload-content/direct-uploads) or [multipart](/v1.3/sdk-reference/python/upload-content/multipart-uploads) upload. |

### AudioSegmentation

The `AudioSegmentation` class specifies how the platform divides the audio into segments using fixed-length intervals.

| Name       | Type                     | Required | Description                                                                                              |
| ---------- | ------------------------ | -------- | -------------------------------------------------------------------------------------------------------- |
| `strategy` | `Literal["fixed"]`       | Yes      | The segmentation strategy. Value: `fixed`.                                                               |
| `fixed`    | `AudioSegmentationFixed` | Yes      | Configuration for fixed segmentation. See [AudioSegmentationFixed](#audiosegmentationfixed) for details. |

### AudioSegmentationFixed

The `AudioSegmentationFixed` class configures fixed-length segmentation for audio.

| Name           | Type  | Required | Description                                                                                                                                                                                                                                                                                                          |
| -------------- | ----- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `duration_sec` | `int` | Yes      | The duration in seconds for each segment. The platform divides the audio into segments of this exact length. The final segment may be shorter if the audio duration is not evenly divisible.<br /><br />**Example**: With `duration_sec: 5`, a 12-second audio file produces segments: \[0-5s], \[5-10s], \[10-12s]. |

### VideoSegmentation

The `VideoSegmentation` type specifies how the platform divides the video into segments. Use one of the following:

**Fixed segmentation**: Divides the video into equal-length segments:

| Name       | Type                          | Required | Description                                                                                                        |
| ---------- | ----------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| `strategy` | `Literal["fixed"]`            | Yes      | The segmentation strategy. Value: `fixed`.                                                                         |
| `fixed`    | `VideoSegmentationFixedFixed` | Yes      | Configuration for fixed segmentation. See [VideoSegmentationFixedFixed](#videosegmentationfixedfixed) for details. |

**Dynamic segmentation**: Divides the video into adaptive segments based on scene changes:

| Name       | Type                              | Required | Description                                                                                                                  |
| ---------- | --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `strategy` | `Literal["dynamic"]`              | Yes      | The segmentation strategy. Value: `dynamic`.                                                                                 |
| `dynamic`  | `VideoSegmentationDynamicDynamic` | Yes      | Configuration for dynamic segmentation. See [VideoSegmentationDynamicDynamic](#videosegmentationdynamicdynamic) for details. |

### VideoSegmentationFixedFixed

The `VideoSegmentationFixedFixed` class configures fixed-length segmentation for video.

| Name           | Type  | Required | Description                                                                                                                                                                                                                                                                                                     |
| -------------- | ----- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `duration_sec` | `int` | Yes      | The duration in seconds for each segment. The platform divides the video into segments of this exact length. The final segment may be shorter if the video duration is not evenly divisible.<br /><br />**Example**: With `duration_sec: 5`, a 12-second video produces segments: \[0-5s], \[5-10s], \[10-12s]. |

### VideoSegmentationDynamicDynamic

The `VideoSegmentationDynamicDynamic` class configures dynamic segmentation for video based on scene changes.

| Name               | Type  | Required | Description                                                                                                                                                                                                                                                                                                                         |
| ------------------ | ----- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `min_duration_sec` | `int` | Yes      | The minimum duration in seconds for each segment. The platform divides the video into segments that are at least this long. Segments adapt to scene changes and content boundaries and may be longer than the minimum.<br /><br />**Example**: With `min_duration_sec: 3`, segments might be: \[0-3.2s], \[3.2-7.8s], \[7.8-12.1s]. |

**Return value**: Returns an `EmbeddingSuccessResponse` object containing the embedding results.

The `EmbeddingSuccessResponse` class contains the following properties:

| Name       | Type                               | Description                       |
| ---------- | ---------------------------------- | --------------------------------- |
| `data`     | `List[EmbeddingData]`              | Array of embedding results.       |
| `metadata` | `Optional[EmbeddingMediaMetadata]` | Metadata about the media content. |

The `EmbeddingData` class contains the following properties:

| Name               | Type                                     | Description                                                        |
| ------------------ | ---------------------------------------- | ------------------------------------------------------------------ |
| `embedding`        | `List[float]`                            | The embedding vector for the content.                              |
| `embedding_option` | `Optional[EmbeddingDataEmbeddingOption]` | The type of embedding. Values: `visual`, `audio`, `transcription`. |
| `embedding_scope`  | `Optional[EmbeddingDataEmbeddingScope]`  | The scope of the embedding. Values: `clip`, `asset`.               |
| `start_sec`        | `Optional[float]`                        | The start time in seconds for this embedding segment.              |
| `end_sec`          | `Optional[float]`                        | The end time in seconds for this embedding segment.                |

**API Reference**: [Create sync embeddings](/v1.3/api-reference/create-embeddings-v2/create-embeddings)
