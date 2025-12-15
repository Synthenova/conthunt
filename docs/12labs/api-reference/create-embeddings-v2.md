# Create embeddings v2

Use the Embed API v2 to create embeddings for text, images, audio, and video content. Embeddings are vector representations that enable semantic search and content understanding.

<Note title="Note">
  This API only supports Marengo version 3.0 or newer.
</Note>

# Choose an endpoint

* For text, images, or audio/video under 10 minutes use the [`POST`](/v1.3/api-reference/create-embeddings-v2/create-embeddings) method of the `/embed-v2` endpoint.
* For audio and video up to 4 hours, use the [`POST`](/v1.3/api-reference/create-embeddings-v2/create-async-embedding-task) method of the `/embed-v2/tasks` endpoint.
