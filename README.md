# Face Attendance — Mobile + PC Ready Product

This is a responsive web application. The same application works from a PC browser and a mobile browser. It uses the device camera, while the Python server performs face recognition and stores attendance in SQLite.

## Start
### Windows
Double-click `run_windows.bat`, then open `http://localhost:5000` on the PC.

### Linux/macOS
Run `./run_linux.sh`, then open `http://localhost:5000`.

## Mobile
The phone and PC must be on the same Wi-Fi network. Start the app on the PC, find the PC's local IP address (for example `192.168.1.10`), then open `http://192.168.1.10:5000` on the phone.

**Camera security note:** Modern mobile browsers generally require HTTPS for camera access when the site is not localhost. For reliable phone deployment, put the app behind an HTTPS reverse proxy or deploy it to an HTTPS server.

## Workflow
Register Student -> Capture Face -> Register -> Train -> Start Camera -> Attendance.

The app prevents duplicate attendance for the same student on the same date and exports CSV/Excel reports.

## Academic project
This is suitable as a BCA final-year project prototype. For production use, add authentication, HTTPS, encrypted backups, access control, consent/privacy notices, and stronger face-recognition/liveness controls.
