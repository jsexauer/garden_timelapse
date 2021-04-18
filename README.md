# garden_timelapse
Simple app for a rapsberry pi to capture timelapse to watch the garden over time

## Setup
1. Create client_id_secret.json using clinet_id.json as a template.  API kye info
is from https://developers.google.com/photos/library/guides/get-started
2. Run app from desktop to create auth_session_secret.json
3. Copy both _secret files to pi.
4. Check pathing in app.

## Run at startup
Edit /etc/rc.local placing this line above exit 0 (the ampersand is important)

```
runuser -l pi -c 'python3 /home/pi/projects/garden_timelapse/main.py &'
```