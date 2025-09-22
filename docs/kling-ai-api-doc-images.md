# Perform API Authentication

## create access key and secret key on the kling.ai website

1. Obtain Access Key and Secret Key
2. Create and name your API key for easy management. You can copy the Access Key and Secret Key with one click.
3. Create API Key Name	One-click copy of Access Key and Secret Key	Supports enabling/disabling, renaming, and deletion

## Perform JWT Verification

Follow the JWT (JSON Web Token, RFC 7519) standard. Use the specified encryption method to generate an API Token, then verify the token via JWT. Refer to the documentation at: 「Kling AI」NEW API Specification

Click JWT Verification	Paste your API Token into the text box and click Verify	If it shows [Verification successful], the API is ready for use

## Construct Authorization

Use the JWT Token you generated to construct the Authorization and put it in the Request Header. Format it as follows: Authorization = “Bearer XXX”. Replace XXX with the API Token from Step 2. (There must be a space between “Bearer” and XXX.)

## Call the API Service
💡
API Domain: https://api-singapore.klingai.com


# Image Generation

## Create Task

| Protocol | Request URL | Request Method | Request Format | Response Format |
| --- | --- | --- | --- | --- |
| https | /v1/images/generations | POST | application/json | application/json |

### Request Header

| Field | Value | Description |
| --- | --- | --- |
| Content-Type | application/json | Data Exchange Format |
| Authorization | Authentication information, refer to API authentication | Authentication information, refer to API authentication |

### Request Body


|      Field             |      Type     |      Required    Field     |      Default     |      Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|------------------------|---------------|----------------------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|     model_name         |     string    |     Optional               |     kling-v1     |     Model   Name          Enum values：kling-v1, kling-v1-5, kling-v2, kling-v2-new, kling-v2-1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|     prompt             |     string    |     Required               |     None         |     Positive   text prompt          Cannot exceed 2500        characters                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|     negative_prompt    |     string    |     Optional               |     Null         |     Negative   text prompt          Cannot exceed 2500        characters        Note:   In the Image-to-Image scenario (when the "image" field is not   empty), negative prompts are not supported.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|     image              |     string    |     Optional               |     Null         |     Reference   Image          Support inputting image        Base64 encoding or image URL (ensure accessibility)        Please   note, if you use the Base64 method, make sure all image data parameters you   pass are in Base64 encoding format. When submitting data, do not add any   prefixes to the Base64-encoded string, such as data:image/png;base64. The   correct parameter format should be the Base64-encoded string itself.     Example:   Correct Base64 encoded parameter:     1     iV...g==     Incorrect   Base64 encoded parameter (includes the data: prefix):     1     data:image/png;base64,iVBORw...g==     Please   provide only the Base64-encoded string portion so that the system can   correctly process and parse your data.          Supported image formats        include.jpg / .jpeg / .png      The image file size cannot        exceed 10MB, and the width and height dimensions of the image shall not        be less than 300px, and the aspect ratio of the image should be between        1:2.5 ~ 2.5:1      the image_reference        parameter is not empty, the current parameter is required       |
|     image_reference    |     string    |     Optional               |     Null         |     Image   reference type          Enum values：subject(character feature reference),        face(character appearance reference)      When using face(character        appearance reference), the uploaded image must contain only one face.      When using kling-v1-5 and        the image parameter is not empty, the current parameter is required        Only   kling-v1-5 supports the current parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|     image_fidelity     |     float     |     Optional               |     0.5          |     Face   reference intensity for user-uploaded images during generation          Value range：[0,1]，The        larger the value, the stronger the reference intensity                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|     human_fidelity     |     float     |     Optional               |     0.45         |     Facial   reference intensity, refers to the similarity of the facial features of the   person in the reference image          Only image_reference        parameter is subject is available      Value range：[0,1]，The        larger the value, the stronger the reference intensity                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|     resolution         |     string    |     Optional               |     1k           |     Image   generation resolution          Enum values：1k, 2k            1k：1K standard       2k：2K high-res            The   support range for different model versions. For more details, please refer to   the current document's "2-0 Capability Map"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|     n                  |     int       |     Optional               |     1            |     Number   of generated images          Value range：[1,9]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|     aspect_ratio       |     string    |     Optional               |     16:9         |     Aspect   ratio of the generated images (width:height)          Enum values：16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3,        21:9        Different   model versions support varying ranges. For details, refer to the Capability   Map                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|     callback_url       |     string    |     Optional               |     None         |     The   callback notification address for the result of this task. If configured, the   server will actively notify when the task status changes          The specific message schema        of the notification can be found in “Callback Protocol”                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

### Response Body
```
{
  "code": 0, //Error Codes；Specific definitions can be found in Error codes
  "message": "string", //Error information
  "request_id": "string", //Request ID, generated by the system, is used to track requests and troubleshoot problems
  "data":{
  	"task_id": "string", //Task ID, generated by the system
    "task_status": "string", //Task status, Enum values：submitted、processing、succeed、failed
    "created_at": 1722769557708, //Task creation time, Unix timestamp, unit ms
    "updated_at": 1722769557708 //Task update time, Unix timestamp, unit ms
  }
}
```


## Query Task (Single)

| Protocol | Request URL | Request Method | Request Format | Response Format |
| --- | --- | --- | --- | --- |
| https | /v1/images/generations/{id} | GET | application/json | application/json |

### Request Header

| Field | Value | Description |
| --- | --- | --- |
| Content-Type | application/json | Data Exchange Format |
| Authorization | Authentication information, refer to API authentication | Authentication information, refer to API authentication |

### Request Path Parameters

| Field | Type | Required Field | Default | Description |
| --- | --- | --- | --- | --- |
| task_id | string | Required | None | The task ID generated by imagesRequest Path Parameters，directly fill the Value in the request path |

### Request Body

None

### Response Body

```
{
  "code": 0, //Error codes；Specific definitions can be found in Error codes
  "message": "string", //Error information
  "request_id": "string", //Request ID, generated by the system, is used to track requests and troubleshoot problems
  "data":{
  	"task_id": "string", //Task ID, generated by the system
    "task_status": "string", //Task status, Enum values：submitted、processing、succeed、failed
    "task_status_msg": "string", //Task status information, displaying the failure reason when the task fails (such as triggering the content risk control of the platform, etc.)
    "created_at": 1722769557708, //Task creation time, Unix timestamp, unit ms
    "updated_at": 1722769557708, //Task update time, Unix timestamp, unit ms
    "task_result":{
      "images":[
        {
          "index": int, //Image Number，0-9
          "url": "string" //URL for generating images，such as：https://h1.inkwai.com/bs2/upload-ylab-stunt/1fa0ac67d8ce6cd55b50d68b967b3a59.png(To ensure information security, generated images/videos will be cleared after 30 days. Please make sure to save them promptly.)
        }
      ]
    }
  }
}
```
