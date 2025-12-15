# Upload content

The `AssetsClient` class provides methods for uploading your videos, images, and audio files to the TwelveLabs platform. Uploading creates an asset that you can then use in different workflows.

Choose an upload method based on your file size and workflow.

# Direct uploads

Upload whole files without splitting them.

**Use this method when**:

* You want a simple upload process
* You want to upload images, videos, or audio content

**Limits**:

* Local files: 200MB maximum
* URL uploads: 4GB maximum

<Card title="Direct uploads" href="/v1.3/sdk-reference/python/upload-content/direct-uploads" />

# Multipart uploads

Upload large files using chunked transfers with parallel processing. This method splits files into smaller chunks for reliable uploads.

**Use this method when**:

* You need to upload local files larger than 200MB
* You want parallel chunk uploads for faster performance
* You want to upload video or audio content

**Limits**:

* Maximum file size: 4GB

<Card title="Multipart uploads" href="/v1.3/sdk-reference/python/upload-content/multipart-uploads" />

# Video indexing tasks

<Info>
  This method will be deprecated in a future version. New implementations should use direct or multipart uploads followed by 

  [separate indexing](/v1.3/sdk-reference/python/index-content#index-an-asset)

  .
</Info>

Upload and index videos in one operation. This method bundles upload and indexing together.

<Card title="Video indexing tasks" href="/v1.3/sdk-reference/python/upload-content/video-indexing-tasks" />
