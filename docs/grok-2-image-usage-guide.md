You're right, the main x.ai website is more focused on the Grok chatbot. The developer-specific information is hosted on its own documentation site.

The `grok-2-image` model is accessible via an API. Here is a developer's guide on how to use it, based on the official documentation.

### 1\. How It Works: The API

You don't download the model. Instead, you send an API request to an x.ai endpoint containing your text prompt. The x.ai servers generate the image and send it back to you, either as a URL or as raw image data.

This process requires an **API key** for authentication.

### 2\. Getting Your API Key

Before you can make any requests, you need to:

1.  Create an x.ai account.
2.  Navigate to the **API Keys** page in your x.ai Console.
3.  Generate a new secret key. **Store this key securely**, as you will not be able to see it again.

You will send this key in the `Authorization` header of your requests.

-----

### 3\. API Request Structure

Here is the essential information for making a request to the `grok-2-image` model.

  * **Endpoint:** `https://api.x.ai/v1/images/generations`
  * **Method:** `POST`
  * **Headers:**
      * `Content-Type: application/json`
      * `Authorization: Bearer <YOUR_XAI_API_KEY>`

#### Request Body Parameters

You send a JSON object in the body of your `POST` request with the following fields:

  * **`model`** (string, required): The model to use. For this, you would specify **`"grok-2-image"`**.
  * **`prompt`** (string, required): A text description of the image you want to generate.
  * **`n`** (integer, optional): The number of images to generate. The default is 1, and the maximum is 10.
  * **`response_format`** (string, optional): The format for the returned image data.
      * **`"url"`** (default): Returns a temporary URL where the image is hosted.
      * **`"b64_json"`**: Returns the image data as a Base64-encoded JSON string.

**Note:** According to the official documentation, parameters like `size`, `quality`, or `style` are not supported at this time.

-----

### 4\. Code Examples

Here are practical examples of how to call the API in different languages.

#### 🏛️ cURL (Terminal)

This is the simplest way to test the endpoint from your command line.

```bash
curl -X POST "https://api.x.ai/v1/images/generations" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_XAI_API_KEY>" \
     -d '{
           "model": "grok-2-image",
           "prompt": "A photorealistic image of a red panda wearing a tiny astronaut helmet, standing on Mars.",
           "n": 1,
           "response_format": "url"
         }'
```

#### 🐍 Python

This example uses the popular `requests` library.

```python
import requests
import json

API_KEY = "<YOUR_XAI_API_KEY>"
IMAGE_ENDPOINT = "https://api.x.ai/v1/images/generations"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "grok-2-image",
    "prompt": "A photorealistic image of a red panda wearing a tiny astronaut helmet, standing on Mars.",
    "n": 1,
    "response_format": "url"
}

try:
    response = requests.post(IMAGE_ENDPOINT, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

    # Process the response
    data = response.json()
    print("Image generation successful!")
    print(json.dumps(data, indent=2))

    # Extract the image URL
    if 'data' in data and len(data['data']) > 0:
        image_url = data['data'][0].get('url')
        if image_url:
            print(f"Image URL: {image_url}")
        else:
            print("Response contained 'b64_json' data.")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response body: {response.text}")
except Exception as err:
    print(f"An error occurred: {err}")

```

#### JavaScript (Node.js)

This example uses `node-fetch`. You would need to install it first (`npm install node-fetch`).

```javascript
import fetch from 'node-fetch';

const API_KEY = '<YOUR_XAI_API_KEY>';
const IMAGE_ENDPOINT = 'https://api.x.ai/v1/images/generations';

const payload = {
  model: 'grok-2-image',
  prompt: 'A photorealistic image of a red panda wearing a tiny astronaut helmet, standing on Mars.',
  n: 1,
  response_format: 'url'
};

async function generateImage() {
  try {
    const response = await fetch(IMAGE_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
    }

    const data = await response.json();
    console.log('Image generation successful!');
    console.log(JSON.stringify(data, null, 2));

    // Extract the image URL
    if (data.data && data.data.length > 0 && data.data[0].url) {
      console.log(`Image URL: ${data.data[0].url}`);
    }

  } catch (error) {
    console.error('Failed to generate image:', error);
  }
}

generateImage();
```

-----

### 5\. Understanding the Response

The API will send back a JSON object.

#### Example Response (for `response_format: "url"`)

You will get a list in the `data` field, with one object for each image you requested.

```json
{
  "created": 1715888888,
  "data": [
    {
      "url": "https://img.x.ai/generated-image-url/...",
      "revised_prompt": "A highly detailed, photorealistic depiction of a small red panda. The panda is upright on its hind legs, outfitted in a miniature, reflective astronaut helmet. It stands on the rust-colored, rocky terrain of Mars, with a faint, dusty atmosphere in the background."
    }
  ]
}
```

  * **`url`**: The temporary URL hosting your generated image.
  * **`revised_prompt`**: The prompt that was *actually* used by the image model. Grok may revise your original prompt for clarity and detail to get a better result.

#### Example Response (for `response_format: "b64_json"`)

Instead of a `url`, you will get the image data directly.

```json
{
  "created": 1715888889,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhE...[very long string of image data]...",
      "revised_prompt": "A highly detailed, photorealistic depiction of a small red panda..."
    }
  ]
}
```

This `b64_json` string can be saved to a file or displayed directly in an application.

-----

This video provides a more general overview of how the Grok 2 model, including its image generation capabilities, was announced and what it can do.