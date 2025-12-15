# Multipart uploads

<Info>
  The Multipart Upload API is available as a limited, private preview. To request access to the preview version, contact us at 

  [sales@twelvelabs.io](mailto:sales@twelvelabs.io)

  .
</Info>

The `MultipartUploadClient` class provides methods to manage multipart upload sessions.

Utilize multipart uploads to upload large files by dividing them into smaller chunks. This approach enables reliable uploads of large files, particularly when processing chunks in parallel or resuming interrupted transfers. TwelveLabs recommends using this method for files larger than 200 MB, with a maximum size limit of 4 GB.

This method creates an asset that you can use in different workflows.

# Workflow

<Steps>
  <Step>
    Determine the total size of your file in bytes. You'll need this value when creating the upload session.
  </Step>

  <Step>
    **Create an upload session**: Call the [`multipart_upload.create`](/v1.3/sdk-reference/python/upload-content/multipart-uploads#create-a-multipart-upload-session) method, providing details about your file, including its size. The response contains, among other information, the unique identifier of the asset, a list of upload URLs, and the size of each chunk in bytes.
  </Step>

  <Step>
    **Split your file**: Use the chunk size from the response to divide your file into chunks of the specified size.
  </Step>

  <Step>
    **Upload chunks**: Transfer each chunk to its designated presigned URL. You can upload the chunks in parallel for improved performance. Save the ETag from each upload response for progress reporting.
  </Step>

  <Step>
    *(Optional)* **Request additional URLs**: Call the [`multipart_upload.get_additional_presigned_urls`](/v1.3/sdk-reference/python/upload-content/multipart-uploads#request-presigned-urls-for-the-remaining-chunks) if you need URLs for remaining chunks or if existing URLs expire.
  </Step>

  <Step>
    **Report progress**: Submit completed chunks via the [`multipart_upload.report_chunk_batch`](/v1.3/sdk-reference/python/upload-content/multipart-uploads#report-uploaded-chunks) method in batches as chunks finish uploading. Use the ETag from each chunk upload as proof of successful transfer.
  </Step>

  <Step>
    **Confirm completion**: The upload is complete when the [`multipart_upload.get_status`](/v1.3/sdk-reference/python/upload-content/multipart-uploads#retrieve-the-status-of-an-upload-session) mathod returns `status: 'completed'`. Use the asset ID from step 1 to perform additional operations on your uploaded video.
  </Step>

  <Step>
    **What you do next depends on your use case**:

    * **For creating embeddings** (videos, audio, images): Use the asset ID with the [Embed API v2](/v1.3/sdk-reference/python/create-embeddings-v-2).
    * **For search and analysis** (videos): [Index an asset](/v1.3/sdk-reference/python/index-content#index-an-asset) using the asset ID.
  </Step>
</Steps>

# Methods

## List incomplete uploads

**Description**: This method returns a list of all incomplete multipart upload sessions in your account.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list_incomplete_uploads(
      self,
      *,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[IncompleteUploadSummary]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.multipart_upload.list_incomplete_uploads(
      page=1,
      page_limit=10,
  )

  print("Incomplete Uploads:")
  for upload in response:
      print(f"  Upload ID: {upload.upload_id}")
      print(f"  Status: {upload.status}")
      print(f"  Total size: {upload.total_size}")
      print(f"  Total chunks: {upload.total_chunks}")
      print(f"  Expires at: {upload.expires_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                           |
| ----------------- | ---------------- | -------- | --------------------------------------------------------------------- |
| `page`            | `int`            | No       | A number that identifies the page to retrieve. Default: `1`.          |
| `page_limit`      | `int`            | No       | The number of items to return on each page. Default: `10`. Max: `50`. |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                       |

**Return value**: Returns a `SyncPager[IncompleteUploadSummary]` object that allows you to iterate through the paginated results.

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

The `IncompleteUploadSummary` class contains the following properties:

| Name           | Type                        | Description                                            |
| -------------- | --------------------------- | ------------------------------------------------------ |
| `upload_id`    | `str`                       | The unique identifier of your upload session.          |
| `status`       | `MultipartUploadStatusType` | The current status of the upload session.              |
| `total_size`   | `int`                       | Total size of the file in bytes.                       |
| `chunk_size`   | `int`                       | The size of each chunk in bytes.                       |
| `total_chunks` | `int`                       | The total number of chunks in this upload session.     |
| `created_at`   | `Optional[datetime]`        | The date and time when the upload session was created. |
| `expires_at`   | `Optional[datetime]`        | The date and time when the upload session expires.     |

**API Reference**: [List incomplete uploads](/v1.3/api-reference/upload-content/multipart-uploads/list-incomplete-uploads)

## Create a multipart upload session

**Description**: This method creates a multipart upload session.

**Supported content**: Video and audio

**File size**: 4GB maximum.

**Additional requirements** depend on your workflow:

* **Search**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)
* **Video analysis**: [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#input-requirements)
* **Create embeddings**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#input-requirements)

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      filename: str,
      total_size: int,
      request_options: typing.Optional[RequestOptions] = None
  ) -> CreateAssetUploadResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  import os

  file_path = "<YOUR_FILE_PATH>"
  file_size = os.path.getsize(file_path)

  upload_session = client.multipart_upload.create(
      filename="<YOUR_FILE_NAME>",
      total_size=file_size,
  )

  print(f"Upload ID: {upload_session.upload_id}")
  print(f"Asset ID: {upload_session.asset_id}")
  print(f"Chunk size: {upload_session.chunk_size}")
  print(f"Total chunks: {upload_session.total_chunks}")
  print(f"Number of initial URLs: {len(upload_session.upload_urls)}")
  print(f"Expires at: {upload_session.expires_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                                                                                                                                                                           |
| ----------------- | ---------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `filename`        | `str`            | Yes      | The original file name of the asset.                                                                                                                                                                                  |
| `total_size`      | `int`            | Yes      | The total size of the file in bytes. The platform uses this value to:<br />- Calculate the optimal chunk size.<br />- Determine the total number of chunks required<br />- Generate the initial set of presigned URLs |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                                                                                                                                                                       |

**Return value**: Returns a `CreateAssetUploadResponse` object containing details about the upload session.

The `CreateAssetUploadResponse` class contains the following properties:

| Name             | Type                                | Description                                                                                                                                                                                                                                                                                                                                   |
| ---------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `upload_id`      | `Optional[str]`                     | The unique identifier of this upload session. Store this value, as you'll need it for the following subsequent operations:<br />- Reporting completed chunks<br />- Requesting additional presigned URLs<br />- Retrieving the status of this upload session<br /><br />This identifier remains valid for 24 hours from the time of creation. |
| `asset_id`       | `Optional[str]`                     | The unique identifier for the asset being created. Store this value, as you'll need it to reference the asset in other API calls. Note that this identifier is reserved immediately, but the asset becomes available for other operations only after the upload is completed successfully.                                                    |
| `upload_urls`    | `Optional[List[PresignedUrlChunk]]` | The initial set of presigned URLs for uploading chunks. Each URL corresponds to a specific chunk.<br /><br />**NOTES**:<br />- URLs expire after one hour.<br />- Depending on the size of the file, this initial set may not include URLs for all chunks. You can request more using the `get_additional_presigned_urls` method.<br />       |
| `upload_headers` | `Optional[Dict[str, str]]`          | Headers to include when uploading chunks to the presigned URLs.                                                                                                                                                                                                                                                                               |
| `chunk_size`     | `Optional[int]`                     | The size in bytes for each chunk, except for the last chunk, which may be smaller. Use this value to divide your file into chunks of this exact size.                                                                                                                                                                                         |
| `total_chunks`   | `Optional[int]`                     | The total number of chunks into which your file must be split. Calculated as: ceiling(`total_size` / `chunk_size`).                                                                                                                                                                                                                           |
| `expires_at`     | `Optional[datetime]`                | A string representing the date and time, in RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when the upload URL will expire. Upload URLs expire 24 hours from their creation. After expiration, you cannot resume the upload, and you must create a new upload session.                                                                             |

The `PresignedUrlChunk` class contains the following properties:

| Name          | Type                 | Description                                                                                            |
| ------------- | -------------------- | ------------------------------------------------------------------------------------------------------ |
| `chunk_index` | `Optional[int]`      | The index of this chunk.                                                                               |
| `url`         | `Optional[str]`      | The presigned URL for uploading this chunk. Each URL can only be used once and expires after one hour. |
| `expires_at`  | `Optional[datetime]` | The date and time when the presigned URL expires.                                                      |

**API Reference**: [Create a multipart upload session](/v1.3/api-reference/upload-content/multipart-uploads/create)

## Retrieve the status of an upload session

**Description**: This method retrieves information about an upload session, including its current status, chunk-level progress, and completion state.

Use this method to:

* Verify upload completion (`status` = `completed`)
* Identify any failed chunks that require a retry
* Monitor the upload progress by comparing `uploaded_size` with `total_size`
* Determine if the session has expired
* Retrieve the status information for each chunk

You must call this method after reporting chunk completion to confirm the upload has transitioned to the `completed` status before using the asset.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def get_status(
      self,
      upload_id: str,
      *,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[ChunkInfo]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.multipart_upload.get_status(
      upload_id="<YOUR_SESSION_ID>",
      page=1,
      page_limit=50,
  )

  print("Chunk status:")
  for chunk in response:
      print(f"  Chunk {chunk.index}: {chunk.status}")
      if chunk.status == "completed":
          print(f"    Uploaded at: {chunk.uploaded_at}")
      elif chunk.status == "failed":
          print(f"    Error: {chunk.error}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                           |
| ----------------- | ---------------- | -------- | --------------------------------------------------------------------- |
| `upload_id`       | `str`            | Yes      | The unique identifier of the upload session.                          |
| `page`            | `int`            | No       | A number that identifies the page to retrieve. Default: `1`.          |
| `page_limit`      | `int`            | No       | The number of items to return on each page. Default: `10`. Max: `50`. |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                       |

**Return value**: Returns a `SyncPager[ChunkInfo]` object that allows you to iterate through the paginated chunk status information.

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

The `ChunkInfo` class contains the following properties:

| Name          | Type                        | Description                                                                                                                                                                                                                                                                                        |
| ------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `index`       | `Optional[int]`             | The index of the chunk. The platform uses 1-based indexing, and this value matches the value of the `chunk_index` field in the list of upload URLs.                                                                                                                                                |
| `status`      | `Optional[ChunkInfoStatus]` | The current status of this chunk. Values:<br />- `completed`: Successfully uploaded and reported.<br />- `pending`: Not yet reported. A chunk may be in this status if it has been uploaded but not yet reported.<br />- `failed`: The upload process failed; you must retry uploading this chunk. |
| `uploaded_at` | `Optional[datetime]`        | The date and time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when this chunk was successfully reported as uploaded. The value of this field is `null` for pending or failed chunks.                                                                                                         |
| `updated_at`  | `Optional[datetime]`        | The date and time when this chunk was last updated.                                                                                                                                                                                                                                                |
| `error`       | `Optional[str]`             | A detailed error message explaining why this chunk failed. The platform returns this field only when the status is failed.                                                                                                                                                                         |

**API Reference**: [Retrieve the status of an upload session](/v1.3/api-reference/multipart-uploads/get-status)

## Report uploaded chunks

**Description**: This method reports successfully uploaded chunks to the platform. The platform finalizes the upload after you report all chunks.

For optimal performance, report chunks in batches and in any order.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def report_chunk_batch(
      self,
      upload_id: str,
      *,
      completed_chunks: typing.Sequence[CompletedChunk],
      request_options: typing.Optional[RequestOptions] = None,
  ) -> ReportChunkBatchResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs, CompletedChunk

  response = client.multipart_upload.report_chunk_batch(
      upload_id="<YOUR_UPLOAD_ID>",
      completed_chunks=[
          CompletedChunk(
              chunk_index=1,
              proof="<YOUR_PROOF_ID>",
              chunk_size=5242880,
          ),
          CompletedChunk(
              chunk_index=2,
              proof="<YOUR_PROOF_ID>",
              chunk_size=5242880,
          ),
          CompletedChunk(
              chunk_index=3,
              proof="<YOUR_PROOF_ID>",
              chunk_size=5242880,
          ),
      ],
  )

  print(f"Processed chunks: {response.processed_chunks}")
  print(f"Duplicate chunks: {response.duplicate_chunks}")
  print(f"Total completed: {response.total_completed}")

  if response.url:
      print(f"Upload complete! Asset URL: {response.url}")
      print(f"Asset ID: {response.asset_id}")
  ```
</CodeGroup>

**Parameters**:

| Name               | Type                       | Required | Description                                                                                                          |
| ------------------ | -------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| `upload_id`        | `str`                      | Yes      | The unique identifier of the upload session.                                                                         |
| `completed_chunks` | `Sequence[CompletedChunk]` | Yes      | The list of chunks successfully uploaded that you're reporting to the platform. Report only after receiving an ETag. |
| `request_options`  | `RequestOptions`           | No       | Request-specific configuration.                                                                                      |

The `CompletedChunk` class contains the following properties:

| Name          | Type              | Description                                                                                                                                                                                                    |
| ------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `chunk_index` | `int`             | The number that identifies which chunk you uploaded. When you received presigned URLs from the platform, each URL was assigned an index number. Use that same number. The chunks are numbered starting from 1. |
| `proof`       | `str`             | The ETag value you received after uploading the chunk. When you upload a chunk to a presigned URLs, the response includes an ETag. Use this value and submit it as proof of successful upload.                 |
| `proof_type`  | `Literal["etag"]` | The verification method. Supported value: `etag`. Default: `etag`.                                                                                                                                             |
| `chunk_size`  | `int`             | The number of bytes uploaded for this chunk. For all chunks except the last, this value equals `chunk_size`. For the last chunk, it may be smaller.                                                            |

**Return value**: Returns a `ReportChunkBatchResponse` object containing information about the reported chunks.

The `ReportChunkBatchResponse` class contains the following properties:

| Name               | Type            | Description                                                                                                                                                                                       |
| ------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | `Optional[str]` | The URL for accessing your asset. The platform returns this field only when all chunks are reported and the upload is complete. If absent, continue uploading and reporting the remaining chunks. |
| `asset_id`         | `Optional[str]` | The unique identifier of this asset.                                                                                                                                                              |
| `processed_chunks` | `Optional[int]` | The number of chunks accepted from this specific request. This equals the number of chunks in your `completed_chunks` array minus any duplicates.                                                 |
| `duplicate_chunks` | `Optional[int]` | The number of chunks in this request that were already reported. Duplicates are ignored and don't affect your upload.                                                                             |
| `total_completed`  | `Optional[int]` | The cumulative count of all unique chunks successfully reported across all requests. When this equals `total_chunks`, the upload is complete.                                                     |

**API Reference**: [Report uploaded chunks](/v1.3/api-reference/upload-content/multipart-uploads/report-chunk-batch)

## Request presigned URLs for the remaining chunks

**Description**: This method generates new presigned URLs for specific chunks that require uploading. Use this method in the following situations:

* Your initial URLs have expired (URLs expire after one hour).
* The initial set of presigned URLs does not include URLs for all chunks.
* You need to retry failed chunk uploads with new URLs.

To specify which chunks need URLs, use the `start` and `count` parameters. For example, to generate URLs for chunks 21 to 30, use `start=21` and `count=10`.

The response provides new URLs, each with a fresh expiration time of one hour.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def get_additional_presigned_urls(
      self,
      upload_id: str,
      *,
      start: int,
      count: int,
      request_options: typing.Optional[RequestOptions] = None
  ) -> RequestAdditionalPresignedUrLsResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.multipart_upload.get_additional_presigned_urls(
      upload_id="<YOUR_UPLOAD_ID>",
      start=21,
      count=10,
  )

  print(f"Upload ID: {response.upload_id}")
  print(f"Start index: {response.start_index}")
  print(f"Count: {response.count}")
  print(f"Generated at: {response.generated_at}")
  print(f"Expires at: {response.expires_at}")

  # Use the presigned URLs to upload chunks
  for url_chunk in response.upload_urls:
      print(f"Chunk {url_chunk.chunk_index}: {url_chunk.url}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                                                                                  |
| ----------------- | ---------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `upload_id`       | `str`            | Yes      | The unique identifier of the upload session.                                                                                 |
| `start`           | `int`            | Yes      | The index of the first chunk number to generate URLs for. Chunks are numbered from 1.                                        |
| `count`           | `int`            | Yes      | The number of presigned URLs to generate starting from the index. You can request a maximum of 50 URLs in a single API call. |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                                                                              |

**Return value**: Returns a `RequestAdditionalPresignedUrLsResponse` object containing the new presigned URLs.

The `RequestAdditionalPresignedUrLsResponse` class contains the following properties:

| Name           | Type                                | Description                                                                                                                                    |
| -------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `upload_id`    | `Optional[str]`                     | The unique identifier of the upload session associated with these URLs.                                                                        |
| `start_index`  | `Optional[int]`                     | The index of the first chunk number in this set of URLs. Matches the start value from your request.                                            |
| `count`        | `Optional[int]`                     | The number of new URLs created. Matches the count value from your request.                                                                     |
| `upload_urls`  | `Optional[List[PresignedUrlChunk]]` | An array of additional presigned URLs for uploading chunks.                                                                                    |
| `generated_at` | `Optional[datetime]`                | The date and time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when these URLs were created. URLs remain valid for 1 hour from this time. |
| `expires_at`   | `Optional[datetime]`                | The date and time when the upload session expires.                                                                                             |

**API Reference**: [Request presigned URLs for the remaining chunks](/v1.3/api-reference/upload-content/multipart-uploads/get-additional-presigned-urls)
