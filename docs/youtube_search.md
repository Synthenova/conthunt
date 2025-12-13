I want to make an API call to https://api.scrapecreators.com/v1/youtube/search. 

  Please help me write code to make this API call and handle the response appropriately. Include error handling and best practices.

  Here are the details:
  
  Endpoint: GET https://api.scrapecreators.com/v1/youtube/search
  
  Description: Search YouTube and get matching videos, channels, playlists, shorts, lives, etc. Video explaining the response format: https://www.tella.tv/video/explaining-youtube-search-results-payload-353a
  
  Required Headers:
  - x-api-key: Your API key
  
  Parameters:
  - query  (Required): Search query
- uploadDate : Upload date
  Options: last_hour, today, this_week, this_month, this_year
- sortBy : Sort by
  Options: relevance, upload_date
- filter : Filter by these options. Note this doesn't work when you use either 'uploadDate' or 'sortBy'. It basically only works when you have a query.
  Options: shorts
- continuationToken : Continuation token to get more videos. Get 'continuationToken' from previous response.
- includeExtras : This will get you the like + comment count and the description. To get the full details of the video, use the /v1/youtube/video endpoint. *This will slow down the response slightly.*
  
  Example Response:
  {
  "videos": [
    {
      "type": "video",
      "id": "BzSzwqb-OEE",
      "url": "https://www.youtube.com/watch?v=BzSzwqb-OEE",
      "title": "NF - RUNNING (Audio)",
      "thumbnail": "https://i.ytimg.com/vi/BzSzwqb-OEE/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLCasEKav1CLqeSSE2IYDqjGiIMBGw",
      "channel": {
        "id": "UCoRR6OLuIZ2-5VxtnQIaN2w",
        "title": "NFrealmusic",
        "handle": "channel/UCoRR6OLuIZ2-5VxtnQIaN2w",
        "thumbnail": "https://yt3.ggpht.com/J1_Si0TYNZ-991v09y8RpCh4_Z_ALwKmPgMYnJqjNhoglVtipf3oEN8LpzG1kS0qsv8Jptpmmg=s88-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "14,860,541 views",
      "viewCountInt": 14860541,
      "publishedTimeText": "2 years ago",
      "publishedTime": "2023-05-28T17:08:46.499Z",
      "lengthText": "4:14",
      "lengthSeconds": 254,
      "badges": []
    },
    {
      "type": "video",
      "id": "-tLKoLN-dz4",
      "url": "https://www.youtube.com/watch?v=-tLKoLN-dz4",
      "title": "Not Alone, Racing the High Lonesome 100",
      "thumbnail": "https://i.ytimg.com/vi/-tLKoLN-dz4/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLD1ziOa9dTFWSL6lyK6m6eO_uZkJg",
      "channel": {
        "id": "UCNKMpnM_Yvf6E-Hhf9btYqA",
        "title": "Jeff Pelletier",
        "handle": "JeffPelletier",
        "thumbnail": "https://yt3.ggpht.com/YLRllcd7Q0iPYDIkJjXGEiOiJStz4KK7iepwcfTVK0yveHKqFSaLVzTvvZ0anO-SeUlXs1jNCIE=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "119,308 views",
      "viewCountInt": 119308,
      "publishedTimeText": "3 months ago",
      "publishedTime": "2025-02-28T18:08:46.499Z",
      "lengthText": "53:18",
      "lengthSeconds": 3198,
      "badges": [
        "4K",
        "CC"
      ]
    },
    {
      "type": "video",
      "id": "2LnqF4CziXY",
      "url": "https://www.youtube.com/watch?v=2LnqF4CziXY",
      "title": "Base running blunder you've never seen costs the Braves a comeback vs. the Padres, a breakdown",
      "thumbnail": "https://i.ytimg.com/vi/2LnqF4CziXY/hqdefault.jpg?sqp=-oaymwEnCOADEI4CSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLAKH3MD2Ehyuh7C0pK-RA_Whf0GAg",
      "channel": {
        "id": "UCl9E4Zxa8CVr2LBLD0_TaNg",
        "title": "Jomboy Media",
        "handle": "JomboyMedia",
        "thumbnail": "https://yt3.ggpht.com/ytc/AIdro_l3ee46SNWQDE3tpPXONvTIEN2ZFGF7DMRLSc4kPx1zhEQ=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "146,461 views",
      "viewCountInt": 146461,
      "publishedTimeText": "19 hours ago",
      "publishedTime": "2025-05-28T17:08:46.499Z",
      "lengthText": "4:56",
      "lengthSeconds": 296,
      "badges": [
        "New"
      ]
    },
    {
      "type": "video",
      "id": "v5ePUS8sspo",
      "url": "https://www.youtube.com/watch?v=v5ePUS8sspo",
      "title": "Why We Run | Eric Floberg, Chapter 1",
      "thumbnail": "https://i.ytimg.com/vi/v5ePUS8sspo/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLDcFW-Qb4HhP5NRcz4QQfx0-qzbVg",
      "channel": {
        "id": "UCN9LezrPgYqJ_FsuculbCew",
        "title": "Path Projects",
        "handle": "pathprojects",
        "thumbnail": "https://yt3.ggpht.com/2OgXxRXjngjCwkJvzxSP-LvTTHg8HZjcNvkyR50-owtvPJAS_8auaC2Swcy8OP_yweTh5kNM=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "38,271 views",
      "viewCountInt": 38271,
      "publishedTimeText": "2 weeks ago",
      "publishedTime": "2025-05-14T17:08:46.499Z",
      "lengthText": "7:09",
      "lengthSeconds": 429,
      "badges": [
        "4K"
      ]
    },
    {
      "type": "video",
      "id": "BQm9bvIbHWg",
      "url": "https://www.youtube.com/watch?v=BQm9bvIbHWg",
      "title": "Shin Sonic - Running (official song)",
      "thumbnail": "https://i.ytimg.com/vi/BQm9bvIbHWg/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLBCDQzMBzFlHO_MNmf_09RvctE1FA",
      "channel": {
        "id": "UC3KTMQwLhXp-e2PNHl4UqgQ",
        "title": "Horror Skunx 2",
        "handle": "HorrorSkunx2",
        "thumbnail": "https://yt3.ggpht.com/DZcKI4hN0NjmeZUDJ0p89GplMV9TvI5p4sc-g8sOmvIAEsOhk1rZgEImleTIX1lm1XcGSoFjibw=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "33,016,214 views",
      "viewCountInt": 33016214,
      "publishedTimeText": "8 months ago",
      "publishedTime": "2024-09-28T17:08:46.499Z",
      "lengthText": "2:27",
      "lengthSeconds": 147,
      "badges": [
        "4K"
      ]
    },
    {
      "type": "video",
      "id": "ZzckdJQXTRw",
      "url": "https://www.youtube.com/watch?v=ZzckdJQXTRw",
      "title": "Nebraska Legislature running out of time with five days left in session",
      "thumbnail": "https://i.ytimg.com/vi/ZzckdJQXTRw/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLDWSuGN6sKLL_0zi0qW6dq9KUJJXw",
      "channel": {
        "id": "UCczdiIilpYSmiF074WMCNiA",
        "title": "KETV NewsWatch 7",
        "handle": "KETV",
        "thumbnail": "https://yt3.ggpht.com/ytc/AIdro_nbSThKRi-Oy5f4MwrLasU8ZKjmPwWQICJWL7Qoi39XxhE=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "131 views",
      "viewCountInt": 131,
      "publishedTimeText": "1 day ago",
      "publishedTime": "2025-05-27T17:08:46.499Z",
      "lengthText": "2:55",
      "lengthSeconds": 175,
      "badges": [
        "New",
        "CC"
      ]
    },
    {
      "type": "video",
      "id": "DQBCdbV2Enc",
      "url": "https://www.youtube.com/watch?v=DQBCdbV2Enc",
      "title": "Virtual Running Videos For Treadmill With Music | Virtual Run Mountain",
      "thumbnail": "https://i.ytimg.com/vi/DQBCdbV2Enc/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLDwizepUqaWsce-i6KKncGQ8gt4Mw",
      "channel": {
        "id": "UCY95zbGK0vlAZ8Gk8OZqa1g",
        "title": "Virtual Running Videos",
        "handle": "virtualrunningvideo",
        "thumbnail": "https://yt3.ggpht.com/ytc/AIdro_nSOB2OGNIDZ8-eSTUX-qGsioNIZQrIjzMhicCXxT_OWw4=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "1,549,036 views",
      "viewCountInt": 1549036,
      "publishedTimeText": "4 years ago",
      "publishedTime": "2021-05-28T17:08:46.499Z",
      "lengthText": "50:20",
      "lengthSeconds": 3020,
      "badges": [
        "4K"
      ]
    },
    {
      "type": "video",
      "id": "8Z1N-wfKq8Q",
      "url": "https://www.youtube.com/watch?v=8Z1N-wfKq8Q",
      "title": "Long Run Home | Wesley Kiptoo Documentary",
      "thumbnail": "https://i.ytimg.com/vi/8Z1N-wfKq8Q/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLCdSHUqQUGg3qfvcvmgSfsa2w76EQ",
      "channel": {
        "id": "UC1aUDqQeH_3lPoilfa--Eaw",
        "title": "The Art of Documentary",
        "handle": "theartofdocumentary",
        "thumbnail": "https://yt3.ggpht.com/Ihd0tsIyhuchHYwbva2RrqqgkWLdkxIRXBJT-TiXOUOo732C7kNAT77iIDy89uGjJOx_DKZcSA=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "733,315 views",
      "viewCountInt": 733315,
      "publishedTimeText": "1 year ago",
      "publishedTime": "2024-05-28T17:08:46.500Z",
      "lengthText": "22:22",
      "lengthSeconds": 1342,
      "badges": [
        "4K"
      ]
    },
    {
      "type": "video",
      "id": "9DpejbEJ5Gs",
      "url": "https://www.youtube.com/watch?v=9DpejbEJ5Gs",
      "title": "Chiké & Simi – Running (To You) [Official Video]",
      "thumbnail": "https://i.ytimg.com/vi/9DpejbEJ5Gs/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLBdg5rjuERQWjbbFyTu6RXIyxdwXQ",
      "channel": {
        "id": "UCVXhwLsuNli6N8FElr7sNvQ",
        "title": "Chike",
        "handle": "channel/UCVXhwLsuNli6N8FElr7sNvQ",
        "thumbnail": "https://yt3.ggpht.com/ZapjSStUkuj7kGKoa-fNzhFMNFQsVCV6yF517qmp5VqQ6ozsVxsAEKiNa0dMfN3Vo-sGEuKj6oo=s88-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "85,803,087 views",
      "viewCountInt": 85803087,
      "publishedTimeText": "4 years ago",
      "publishedTime": "2021-05-28T17:08:46.500Z",
      "lengthText": "3:35",
      "lengthSeconds": 215,
      "badges": []
    },
    {
      "type": "video",
      "id": "6l0Qp1GXY7w",
      "url": "https://www.youtube.com/watch?v=6l0Qp1GXY7w",
      "title": "NF - RUNNING (Lyrics)",
      "thumbnail": "https://i.ytimg.com/vi/6l0Qp1GXY7w/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLBWYszI_N1ezpehAw-Tv7BZDz5j8Q",
      "channel": {
        "id": "UCcJZ-w0N3-Z2jnJ8UgoBclQ",
        "title": "SauceOnly",
        "handle": "SauceOnly",
        "thumbnail": "https://yt3.ggpht.com/dy5MPezFhnDfpaf7loqoSTGAS9LuIo4EOs-ckW9FMGU15KlG7SFtvzFNVEcfH8DCBpHs8Hxe=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "2,117,140 views",
      "viewCountInt": 2117140,
      "publishedTimeText": "2 years ago",
      "publishedTime": "2023-05-28T17:08:46.500Z",
      "lengthText": "4:14",
      "lengthSeconds": 254,
      "badges": []
    },
    {
      "type": "video",
      "id": "K1QDYuHGa_I",
      "url": "https://www.youtube.com/watch?v=K1QDYuHGa_I",
      "title": "David Goggins - How To Run Every Single Morning",
      "thumbnail": "https://i.ytimg.com/vi/K1QDYuHGa_I/hq720.jpg?sqp=-oaymwEnCNAFEJQDSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLAQQN7_MjBcgTLtPH3bi-5rvakK2g",
      "channel": {
        "id": "UCIaH-gZIVC432YRjNVvnyCA",
        "title": "Chris Williamson",
        "handle": "ChrisWillx",
        "thumbnail": "https://yt3.ggpht.com/ytc/AIdro_mmN30Y4ap7dtPfLw8Algolz_LGtHHpTJxa-qAw-MCQpdo=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "5,030,730 views",
      "viewCountInt": 5030730,
      "publishedTimeText": "2 years ago",
      "publishedTime": "2023-05-28T17:08:46.500Z",
      "lengthText": "11:23",
      "lengthSeconds": 683,
      "badges": [
        "4K"
      ]
    }
  ],
  "channels": [],
  "playlists": [],
  "shorts": [
    {
      "type": "short",
      "id": "uMNvF-lSCHg",
      "url": "https://www.youtube.com/watch?v=uMNvF-lSCHg",
      "title": "LONG RUN ROUTINE #run #runvlog #runner #shorts #morning",
      "thumbnail": "https://i.ytimg.com/vi/uMNvF-lSCHg/hq720.jpg?sqp=-oaymwFBCNAFEJQDSFryq4qpAzMIARUAAIhCGADYAQHiAQoIGBACGAY4AUAB8AEB-AG2CIACgA-KAgwIABABGFsgXyhlMA8=&rs=AOn4CLA_P-5ExEn9EGLJDNeJedsxb3k1eQ",
      "channel": {
        "id": "UCGRdcRxpJWi5Q2oDCrMDUuQ",
        "title": "Abby and Ryan",
        "handle": "abbyandryan",
        "thumbnail": "https://yt3.ggpht.com/8UdUEesepx1Ry_rFUPJOJgndTCKno9VTkSysnuJpFjMj63N6av0pNwnqoiKh_7PN2dw7PGIp=s68-c-k-c0x00ffffff-no-rj"
      },
      "viewCountText": "462,705 views",
      "viewCountInt": 462705,
      "publishedTimeText": "10 months ago",
      "publishedTime": "2024-07-28T17:08:46.498Z",
      "lengthText": "0:44",
      "lengthSeconds": 44,
      "badges": []
    }
  ],
  "shelves": [
    {
      "type": "shelf",
      "title": "Shorts",
      "items": [
        {
          "type": "short",
          "id": "LLBR5nO05tE",
          "url": "https://www.youtube.com/watch?v=LLBR5nO05tE",
          "title": "running through walls gone wrong",
          "thumbnail": "https://i.ytimg.com/vi/LLBR5nO05tE/oardefault.jpg?sqp=-oaymwEoCJUDENAFSFqQAgHyq4qpAxcIARUAAIhC2AEB4gEKCBgQAhgGOAFAAQ==&rs=AOn4CLCYYIIDmBllgkLP68AjVs25UpyevQ",
          "viewCountText": "750K",
          "viewCountInt": 750000
        }
      ]
    }
  ],
  "lives": [],
  "continuationToken": "EooDEg..."
}
  
  