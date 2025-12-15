# Upload content

Upload your videos, images, and audio files to the TwelveLabs platform. Uploading creates an asset that you can then use in different workflows.

{/* After you upload a file, you receive an asset ID. What you do next depends on your use case:

**For entity search** (images): Use the asset ID to [create entities](/v1.3/api-reference/entities/entity-collections/entities/create)

**For creating embeddings** (videos, audio, images): Use the asset ID with the [Embed API v2](/v1.3/api-reference/create-embeddings-v2)

**For search and analysis** (videos):
    1. [Index your content](/v1.3/api-reference/index-content) 
    2. [Search](/v1.3/api-reference/entities/entity-collections/entities/remove-assets) or [analyze it](/v1.3/api-reference/analyze-videos). */}

Choose an upload method based on your file size and workflow.

# Direct uploads

Upload whole files without splitting them.

{/* This method returns an asset ID that you use to index your content. */}

**Use this method when**:

{/* - Your files are under 4GB */}

* You want a simple upload process
* You want to upload images, videos, or audio content

**Limits**:

* Local files: 200MB maximum
* URL uploads: 4GB maximum

<Card title="Direct uploads" href="/v1.3/api-reference/upload-content/direct-uploads" />

# Multipart uploads

Upload large files using chunked transfers with parallel processing. This method splits files into smaller chunks for reliable uploads.

{/* and returns an asset ID. */}

**Use this method when**:

* You need to upload local files larger than 200MB
* You want parallel chunk uploads for faster performance
* You want to upload video or audio content

**Limits**:

* Maximum file size: 4GB

<Card title="Multipart uploads" href="/v1.3/api-reference/upload-content/multipart-uploads" />

# Video indexing tasks

<Info>
  This method will be deprecated in a future version. New implementations should use direct or multipart uploads followed by 

  [separate indexing](/v1.3/api-reference/index-content/create)

  .
</Info>

Upload and index videos in one operation. This method bundles upload and indexing together.

<Card title="Video indexing tasks" href="/v1.3/api-reference/upload-content/tasks" />
