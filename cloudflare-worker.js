// Cloudflare Worker to proxy Backblaze B2 with free bandwidth
// Deploy this at: https://workers.cloudflare.com/

export default {
	async fetch(request, env, ctx) {
		const url = new URL(request.url);
		
		// Decode the URL path to handle special characters (commas, parentheses, etc.)
		// B2 doesn't accept percent-encoded commas (%2C), so we need to decode before forwarding
		const decodedPath = decodeURIComponent(url.pathname);
		
		// Build the B2 URL with the decoded path
		const b2Url = `https://f003.backblazeb2.com/file/musiquiz-collections1${decodedPath}`;
		
		// Forward the request to B2
		const response = await fetch(b2Url, {
			method: request.method,
			headers: request.headers,
		});
		
		// Clone the response so we can modify headers
		const newResponse = new Response(response.body, response);
		
		// Add CORS headers
		newResponse.headers.set('Access-Control-Allow-Origin', '*');
		newResponse.headers.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
		newResponse.headers.set('Access-Control-Allow-Headers', '*');
		
		// Add caching for 1 year (audio files don't change)
		newResponse.headers.set('Cache-Control', 'public, max-age=31536000');
		
		return newResponse;
	},
};
