const http = require('http');

const PORT = process.env.PORT || 3333;

// In-memory storage
let pendingRequests = [];
let completedRequests = [];

// Dashboard HTML
function getDashboardHTML() {
    const pending = pendingRequests.filter(r => r.status === 'pending');
    const completed = completedRequests.slice(-10); // Last 10 completed
    
    return `<!DOCTYPE html>
<html>
<head>
    <title>SOS Emergency Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #ff6b6b; text-align: center; }
        .status { padding: 20px; border-radius: 10px; margin: 20px 0; }
        .pending { background: #ff6b6b33; border: 2px solid #ff6b6b; }
        .clear { background: #4ecdc433; border: 2px solid #4ecdc4; }
        .request { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ff6b6b; }
        .completed { border-left-color: #4ecdc4; opacity: 0.7; }
        .label { color: #888; font-size: 12px; }
        .value { font-size: 18px; font-weight: bold; }
        .time { color: #ffd93d; }
        .count { font-size: 48px; text-align: center; }
        .refresh { text-align: center; color: #666; font-size: 12px; }
        a { color: #4ecdc4; }
    </style>
</head>
<body>
    <h1> SOS Emergency Dashboard</h1>
    <p class="refresh">Auto-refreshes every 5 seconds | <a href="/pending">API: /pending</a></p>
    
    <div class="status ${pending.length > 0 ? 'pending' : 'clear'}">
        <div class="count">${pending.length}</div>
        <div style="text-align:center">${pending.length > 0 ? ' PENDING EMERGENCY REQUESTS' : ' No pending requests'}</div>
    </div>
    
    ${pending.length > 0 ? '<h2> Pending Requests</h2>' : ''}
    ${pending.map(r => `
        <div class="request">
            <div class="label">Request ID</div>
            <div class="value">${r.id}</div>
            <div class="label">Location</div>
            <div class="value"> ${r.latitude}, ${r.longitude}</div>
            <div class="label">User</div>
            <div class="value"> ${r.user_id}</div>
            <div class="label">Time</div>
            <div class="value time"> ${r.timestamp}</div>
        </div>
    `).join('')}
    
    ${completed.length > 0 ? '<h2> Recently Completed</h2>' : ''}
    ${completed.map(r => `
        <div class="request completed">
            <span class="value">${r.id}</span> - 
            <span> ${r.latitude}, ${r.longitude}</span> - 
            <span class="time">Completed: ${r.completed_at || 'N/A'}</span>
        </div>
    `).join('')}
    
    <hr style="border-color:#333;margin:30px 0">
    <h3> Test: Send SOS Request</h3>
    <pre style="background:#16213e;padding:15px;border-radius:8px;overflow-x:auto">
curl -X POST ${process.env.RENDER_EXTERNAL_URL || 'https://serverforridebooking.onrender.com'}/book-ride \\
  -H "Content-Type: application/json" \\
  -d '{"latitude": 17.385, "longitude": 78.486, "user_id": "test_user"}'
    </pre>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, GET, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    // Dashboard
    if (req.method === 'GET' && (req.url === '/' || req.url === '/dashboard')) {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(getDashboardHTML());
        return;
    }
    
    // POST /book-ride
    if (req.method === 'POST' && req.url === '/book-ride') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const request = {
                    id: Date.now().toString(),
                    latitude: data.latitude,
                    longitude: data.longitude,
                    user_id: data.user_id || 'emergency_user',
                    timestamp: new Date().toISOString(),
                    status: 'pending'
                };
                
                pendingRequests.push(request);
                
                console.log('\n EMERGENCY RIDE REQUEST!');
                console.log(` ${data.latitude}, ${data.longitude}`);
                console.log(` ${data.user_id || 'unknown'}`);
                console.log(` ${request.id}`);
                
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    success: true,
                    message: 'Ride request queued!',
                    request_id: request.id,
                    dashboard: 'https://serverforridebooking.onrender.com/'
                }));
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Invalid JSON' }));
            }
        });
        return;
    }
    
    // GET /pending
    if (req.method === 'GET' && req.url === '/pending') {
        const pending = pendingRequests.filter(r => r.status === 'pending');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(pending));
        return;
    }
    
    // POST /complete/:id
    if (req.method === 'POST' && req.url.startsWith('/complete/')) {
        const id = req.url.split('/complete/')[1];
        const idx = pendingRequests.findIndex(r => r.id === id);
        if (idx !== -1) {
            pendingRequests[idx].status = 'completed';
            pendingRequests[idx].completed_at = new Date().toISOString();
            completedRequests.push(pendingRequests[idx]);
            pendingRequests.splice(idx, 1);
            console.log(` Request ${id} completed`);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true }));
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Not found' }));
        }
        return;
    }
    
    // DELETE /clear
    if (req.method === 'DELETE' && req.url === '/clear') {
        pendingRequests = [];
        completedRequests = [];
        console.log(' Cleared');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true }));
        return;
    }
    
    // GET /clear (for easy browser clear)
    if (req.method === 'GET' && req.url === '/clear') {
        pendingRequests = [];
        completedRequests = [];
        res.writeHead(302, { 'Location': '/' });
        res.end();
        return;
    }
    
    // API info
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
        status: 'SOS Endpoint',
        dashboard: '/',
        endpoints: ['POST /book-ride', 'GET /pending', 'POST /complete/:id', 'GET /clear']
    }));
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(` SOS Server on port ${PORT}`);
    console.log(` Dashboard: http://localhost:${PORT}/`);
});
