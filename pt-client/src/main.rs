// Cargo.toml deps: tokio, bytes, tokio-util, tracing, clap, anyhow
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt, AsyncBufReadExt, BufReader};
use tokio::task;
use tracing::{info, error};
use std::io::{self as stdio, Write};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // send logs to stderr so we don't pollute stdout (stdout is reserved for the protocol)
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .init();

    // bind fixed port so torrc Bridge line can reach us
    let listener = TcpListener::bind("127.0.0.1:3030").await?;
    let local_addr = listener.local_addr()?;

    // Read configuration lines from Tor on stdin until we hit an empty line.
    // Tor sends key=value lines on stdin and then a blank line to indicate the end of the config.
    let mut stdin_reader = BufReader::new(tokio::io::stdin());
    let mut line = String::new();
    loop {
        line.clear();
        let n = stdin_reader.read_line(&mut line).await?;
        if n == 0 {
            // EOF on stdin; break (Tor may have closed, but continue)
            break;
        }
        // stop when encountering the blank line that terminates the config block
        if line.trim().is_empty() {
            break;
        }
        // optional: you could parse config lines (TOR_PT_*) here if you need them
        // but do NOT print them to stdout; logging to stderr is fine.
    }

    // Print the exact handshake lines expected by Tor on stdout, flush immediately.
    println!("PROXY {} socks5 127.0.0.1:{}", "pt", local_addr.port());
    println!("PROXY DONE");
    stdio::stdout().flush()?; // ensure Tor sees the lines right away

    loop {
        let (inbound, peer) = listener.accept().await?;
        info!("accepted from {}", peer);
        // spawn handler
        task::spawn(async move {
            if let Err(e) = handle_conn(inbound).await {
                error!("connection error: {:?}", e);
            }
        });
    }
}

async fn handle_conn(mut inbound: TcpStream) -> anyhow::Result<()> {
    // Here you should read the SOCKS request (if using SOCKS) or assume Tor opens a raw stream.
    // For simplicity: connect to your PT server endpoint (obfuscated channel peer)
    let mut outbound = TcpStream::connect("198.51.100.1:1984").await?; // bridge/PT server

    // Now forward data both ways, applying transform hooks
    let (mut ri, mut wi) = inbound.split();
    let (mut ro, mut wo) = outbound.split();

    let client_to_server = async {
        let mut buf = [0u8; 4096];
        loop {
            let n = ri.read(&mut buf).await?;
            if n == 0 { break; }
            let out = transform_outgoing(&buf[..n]).await?;
            wo.write_all(&out).await?;
        }
        Ok::<(), anyhow::Error>(())
    };

    let server_to_client = async {
        let mut buf = [0u8; 4096];
        loop {
            let n = ro.read(&mut buf).await?;
            if n == 0 { break; }
            let out = transform_incoming(&buf[..n]).await?;
            wi.write_all(&out).await?;
        }
        Ok::<(), anyhow::Error>(())
    };

    tokio::try_join!(client_to_server, server_to_client)?;
    Ok(())
}

// TODO: implement your obfuscation here
async fn transform_outgoing(inb: &[u8]) -> anyhow::Result<Vec<u8>> {
    // placeholder: identity
    Ok(inb.to_vec())
}
async fn transform_incoming(inb: &[u8]) -> anyhow::Result<Vec<u8>> {
    Ok(inb.to_vec())
}
