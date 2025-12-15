# Manage entities

<Info>
   The Entity Search feature is currently in beta.
</Info>

Entities represent specific persons that you want to find in your videos. Each entity is part of an entity collection and contains one or more assets that help identify the person. Each asset is an image. Entities serve as the searchable units, and you can reference them in your search queries.

<Note title="Notes">
  * The Marengo 3.0 video understanding engine must be enabled in your index.
  * The platform automatically creates a sample entity collection when you create your account. Users on the Free plan can have a total of one entity collection with up to fifteen entities. The default collection is included in this limit. To create more entity collections, upgrade to the Developer plan. For instructions, see the [Upgrade your plan](/v1.3/docs/get-started/manage-your-plan#upgrade-your-plan) section.
</Note>

To find entities in your video content, follow the steps below:

<Steps>
  <Step>
    [Create an entity collection](/v1.3/api-reference/entities/entity-collections/create) to group related people.
  </Step>

  <Step>
    [Create assets](/v1.3/api-reference/entities/assets/create) (reference images) for each person.
  </Step>

  <Step>
    [Create entities](/v1.3/api-reference/entities/entity-collections/entities/create) and link them to their assets.
  </Step>

  <Step>
    [Use entity IDs in search queries](/v1.3/api-reference/any-to-video-search/make-search-request) with the format `<@entity_id>`.
  </Step>
</Steps>
