import os
import requests


class TikTokClient:
    """Minimal TikTok uploader with a safe dry-run mode.

    This class supports two modes:
    - dry_run=True: no network calls; returns a fake response and logs actions.
    - dry_run=False: attempts to upload to an `upload_url` (env `TIKTOK_UPLOAD_URL`) and
      then call a `publish_url` (env `TIKTOK_PUBLISH_URL`).

    Note: TikTok's official Content Publishing API requires OAuth flow and app approval.
    To use real uploads, obtain the proper upload/publish endpoints from TikTok's API
    responses (or implement the OAuth flow) and set `TIKTOK_UPLOAD_URL` and
    `TIKTOK_PUBLISH_URL` environment variables. This client keeps the real upload
    implementation intentionally generic so you can plug in the exact endpoints.
    """

    def __init__(self, access_token=None, dry_run=True, upload_url=None, publish_url=None):
        self.dry_run = dry_run
        self.access_token = access_token or os.getenv('TIKTOK_ACCESS_TOKEN')
        self.upload_url = upload_url or os.getenv('TIKTOK_UPLOAD_URL')
        self.publish_url = publish_url or os.getenv('TIKTOK_PUBLISH_URL')

    def upload_video(self, video_path, title=None, description=None):
        if self.dry_run:
            print(f"[TikTokClient:dry-run] Would upload {video_path} with title={title}")
            return {"status": "dry-run", "video_id": "dryrun-1234"}

        if not self.upload_url:
            raise RuntimeError('TIKTOK_UPLOAD_URL not configured; cannot perform real upload')

        with open(video_path, 'rb') as fh:
            files = {'video': (os.path.basename(video_path), fh, 'video/mp4')}
            data = {}
            if self.access_token:
                data['access_token'] = self.access_token
            if title:
                data['title'] = title
            if description:
                data['description'] = description

            resp = requests.post(self.upload_url, files=files, data=data)
            resp.raise_for_status()
            upload_resp = resp.json()

        # Try to extract a media_id from common response shapes
        media_id = None
        if isinstance(upload_resp, dict):
            media_id = upload_resp.get('media_id') or (upload_resp.get('data') or {}).get('media_id')

        if not media_id:
            # If upload endpoint returns a URL to PUT to, return the response instead
            return {"status": "uploaded", "response": upload_resp}

        # If publish_url is configured, call it to publish the uploaded media
        if self.publish_url:
            publish_payload = {'media_id': media_id}
            if self.access_token:
                publish_payload['access_token'] = self.access_token
            if title:
                publish_payload['title'] = title
            if description:
                publish_payload['description'] = description

            pub = requests.post(self.publish_url, json=publish_payload)
            pub.raise_for_status()
            return pub.json()

        return {"status": "uploaded", "media_id": media_id}
