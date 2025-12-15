# Index content

Index your uploaded assets to make them searchable and analyzable.

# Workflow

Before you begin, [create an index](/v1.3/api-reference/indexes/create) if you don't have one.

<Steps>
  <Step>
    Upload your content using [direct uploads](/v1.3/api-reference/upload-content/direct-uploads) or [multipart uploads](/v1.3/api-reference/upload-content/multipart-uploads). The platform creates an asset and return its unique identifier.
  </Step>

  <Step>
    Index your content using the [`POST`](/v1.3/api-reference/index-content/create) method of the `/indexes/{index-id}/indexed-assets`.
  </Step>

  <Step>
    Monitor the indexing status until it shows `ready` using the [`GET`](/v1.3/api-reference/index-content/retrieve) method of the `/indexes/{index-id}/indexed-assets/{indexed-asset-id}` endpoint.
  </Step>

  <Step>
    [Search](/v1.3/api-reference/any-to-video-search) or [analyze](/v1.3/api-reference/analyze-videos) your content.
  </Step>
</Steps>
