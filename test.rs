use reqwest::Client;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Tor SOCKS5 proxy address (change if your tor uses a different host:port)
    let socks_proxy = "socks5h://127.0.0.1:9050";

    // Build reqwest client with proxy
    let proxy = reqwest::Proxy::all(socks_proxy)?;

    let client = Client::builder()
        .proxy(proxy)
        // sensible timeouts for local dev
        .timeout(Duration::from_secs(20))
        // set a browser-like UA to avoid trivial blocks
        .user_agent("Mozilla/5.0 (compatible; tor-check/1.0; +https://example.invalid/)")
        .build()?;

    // Target: check.torproject.org. Use HTTPS so we validate TLS via rustls.
    let url = "https://check.torproject.org/";

    println!("Requesting {} via {}", url, socks_proxy);

    let resp = client.get(url).send().await?;

    println!("Status: {}", resp.status());

    // Read full body (for small pages like check.torproject.org it's fine).
    let body = resp.text().await?;

    // Print first N chars to keep terminal neat; also check for the "Congratulations" text.
    const MAX_PRINT: usize = 4000;
    let to_print = if body.len() > MAX_PRINT {
        &body[..MAX_PRINT]
    } else {
        &body
    };

    println!("--- body (truncated to {} bytes) ---", to_print.len());
    println!("{}", to_print);
    println!("--- end ---");

    // Quick check: look for the Tor success string (not guaranteed forever, but common).
    if body.contains("Congratulations. This browser is configured to use Tor") {
        println!("Detected success message: traffic went through Tor.");
    } else {
        println!("No explicit Tor success string found. Inspect the HTML above.");
    }

    Ok(())
}
