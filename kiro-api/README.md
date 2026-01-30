# SOS Ride Booking Server

Simple endpoint server for triggering Kiro agent to book emergency Uber rides.

## Endpoint

**POST** `/book-ride`

```json
{
  "latitude": 17.38,
  "longitude": 78.45,
  "user_id": "user123"
}
```

## Deploy to Render

1. Fork this repo
2. Go to [render.com](https://render.com)
3. Create new Web Service → Connect GitHub
4. Select this repo
5. Done! You'll get a URL like `https://your-app.onrender.com`

## Local Testing

```bash
npm install
npm start
```

Then POST to `http://localhost:3333/book-ride`
