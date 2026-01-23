# Podcast Distribution Guide

Now that you have your podcast pipeline running and generating an RSS feed, here is how to distribute it to the world.

## 1. Prepare Your Podcast Artwork

Podcast directories (Apple, Spotify, etc.) are very strict about artwork.
*   **Format**: JSON or PNG.
*   **Size**: Minimum 1400x1400 pixels, Maximum 3000x3000 pixels.
*   **Shape**: Perfect square.
*   **Color Space**: RGB.
*   **File Size**: Ideally under 500KB for faster loading, but strict limit is usually higher.

**Step 1:** Create your artwork and save it as `cover.png`.

**Step 2:** Upload it using the helper script:
```bash
python upload_artwork.py cover.png
```

**Step 3:** Update your `.env` file with the URL returned by the script:
```
PODCAST_IMAGE_URL=https://storage.googleapis.com/YOUR_BUCKET_NAME/cover.png
```

**Step 4:** Re-run `main.py` to update the `feed.xml` with the new image URL.
```bash
python main.py
```

## 2. Validate Your RSS Feed

Before submitting, ensure your feed is valid.
1.  **Get your Feed URL**: This is printed at the end of `main.py` (e.g., `https://storage.googleapis.com/YOUR_BUCKET_NAME/feed.xml`).
2.  **Use a Validator**:
    *   [Cast Feed Validator](https://castfeedvalidator.com/) (Recommended - envisions how it looks in apps)
    *   [W3C Feed Validation Service](https://validator.w3.org/feed/) (Strict technical validation)

Fix any errors reported by these tools before proceeding.

## 3. Submit to Podcast Directories

You only need to submit your RSS feed URL once to each directory. They will automatically check your feed for new episodes periodically.

### Apple Podcasts (iTunes)
1.  Go to [Apple Podcasts Connect](https://podcastsconnect.apple.com/).
2.  Log in with your Apple ID.
3.  Click the **(+)** button and select **New Show**.
4.  Select "Add a show with an RSS feed".
5.  Paste your **Feed URL**.
6.  Apple will preview your show. Fix any metadata issues if needed.
7.  Click **Submit**. Approval can take 24-72 hours.

### Spotify
1.  Go to [Spotify for Podcasters](https://podcasters.spotify.com/).
2.  Log in or create an account.
3.  Click "Get Started" -> "I have a podcast".
4.  Paste your **Feed URL**.
5.  Verify ownership (they will send a code to the email in your RSS feed - `PODCAST_EMAIL` in `.env`).
6.  Add category info and submit. It's usually live within a few hours.

### YouTube Music (formerly Google Podcasts)
1.  Go to [YouTube Studio](https://studio.youtube.com/).
2.  Click **Create** -> **New podcast**.
3.  Select "Submit RSS feed".
4.  Paste your **Feed URL**.
5.  Follow the verification steps.

### Amazon Music / Audible
1.  Go to [Amazon Music for Podcasters](https://podcasters.amazon.com/).
2.  Add your RSS feed.

### Other Apps (Overcast, Pocket Casts, etc.)
Most other apps pull from the Apple Podcasts directory. Once you are on Apple, you will eventually appear everywhere else.

## 4. Troubleshooting

*   **Permissions Error**: If validators can't read your feed, ensure your GCS bucket or file is **Public**.
    *   Go to Google Cloud Console -> Storage -> Buckets.
    *   Check the "Permissions" tab and ensure `allUsers` has `Storage Object Viewer` role.
*   **Image Not Updating**: Podcast apps cache images aggressively. If you change your artwork, you might need to change the filename (e.g., `cover-v2.png`) to force an update.
*   **New Episodes Not Showing**: It can take up to 24 hours for directories to detect a new episode in your feed.

