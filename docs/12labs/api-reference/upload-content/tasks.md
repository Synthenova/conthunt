# Video indexing tasks

<Info>
  This method will be deprecated in a future version. New implementations should use direct or multipart uploads followed by 

  [separate indexing](/v1.3/api-reference/index-content/create)

  .
</Info>

Upload and index videos in a single operation. This method bundles upload and indexing together and returns a task ID that you monitor until the process completes.

<Note title="Note">
  When using this endpoint, you can set up webhooks to receive notifications. For details, see the [Webhooks](/v1.3/docs/advanced/webhooks/manage) section.
</Note>
