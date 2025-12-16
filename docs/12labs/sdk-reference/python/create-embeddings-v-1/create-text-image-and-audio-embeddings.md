# Create text, image, and audio embeddings

The `EmbedClient` class provides methods to create text, image, and audio embeddings.

# Create text, image, and audio embeddings

**Description**: This method creates a new embedding.

Note that you must specify at least the following parameters:

* `model_name`: The name of the video understanding model to use.

* One or more of the following input types:
  * `text`: For text embeddings
  * `audio_url` or `audio_file`: For audio embeddings. If you specify both, the `audio_url` parameter takes precedence.
  * `image_url` or `image_file`: For image embeddings. If you specify both, the `image_url` parameter takes precedence.

You must provide at least one input type, but you can include multiple types in a single function call.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      model_name: Literal["marengo3.0","marengo-retrieval-2.7"],
      *,
      # text params
      text: str = None,
      text_truncate: Literal["none", "start", "end"] = None,
      # audio params
      audio_url: str = None,
      audio_file: Union[str, BinaryIO, None] = None,
      # image params
      image_url: str = None,
      image_file: Union[str, BinaryIO, None] = None,
      **kwargs,
  ) -> models.CreateEmbeddingsResult
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  def print_segments(segments, max_elements: int = 5):
      for segment in segments:
          if hasattr(segment, 'start_offset_sec'):
              print(f"  start_offset_sec={segment.start_offset_sec}")
          print(f"  embeddings: {segment.float_[:max_elements]}")

  res = client.embed.create(
      model_name="marengo3.0",
      text="<YOUR_TEXT>",
      audio_url="<YOUR_AUDIO_URL>",
      image_url="<YOUR_IMAGE_URL>",
      audio_start_offset_sec=10.0
  )

  if hasattr(res, 'text_embedding') and res.text_embedding and res.text_embedding.segments:
      print("Created text embeddings:")
      print_segments(res.text_embedding.segments)
  if hasattr(res, 'image_embedding') and res.image_embedding.segments:
      print("Created image embeddings:")
      print_segments(res.image_embedding.segments)
  if hasattr(res, 'audio_embedding') and res.audio_embedding.segments:
      print("Created audio embeddings:")
      print_segments(res.audio_embedding.segments)
  ```
</CodeGroup>

**Parameters**:

| Name                     | Type             | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------ | ---------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model_name`             | `str`            | Yes      | The name of the video understanding model to use. The following models are available:<br />- `marengo3.0`: Enhanced model with sports intelligence and extended content support. For a list of the new features, see the [New in Marengo 3.0](/v1.3/docs/concepts/models/marengo#new-in-marengo-30) section.<br />- `marengo2.7`: Video embedding model for multimodal search.                                                                                                           |
| `text`                   | `str`            | No       | The text for which you want to create an embedding.                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `text_truncate`          | `str`            | No       | Controls how the platform handles text that exceeds token limits.<br /><br />**Marengo 3.0**: This parameter is deprecated. The platform automatically truncates text exceeding 500 tokens from the end.<br /><br />**Marengo 2.7**: Specifies truncation method for text exceeding 77 tokens:<br />- `start`: Removes tokens from the beginning<br />- `end`: Removes tokens from the end (default)<br />- `none`: Returns an error if the text is longer than the maximum token limit. |
| `image_url`              | `str`            | No       | The publicly accessible URL of the image for which you wish to create an embedding. Required for image embeddings if `image_file` is not provided.                                                                                                                                                                                                                                                                                                                                       |
| `image_file`             | `core.File`      | No       | A local image file. Required for image embeddings if `image_url` is not provided.                                                                                                                                                                                                                                                                                                                                                                                                        |
| `audio_url`              | `str`            | No       | The publicly accessible URL of the audio file for which you wish to create an embedding. Required for audio embeddings if `audio_file` is not provided.                                                                                                                                                                                                                                                                                                                                  |
| `audio_file`             | `core.File`      | No       | A local audio file. Required for audio embeddings if `audio_url` is not provided.                                                                                                                                                                                                                                                                                                                                                                                                        |
| `audio_start_offset_sec` | `float`          | No       | Specifies the start time, in seconds, from which the platform generates the audio embeddings. Default: `0`.                                                                                                                                                                                                                                                                                                                                                                              |
| `request_options`        | `RequestOptions` | No       | Request-specific configuration.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

**Return value**: Returns an `EmbeddingResponse` object containing the embedding results.

The `EmbeddingResponse` class contains the following properties:

| Name              | Type                             | Description                                                                                                                        |
| ----------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `model_name`      | `str`                            | The name of the video understanding model the platform has used to create this embedding.                                          |
| `text_embedding`  | `Optional[TextEmbeddingResult]`  | An object that contains the generated text embedding vector and associated information. Present when a text was processed.         |
| `image_embedding` | `Optional[ImageEmbeddingResult]` | An object that contains the generated image embedding vector and associated information. Present when an image was processed.      |
| `audio_embedding` | `Optional[AudioEmbeddingResult]` | An object that contains the generated audio embedding vector and associated information. Present when an audio file was processed. |

The `TextEmbeddingResult` class contains the following properties:

| Name            | Type                          | Description                                       |
| --------------- | ----------------------------- | ------------------------------------------------- |
| `error_message` | `Optional[str]`               | Error message if the embedding generation failed. |
| `segments`      | `Optional[List[BaseSegment]]` | An object that contains the embedding.            |

The `AudioEmbeddingResult` class contains the following properties:

| Name            | Type                              | Description                                               |
| --------------- | --------------------------------- | --------------------------------------------------------- |
| `segments`      | `Optional[List[AudioSegment]]`    | An object that contains the embedding and its start time. |
| `error_message` | `Optional[str]`                   | Error message if the embedding generation failed.         |
| `metadata`      | `Optional[BaseEmbeddingMetadata]` | Metadata about the embedding.                             |

The `ImageEmbeddingResult` class contains the following properties:

| Name            | Type                              | Description                                       |
| --------------- | --------------------------------- | ------------------------------------------------- |
| `error_message` | `Optional[str]`                   | Error message if the embedding generation failed. |
| `segments`      | `Optional[List[BaseSegment]]`     | An object that contains the embedding.            |
| `metadata`      | `Optional[BaseEmbeddingMetadata]` | Metadata about the embedding.                     |

The `BaseSegment` class contains the following properties:

| Name     | Type                    | Description                                                                                                                                |
| -------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `float_` | `Optional[List[float]]` | An array of floating point numbers representing the embedding. You can use this array with cosine similarity for various downstream tasks. |

The `AudioSegment` class extends `BaseSegment` and contains the following additional properties:

| Name               | Type              | Description                                                     |
| ------------------ | ----------------- | --------------------------------------------------------------- |
| `start_offset_sec` | `Optional[float]` | The start time in seconds from the beginning of the audio file. |
| `end_offset_sec`   | `Optional[float]` | The end time in seconds from the beginning of the audio file.   |

The `BaseEmbeddingMetadata` class contains the following properties:

| Name             | Type            | Description                                                                                               |
| ---------------- | --------------- | --------------------------------------------------------------------------------------------------------- |
| `input_url`      | `Optional[str]` | The URL of the media file used to generate the embedding. Present if a URL was provided in the request.   |
| `input_filename` | `Optional[str]` | The name of the media file used to generate the embedding. Present if a file was provided in the request. |

**API Reference**: [Create text, audio, and image embeddings](/v1.3/api-reference/create-embeddings-v1/text-image-audio-embeddings/create-text-image-audio-embeddings).

**Related guides**:

* [Create text embeddings](/v1.3/docs/guides/create-embeddings/text)
* [Create audio embeddings](/v1.3/docs/guides/create-embeddings/audio)
* [Create image embeddings](/v1.3/docs/guides/create-embeddings/image)

# Error codes

This section lists the most common error messages you may encounter while creating text, image, and audio embeddings.

* `parameter_invalid`
  * The `text` parameter is invalid. The text token length should be less than or equal to 77.
  * The `text_truncate` parameter is invalid. You should use one of the following values: `none`, `start`, `end`.
