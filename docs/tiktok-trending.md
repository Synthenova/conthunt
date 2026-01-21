I want to make an API call to https://api.scrapecreators.com/v1/tiktok/get-trending-feed. 

  Please help me write code to make this API call and handle the response appropriately. Include error handling and best practices.

  Here are the details:
  
  Endpoint: GET https://api.scrapecreators.com/v1/tiktok/get-trending-feed
  
  Description: Get the trending feed from TikTok.
  
  Required Headers:
  - x-api-key: Your API key
  
  Parameters:
  - region  (Required): Where you want the proxy to be. This doesn't mean that you will only see TikToks from this region, you will just see the content that isn't banned in that region.
- trim : Set to true to get a trimmed response.
  
  Example Response:
  {
  "aweme_list": [
    {
      "aweme_id": "7540000301621841183",
      "desc": "#hudsonvalley #fallgetaway #farm #upstateny #resort ",
      "desc_language": "un",
      "region": "US",
      "statistics": {
        "aweme_id": "7540000301621841183",
        "comment_count": 646,
        "digg_count": 71423,
        "download_count": 130,
        "play_count": 1443873,
        "share_count": 8440,
        "forward_count": 0,
        "lose_count": 0,
        "lose_comment_count": 0,
        "whatsapp_share_count": 37,
        "collect_count": 21957,
        "repost_count": 0
      },
      "video": {
        "play_addr": {
          "uri": "https://v16m.tiktokcdn-us.com/55f0fa91eb07f93e6cc97b69cf44bd28/68b782c0/video/tos/useast5/tos-useast5-ve-27dcd7c799-tx/ocTKSt6SBoLEzYiMEvPhB7Ak7g1fI9ZDxCOqp8/?a=1233&bti=OHYpOTY0Zik3OjlmOm01MzE6ZDQ0MDo%3D&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&br=124&bt=62&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=audio_mpeg&qs=3&rc=NTQ3O2hnOzo1NjU6NGRoaUBpMzV2M2k6ZnduaDMzNzU8M0AvMy8yMzVeNjIxNC9hYjQvYSM2L3FpcjRvYmtgLS1kMTZzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e00088000&shp=d05b14bd&shcp=-",
          "url_list": [
            "https://v16m.tiktokcdn-us.com/55f0fa91eb07f93e6cc97b69cf44bd28/68b782c0/video/tos/useast5/tos-useast5-ve-27dcd7c799-tx/ocTKSt6SBoLEzYiMEvPhB7Ak7g1fI9ZDxCOqp8/?a=1233&bti=OHYpOTY0Zik3OjlmOm01MzE6ZDQ0MDo%3D&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&br=124&bt=62&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=audio_mpeg&qs=3&rc=NTQ3O2hnOzo1NjU6NGRoaUBpMzV2M2k6ZnduaDMzNzU8M0AvMy8yMzVeNjIxNC9hYjQvYSM2L3FpcjRvYmtgLS1kMTZzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e00088000&shp=d05b14bd&shcp=-",
            "https://v19.tiktokcdn-us.com/e03d8fc87042d233b0cb7da3956adae5/68b782c0/video/tos/useast5/tos-useast5-ve-27dcd7c799-tx/ocTKSt6SBoLEzYiMEvPhB7Ak7g1fI9ZDxCOqp8/?a=1233&bti=OHYpOTY0Zik3OjlmOm01MzE6ZDQ0MDo%3D&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&br=124&bt=62&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=audio_mpeg&qs=3&rc=NTQ3O2hnOzo1NjU6NGRoaUBpMzV2M2k6ZnduaDMzNzU8M0AvMy8yMzVeNjIxNC9hYjQvYSM2L3FpcjRvYmtgLS1kMTZzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e00088000&shp=d05b14bd&shcp=-",
            "https://api16-normal-useast5.tiktokv.us/aweme/v1/play/?video_id=v09942g40000cenketrc77ufl0ts2290&line=0&is_play_url=1&source=FEED&file_id=2f7eead12772435297a88d6e58246122&item_id=7183038472843692805&signaturev3=dmlkZW9faWQ7ZmlsZV9pZDtpdGVtX2lkLmVmNjczNDdkZDYxMDMxMWFmNjY5NTgyMWE1ZjI3MzA0&shp=d05b14bd&shcp=-"
          ],
          "width": 720,
          "height": 720,
          "url_key": "7183038472843692805",
          "url_prefix": null
        },
        "cover": {
          "uri": "tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13",
          "url_list": [
            "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13~tplv-photomode-image-cover:640:0:q70.webp?dr=12229&refresh_token=df32aa50&x-expires=1757545200&x-signature=zurwCGa5E9ieLV%2FaQHxx19%2FvpJY%3D&t=5897f7ec&ps=d5b8ac02&shp=d05b14bd&shcp=1a816805&idc=useast5&s=FEED&biz_tag=tt_photomode&sc=cover"
          ],
          "width": 640,
          "height": 853,
          "url_prefix": null
        }
      },
      "image_post_info": {
        "images": [
          {
            "display_image": {
              "uri": "tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13",
              "url_list": [
                "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13~tplv-photomode-sr-vqe2:1080:0:1080:0:q75.webp?dr=10952&refresh_token=0efd0e37&x-expires=1757545200&x-signature=uEKcmDy5CeI9%2BCTYKvVleyhFFfc%3D&t=5897f7ec&ps=28cf8ac7&shp=d05b14bd&shcp=1a816805&idc=useast5&s=FEED&biz_tag=tt_photomode&sc=image",
                "https://p16-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13~tplv-photomode-sr-vqe2:1080:0:1080:0:q75.webp?dr=10952&refresh_token=867a0203&x-expires=1757545200&x-signature=aYWk4ePDaIh4fz%2FSYVZWyHxiKaE%3D&t=5897f7ec&ps=28cf8ac7&shp=d05b14bd&shcp=1a816805&idc=useast5&s=FEED&biz_tag=tt_photomode&sc=image",
                "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-i-photomode-tx2/3a1c4f9217414c3c95dd8d25c2dd8d13~tplv-photomode-sr-vqe2:1080:0:1080:0:q75.jpeg?dr=10952&refresh_token=8542f141&x-expires=1757545200&x-signature=3Y92w55AAHHrWh4YG7IMfYevoJs%3D&t=5897f7ec&ps=28cf8ac7&shp=d05b14bd&shcp=1a816805&idc=useast5&s=FEED&biz_tag=tt_photomode&sc=image"
              ],
              "width": 1080,
              "height": 1440,
              "url_prefix": null,
              "preview": {
                "data": "JjKsVpu2lacDqKQTr3r1vbQ7nneyl2DbRtqwiB1yKd5VaJpmb0K22irPkmincCSdbct0FZ9/ZuVzCDitAaVMzAs1atvBHHGEfBrweW2x7HMcpbTywjY4OavwmSTDHpW02n2ztuIFJLZpsxHWqqTS0Zk4RfQgQIEGaKqyRzo2ADiitPrbRj9XRtyE7TiqDl93etHFNMantWB0FAFz61PCHzk1PsUdqUDFMBdqnqKKXNFKyAKKKKAENAoooASiiimB/9k=",
                "preview_type": 2,
                "meta_key": ""
              }
            }
          }
        ],
        "title": "The most perfect fall getaway for the day or the night! 🍂",
        "post_extra": "{\"photo_cover_shrink\":false,\"photo_blurhash\":false,\"photo_progressive\":false}"
      },
      "author": {
        "uid": "6754760670083138566",
        "short_id": "0",
        "nickname": "Bre 🤍",
        "signature": "3rd grade teacher 🍎| making life cute 🪞| home inspo loading… 🏡🤎”",
        "avatar_thumb": {
          "uri": "tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18",
          "url_list": [
            "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18~tplv-tiktokx-cropcenter-q:100:100:q70.heic?dr=8835&idc=useast5&ps=87d6e48a&refresh_token=22f3402b&s=FEED&sc=avatar&shcp=1a816805&shp=d05b14bd&t=223449c4&x-expires=1756335600&x-signature=vQBsMRRY5xPAgpNt%2F6JchCzoVDE%3D",
            "https://p16-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18~tplv-tiktokx-cropcenter-q:100:100:q70.heic?dr=8835&idc=useast5&ps=87d6e48a&refresh_token=20e70157&s=FEED&sc=avatar&shcp=1a816805&shp=d05b14bd&t=223449c4&x-expires=1756335600&x-signature=BwGDs7Qyi%2FZPtMAfjNrsdLBJmmg%3D"
          ],
          "width": 720,
          "height": 720,
          "url_prefix": null
        },
        "avatar_medium": {
          "uri": "tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18",
          "url_list": [
            "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18~tplv-tiktokx-cropcenter-q:720:720:q70.heic?dr=8836&idc=useast5&ps=87d6e48a&refresh_token=93846dfc&s=FEED&sc=avatar&shcp=1a816805&shp=d05b14bd&t=223449c4&x-expires=1756335600&x-signature=y49Gf4w80feFtWOJCykL7x2c20Q%3D",
            "https://p16-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/3bc038986117debaa55c18bae5685e18~tplv-tiktokx-cropcenter-q:720:720:q70.heic?dr=8836&idc=useast5&ps=87d6e48a&refresh_token=9adabdff&s=FEED&sc=avatar&shcp=1a816805&shp=d05b14bd&t=223449c4&x-expires=1756335600&x-signature=kODwU7cWAsJJcv3KRA5Sipsg8L8%3D"
          ],
          "width": 720,
          "height": 720,
          "url_prefix": null
        },
        "region": "US",
        "language": "en",
        "sec_uid": "MS4wLjABAAAANbZGXVN-iwJvesiIVGgD_nRTpyI4PGOXHEbt01cN9U5S3Ih21qUe5WQ9ztsn2J6h",
        "social_info": "{\"imprs_info\":\"vv_100k+\",\"is_cold_info\":\"0\"}",
        "events": null
      },
      "create_time": 1755543133,
      "is_ad": false,
      "is_eligible_for_commission": false,
      "create_time_utc": "2025-08-18T18:52:13.000Z",
      "url": "https://www.tiktok.com/@breannafriedman0/photo/7540000301621841183"
    },
    {
      "aweme_id": "7540968798585670968",
      "desc": "Thrilling 3D motorcycle chases in the city. Evade cops at top speed!",
      "desc_language": "en",
      "region": "VN",
      "statistics": {
        "aweme_id": "7540968798585670968",
        "comment_count": 27,
        "digg_count": 6035,
        "download_count": 72,
        "play_count": 589406,
        "share_count": 192,
        "forward_count": 0,
        "lose_count": 0,
        "lose_comment_count": 0,
        "whatsapp_share_count": 6,
        "collect_count": 442,
        "repost_count": 0
      },
      "video": {
        "play_addr": {
          "uri": "v14033g50000d2jed4vog65sp3hesl60",
          "url_list": [
            "https://v16m.tiktokcdn-us.com/d25a50c8986e5c586718967918f1d43a/68ae9c38/video/tos/alisg/tos-alisg-ve-0051c001-sg/ogoVQNqDADEWcgdEYzeBfFy5aBUBTIckNupXSg/?a=1233&bti=Ozk3QGo4dik3OjlmMzAuYCM6bTQ0MDo%3D&ch=0&cr=13&dr=0&er=0&lr=all&net=0&cd=0%7C0%7C0%7C&cv=1&br=1820&bt=910&cs=0&ds=6&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=video_mp4&qs=0&rc=OTtpZmkzZGVoaGQ8NDplM0BpM29oNnY5cjdoNTMzODYzNEBgYS8vYzExXzQxYDNeXjRfYSMzcGVtMmRzYWdhLS1kMDFzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e000b8000",
            "https://v19.tiktokcdn-us.com/dbec75da646c73c3eebb3b113e200a8e/68ae9c38/video/tos/alisg/tos-alisg-ve-0051c001-sg/ogoVQNqDADEWcgdEYzeBfFy5aBUBTIckNupXSg/?a=1233&bti=Ozk3QGo4dik3OjlmMzAuYCM6bTQ0MDo%3D&ch=0&cr=13&dr=0&er=0&lr=all&net=0&cd=0%7C0%7C0%7C&cv=1&br=1820&bt=910&cs=0&ds=6&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=video_mp4&qs=0&rc=OTtpZmkzZGVoaGQ8NDplM0BpM29oNnY5cjdoNTMzODYzNEBgYS8vYzExXzQxYDNeXjRfYSMzcGVtMmRzYWdhLS1kMDFzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e000b8000",
            "https://api16-normal-useast5.tiktokv.us/aweme/v1/play/?faid=1233&file_id=b07ba7a169ca4e7ebb4a40ff2c2fd8c6&is_play_url=1&item_id=7540968798585670968&line=0&signaturev3=dmlkZW9faWQ7ZmlsZV9pZDtpdGVtX2lkLjViYWIwNDI3NWMwNzA1ZTI3YjhkMjU1OGJmM2M5N2Nk&source=FEED&video_id=v14033g50000d2jed4vog65sp3hesl60"
          ],
          "width": 576,
          "height": 1024,
          "url_key": "v14033g50000d2jed4vog65sp3hesl60_h264_540p_931925",
          "data_size": 2337618,
          "file_hash": "f6dcdd4d0b736166ba8d0ce6a58640a5",
          "url_prefix": null
        },
        "download_addr": {
          "uri": "v14033g50000d2jed4vog65sp3hesl60",
          "url_list": [
            "https://v16m.tiktokcdn-us.com/2f0e172365ed83d4fcc3080a47e8c044/68ae9c38/video/tos/alisg/tos-alisg-ve-0051c001-sg/oIFXzugkDIVyYN5aAcFgUNNTqBfeoFBQEBgcDp/?a=1233&bti=Ozk3QGo4dik3OjlmMzAuYCM6bTQ0MDo%3D&ch=0&cr=13&dr=0&er=0&lr=all&net=0&cd=0%7C0%7C0%7C&cv=1&br=2074&bt=1037&cs=0&ds=3&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=video_mp4&qs=0&rc=NjtnOmQ1PDZpNGY8PGU8aUBpM29oNnY5cjdoNTMzODYzNEBiNDJeNV4xNWIxLmE1MF41YSMzcGVtMmRzYWdhLS1kMDFzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e000b8000",
            "https://v19.tiktokcdn-us.com/eb93c17307107d077971e1a577100ac7/68ae9c38/video/tos/alisg/tos-alisg-ve-0051c001-sg/oIFXzugkDIVyYN5aAcFgUNNTqBfeoFBQEBgcDp/?a=1233&bti=Ozk3QGo4dik3OjlmMzAuYCM6bTQ0MDo%3D&ch=0&cr=13&dr=0&er=0&lr=all&net=0&cd=0%7C0%7C0%7C&cv=1&br=2074&bt=1037&cs=0&ds=3&ft=arR-Iq4fmbdPD1250i5T3wUk~i~AMeF~O5&mime_type=video_mp4&qs=0&rc=NjtnOmQ1PDZpNGY8PGU8aUBpM29oNnY5cjdoNTMzODYzNEBiNDJeNV4xNWIxLmE1MF41YSMzcGVtMmRzYWdhLS1kMDFzcw%3D%3D&vvpl=1&l=20250826234818FC500F9F5A67BF1C488E&btag=e000b8000",
            "https://api16-normal-useast5.tiktokv.us/aweme/v1/play/?video_id=v14033g50000d2jed4vog65sp3hesl60&line=0&watermark=1&logo_name=tiktok&source=FEED&file_id=8fa93b89d91c41ef8349a28aa75d78e3&item_id=7540968798585670968&signaturev3=dmlkZW9faWQ7ZmlsZV9pZDtpdGVtX2lkLjM5MzUzNGNhZmE3YzA3MTQwMGViYWI1MzIxMDQwMTll&shp=d05b14bd&shcp=-"
          ],
          "width": 720,
          "height": 720,
          "data_size": 2665400,
          "url_prefix": null
        }
      },
      "author": {
        "uid": "7457141013010826241",
        "short_id": "0",
        "nickname": "lyngame.52",
        "signature": "",
        "follow_status": 0,
        "is_block": false,
        "custom_verify": "",
        "unique_id": "lyngame.52",
        "region": "VN",
        "is_discipline_member": false,
        "secret": 0,
        "language": "vi",
        "type_label": [],
        "relative_users": null,
        "cha_list": null,
        "sec_uid": "MS4wLjABAAAAQLDjklcDNJ4ylkeY_3oFIf5KtaEorKG1-n0ZwmRORZig3y30uvmayXicp8pAdUvt"
      },
      "create_time": 1755768714,
      "is_ad": false,
      "is_eligible_for_commission": false,
      "create_time_utc": "2025-08-21T09:31:54.000Z",
      "url": "https://www.tiktok.com/@lyngame.52/video/7540968798585670968"
    }
  ]
}
  
  