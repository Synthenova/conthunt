I want to make an API call to https://api.scrapecreators.com/v1/instagram/reels/search. 

  Please help me write code to make this API call and handle the response appropriately. Include error handling and best practices.

  Here are the details:
  
  Endpoint: GET https://api.scrapecreators.com/v1/instagram/reels/search
  
  Description: Search for reels by keyword. Can only return a max of 60. *Costs 1 credit per 10 reels. Might be a little slow if you request more than 20, reason is we have to scrape search results first, then scrape every reel from each results.
  
  Required Headers:
  - x-api-key: Your API key
  
  Parameters:
  - query  (Required): Keyword to search for
- amount : Number of reels to return (max 60)
  
  Example Response:
  {
  "success": true,
  "credits_remaining": 9981694,
  "reels": [
    {
      "id": "3744043036998479424",
      "__typename": "XDTGraphVideo",
      "shortcode": "DP1g04sEa5A",
      "url": "https://www.instagram.com/reel/DP1g04sEa5A/",
      "caption": "With the rising popularity of hybrid training, here’s everything you need to know as a runner when incorporating lifting into your routine from expert coach @abbiedennisonfit to maximize your training. 🏋️‍♂️🏃‍♀️",
      "thumbnail_src": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-15/565557031_1157104719083158_8739689908830923358_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=110&_nc_oc=Q6cZ2QFSRLOM1XJUl8wbnRxe9rLHovrLCQXvzYw_Ayt4IzUFKfmW7yHQ7UBFvhFf4jpPXRU&_nc_ohc=B_YjbljW4FMQ7kNvwGCaOc2&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeqqwkfS7txhl5Bp3k5FzNZxzdcGMtjimnwglm-EnPa8w&oe=68F5BD97&_nc_sid=d885a2",
      "display_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-15/565557031_1157104719083158_8739689908830923358_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=110&_nc_oc=Q6cZ2QFSRLOM1XJUl8wbnRxe9rLHovrLCQXvzYw_Ayt4IzUFKfmW7yHQ7UBFvhFf4jpPXRU&_nc_ohc=B_YjbljW4FMQ7kNvwGCaOc2&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afef3rx84NlqQ6y3H5SiixKNDQl23PdbW2TBmUfXnpvveA&oe=68F5BD97&_nc_sid=d885a2",
      "video_url": "https://instagram.fsac1-1.fna.fbcdn.net/o1/v/t2/f2/m86/AQMMUqzH7-QP-VU_TMyHmXPHoB_hnMdObjAOVaVV_YVstn1CDiLKRNMJu177aOzJx2PY8Y1Ui3adAjKJxjDKsE5UsaOn4wp9dt1deaQ.mp4?_nc_cat=103&_nc_oc=Adkzrw2US_6jcRXZtE3fg0qGX10hN2WevFUbH7HXAupR6ZQ8IWkP2xd9Gd_ZvfmJEzY&_nc_sid=5e9851&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_ohc=8RPKpNYEaCQQ7kNvwHckSux&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MTU3NDgzNzgwMzg5ODY1OCwidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjQ5LCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=9b654ff84def05e2&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC8xNDQ5N0FBMDU3NjQyRTQ5Q0M3MURBREQ5Qzg3RTg4MF92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HR1d2dVNFN3JJbkF5VVFGQUExd0c4ZExkUVpYYnN0VEFRQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmxNyK_s-TzAUVAigCQzMsF0BI7tkWhysCGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&_nc_zt=28&oh=00_AfdhdvEzaiBBvCs0JrP02nuX4PWn_oXV5nKBKVtdptJS2w&oe=68F1FCA4",
      "has_audio": false,
      "accessibility_caption": null,
      "video_view_count": 3770,
      "video_play_count": 14750,
      "product_type": "clips",
      "video_duration": 49.866,
      "clips_music_attribution_info": {
        "artist_name": "joinladder",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "24452552341111704"
      },
      "is_video": true,
      "owner": {
        "id": "2028540658",
        "username": "joinladder",
        "is_verified": true,
        "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/414699760_1541932796554865_7348215616885103575_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby40MDAuYzIifQ&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2QFSRLOM1XJUl8wbnRxe9rLHovrLCQXvzYw_Ayt4IzUFKfmW7yHQ7UBFvhFf4jpPXRU&_nc_ohc=sbtSZ73M3qEQ7kNvwFZO-oH&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfctSPeqgI2yErkP99LpMcbygvps7584rVYZvlMssVpVpQ&oe=68F5F43B&_nc_sid=d885a2",
        "full_name": "Ladder",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 411575,
        "post_count": 1107
      },
      "taken_at": "2025-10-15T16:13:09.000Z",
      "is_ad": false,
      "like_count": 350,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 5,
      "comments": [
        {
          "id": "18012401585627100",
          "text": "HYBRID 🐐!",
          "owner": {
            "id": "370586152",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/87236753_2400841140245926_166946710235381760_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=110&_nc_oc=Q6cZ2QFSRLOM1XJUl8wbnRxe9rLHovrLCQXvzYw_Ayt4IzUFKfmW7yHQ7UBFvhFf4jpPXRU&_nc_ohc=zes52-H7dnAQ7kNvwGKoyEw&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcV3H1wR4R6SdYt87mlxLEfHpjjZNGhqJQQfayR0WLI1Q&oe=68F5D0B5&_nc_sid=d885a2",
            "username": "edsel"
          },
          "like_count": 1,
          "created_at": "2025-10-15T17:20:33.000Z"
        },
        {
          "id": "18065462174368601",
          "text": "So well said! 👏",
          "owner": {
            "id": "68271436981",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/538400719_17895934848276982_5977579541004963910_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=110&_nc_oc=Q6cZ2QFSRLOM1XJUl8wbnRxe9rLHovrLCQXvzYw_Ayt4IzUFKfmW7yHQ7UBFvhFf4jpPXRU&_nc_ohc=LDP5Xz_V1JoQ7kNvwGhxUqk&_nc_gid=CGRNPnxZLmzbt_lv86M_ng&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afc-mTVCUB5mHpxUuJSQ8MB5Dl4WXRU-uSi8rMasSZuMWg&oe=68F5E040&_nc_sid=d885a2",
            "username": "coachyasmeenthebean"
          },
          "like_count": 2,
          "created_at": "2025-10-15T17:11:33.000Z"
        }
      ]
    },
    {
      "id": "3688898324799754410",
      "__typename": "XDTGraphVideo",
      "shortcode": "DMxmXtWORCq",
      "url": "https://www.instagram.com/reel/DMxmXtWORCq/",
      "caption": "Running IS SO NATURAL! So let’s bring it back down to basics and use a couple tips to get you back to running! ✨\n.\nWhat “running tip” has helped your form the most!?",
      "thumbnail_src": "https://scontent-atl3-1.cdninstagram.com/v/t51.2885-15/526749178_18516886933023048_6639429883423121774_n.jpg?stp=c0.882.2268.2268a_dst-jpg_e35_s640x640_sh0.08_tt6&_nc_ht=scontent-atl3-1.cdninstagram.com&_nc_cat=100&_nc_oc=Q6cZ2QHIkTieN4SOx7iLhz7vrezFqIfLNtnywYve__d8sVpu-JJ2BIu51-WRZuElUAGIErs&_nc_ohc=GJud7W9cLlsQ7kNvwFbHPYb&_nc_gid=wbvdbPBBRGKFT3wuniOqGQ&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AffLbudqnLxcZh7R6K6QbUA6oXQNjCe2KM4dIqAckoHivQ&oe=68F5EE65&_nc_sid=d885a2",
      "display_url": "https://scontent-atl3-1.cdninstagram.com/v/t51.2885-15/526749178_18516886933023048_6639429883423121774_n.jpg?stp=dst-jpg_e35_p1080x1080_sh0.08_tt6&_nc_ht=scontent-atl3-1.cdninstagram.com&_nc_cat=100&_nc_oc=Q6cZ2QHIkTieN4SOx7iLhz7vrezFqIfLNtnywYve__d8sVpu-JJ2BIu51-WRZuElUAGIErs&_nc_ohc=GJud7W9cLlsQ7kNvwFbHPYb&_nc_gid=wbvdbPBBRGKFT3wuniOqGQ&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcitVOwGEnyrXta-cGnnnXCSwY1syLI5R1TEkjJ4cPSoA&oe=68F5EE65&_nc_sid=d885a2",
      "video_url": "https://scontent-atl3-3.cdninstagram.com/o1/v/t2/f2/m412/AQNZNFwZkX8Yg4viQWhqhVFn0jJNrprdCDHJYXJxts2T7xWq_66nH3kdW9AopkNMENxI25FwbcLXsFZ7UW1o2BsFhIkZh5XmBdlbvljjKWRpGA.mp4?_nc_cat=108&_nc_sid=5e9851&_nc_ht=scontent-atl3-3.cdninstagram.com&_nc_ohc=JyfVgRIwEcEQ7kNvwHU3AKx&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuMTA4MC5kYXNoX2gyNjQtYmFzaWMtZ2VuMl8xMDgwcCIsInhwdl9hc3NldF9pZCI6NzYwNDI3Nzk2OTM3NzQzLCJ2aV91c2VjYXNlX2lkIjoxMDgyNywiZHVyYXRpb25fcyI6NTAsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&vs=5dbe4d0bebcb000f&_nc_vs=HBksFQIYRWZiX3Blcm1hbmVudC8yQTQwQUZDREZEMkM1MDBDRTMyRTlDQjJENTA0MDI5MF9tdF8wX3ZpZGVvX2Rhc2hpbml0Lm1wNBUAAsgBEgAVAhg6cGFzc3Rocm91Z2hfZXZlcnN0b3JlL0dKV0JMeDlYT3B0YU84c0NBT0VxN2c4eUtqUUVicV9FQUFBRhUCAsgBEgAoABgAGwKIB3VzZV9vaWwBMRJwcm9ncmVzc2l2ZV9yZWNpcGUBMRUAACae8LXL3ObZAhUCKAJDMywXQEl6n752yLQYGmRhc2hfaDI2NC1iYXNpYy1nZW4yXzEwODBwEQB1_gdllqkBAA&_nc_gid=wbvdbPBBRGKFT3wuniOqGQ&_nc_zt=28&oh=00_AffTE8o0eO9vX0PANdqz1EaY1FZUo4UoUrx2_qmFnU7Tjw&oe=68F5D628",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 129901,
      "video_play_count": 354617,
      "product_type": "clips",
      "video_duration": 50.958,
      "clips_music_attribution_info": {
        "artist_name": "_charihawkins",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "4028176267394486"
      },
      "is_video": true,
      "owner": {
        "id": "18391047",
        "username": "_charihawkins",
        "is_verified": true,
        "profile_pic_url": "https://scontent-atl3-1.cdninstagram.com/v/t51.2885-19/87861832_204457680957913_1821855222075490304_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmV4cGVyaW1lbnRhbCJ9&_nc_ht=scontent-atl3-1.cdninstagram.com&_nc_cat=1&_nc_oc=Q6cZ2QHIkTieN4SOx7iLhz7vrezFqIfLNtnywYve__d8sVpu-JJ2BIu51-WRZuElUAGIErs&_nc_ohc=cJtNe9dn7fYQ7kNvwEfW8Dd&_nc_gid=wbvdbPBBRGKFT3wuniOqGQ&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeUSvI0_6RY2TFs9TAk3W7gxW0y30hExmhLY0E_m4RcJA&oe=68F5CEAD&_nc_sid=d885a2",
        "full_name": "Chari Hawkins",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 1156482,
        "post_count": 1718
      },
      "taken_at": "2025-07-31T14:18:17.000Z",
      "is_ad": false,
      "like_count": 13463,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 143,
      "comments": [
        {
          "id": "17964623390993367",
          "text": "Awesome but which trainers pls",
          "owner": {
            "id": "1631532406",
            "is_verified": false,
            "profile_pic_url": "https://scontent-atl3-3.cdninstagram.com/v/t51.2885-19/537761320_18521154505044407_8696756238745088227_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmV4cGVyaW1lbnRhbCJ9&_nc_ht=scontent-atl3-3.cdninstagram.com&_nc_cat=111&_nc_oc=Q6cZ2QHIkTieN4SOx7iLhz7vrezFqIfLNtnywYve__d8sVpu-JJ2BIu51-WRZuElUAGIErs&_nc_ohc=Cmn-pyhvYUAQ7kNvwFi43Ac&_nc_gid=wbvdbPBBRGKFT3wuniOqGQ&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afd0eqxaIm7Hi9K-5F-d1-bjWrpO7o1_IbipAYSWJUUjOw&oe=68F5D3F5&_nc_sid=d885a2",
            "username": "bhupsgill"
          },
          "like_count": 0,
          "created_at": "2025-10-11T19:59:00.000Z"
        }
      ]
    },
    {
      "id": "3741064585298368650",
      "__typename": "XDTGraphVideo",
      "shortcode": "DPq7mtYgNiK",
      "url": "https://www.instagram.com/reel/DPq7mtYgNiK/",
      "caption": "#reel #advice #running",
      "thumbnail_src": "https://scontent-lga3-2.cdninstagram.com/v/t51.2885-15/562885838_2022790965152197_7587951513268960853_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=scontent-lga3-2.cdninstagram.com&_nc_cat=101&_nc_oc=Q6cZ2QFdTQyJjcR7BLFzNaIMOA_JnhYP2TdVsnOzVuz0x1tKcrNjC44kQuEkZ-Z3y10f_kE&_nc_ohc=yhx9u291jr8Q7kNvwFIbR2W&_nc_gid=jHMbPRDMXCHBmygmcP0MdA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdXrgy20hRQkKUH7lEIvvxgaYjmsvdOKxPFopA0TQHszQ&oe=68F5DCDA&_nc_sid=d885a2",
      "display_url": "https://scontent-lga3-2.cdninstagram.com/v/t51.2885-15/562885838_2022790965152197_7587951513268960853_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=scontent-lga3-2.cdninstagram.com&_nc_cat=101&_nc_oc=Q6cZ2QFdTQyJjcR7BLFzNaIMOA_JnhYP2TdVsnOzVuz0x1tKcrNjC44kQuEkZ-Z3y10f_kE&_nc_ohc=yhx9u291jr8Q7kNvwFIbR2W&_nc_gid=jHMbPRDMXCHBmygmcP0MdA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeOTkkRd3e_4mb0CiawgiNUJ9EFsNL_7KlJD4tBHdjKjg&oe=68F5DCDA&_nc_sid=d885a2",
      "video_url": "https://scontent-lga3-3.cdninstagram.com/o1/v/t2/f2/m86/AQMYcykzC8MDhekwtkLOe1kn7j_NUNWZPbOGtS2sgGIsioYbrr72VefZ7piM6Oc4PZYxOncD97CQSW7rcYwjVAPngCot2Jhznq4_p7I.mp4?_nc_cat=106&_nc_sid=5e9851&_nc_ht=scontent-lga3-3.cdninstagram.com&_nc_ohc=B8zpKUhF9GkQ7kNvwHdsUyi&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6NDI4NDA3NzY1ODU0MDE0NSwidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjYyLCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=f6776e764bd8b47d&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC9CMTRDNkFFMkJDMkE5Rjk1ODJDMkUyMzcyRkVENjlBNF92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HRFFVbkNIS2xIWmE5S3dFQUYwNXJiR0czZ1ZYYnN0VEFRQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAm4qG48JGWnA8VAigCQzMsF0BPJmZmZmZmGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=jHMbPRDMXCHBmygmcP0MdA&_nc_zt=28&oh=00_AfemDbG26MaeUJCBOZjJd8AJYwRs9b28Kz8MCORuYsbr4A&oe=68F1F91B",
      "has_audio": false,
      "accessibility_caption": null,
      "video_view_count": 750,
      "video_play_count": 1499,
      "product_type": "clips",
      "video_duration": 62.3,
      "clips_music_attribution_info": {
        "artist_name": "nikoschultzzz",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "2332084043912295"
      },
      "is_video": true,
      "owner": {
        "id": "18640324565",
        "username": "nikoschultzzz",
        "is_verified": false,
        "profile_pic_url": "https://scontent-lga3-1.cdninstagram.com/v/t51.2885-19/520225429_18094972960620566_8440452482976979226_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-lga3-1.cdninstagram.com&_nc_cat=102&_nc_oc=Q6cZ2QFdTQyJjcR7BLFzNaIMOA_JnhYP2TdVsnOzVuz0x1tKcrNjC44kQuEkZ-Z3y10f_kE&_nc_ohc=LfwqSE7i438Q7kNvwHIRpgr&_nc_gid=jHMbPRDMXCHBmygmcP0MdA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdjvWYeE7Fa99h64JYy99LI3dpjdgu4cNV_Ox6-mhe9wg&oe=68F5D7CE&_nc_sid=d885a2",
        "full_name": "Niko🥇Schultz",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 15624,
        "post_count": 40
      },
      "taken_at": "2025-10-11T13:35:21.000Z",
      "is_ad": false,
      "like_count": 37,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 0,
      "comments": []
    },
    {
      "id": "3379152268890770689",
      "__typename": "XDTGraphVideo",
      "shortcode": "C7lKRXFMI0B",
      "url": "https://www.instagram.com/reel/C7lKRXFMI0B/",
      "caption": "16 years of coaching running technique distilled down to these simple cues and within 30 minutes of practice the transformation is done.\n\nRunning is a series of single legged alternate hops, where in split seconds we have to balance the huge weight that is our head and reassemble all our boney segments and tissue that stand erect on a relatively small base of support (our feet). \n\nFirst we strip the movement right back and relearn to perform a rhythmic jump, with an upright posture, landing flat footed with a soft shock absorbing knee.\n\nTo become a skilled runner you have to reconnect with running as naturally as possible, otherwise you lose touch with your innate efficiency and run the risk of falling into a constant cycle of injury.\n.\nSkillful natural running is focused on refining these 3 things:\n\n• Posture (upright, head, chest over hips) lead with your heart, stop chasing your head.\n\n• Rhythm (180 steps per minute. Pick your feet up. Think light relaxed feet that pull up from the ground, rather than push off the ground.  Use your hamstrings!\n\n• Relaxation - (relax shoulders feet wrists. reconnect with nasal breathing techniques to remain calm and aid efficiency and recovery. \n\nIf you can’t explain it simply, you don’t understand it well enough.\n\nAlbert Einstein\n\n#run\n#running \n#runningtechnique",
      "thumbnail_src": "https://instagram.fbey21-2.fna.fbcdn.net/v/t51.2885-15/496933423_583251104786183_3889562323963703203_n.jpg?stp=c0.280.720.720a_dst-jpg_e15_s640x640_tt6&_nc_ht=instagram.fbey21-2.fna.fbcdn.net&_nc_cat=111&_nc_oc=Q6cZ2QFvhbgqh98qeBgwA4rThnzSTMZqZ1P6C3KnPfMFblW4yZIGwvdVrPDhX9rMXwmeSf0&_nc_ohc=pXxSAnAHEAwQ7kNvwFb8dOZ&_nc_gid=yJs0pHnijHDM3Os4UP3S5w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfctE9ZNp-bwRVEImnAd1hj1S6EqOoitP8dz6r7yZoc98Q&oe=68F5EAC6&_nc_sid=d885a2",
      "display_url": "https://instagram.fbey21-2.fna.fbcdn.net/v/t51.2885-15/496933423_583251104786183_3889562323963703203_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fbey21-2.fna.fbcdn.net&_nc_cat=111&_nc_oc=Q6cZ2QFvhbgqh98qeBgwA4rThnzSTMZqZ1P6C3KnPfMFblW4yZIGwvdVrPDhX9rMXwmeSf0&_nc_ohc=pXxSAnAHEAwQ7kNvwFb8dOZ&_nc_gid=yJs0pHnijHDM3Os4UP3S5w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AffzDl0i3VUGm7FJp5u1zjXQ1ZwVMRAi5jGZ7w5CgHjLAA&oe=68F5EAC6&_nc_sid=d885a2",
      "video_url": "https://instagram.fbey21-2.fna.fbcdn.net/o1/v/t2/f2/m82/AQNGQTgfA7juwEYYsXYgvcyBmUt5pRk9PpCX-cuJKO8hkYRlcqwtEGaYfhyqgpq87CcZYHdsc0FdqWEJD5QDARP1vLiD-GLZMLLjWxc.mp4?_nc_cat=101&_nc_oc=Adk-Ck731A4sWe6s7bRpzW_EDxuP7ejhXhBwaHhXqLh-LQobAi-lgyQOu4k8DmrGwyc&_nc_sid=5e9851&_nc_ht=instagram.fbey21-2.fna.fbcdn.net&_nc_ohc=NOLxiwHn9R0Q7kNvwGmCKIG&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MzQyNTE0MDM1NTI2NTU5LCJhc3NldF9hZ2VfZGF5cyI6NTAzLCJ2aV91c2VjYXNlX2lkIjoxMDA5OSwiZHVyYXRpb25fcyI6NzcsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&vs=58576960f70afaf7&_nc_vs=HBksFQIYT2lnX3hwdl9yZWVsc19wZXJtYW5lbnRfcHJvZC8wNTQ4QkYyQUIwMjVERTcwRTEyMTFFMUNDNkEwMjU4Nl92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HUG5wcEJwTXNvRjhnSW9CQUROOHNhV1BfX0lHYnFfRUFBQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmvq7YtvjgmwEVAigCQzMsF0BTXdLxqfvnGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=yJs0pHnijHDM3Os4UP3S5w&_nc_zt=28&oh=00_Afd5n3DxIi4cUG13bopHC9k9IBi2SIfA41PXDCle71NRhw&oe=68F1CCD6",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 523868,
      "video_play_count": 895978,
      "product_type": "clips",
      "video_duration": 77.466,
      "clips_music_attribution_info": {
        "artist_name": "Timber Timbre",
        "song_name": "Run From Me",
        "uses_original_audio": false,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "212437172723491"
      },
      "is_video": true,
      "owner": {
        "id": "255105071",
        "username": "thenaturallifestylist",
        "is_verified": true,
        "profile_pic_url": "https://instagram.fbey21-2.fna.fbcdn.net/v/t51.2885-19/516817506_18507757801001072_6574707119813888920_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fbey21-2.fna.fbcdn.net&_nc_cat=108&_nc_oc=Q6cZ2QFvhbgqh98qeBgwA4rThnzSTMZqZ1P6C3KnPfMFblW4yZIGwvdVrPDhX9rMXwmeSf0&_nc_ohc=XhRg2TSo-8wQ7kNvwHqksM7&_nc_gid=yJs0pHnijHDM3Os4UP3S5w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afetx5H5xplTHX_0XkiwZVX4rrmrISRytlefeZP2hY13Dg&oe=68F5F492&_nc_sid=d885a2",
        "full_name": "Tony Riddle",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 148540,
        "post_count": 3997
      },
      "taken_at": "2024-05-30T05:22:11.000Z",
      "is_ad": false,
      "like_count": 19096,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 226,
      "comments": []
    },
    {
      "id": "3743817520664213274",
      "__typename": "XDTGraphVideo",
      "shortcode": "DP0tjMPEvca",
      "url": "https://www.instagram.com/reel/DP0tjMPEvca/",
      "caption": "Runner’s 10 Minute Mobility Routine\n\nYou don’t need hour-long routines or complicated movements to make a difference. Just 10 minutes of the right movements, a few times each week, can keep your body moving well and your stride feeling easy.\n\nConsistency wins, a little mobility done often will always top trump high intensity every so often.\n\nIf you want more ways to improve your running and overall strength & fitness then comment ‘RSP’ and I’ll send you more info about my runstrong programme. \n\nFollow @sjc.physio and my clinic @sjc.physio.clinic for simple, effective guidance that helps you move better and run stronger.",
      "thumbnail_src": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-15/565415053_1273452861114984_3984647866288621528_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QH3scD68TZRoVziKRtNgZJVJ1ECx-6UOccFfRc6jByY6Zlx8LOQmQVmxK_ubCN_GwE&_nc_ohc=cs8_M3YuOh0Q7kNvwG5_z8R&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afc0K1LqESpHJ6K5TsVxYsJNgAg_SsWzep5pQWqx78VLFQ&oe=68F5F14A&_nc_sid=d885a2",
      "display_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-15/565415053_1273452861114984_3984647866288621528_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QH3scD68TZRoVziKRtNgZJVJ1ECx-6UOccFfRc6jByY6Zlx8LOQmQVmxK_ubCN_GwE&_nc_ohc=cs8_M3YuOh0Q7kNvwG5_z8R&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdlDvds2YqirrLXLphcK06Uv245x-6t9ePBs8mtVHY9KA&oe=68F5F14A&_nc_sid=d885a2",
      "video_url": "https://instagram.fsac1-1.fna.fbcdn.net/o1/v/t2/f2/m86/AQNYRLctFMKSOEcYGhI8BHMVZLc_ByKmCeiSsRtXElYV80VL6ub4q5va0_uPqXW8Bj6ttGwPAY_DY3pQG6rjMJrHcgPr9162ey4dxks.mp4?_nc_cat=111&_nc_oc=AdnS3G07ji8VQf2ZEUdZtZhN_nJ7v3dkPbGxWxfahGNfUSWmAIkk6w2khnhszehP-2A&_nc_sid=5e9851&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_ohc=LjuJ0oRUvGkQ7kNvwHVmGmr&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MjAzMTg3MTU3MDk5NzI0MSwidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjk0LCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=ae8caffb489eb42&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC80RDRFRTUwQ0UwNjJGQzc4Mjc0QkRGMkVENjBFRjBBQV92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HTFBhdENHcWZ6NWR2TzBDQUtsVGVyMWFBbGRZYnN0VEFRQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAm8r-_877-mwcVAigCQzMsF0BXt2yLQ5WBGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&_nc_zt=28&oh=00_AfeAiMwn7EwcKTWJfnlyL8KFZ09puQ-zFTpfr3Rj7RvXiQ&oe=68F1F780",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 4965,
      "video_play_count": 12604,
      "product_type": "clips",
      "video_duration": 94.866,
      "clips_music_attribution_info": {
        "artist_name": "sjc.physio",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "810384148378696"
      },
      "is_video": true,
      "owner": {
        "id": "25834392463",
        "username": "sjc.physio",
        "is_verified": true,
        "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/431115981_263423640143131_5665780355650325939_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=107&_nc_oc=Q6cZ2QH3scD68TZRoVziKRtNgZJVJ1ECx-6UOccFfRc6jByY6Zlx8LOQmQVmxK_ubCN_GwE&_nc_ohc=T7bQHp37KLsQ7kNvwHLiwVr&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afd3mCcUx2HUlRbrTgz7zs9IriBpOxZaoJuvIn_XuqA_Vg&oe=68F5C93F&_nc_sid=d885a2",
        "full_name": "Sam Caddick | Running Physio & Coach",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 94973,
        "post_count": 738
      },
      "taken_at": "2025-10-15T08:48:36.000Z",
      "is_ad": false,
      "like_count": -1,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 4,
      "comments": [
        {
          "id": "17986471880902986",
          "text": "They look great. What is that block you’re kneeling on towards the end?",
          "owner": {
            "id": "1431590396",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/504391967_18504003145038397_9030986831462356239_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby45NjAuYzIifQ&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=101&_nc_oc=Q6cZ2QH3scD68TZRoVziKRtNgZJVJ1ECx-6UOccFfRc6jByY6Zlx8LOQmQVmxK_ubCN_GwE&_nc_ohc=duOfeAjO1vAQ7kNvwEbe8KY&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afe9QFs2N3K2w36joYWuMcZrQWPCwS1wLR6rahzRBj-UCQ&oe=68F5D965&_nc_sid=d885a2",
            "username": "reidy_78"
          },
          "like_count": 0,
          "created_at": "2025-10-15T18:54:15.000Z"
        },
        {
          "id": "18079139768089887",
          "text": "How often we should do mobility routine?",
          "owner": {
            "id": "13084981200",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fsac1-1.fna.fbcdn.net/v/t51.2885-19/285941804_550897609782009_616310551244465824_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby42ODguYzIifQ&_nc_ht=instagram.fsac1-1.fna.fbcdn.net&_nc_cat=109&_nc_oc=Q6cZ2QH3scD68TZRoVziKRtNgZJVJ1ECx-6UOccFfRc6jByY6Zlx8LOQmQVmxK_ubCN_GwE&_nc_ohc=l9DUYi8Cm_kQ7kNvwHL7Kqk&_nc_gid=bT4bDdttfvmbnmEiLpcqGg&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfccMBGR_7YK3d_u_2ZGohXwXZeSK93t7fYrN0EriM6ttw&oe=68F5E5E6&_nc_sid=d885a2",
            "username": "liniguimaraes"
          },
          "like_count": 0,
          "created_at": "2025-10-15T09:26:21.000Z"
        }
      ]
    },
    {
      "id": "3697197385102380821",
      "__typename": "XDTGraphVideo",
      "shortcode": "DNPFW7jh88V",
      "url": "https://www.instagram.com/reel/DNPFW7jh88V/",
      "caption": "The question I got most often when I came off of social media was “where did Goggins go?” \n\nPeople speculated that my knees were bad, maybe my health, maybe even a deep depression. It was none of that. \n\nSimply put, I grow in the darkness not in the light. \n\nStay hard!",
      "thumbnail_src": "https://instagram.fbom20-1.fna.fbcdn.net/v/t51.2885-15/531087284_18405845509112925_8658976263449556204_n.jpg?stp=c0.280.720.720a_dst-jpg_e15_s640x640_tt6&_nc_ht=instagram.fbom20-1.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2QG-MwaMK0-KprJg6Gwxx9pT11942YMwvAcb5hbLvMJbRIEtrGWI0HvV4Qk7GQr6XNE&_nc_ohc=fh8wgLNvDpQQ7kNvwE8Vg3k&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeR-9PzsO_Jp2xWB5fXzWu-udoE98L5uqT8tjRdskQqFg&oe=68F5E4A4&_nc_sid=d885a2",
      "display_url": "https://instagram.fbom20-1.fna.fbcdn.net/v/t51.2885-15/531087284_18405845509112925_8658976263449556204_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fbom20-1.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2QG-MwaMK0-KprJg6Gwxx9pT11942YMwvAcb5hbLvMJbRIEtrGWI0HvV4Qk7GQr6XNE&_nc_ohc=fh8wgLNvDpQQ7kNvwE8Vg3k&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AffYo9KI0ug26bv_0CxHg2TntnWP3fDMYM-r36z9hvHEOA&oe=68F5E4A4&_nc_sid=d885a2",
      "video_url": "https://instagram.fbom20-1.fna.fbcdn.net/o1/v/t2/f2/m86/AQPOZB4P7YuJimZ44QXtGGfqJKuHnBvp59Eh3vuIrizKCcM6xdoN1XAMhu3bEcofMOEGcRBrfeYhADkE3DTLDPca11eiWWUx4MYbzu8.mp4?_nc_cat=109&_nc_oc=AdnZbP1qRuaMIj9FiRRN25p0q8cxa8B9dEVd0WZKWzhn-GBafQa_twVC3Wx5j-5_gZs&_nc_sid=5e9851&_nc_ht=instagram.fbom20-1.fna.fbcdn.net&_nc_ohc=-2C6JTZQjY8Q7kNvwEWc-eU&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MTQzNjE2MjgxMDkzNjY0MCwidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjQ4LCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=1a2c2e21fd90b579&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC8xMTRBMkY3MEI3QzExMDlDNTdBQjY1MDUwQjEzODdBM192aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HT0Q3blI5ZTc4VkE1TEZYQUd2SVZINE1fWUZDYnFfRUFBQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmgPX74taLjQUVAigCQzMsF0BIgAAAAAAAGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&_nc_zt=28&oh=00_AfdhzebD6SpWqJ-cxkTstGuD-LRR02bjfFply0WkR8D4PA&oe=68F1F18A",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 11544096,
      "video_play_count": 30325471,
      "product_type": "clips",
      "video_duration": 49,
      "clips_music_attribution_info": {
        "artist_name": "davidgoggins",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "601664252823286"
      },
      "is_video": true,
      "owner": {
        "id": "3544528924",
        "username": "davidgoggins",
        "is_verified": true,
        "profile_pic_url": "https://instagram.fbom20-1.fna.fbcdn.net/v/t51.2885-19/312997181_858626005139514_2931723474253028126_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4zMjAuYzIifQ&_nc_ht=instagram.fbom20-1.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2QG-MwaMK0-KprJg6Gwxx9pT11942YMwvAcb5hbLvMJbRIEtrGWI0HvV4Qk7GQr6XNE&_nc_ohc=JAUvr1pE9E0Q7kNvwEvYg2s&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcHUzFJTP9QTzeqPYrhW9c62IrGMDIYpGrtgvW6FzJonQ&oe=68F5CA36&_nc_sid=d885a2",
        "full_name": "David Goggins",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 13999079,
        "post_count": 122
      },
      "taken_at": "2025-08-12T00:59:42.000Z",
      "is_ad": false,
      "like_count": 2423024,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 18729,
      "comments": [
        {
          "id": "18290887480281318",
          "text": "neden özürlü gibi koşuyorsun amk asiri merak ediyorum",
          "owner": {
            "id": "59214042181",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fbom20-1.fna.fbcdn.net/v/t51.2885-19/541242122_17960173232970182_4358700941949830130_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fbom20-1.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QG-MwaMK0-KprJg6Gwxx9pT11942YMwvAcb5hbLvMJbRIEtrGWI0HvV4Qk7GQr6XNE&_nc_ohc=yE61XY8TVzQQ7kNvwGNfc9N&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdVkoausPTYOsXDwIP4J2hurK9PPXY3t0I30N9VP8i13g&oe=68F5D6A4&_nc_sid=d885a2",
            "username": "eyubte"
          },
          "like_count": 0,
          "created_at": "2025-10-15T20:23:12.000Z"
        },
        {
          "id": "18350009806161207",
          "text": "❤️ Stay hard! You are an inspiration. Thank you for being you!",
          "owner": {
            "id": "8626460059",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fbom20-2.fna.fbcdn.net/v/t51.2885-19/183457714_1819438368232512_8817983417833335844_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fbom20-2.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QG-MwaMK0-KprJg6Gwxx9pT11942YMwvAcb5hbLvMJbRIEtrGWI0HvV4Qk7GQr6XNE&_nc_ohc=zZNNpL_t_RYQ7kNvwFa-c_A&_nc_gid=PA0Ll3SAUKHcd6VZ9WF12A&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afd0IfqHSG7Z3um3w_o1zvTosnjrP67YR93UCkH93GMZSg&oe=68F5F313&_nc_sid=d885a2",
            "username": "torrez_art"
          },
          "like_count": 0,
          "created_at": "2025-10-15T20:00:14.000Z"
        }
      ]
    },
    {
      "id": "3644949911826620377",
      "__typename": "XDTGraphVideo",
      "shortcode": "DKVdqIOhF_Z",
      "url": "https://www.instagram.com/reel/DKVdqIOhF_Z/",
      "caption": "no gatekeeping: beginner running tips that actually work 💅🏽\n\n#Runner #beginnerrunner #runningtips",
      "thumbnail_src": "https://instagram.fphl1-1.fna.fbcdn.net/v/t51.2885-15/503157575_2034599983695062_710889559799422569_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QFDNe9andjhhuhyb2yGHxLZ65H5LVCdrpddgdaA5t9ntvG9Ejw60tAO4vjbJDTAQj0&_nc_ohc=mf67CErQz5kQ7kNvwEUOC3a&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afcn0dgoSgQU3gXSRpcJCSZMt5MwmTKBfEu9i7-izWOItQ&oe=68F5EC73&_nc_sid=d885a2",
      "display_url": "https://instagram.fphl1-1.fna.fbcdn.net/v/t51.2885-15/503157575_2034599983695062_710889559799422569_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QFDNe9andjhhuhyb2yGHxLZ65H5LVCdrpddgdaA5t9ntvG9Ejw60tAO4vjbJDTAQj0&_nc_ohc=mf67CErQz5kQ7kNvwEUOC3a&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfehCSDGdo16RwvDlfCQiemu9pSsb859IcuOVhpxf05pqA&oe=68F5EC73&_nc_sid=d885a2",
      "video_url": "https://instagram.fphl1-1.fna.fbcdn.net/o1/v/t2/f2/m367/AQMK57RuEViIjxGHPBL2rYMJZMYJb7KcQPBJVhXnZK3bjFfdvpdS_-K64LJPBdB62r2fxU2X4O4q5fh7PyExDuHQxEvAqY5Hsdjb9nQ.mp4?_nc_cat=110&_nc_oc=Adm33UFUeUzmv7PEOIk0-BkLB50xAvl1_yyt8jTy9VCwrKaHVCX1g5d_yAbznfxO8r8&_nc_sid=5e9851&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_ohc=pfF_KKWZ0v4Q7kNvwGY91v2&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MTExMjUyNjIzMDY3MDE5OCwidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjU2LCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=e34aa86939aa6eea&_nc_vs=HBksFQIYQGlnX2VwaGVtZXJhbC80NDQ3MzBFNjkwMkFCM0E3MTI5ODA4NTZFQ0IzNEZBQV92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HTWxQLUIyQlMzUFRvWm9HQUhLYW1vV2xob29rYnFfRUFBQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAm7K3CrMb1-QMVAigCQzMsF0BMQAAAAAAAGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&_nc_zt=28&oh=00_AfdJJE7dn6dbnCJGf9O35EQ64T0umQieTaq3EVElVikdiA&oe=68F5E7FB",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 437,
      "video_play_count": 6641,
      "product_type": "clips",
      "video_duration": 56.5,
      "clips_music_attribution_info": {
        "artist_name": "vanessanhattaway",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "2110525109448071"
      },
      "is_video": true,
      "owner": {
        "id": "38729817",
        "username": "vanessanhattaway",
        "is_verified": false,
        "profile_pic_url": "https://instagram.fphl1-1.fna.fbcdn.net/v/t51.2885-19/527437489_18526040794009818_939945512121048976_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_cat=106&_nc_oc=Q6cZ2QFDNe9andjhhuhyb2yGHxLZ65H5LVCdrpddgdaA5t9ntvG9Ejw60tAO4vjbJDTAQj0&_nc_ohc=G9v5g_NSQkIQ7kNvwG8VmGq&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AffpUJNYZbIJmr5qQgm9RUvedRum2nD6cy7q8byGNy0sQA&oe=68F5D222&_nc_sid=d885a2",
        "full_name": "Vanessa Hattaway",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 25583,
        "post_count": 232
      },
      "taken_at": "2025-05-31T22:53:02.000Z",
      "is_ad": false,
      "like_count": -1,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": {
        "id": "213413990",
        "has_public_page": true,
        "name": "Newport Beach, California",
        "slug": "newport-beach-california",
        "address_json": "{\"street_address\": \"\", \"zip_code\": \"\", \"city_name\": \"Newport Beach, California\", \"region_name\": \"\", \"country_code\": \"\", \"exact_city_match\": true, \"exact_region_match\": false, \"exact_country_match\": false}"
      },
      "comment_count": 9,
      "comments": [
        {
          "id": "18060318059055213",
          "text": "Do you have any brands of running shoes that you recommend?",
          "owner": {
            "id": "33606588",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fphl1-1.fna.fbcdn.net/v/t51.2885-19/544156659_18527218516006589_2451016658005432159_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_cat=105&_nc_oc=Q6cZ2QFDNe9andjhhuhyb2yGHxLZ65H5LVCdrpddgdaA5t9ntvG9Ejw60tAO4vjbJDTAQj0&_nc_ohc=PAIGVe5MSDMQ7kNvwFcbNdH&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcHhTRxuObJHK9_mqcTn8Ir-ar1v6KwmcqLH7-RFlBXFQ&oe=68F5E989&_nc_sid=d885a2",
            "username": "alissamiyamoto"
          },
          "like_count": 1,
          "created_at": "2025-08-06T21:11:52.000Z"
        },
        {
          "id": "17955044039977733",
          "text": "Beginner tip: download @kali.curated 🫣🧡",
          "owner": {
            "id": "48156568982",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fphl1-1.fna.fbcdn.net/v/t51.2885-19/447849373_3422431034715372_912385784664004663_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby40OTEuYzIifQ&_nc_ht=instagram.fphl1-1.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QFDNe9andjhhuhyb2yGHxLZ65H5LVCdrpddgdaA5t9ntvG9Ejw60tAO4vjbJDTAQj0&_nc_ohc=EB-hbkh85qUQ7kNvwFezyFT&_nc_gid=3WSgkEKY2Ck_TJ-0awUVjA&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdSoDrU1VqbJcvn3SsF6sSC92z9tv7RWEOdZ7icmAargQ&oe=68F5E8D7&_nc_sid=d885a2",
            "username": "kali.curated"
          },
          "like_count": 0,
          "created_at": "2025-07-09T17:47:07.000Z"
        }
      ]
    },
    {
      "id": "3742197142791187513",
      "__typename": "XDTGraphVideo",
      "shortcode": "DPu9HlvjOw5",
      "url": "https://www.instagram.com/reel/DPu9HlvjOw5/",
      "caption": "We asked Chicago Runnas why they’re running the marathon today ✨🙌\n\nEveryone’s out here with their own story, and that’s what makes this day so special.\n\n#RunnaCommunity #ChicagoMarathon #partoftheplan",
      "thumbnail_src": "https://scontent-ber1-1.cdninstagram.com/v/t51.2885-15/564905014_787180087429386_8041944452234726896_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_cat=106&_nc_oc=Q6cZ2QEWbRiyNfe8G6_TUaH4nmIBD3SodhNEAJLc8zL1PnbhERATXWpNOvK-H90UiQvKOlw&_nc_ohc=PT4QwX9HSh8Q7kNvwEnFzgz&_nc_gid=RIwskvP7GECzGCf5PwDV-w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcE9qnPtNWCUiyhg84qIhqX4Ws-ZbpbboVOPRwl9n5HMQ&oe=68F5D003&_nc_sid=d885a2",
      "display_url": "https://scontent-ber1-1.cdninstagram.com/v/t51.2885-15/564905014_787180087429386_8041944452234726896_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_cat=106&_nc_oc=Q6cZ2QEWbRiyNfe8G6_TUaH4nmIBD3SodhNEAJLc8zL1PnbhERATXWpNOvK-H90UiQvKOlw&_nc_ohc=PT4QwX9HSh8Q7kNvwEnFzgz&_nc_gid=RIwskvP7GECzGCf5PwDV-w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afc1EnFyDstnia_L2XQpICGbHoYAdXubTAFdowmL-9Y7wQ&oe=68F5D003&_nc_sid=d885a2",
      "video_url": "https://scontent-ber1-1.cdninstagram.com/o1/v/t16/f2/m69/AQO50Qn1vnrGIfNRAaGlebwwKQgnHYNq9bJ-fCBT1EvrAUZaKp4E3UvGlLpLHxynuAswYh35nmwnt0KvidpI7ZQl.mp4?strext=1&_nc_cat=106&_nc_sid=5e9851&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_ohc=QgmYkGQKGNcQ7kNvwFzybYr&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MTE2NTg4NDIwODc3ODA4NywidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjYzLCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=bcdafa70e6170259&_nc_vs=HBksFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HSHBKcHlFQS02NlZoM01HQU4xRXE0U0lwdFlmYnNwVEFRQUYVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HS3drYnlIV1N0VlA5djRDQUxaZFpDWS1XNVlyYnN0VEFRQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmzq3oobKXkgQVAigCQzMsF0BPorAgxJumGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=RIwskvP7GECzGCf5PwDV-w&_nc_zt=28&oh=00_Afc4QaBQ771L-kwxvvNTY5KmzRZQs6RgvHF-IRdf-yh2zw&oe=68F5BDF6",
      "has_audio": false,
      "accessibility_caption": null,
      "video_view_count": 180117,
      "video_play_count": 364639,
      "product_type": "clips",
      "video_duration": 63.271,
      "clips_music_attribution_info": {
        "artist_name": "fairytale mp3",
        "song_name": "To Build A Home - Piano",
        "uses_original_audio": false,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "1346466126019067"
      },
      "is_video": true,
      "owner": {
        "id": "45274882639",
        "username": "runna",
        "is_verified": true,
        "profile_pic_url": "https://scontent-ber1-1.cdninstagram.com/v/t51.2885-19/515368671_18074322308506640_4430541990677209637_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_cat=1&_nc_oc=Q6cZ2QEWbRiyNfe8G6_TUaH4nmIBD3SodhNEAJLc8zL1PnbhERATXWpNOvK-H90UiQvKOlw&_nc_ohc=FJspWQaX1TUQ7kNvwH3xXjO&_nc_gid=RIwskvP7GECzGCf5PwDV-w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcmbYo1qZAAqgRC40YqJ3Zx4x9Bc-VPLQVw8idAiQcZkg&oe=68F5C2F6&_nc_sid=d885a2",
        "full_name": "Runna | Running Coaching App",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 650459,
        "post_count": 1929
      },
      "taken_at": "2025-10-13T03:05:17.000Z",
      "is_ad": false,
      "like_count": 18619,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 99,
      "comments": [
        {
          "id": "18048740030649733",
          "text": "🥹🥹🥹",
          "owner": {
            "id": "578290457",
            "is_verified": true,
            "profile_pic_url": "https://scontent-ber1-1.cdninstagram.com/v/t51.2885-19/402445735_3007588586038035_3006215345847512580_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby41MTIuYzIifQ&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_cat=103&_nc_oc=Q6cZ2QEWbRiyNfe8G6_TUaH4nmIBD3SodhNEAJLc8zL1PnbhERATXWpNOvK-H90UiQvKOlw&_nc_ohc=7ffTH_vdfS8Q7kNvwEuCUl_&_nc_gid=RIwskvP7GECzGCf5PwDV-w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfehSxBviBIUtZUQJ9wWloQkouwqpzpulm70s2mMHvgpyA&oe=68F5F508&_nc_sid=d885a2",
            "username": "percelldugger"
          },
          "like_count": 0,
          "created_at": "2025-10-15T17:12:18.000Z"
        },
        {
          "id": "18154779103402433",
          "text": "Omg that 8 month baby bump was a jump scare! lol Wasn’t expecting it at all and what a super mom to run a marathon that pregnant🦸🏻‍♀️",
          "owner": {
            "id": "25438483",
            "is_verified": false,
            "profile_pic_url": "https://scontent-ber1-1.cdninstagram.com/v/t51.2885-19/473631464_597580923010335_7196891422291821381_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-ber1-1.cdninstagram.com&_nc_cat=103&_nc_oc=Q6cZ2QEWbRiyNfe8G6_TUaH4nmIBD3SodhNEAJLc8zL1PnbhERATXWpNOvK-H90UiQvKOlw&_nc_ohc=r_wTmCszOMsQ7kNvwEB9c-b&_nc_gid=RIwskvP7GECzGCf5PwDV-w&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcAxoHIIyNI93aE2IBXxWsBuPrOVEwYbJPl8EWD32Gibw&oe=68F5E848&_nc_sid=d885a2",
            "username": "jiannamariel"
          },
          "like_count": 0,
          "created_at": "2025-10-15T16:52:24.000Z"
        }
      ]
    },
    {
      "id": "3743549735668126548",
      "__typename": "XDTGraphVideo",
      "shortcode": "DPzwqaBgZNU",
      "url": "https://www.instagram.com/reel/DPzwqaBgZNU/",
      "caption": "Still can’t get over race weekend! 2025 2XU Long Beach Marathon was truly epic 🔥 The runners, bikers, and community showed up the only way Long Beach does!",
      "thumbnail_src": "https://scontent-iad3-2.cdninstagram.com/v/t51.2885-15/564609078_786421130977224_783996240658698457_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=scontent-iad3-2.cdninstagram.com&_nc_cat=100&_nc_oc=Q6cZ2QEtstWYdstXnFyslAoubCaZlzD0IY6obSapxGUje1LcslXBk1_NhfBoTVKo_p1c4Sc&_nc_ohc=p10fOQDgt9kQ7kNvwF2oBHf&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcFD8N8bLctXzZT9QOBOVdvTY_QI-P-FG0KqYN1bSIcXA&oe=68F5C6BF&_nc_sid=d885a2",
      "display_url": "https://scontent-iad3-2.cdninstagram.com/v/t51.2885-15/564609078_786421130977224_783996240658698457_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=scontent-iad3-2.cdninstagram.com&_nc_cat=100&_nc_oc=Q6cZ2QEtstWYdstXnFyslAoubCaZlzD0IY6obSapxGUje1LcslXBk1_NhfBoTVKo_p1c4Sc&_nc_ohc=p10fOQDgt9kQ7kNvwF2oBHf&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AffS9hJk6vNdYbbrBjrAeLcgL0C3pGCHR33MixF6vhCNpw&oe=68F5C6BF&_nc_sid=d885a2",
      "video_url": "https://scontent-iad3-1.cdninstagram.com/o1/v/t2/f2/m86/AQP_P5_ZEWOhcT3fccxWiD5Kc2xVGBJYSOtDhBSBai1oeVjxx2CzbCi-hbbM5CummEzKbg7BRAbgtFASoDH2-OSn-_vx2X6cpKSIJoE.mp4?_nc_cat=102&_nc_sid=5e9851&_nc_ht=scontent-iad3-1.cdninstagram.com&_nc_ohc=UHvnGR90URUQ7kNvwGdqiiw&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6NjkzMTc5ODk2NTc1MTIwLCJ2aV91c2VjYXNlX2lkIjoxMDA5OSwiZHVyYXRpb25fcyI6NjIsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&vs=c0e71275480dc8a1&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC81RDQxMTBGMEZBNjQ1RjQ1NTgyRDYxM0ZFMEFCM0U4MF92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HS29scENFUzhTeGxVbFVFQUxVWGxmRV9meU0yYnN0VEFRQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmoNKB2LCcuwIVAigCQzMsF0BPKfvnbItEGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&_nc_zt=28&oh=00_AfcPr2MFUVI-aN_cDlIYI2E7i9lqnsOYswOl1Pi0K8OS-Q&oe=68F1D20F",
      "has_audio": false,
      "accessibility_caption": null,
      "video_view_count": 3769,
      "video_play_count": 14847,
      "product_type": "clips",
      "video_duration": 62.328,
      "clips_music_attribution_info": {
        "artist_name": "longbeachmarathon",
        "song_name": "Original audio",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "784747837801315"
      },
      "is_video": true,
      "owner": {
        "id": "1821429291",
        "username": "longbeachmarathon",
        "is_verified": false,
        "profile_pic_url": "https://scontent-iad3-1.cdninstagram.com/v/t51.2885-19/559938259_18535714801053292_8028670286410762882_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-iad3-1.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2QEtstWYdstXnFyslAoubCaZlzD0IY6obSapxGUje1LcslXBk1_NhfBoTVKo_p1c4Sc&_nc_ohc=O7Ia99faNDQQ7kNvwHaxUTO&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Afc-jX4eGS7RmE_0Xtf_Zr4IZXQTBTJNtNqVzKqTgp_jTA&oe=68F5C5EF&_nc_sid=d885a2",
        "full_name": "2XU Long Beach Marathon",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 28265,
        "post_count": 1498
      },
      "taken_at": "2025-10-15T00:12:52.000Z",
      "is_ad": false,
      "like_count": 720,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 36,
      "comments": [
        {
          "id": "18096936784674971",
          "text": "Such a great weekend!!",
          "owner": {
            "id": "5553038465",
            "is_verified": false,
            "profile_pic_url": "https://scontent-iad3-2.cdninstagram.com/v/t51.2885-19/323700076_745739286498402_4280807999626620465_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby40NjYuYzIifQ&_nc_ht=scontent-iad3-2.cdninstagram.com&_nc_cat=106&_nc_oc=Q6cZ2QEtstWYdstXnFyslAoubCaZlzD0IY6obSapxGUje1LcslXBk1_NhfBoTVKo_p1c4Sc&_nc_ohc=nEYlkdHTWu8Q7kNvwGwgr-q&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdGcYIKL85QjrERPbN6UIRlER8oYZU-mYrYYhFKMk4GBw&oe=68F5DE82&_nc_sid=d885a2",
            "username": "janelauhomes"
          },
          "like_count": 0,
          "created_at": "2025-10-15T16:44:53.000Z"
        },
        {
          "id": "18063647924591788",
          "text": "A blast being the MC yelling out names of the awesome runners.",
          "owner": {
            "id": "41001942",
            "is_verified": true,
            "profile_pic_url": "https://scontent-iad3-1.cdninstagram.com/v/t51.2885-19/44515937_2804621966229950_2403141911301849088_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby40NDEuYzIifQ&_nc_ht=scontent-iad3-1.cdninstagram.com&_nc_cat=102&_nc_oc=Q6cZ2QEtstWYdstXnFyslAoubCaZlzD0IY6obSapxGUje1LcslXBk1_NhfBoTVKo_p1c4Sc&_nc_ohc=0gBqOSxoDroQ7kNvwFoA4Bd&_nc_gid=OgxAkhNs-cheN3iLRZZhCw&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_Affi6R1IJGy-51K0A4Tg3uT-MFKOf7Spc3gTU-7SDeEGdg&oe=68F5DAD4&_nc_sid=d885a2",
            "username": "betovision"
          },
          "like_count": 0,
          "created_at": "2025-10-15T16:07:13.000Z"
        }
      ]
    },
    {
      "id": "3699117831263378693",
      "__typename": "XDTGraphVideo",
      "shortcode": "DNV6BGaxF0F",
      "url": "https://www.instagram.com/reel/DNV6BGaxF0F/",
      "caption": "Did you know perfecting your running form can help you become a stronger, more efficient runner?\n\nOver time, you’ll start running with less effort meaning more pace targets hit on Runna, and more kudos coming your way on Strava 👊\n\nSave this video and let’s perfect that running form! \n\n#strava #runningform #runna #marathontraining #stravaxrunna",
      "thumbnail_src": "https://instagram.fkul3-5.fna.fbcdn.net/v/t51.2885-15/530977447_24238418199177120_5738778586458432092_n.jpg?stp=c0.248.640.640a_dst-jpg_e15_tt6&_nc_ht=instagram.fkul3-5.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QEtQPNBpen9uPqX3E4WzAsOjzLbPgAfo8LeHd6ezBVoz5Z-YZEvKlUuIavyX2ajCSw&_nc_ohc=kBIYVaEctXYQ7kNvwHoFmLg&_nc_gid=PW4LTJ720jU0-vzxlhC7ug&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeUWnrECcysZQ0kDK1bqat1OJWcB0S5FQSB_PlM_otr0A&oe=68F5D650&_nc_sid=d885a2",
      "display_url": "https://instagram.fkul3-5.fna.fbcdn.net/v/t51.2885-15/530977447_24238418199177120_5738778586458432092_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=instagram.fkul3-5.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QEtQPNBpen9uPqX3E4WzAsOjzLbPgAfo8LeHd6ezBVoz5Z-YZEvKlUuIavyX2ajCSw&_nc_ohc=kBIYVaEctXYQ7kNvwHoFmLg&_nc_gid=PW4LTJ720jU0-vzxlhC7ug&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfcchFm7LHFc0lbY7EeCZ7qX1yR7iOxL8oGWBnBotfs4JA&oe=68F5D650&_nc_sid=d885a2",
      "video_url": "https://instagram.fkul3-5.fna.fbcdn.net/o1/v/t2/f2/m86/AQN7cw2nnk0bJXafDMXe7Vnz3td3Rjgj7wvosxVAf1L-p2EagPaHUpBDriilvOg-eWj1gHsO4BV3YTXMI8kCEwRmL-s1l265ALKGH6g.mp4?_nc_cat=100&_nc_oc=AdnXiwYtcUJa-n8cOjf5jb8nQG65EWtqM_1IAGEynFQeYYswfCKcEpBQF3htXMgoa3g&_nc_sid=5e9851&_nc_ht=instagram.fkul3-5.fna.fbcdn.net&_nc_ohc=MEzjyWrU_m8Q7kNvwE3QA4W&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6NjY4ODAwMTY4ODA4MDgwLCJ2aV91c2VjYXNlX2lkIjoxMDA5OSwiZHVyYXRpb25fcyI6NjIsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&vs=c5002011436d44&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC82MTRBNzBGNDUxRDIwRTI5REU1RTNGNDM3NzMzQzhBQV92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HUDc5MHhfUUVBcDlYWDRFQUt6ZDZzTDFaRGhzYnFfRUFBQUYVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmoLrmx6WRsAIVAigCQzMsF0BPKPXCj1wpGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=PW4LTJ720jU0-vzxlhC7ug&_nc_zt=28&oh=00_AfdnkaygXlUgMUrgJNBuxHjHdQaTPe4bT6BTFSCJ-X4bwQ&oe=68F1F53D",
      "has_audio": true,
      "accessibility_caption": null,
      "video_view_count": 97613,
      "video_play_count": 306017,
      "product_type": "clips",
      "video_duration": 62.32,
      "clips_music_attribution_info": {
        "artist_name": "isaintjames",
        "song_name": "Someday Soon",
        "uses_original_audio": true,
        "should_mute_audio": false,
        "should_mute_audio_reason": "",
        "audio_id": "467342335731489"
      },
      "is_video": true,
      "owner": {
        "id": "45274882639",
        "username": "runna",
        "is_verified": true,
        "profile_pic_url": "https://instagram.fkul3-3.fna.fbcdn.net/v/t51.2885-19/515368671_18074322308506640_4430541990677209637_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=instagram.fkul3-3.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2QEtQPNBpen9uPqX3E4WzAsOjzLbPgAfo8LeHd6ezBVoz5Z-YZEvKlUuIavyX2ajCSw&_nc_ohc=FJspWQaX1TUQ7kNvwGB5RUw&_nc_gid=PW4LTJ720jU0-vzxlhC7ug&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfdXC7_a9mCf7a3N7HKDH4qn9rUPxREuC3rgTdqTF1UGfQ&oe=68F5C2F6&_nc_sid=d885a2",
        "full_name": "Runna | Running Coaching App",
        "is_private": false,
        "is_unpublished": false,
        "follower_count": 650460,
        "post_count": 1929
      },
      "taken_at": "2025-08-14T16:35:47.000Z",
      "is_ad": false,
      "like_count": 3869,
      "is_affiliate": false,
      "is_paid_partnership": false,
      "location": null,
      "comment_count": 32,
      "comments": [
        {
          "id": "17862323160466640",
          "text": "We would be extremely excited to analyse Anya's running form - allowing our tech to study her gait and running form powered by science 🧡💙",
          "owner": {
            "id": "50543127377",
            "is_verified": false,
            "profile_pic_url": "https://instagram.fkul3-5.fna.fbcdn.net/v/t51.2885-19/504397013_18022855640687378_7459781583261816266_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDI0LmMyIn0&_nc_ht=instagram.fkul3-5.fna.fbcdn.net&_nc_cat=102&_nc_oc=Q6cZ2QEtQPNBpen9uPqX3E4WzAsOjzLbPgAfo8LeHd6ezBVoz5Z-YZEvKlUuIavyX2ajCSw&_nc_ohc=QlqMXoqTfoUQ7kNvwGkSfzQ&_nc_gid=PW4LTJ720jU0-vzxlhC7ug&edm=ANTKIIoBAAAA&ccb=7-5&oh=00_AfeLcqNALYU4YG_suVOQ39rNBHeLZyCFQgxZDEhDTEAHXw&oe=68F5DD4F&_nc_sid=d885a2",
            "username": "ochyapp"
          },
          "like_count": 0,
          "created_at": "2025-09-01T18:25:18.000Z"
        }
      ]
    }
  ]
}
  
  