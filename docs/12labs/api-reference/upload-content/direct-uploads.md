# Direct uploads

Upload videos, images, and audio files to the TwelveLabs platform. Direct uploads are processed asynchronously - you initiate the upload and monitor its status until the asset is ready. This method creates an asset that you can use in different workflows.

# Workflow

<Steps>
  <Step>
    Upload your file using the [`POST`](/v1.3/api-reference/upload-content/direct-uploads/create) method of the `/assets` endpoint. You receive the asset ID in the response.
  </Step>

  <Step>
    Monitor the indexing status using the [`GET`](/v1.3/api-reference/index-content/retrieve) method of the `/indexes/{index-id}/indexed-assets/{indexed-asset-id}` endpoint until it's ready.
  </Step>

  <Step>
    What you do next depends on your use case:

    * **For creating embeddings** (videos, audio, images): Use the asset ID with the [Embed API v2](/v1.3/api-reference/create-embeddings-v2).
    * **For entity search** (images): Use the asset ID to [create entities](/v1.3/api-reference/entities/entity-collections/entities/create).
    * **For search and analysis** (videos): [Index your asset](/api-reference/index-content/create) using the asset ID.
  </Step>
</Steps>
