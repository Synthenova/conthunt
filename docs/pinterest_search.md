I want to make an API call to https://api.scrapecreators.com/v1/pinterest/search. 

  Please help me write code to make this API call and handle the response appropriately. Include error handling and best practices.

  Here are the details:
  
  Endpoint: GET https://api.scrapecreators.com/v1/pinterest/search
  
  Description: Search Pinterest
  
  Required Headers:
  - x-api-key: Your API key
  
  Parameters:
  - query  (Required): Search query
- cursor : Cursor
- trim : Set to true for a trimmed down version of the response
  
  Example Response:
  {
  "success": true,
  "pins": [
    {
      "node_id": "UGluOjM3Mjk2MTIyNTY2MDUxNDQ=",
      "url": "https://www.pinterest.com/pin/3729612256605144/",
      "auto_alt_text": "a close up of a plate of food with meat",
      "id": "3729612256605144",
      "is_promoted": false,
      "description": "Italian Pot Roast: A Hearty and Flavorful Recipe",
      "title": "",
      "images": {
        "orig": {
          "width": 1024,
          "height": 1024,
          "url": "https://i.pinimg.com/originals/c0/ad/f4/c0adf44a87470e7287219893efa5df75.webp"
        }
      },
      "link": "https://myauntyrecipes.com/2024/10/23/italian-pot-roast/?tp_image_id=7421",
      "domain": "myauntyrecipes.com",
      "seo_alt_text": "a close up of a plate of food with meat",
      "board": {
        "node_id": "Qm9hcmQ6MzcyOTY4MDg4MDQyNzg2OA==",
        "name": "Food",
        "cover_images": {
          "222x": {
            "url": "https://i.pinimg.com/222x/fb/a4/05/fba405834dc4bb6cceefe63c7d2f566c.jpg",
            "width": 222,
            "height": null
          }
        },
        "owner": {
          "node_id": "VXNlcjozNzI5NzQ5NTk5ODUyNTc1",
          "verified_identity": {},
          "follower_count": 85,
          "full_name": "Courtney Elizabeth",
          "image_large_url": "https://i.pinimg.com/140x140_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
          "is_ads_only_profile": false,
          "id": "3729749599852575",
          "image_small_url": "https://i.pinimg.com/30x30_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
          "image_medium_url": "https://i.pinimg.com/75x75_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
          "ads_only_profile_site": null,
          "is_primary_website_verified": false,
          "is_verified_merchant": false,
          "username": "csadak"
        },
        "id": "3729680880427868",
        "url": "/csadak/food/",
        "collaborating_users": [],
        "images": {
          "170x": [
            {
              "url": "https://i.pinimg.com/170x/8c/80/93/8c80939c8ed0349262b9bb32a8e0192f.jpg",
              "width": 170,
              "height": 339,
              "dominant_color": "#E1B342"
            }
          ]
        },
        "pin_count": 423,
        "is_collaborative": false,
        "section_count": 10,
        "board_order_modified_at": "Sat, 19 Apr 2025 17:05:53 +0000",
        "type": "board",
        "collaborator_count": 0
      },
      "grid_title": "Savory Italian Pot Roast",
      "native_creator": null,
      "created_at": "Tue, 07 Jan 2025 18:23:09 +0000",
      "pinner": {
        "node_id": "VXNlcjozNzI5NzQ5NTk5ODUyNTc1",
        "verified_identity": {},
        "follower_count": 85,
        "full_name": "Courtney Elizabeth",
        "image_large_url": "https://i.pinimg.com/140x140_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
        "is_ads_only_profile": false,
        "id": "3729749599852575",
        "image_small_url": "https://i.pinimg.com/30x30_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
        "image_medium_url": "https://i.pinimg.com/75x75_RS/71/b7/c7/71b7c71b452076af02217324c26b3f08.jpg",
        "ads_only_profile_site": null,
        "is_primary_website_verified": false,
        "is_verified_merchant": false,
        "username": "csadak"
      },
      "videos": null,
      "story_pin_data": null
    }
  ],
  "cursor": "Y2JVSG81V2..."
}
  
  