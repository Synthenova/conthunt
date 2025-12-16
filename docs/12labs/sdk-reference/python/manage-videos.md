# Manage videos

<Info>
  This API will be deprecated in a future version. New implementations should use the 

  [Index content](/v1.3/sdk-reference/python/index-content)

   API.
</Info>

The `IndexesClient.VideosClient` class provides methods to manage the videos you've uploaded to the platform.

# Methods

## Retrieve video information

**Description**: This method retrieves information about the specified video.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
      self,
      index_id: str,
      video_id: str,
      *,
      embedding_option: Optional[Union[VideosRetrieveRequestEmbeddingOptionItem, Sequence[VideosRetrieveRequestEmbeddingOptionItem]]] = None,
      transcription: Optional[bool] = None,
      request_options: Optional[RequestOptions] = None,
  ) -> VideosRetrieveResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from typing import List

  video = client.indexes.videos.retrieve(index_id="<YOUR_INDEX_ID>", video_id="<YOUR_VIDEO_ID>", embedding_option=["visual-text", "audio"])
  print(f"ID: {video.id}")
  print(f"Created at: {video.created_at}")
  print(f"Updated at: {video.updated_at}")
  print(f"Indexed at: {video.indexed_at}")
  print("System metadata:")
  print(f" Filename: {video.system_metadata.filename}")
  print(f" Duration: {video.system_metadata.duration}")
  print(f" FPS: {video.system_metadata.fps}")
  print(f" Width: {video.system_metadata.width}")
  print(f" Height: {video.system_metadata.height}")
  print(f" Size: {video.system_metadata.size}")
  if video.user_metadata:
      print("User metadata:")
      for key, value in video.user_metadata.items():
          print(f"{key}: {value}")
  if video.hls:
      print("HLS:")
      print(f" Video URL: {video.hls.video_url}")
      print(" Thumbnail URLs:")
      for url in video.hls.thumbnail_urls or []:
          print(f" {url}")
      print(f" Status: {video.hls.status}")
      print(f" Updated At: {video.hls.updated_at}")
  if video.transcription:
      print("Transcription:")
      for item in video.transcription:
          print(f" {item.start}-{item.end}s: {item.value}")

  ```
</CodeGroup>

**Parameters**:

| Name               | Type                                                                                                                  | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                             |
| :----------------- | :-------------------------------------------------------------------------------------------------------------------- | :------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `index_id`         | `str`                                                                                                                 | Yes      | The unique identifier of the index to which the video has been uploaded.                                                                                                                                                                                                                                                                                                                                                |
| `video_id`         | `str`                                                                                                                 | Yes      | The unique identifier of the video to retrieve.                                                                                                                                                                                                                                                                                                                                                                         |
| `embedding_option` | `Union`<br />`[VideosRetrieveRequestEmbeddingOptionItem, Sequence`<br />`[VideosRetrieveRequestEmbeddingOptionItem]]` | No       | Specifies which types of embeddings to retrieve. Values vary depending on the version of the model. For details, see the [Embedding options](/v1.3/docs/concepts/modalities#embedding-options) section.<br />To retrieve embeddings for a video, it must be indexed using the Marengo video understanding model version 2.7 or later.<br />The platform does not return embeddings if you don't provide this parameter. |
| `transcription`    | `bool`                                                                                                                | No       | Indicates whether to retrieve a transcription of the spoken words for the indexed video.                                                                                                                                                                                                                                                                                                                                |
| `request_options`  | `RequestOptions`                                                                                                      | No       | Request-specific configuration.                                                                                                                                                                                                                                                                                                                                                                                         |

**Return value**: Returns a `VideosRetrieveResponse` object representing the retrieved video.

The `VideosRetrieveResponse` class contains the following properties:

| Name              | Type                                             | Description                                                                                                                        |
| ----------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `id`              | `Optional[str]`                                  | The unique identifier of the video.                                                                                                |
| `created_at`      | `Optional[str]`                                  | The date and time, in the RFC 3339 format, that the video indexing task was created.                                               |
| `updated_at`      | `Optional[str]`                                  | The date and time, in the RFC 3339 format, that the corresponding video indexing task was last updated.                            |
| `indexed_at`      | `Optional[str]`                                  | The date and time, in the RFC 3339 format, that the video indexing task has been completed.                                        |
| `system_metadata` | `Optional[VideosRetrieveResponseSystemMetadata]` | System-generated metadata about the video.                                                                                         |
| `user_metadata`   | `Optional[Dict[str, Optional[Any]]]`             | User-generated metadata about the video.                                                                                           |
| `hls`             | `Optional[HlsObject]`                            | HLS streaming information for the video.                                                                                           |
| `embedding`       | `Optional[VideosRetrieveResponseEmbedding]`      | Contains the embedding and the associated information. Returned when the `embedding_option` parameter is specified in the request. |
| `transcription`   | `Optional[TranscriptionData]`                    | A list of transcription segments with spoken words and their timestamps.                                                           |

The `VideosRetrieveResponseSystemMetadata` class contains the following properties:

| Name       | Type              | Description                         |
| ---------- | ----------------- | ----------------------------------- |
| `duration` | `Optional[float]` | The duration of the video.          |
| `filename` | `Optional[str]`   | The filename of the video.          |
| `fps`      | `Optional[float]` | The frames per second of the video. |
| `height`   | `Optional[int]`   | The height of the video.            |
| `width`    | `Optional[int]`   | The width of the video.             |

The `VideosRetrieveResponseEmbedding` class contains the following properties:

| Name              | Type                                                      | Description                                                             |
| ----------------- | --------------------------------------------------------- | ----------------------------------------------------------------------- |
| `model_name`      | `Optional[str]`                                           | The name of the video understanding model used to create the embedding. |
| `video_embedding` | `Optional[VideosRetrieveResponseEmbeddingVideoEmbedding]` | An object that contains the embeddings.                                 |

The `VideosRetrieveResponseEmbeddingVideoEmbedding` class contains the following properties:

| Name       | Type                           | Description                                                                   |
| ---------- | ------------------------------ | ----------------------------------------------------------------------------- |
| `segments` | `Optional[List[VideoSegment]]` | An array of objects that contains the embeddings for each individual segment. |

The `TranscriptionDataItem` class contains the following properties:

| Name    | Type              | Description                                                |
| ------- | ----------------- | ---------------------------------------------------------- |
| `start` | `Optional[float]` | The start of the time range, expressed in seconds.         |
| `end`   | `Optional[float]` | The end of the time range, expressed in seconds.           |
| `value` | `Optional[str]`   | Text representing the spoken words within this time range. |

**API Reference**: [Retrieve video information](/v1.3/api-reference/videos/retrieve).

## List videos

**Description**: This method returns a list of the videos in the specified index. By default, the platform returns your videos sorted by creation date, with the newest at the top of the list.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list(
      self,
      index_id: str,
      *,
      page: Optional[int] = None,
      page_limit: Optional[int] = None,
      sort_by: Optional[str] = None,
      sort_option: Optional[str] = None,
      filename: Optional[str] = None,
      duration: Optional[float] = None,
      fps: Optional[float] = None,
      width: Optional[float] = None,
      height: Optional[int] = None,
      size: Optional[float] = None,
      created_at: Optional[str] = None,
      updated_at: Optional[str] = None,
      user_metadata: Optional[Dict[str, Optional[VideosListRequestUserMetadataValue]]] = None,
      request_options: Optional[RequestOptions] = None,
  ) -> SyncPager[VideoVector]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from typing import List

  response = client.indexes.videos.list(
      index_id="<YOUR_VIDEO_ID>",
      filename="01.mp4",
      size=1024,
      width=920,
      height=1080,
      duration=100,
      fps=30,
      user_metadata={"category": "nature"},
      created_at="2024-09-17T07:53:46.365Z",
      updated_at="2024-09-17T07:53:46.365Z",
      page=1,
      page_limit=5,
      sort_by="created_at",
      sort_option="desc"
  )

  for video in response:
      print(f"ID: {video.id}")
      print(f"Created at: {video.created_at}")
      print(f"Updated at: {video.updated_at}")
      print(f"Indexed at: {video.indexed_at}")
      print("System metadata:")
      print(f" Filename: {video.system_metadata.filename}")
      print(f" Duration: {video.system_metadata.duration}")
      print(f" FPS: {video.system_metadata.fps}")
      print(f" Width: {video.system_metadata.width}")
      print(f" Height: {video.system_metadata.height}")
      print(f" Size: {video.system_metadata.size}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                                                      | Required | Description                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `index_id`        | `str`                                                                     | Yes      | The unique identifier of the index for which the API will retrieve the videos.                                               |
| `page`            | `int`                                                                     | No       | A number that identifies the page to retrieve. Default: `1`.                                                                 |
| `page_limit`      | `int`                                                                     | No       | The number of items to return on each page. Default: `10`. Max: `50`.                                                        |
| `sort_by`         | `str`                                                                     | No       | The field to sort on. Available options: `updated_at`, `created_at`. Default: `created_at`.                                  |
| `sort_option`     | `str`                                                                     | No       | The sorting direction. Available options: `asc`, `desc`. Default: `desc`.                                                    |
| `filename`        | `str`                                                                     | No       | Filter by filename.                                                                                                          |
| `duration`        | `float`                                                                   | No       | Filter by duration. Expressed in seconds.                                                                                    |
| `fps`             | `float`                                                                   | No       | Filter by frames per second.                                                                                                 |
| `width`           | `float`                                                                   | No       | Filter by width.                                                                                                             |
| `height`          | `int`                                                                     | No       | Filter by height.                                                                                                            |
| `size`            | `float`                                                                   | No       | Filter by size. Expressed in bytes.                                                                                          |
| `created_at`      | `str`                                                                     | No       | Filter videos by the creation date and time of their associated indexing tasks, in the RFC 3339 format.                      |
| `updated_at`      | `str`                                                                     | No       | Filter videos by the last update date and time, in the RFC 3339 format. Applies only to videos updated using the PUT method. |
| `user_metadata`   | `Dict`<br />`[str, Optional`<br />`[VideosListRequestUserMetadataValue]]` | No       | Filter by user-defined metadata. You must first add user-defined metadata to your video.                                     |
| `request_options` | `RequestOptions`                                                          | No       | Request-specific configuration.                                                                                              |

**Return value**: Returns a `SyncPager[VideoVector]` object that allows you to iterate through the paginated list of videos in the specified index.

The `SyncPager[T]` class contains the following properties and methods:

| Name           | Type                                             | Description                                                            |
| -------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `items`        | `Optional[List[T]]`                              | A list containing the current page of items. Can be `None`.            |
| `has_next`     | `bool`                                           | Indicates whether there is a next page to load.                        |
| `get_next`     | `Optional[Callable[[], Optional[SyncPager[T]]]]` | A callable function that retrieves the next page. Can be `None`.       |
| `response`     | `Optional[BaseHttpResponse]`                     | The HTTP response object. Can be `None`.                               |
| `next_page()`  | `Optional[SyncPager[T]]`                         | Calls `get_next()` if available and returns the next page object.      |
| `__iter__()`   | `Iterator[T]`                                    | Allows iteration through all items across all pages using `for` loops. |
| `iter_pages()` | `Iterator[SyncPager[T]]`                         | Allows iteration through page objects themselves.                      |

The `VideoVector` class contains the following properties:

| Name              | Type                                  | Description                                                                                                                                                |
| ----------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`              | `Optional[str]`                       | The unique identifier of a video. The platform creates a new video object and assigns it a unique identifier when the video has successfully been indexed. |
| `created_at`      | `Optional[str]`                       | The date and time, in the RFC 3339 format, that the video indexing task was created.                                                                       |
| `updated_at`      | `Optional[str]`                       | The date and time, in the RFC 3339 format, that the video indexing task object was last updated.                                                           |
| `indexed_at`      | `Optional[str]`                       | The date and time, in the RFC 3339 format, that the video indexing task has been completed.                                                                |
| `system_metadata` | `Optional[VideoVectorSystemMetadata]` | System-generated metadata about the video.                                                                                                                 |

The `VideoVectorSystemMetadata` class contains the following properties:

| Name       | Type              | Description                         |
| ---------- | ----------------- | ----------------------------------- |
| `filename` | `Optional[str]`   | The filename of the video.          |
| `duration` | `Optional[float]` | The duration of the video.          |
| `fps`      | `Optional[float]` | The frames per second of the video. |
| `width`    | `Optional[int]`   | The width of the video.             |
| `height`   | `Optional[int]`   | The height of the video.            |
| `size`     | `Optional[float]` | The size of the video in bytes.     |

**API Reference**: [List videos](/v1.3/api-reference/videos/list) page.

## Update video information

**Description**: This method updates the title and metadata of a video.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def update(
      self,
      index_id: str,
      video_id: str,
      *,
      user_metadata: Optional[Dict[str, Optional[Any]]] = OMIT,
      request_options: Optional[RequestOptions] = None,
  ) -> None
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client.indexes.videos.update(
      index_id="<YOUR_INDEX_ID>",
      video_id="<YOUR_VIDEO_ID>",
      user_metadata={
          "category": "recentlyAdded",
          "batchNumber": 5,
          "rating": 9.3,
          "needsReview": True
      }
  )
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                 | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| :---------------- | :----------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `index_id`        | `str`                                | Yes      | The unique identifier of the index to which the video has been uploaded.                                                                                                                                                                                                                                                                                                                                                                                                        |
| `video_id`        | `str`                                | Yes      | The unique identifier of the video to update.                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `user_metadata`   | `Optional[Dict[str, Optional[Any]]]` | No       | Metadata that helps you categorize your videos. You can specify a list of keys and values. Keys must be of type `string`, and values can be of the following types: `string`, `integer`, `float` or `boolean`. If you want to store other types of data such as objects or arrays, you must convert your data into string values. You cannot override system-generated metadata fields: `duration`, `filename`, `fps`, `height`, `model_names`, `size`, `video_title`, `width`. |
| `request_options` | `RequestOptions`                     | No       | Request-specific configuration.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

**Return value**: `None`. The method doesn't return any value.

**API Reference**: [Update video information](/v1.3/api-reference/videos/update).

## Delete video information

**Description**: This method deletes all the information about the specified video. This action cannot be undone.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def delete(
      self,
      index_id: str,
      video_id: str,
      *,
      request_options: Optional[RequestOptions] = None
  ) -> None
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client.indexes.videos.delete(index_id="<YOUR_INDEX_ID>", video_id="<YOUR_VIDEO_ID>")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                              |
| :---------------- | :--------------- | :------- | :----------------------------------------------------------------------- |
| `index_id`        | `str`            | Yes      | The unique identifier of the index to which the video has been uploaded. |
| `video_id`        | `str`            | Yes      | The unique identifier of the video to delete.                            |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                          |

**Return value**: `None`. The method doesn't return any value.

**API Reference**: [Delete video information](/v1.3/api-reference/videos/delete).
