# Multipart uploads

<Info>
  The Multipart Upload API is available as a limited, private preview. To request access to the preview version, contact us at 

  [sales@twelvelabs.io](mailto:sales@twelvelabs.io)

  .
</Info>

Utilize the Multipart Upload API to upload large files by dividing them into smaller chunks. This approach enables reliable uploads of large files, particularly when processing chunks in parallel or resuming interrupted transfers. TwelveLabs recommends using this API for files larger than 200 MB, with a maximum size limit of 4 GB.

This method creates an asset that you can use in different workflows.

# Workflow

<Steps>
  <Step>
    Determine the total size of your file in bytes. You'll need this value when creating the upload session.
  </Step>

  <Step>
    **Create an upload session**: Invoke the [`POST`](/v1.3/api-reference/multipart-uploads/create) method of the `/assets/multipart-uploads` endpoint, providing details about your file, including its size. The response contains, among other information, the unique identifier of the asset, a list of upload URLs, and the size of each chunk in bytes.
  </Step>

  <Step>
    **Split your file**: Use the chunk size from the response to divide your file into chunks of the specified size.
  </Step>

  <Step>
    **Upload chunks**: Transfer each chunk to its designated presigned URL. You can upload the chunks in parallel for improved performance. Save the ETag from each upload response for progress reporting.
  </Step>

  <Step>
    *(Optional)* **Request additional URLs**: Invoke the [`POST`](/v1.3/api-reference/multipart-uploads/get-additional-presigned-urls) method of the `/assets/multipart-uploads/{upload_id}/presigned-urls` endpoint if you need URLs for remaining chunks or if existing URLs expire.
  </Step>

  <Step>
    **Report progress**: Submit completed chunks via the [`POST`](/v1.3/api-reference/multipart-uploads/report-chunk-batch) method of the `/assets/multipart-uploads/{upload_id}` endpoint in batches as chunks finish uploading. Use the ETag from each chunk upload as proof of successful transfer.
  </Step>

  <Step>
    **Confirm completion**: The upload is complete when the [`GET`](/v1.3/api-reference/multipart-uploads/get-status) method of the `/assets/multipart-uploads/{upload_id}` endpoint returns `status: 'completed'`. Use the asset ID from step 1 to perform additional operations on your uploaded video.
  </Step>

  <Step>
    **What you do next depends on your use case**:

    * **For creating embeddings** (videos, audio, images): Use the asset ID with the [Embed API v2](/v1.3/api-reference/create-embeddings-v2).
    * **For search and analysis** (videos): [Index your content](/api-reference/index-content/create) using the asset ID.
  </Step>
</Steps>

Note the following about multipart uploads:

* Upload sessions expire after 24 hours.
* Presigned URLs expire after one hour. You can request additional URLs if the original ones expire.
* Clean up temporary chunk files after the upload completes.

# Sample implementation

For a complete working example, see the [Python multipart upload script](https://github.com/twelvelabs-io/twelvelabs-developer-experience/blob/main/scripts/multipart.py) that demonstrates the entire workflow with error handling and parallel chunk uploads.
